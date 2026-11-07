#!/usr/bin/env python3
"""Export committed protocol implementations with paths relative to net-lab."""

import argparse
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'private/submissions/commit.patch')
    args = parser.parse_args()
    if git('diff', 'HEAD', '--', 'net-lab/src'):
        parser.error('Commit protocol source changes before exporting the patch.')
    patch = git('diff', '--binary', '--full-index', '--relative=net-lab',
                'refs/tags/course/net-lab-base', 'HEAD', '--', 'net-lab/src')
    if not patch:
        parser.error('No protocol changes relative to course/net-lab-base.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patch)
    print(f'Exported {args.output}')
    print(patch.decode().splitlines()[0])


if __name__ == '__main__':
    main()
