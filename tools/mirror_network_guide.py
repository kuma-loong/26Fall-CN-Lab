#!/usr/bin/env python3
"""Mirror the campus Sphinx guide, including documents absent from its TOC.

Uses only Python's standard library. Download into a NEW directory, validate it,
then replace the previous snapshot separately. Proxy environment variables are
intentionally ignored: the source is served on the campus network.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import quote, unquote, urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import ProxyHandler, Request, build_opener
import zlib


CSS_URL = re.compile(r'url\(\s*[\'"]?([^\s\)\'\"]+)[\'"]?\s*\)', re.I)
CSS_IMPORT = re.compile(r'@import\s+[\'"]([^\'"]+)[\'"]', re.I)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('name'):
            self.ids.add(attrs['name'])
        for key in ('href', 'src', 'poster') + (('data',) if tag == 'object' else ()):
            if attrs.get(key):
                self.links.append(attrs[key])
        if attrs.get('srcset'):
            self.links.extend(part.strip().split()[0]
                              for part in attrs['srcset'].split(',') if part.strip())
        if attrs.get('style'):
            self.links.extend(CSS_URL.findall(attrs['style']))
        # Sphinx loads its search index dynamically instead of using a src tag.
        if tag == 'script' and attrs.get('src', '').endswith('searchtools.js'):
            self.links.append('searchindex.js')

    handle_startendtag = handle_starttag


def inventory_docs(data):
    lines = zlib.decompress(data.split(b'\n', 4)[4]).decode().splitlines()
    return {line.split(maxsplit=4)[3] for line in lines if ' std:doc ' in line}


def search_docs(data):
    match = re.search(r'"?docnames"?\s*:\s*(\[.*?\])', data.decode())
    return {name + '.html' for name in json.loads(match[1])}


def write_catalog(output):
    rows = []
    lines = zlib.decompress((output / 'objects.inv').read_bytes().split(b'\n', 4)[4]).decode().splitlines()
    for line in lines:
        if ' std:doc ' not in line:
            continue
        name, _, _, path, title = line.split(maxsplit=4)
        title = name if title == '-' else title
        rows.append(f'<tr><td><a href="{escape(path, quote=True)}">{escape(title)}</a></td>'
                    f'<td><code>{escape(path)}</code></td></tr>')
    (output / 'mirror-catalog.html').write_text(
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>指导书离线全量目录</title>'
        '<style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 16px;line-height:1.6}'
        'table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:8px;border-bottom:1px solid #ddd}'
        'a{color:#17679b}code{overflow-wrap:anywhere}</style>'
        '<h1>指导书离线全量目录</h1>'
        '<p>此目录由抓取工具根据官网 Sphinx 文档清单生成，包含全部 97 篇文档，'
        '其中包括官网保留的历史实验和旧版页面。本学期实验安排以'
        '<a href="index.html">官网首页导航</a>为准。</p>'
        '<p><a href="search.html">搜索文档</a> · '
        '<a href="mirror-manifest.json">抓取来源与校验清单</a></p>'
        '<table><thead><tr><th>标题</th><th>路径</th></tr></thead><tbody>'
        + '\n'.join(rows) + '</tbody></table></html>\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--base-url', default='https://comp-network.p.cs-lab.top/')
    parser.add_argument('--workers', default=4, type=int)
    parser.add_argument('--source-repository', default='https://git.cs-lab.top/cslab/comp-network',
                        help='Official repository used to recover broken image URLs')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('--output must be a new directory (existing snapshots are never overwritten)')
    args.output.mkdir(parents=True)
    base = args.base_url.rstrip('/') + '/'
    origin = urlsplit(base)
    repository = urlsplit(args.source_repository)
    entries, failures, externals = {}, {}, set()
    pending = {urljoin(base, p) for p in ('index.html', 'search.html', 'genindex.html',
                                        'objects.inv', 'searchindex.js')}
    seen, variants = set(), {}
    inventory, search = set(), set()
    started = datetime.now(timezone.utc).isoformat()

    def local_path(url):
        path = unquote(urlsplit(url).path).lstrip('/')
        if not path or path.endswith('/'):
            path += 'index.html'
        if '..' in Path(path).parts or '\\' in path:
            raise ValueError('Unsafe URL path: ' + url)
        return path

    def resolve(parent, ref):
        if not ref or ref.startswith(('data:', 'javascript:', 'mailto:', 'tel:')):
            return None
        url = urldefrag(urljoin(parent, ref))[0]
        parts = urlsplit(url)
        if parts.scheme not in ('http', 'https'):
            return None
        if parts.netloc != origin.netloc:
            externals.add(url)
            return None
        # Scheme aliases on this same host use the canonical campus HTTPS URL.
        return urlunsplit((origin.scheme, origin.netloc,
                           quote(parts.path or '/', safe='/%:@!$&\'()*+,;=-._~'),
                           quote(parts.query, safe='=&%/:?+'), ''))

    def fetch(url):
        for attempt in range(3):
            try:
                opener = build_opener(ProxyHandler({}))
                request = Request(url, headers={'User-Agent': 'CampusGuideOfflineMirror/1.0',
                                                'Accept-Encoding': 'identity'})
                with opener.open(request, timeout=40) as response:
                    final = response.geturl()
                    if urlsplit(final).netloc != urlsplit(url).netloc:
                        raise ValueError('Unexpected cross-origin redirect: ' + final)
                    return url, response.read(), dict(response.headers), None
            except Exception as exc:
                if attempt == 2:
                    return url, None, {}, str(exc)
                time.sleep(attempt + 1)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        while pending:
            batch = sorted(pending - seen)
            pending = set()
            seen.update(batch)
            if not batch:
                break
            print(f'Fetching {len(batch)} URLs; {len(entries)} files saved', flush=True)
            for url, data, headers, error in pool.map(fetch, batch):
                if error:
                    failures[url] = error
                    continue
                path = local_path(url)
                digest = hashlib.sha256(data).hexdigest()
                if path in entries and entries[path]['sha256'] != digest:
                    raise RuntimeError('Different responses map to the same file: ' + url)
                target = args.output / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                variants.setdefault(path, set()).add(url)
                entries[path] = {'urls': sorted(variants[path]), 'bytes': len(data),
                                 'sha256': digest, 'content_type': headers.get('Content-Type'),
                                 'last_modified': headers.get('Last-Modified'),
                                 'etag': headers.get('Etag', headers.get('ETag'))}
                refs = []
                if path.endswith('.html'):
                    refs = Page(data.decode('utf-8')).links
                elif path.endswith('.css'):
                    text = data.decode('utf-8')
                    refs = CSS_URL.findall(text) + CSS_IMPORT.findall(text)
                elif path == 'objects.inv':
                    inventory = inventory_docs(data)
                    refs = list(inventory)
                elif path == 'searchindex.js':
                    search = search_docs(data)
                    refs = list(search)
                elif path.endswith('.js'):
                    # Include Sphinx scripts loaded at runtime (e.g. language data).
                    refs = re.findall(r'(?:[\'"])([^\'"\s]+\.(?:js|css))(?:[\'"])',
                                      data.decode('utf-8'))
                    # Sphinx's search loader resolves _static/* from the HTML page.
                    refs = [urljoin(base, ref) if ref.startswith('_static/') else ref
                            for ref in refs]
                for ref in refs:
                    resolved = resolve(url, ref)
                    if resolved and resolved not in seen:
                        pending.add(resolved)

    # Some archived pages use lowercase image extensions even though the source
    # files have uppercase extensions. Recover only a unique case-insensitive
    # match in that exact document's source directory, pinned to a commit and
    # checked against its Git blob hash. The HTML and RST remain byte-identical.
    recoveries = []
    image_failures = {url: error for url, error in failures.items()
                      if error == 'HTTP Error 404: Not Found'
                      and Path(local_path(url)).suffix.lower() in ('.jpg', '.png', '.svg', '.gif')}
    if image_failures:
        api = f'{repository.scheme}://{repository.netloc}/api/v1/repos{repository.path}'
        _, metadata, _, error = fetch(api)
        if error:
            raise RuntimeError('Cannot inspect official source repository: ' + error)
        branch = json.loads(metadata)['default_branch']
        _, data, _, error = fetch(api + '/git/trees/' + quote(branch, safe='') + '?recursive=true')
        if error:
            raise RuntimeError('Cannot inspect source tree: ' + error)
        tree = json.loads(data)
        if tree.get('truncated'):
            raise RuntimeError('Source tree response is truncated')
        for url in image_failures:
            path = local_path(url)
            source_path = 'source/' + path.split('/')[0] + '/' + Path(path).name
            matches = [entry for entry in tree['tree'] if entry['type'] == 'blob'
                       and entry['path'].casefold() == source_path.casefold()]
            if len(matches) != 1:
                continue
            entry = matches[0]
            source_url = args.source_repository.rstrip('/') + '/raw/commit/' + tree['sha'] + '/' + quote(entry['path'])
            _, data, headers, error = fetch(source_url)
            if error:
                raise RuntimeError('Cannot recover source image: ' + error)
            blob_hash = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if blob_hash != entry['sha']:
                raise RuntimeError('Source image Git blob checksum mismatch: ' + source_url)
            target = args.output / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            entries[path] = {'urls': [source_url], 'bytes': len(data),
                             'sha256': hashlib.sha256(data).hexdigest(),
                             'content_type': headers.get('Content-Type'),
                             'git_blob_sha1': blob_hash}
            recoveries.append({'path': path, 'upstream_broken_url': url,
                               'source_url': source_url, 'source_commit': tree['sha'],
                               'source_path': entry['path'], 'git_blob_sha1': blob_hash})
            del failures[url]

    missing, anchors, ids = [], [], {}
    for path in entries:
        if path.endswith('.html'):
            ids[path] = Page((args.output / path).read_text()).ids
    for path in entries:
        if not path.endswith(('.html', '.css')):
            continue
        text = (args.output / path).read_text()
        refs = Page(text).links if path.endswith('.html') else CSS_URL.findall(text) + CSS_IMPORT.findall(text)
        for ref in refs:
            resolved = resolve(urljoin(base, path), ref)
            if not resolved:
                continue
            dest = local_path(resolved)
            if dest not in entries:
                missing.append({'from': path, 'ref': ref, 'target': dest})
            fragment = unquote(urlsplit(urljoin(urljoin(base, path), ref)).fragment)
            if fragment and dest in ids and fragment not in ids[dest]:
                anchors.append({'from': path, 'ref': ref, 'target': dest})
    missing_docs = sorted((inventory | search) - entries.keys())
    report = {'source': base, 'started_at_utc': started,
              'finished_at_utc': datetime.now(timezone.utc).isoformat(),
              'proxy': 'disabled; direct campus network',
              'preservation': 'Original response bytes; no content or link rewriting',
              'generated_files': ['mirror-catalog.html', 'mirror-manifest.json'],
              'files': len(entries), 'bytes': sum(e['bytes'] for e in entries.values()),
              'html_pages': len(ids), 'inventory_documents': len(inventory),
              'search_documents': len(search), 'inventory_search_agree': inventory == search,
              'missing_documents': missing_docs, 'failed_requests': failures,
              'source_image_recoveries': recoveries,
              'missing_local_links': missing, 'upstream_broken_anchors': anchors,
              'external_links': sorted(externals), 'entries': dict(sorted(entries.items()))}
    (args.output / 'mirror-manifest.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    write_catalog(args.output)
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ('entries', 'external_links', 'upstream_broken_anchors',
                                   'source_image_recoveries')},
                     ensure_ascii=False, indent=2), flush=True)
    if failures or missing or missing_docs or inventory != search:
        raise SystemExit('Mirror incomplete; see mirror-manifest.json. Previous snapshot is untouched.')


if __name__ == '__main__':
    main()
