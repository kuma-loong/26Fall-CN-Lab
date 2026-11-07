# 26Fall-CN-Lab

哈尔滨工业大学（深圳）2026 年秋季计算机网络课程实验仓库。

## 仓库内容

- [实验指导书](comp-network-guide/index.html)：课程实验指导书的离线网页，下载仓库后可用浏览器打开。
- [指导书文本源文件](comp-network-guide/_sources/)：可直接查看的实验说明。
- [离线全量目录](comp-network-guide/mirror-catalog.html)：包括官网索引中保留的历史页面；本学期实验以指导书首页导航为准。
- 实验实现、设备配置与实验记录随课程进度补充。

## 离线指导书

2026-11-07 通过本机校内网络重新抓取 [课程官网](https://comp-network.p.cs-lab.top/index.html)。使用官网 `objects.inv` 与 `searchindex.js` 交叉核对，收录全部 97 篇文档及搜索、索引页，共 99 个原站 HTML 页面、97 份 RST 文本源文件，以及图片、字体、样式、脚本和站内下载附件。

旧版遗漏了 42 篇文档；已有的 55 份 RST 文本与本次线上版本一致。本次保留网页及文本原文，并从官网链接的源码仓库恢复了 12 个因扩展名大小写错误而失效的图片路径。每个文件的来源、SHA-256、图片恢复记录见 [抓取清单](comp-network-guide/mirror-manifest.json)。源码仓库、网盘、视频等外部链接仍需联网访问。

可以直接打开 `comp-network-guide/index.html` 阅读。使用完整搜索功能（含结果摘要）时，请在仓库根目录启动本地服务：

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory comp-network-guide
```

然后访问 <http://127.0.0.1:8000/>。浏览器逐页检查已覆盖 99 个页面及 877 处图片引用，未发现缺图或缺失样式。官网原有的一处失效锚点 `appendix-g/lab7.html → appendix-b/1win.html#main` 保持原文，目标页面可以正常打开，详情记录在抓取清单中。

后续更新可运行以下命令（需要校内网络，脚本自动绕过环境代理；输出目录必须不存在）：

```sh
python3 tools/mirror_network_guide.py --output /tmp/comp-network-guide-new
```

脚本下载后会检查文档覆盖、站内链接和资源完整性，校验通过后再用新目录替换当前快照。

## 实验导航

| 实验 | 指导书 |
| --- | --- |
| 实验 1：VLAN 与接口模式配置 | [华为交换机配置与实验步骤](comp-network-guide/_sources/lab1-vlan/0huawei.rst.txt) |

## 课程索引

[HITsz-CS-Labs](https://github.com/kuma-loong/HITsz-CS-Labs)
