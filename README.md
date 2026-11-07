# 26Fall-CN-Lab

哈尔滨工业大学（深圳）2026 秋季计算机网络实验。

| 实验 | 内容 | 状态 |
| --- | --- | --- |
| Lab 2 | 以太网帧收发、首部处理、最小帧填充 | 完成 |
| Lab 3 | ARP 请求/响应、地址缓存、待发送报文缓存 | 完成 |

代码在 [`net-lab/src/`](net-lab/src/)，基于[课程框架](https://git.cs-lab.top/cslab/net-lab.git)；其余协议保留初始实现。课程测试及输入数据保持原样，另提供逐字节 pcap 核对工具。

## 实验环境

使用 [Docker 环境](docker/compose.yaml)：Ubuntu 22.04、GCC、CMake、libpcap、GDB、tcpdump/tshark。源码挂载到容器内的 `/app`。

首次启动（宿主机需已安装 Docker 和 Compose）：

```sh
cd docker
printf 'LAB_UID=%s\nLAB_GID=%s\n' "$(id -u)" "$(id -g)" > .env
docker compose up -d --build
docker compose exec lab bash
```

## 快速运行

在容器的 `/app` 中执行：

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --target eth_in eth_out arp_test -j2
ctest --test-dir build -R '^(eth_in|eth_out|arp_test)$' --output-on-failure
python3 tools/verify_pcaps.py
```

三项组件测试及报文字节核对均通过。后续在线实验需将非 `TEST` 分支 IP 设为 `192.168.254.2`，并在容器内运行 `setup-net-lab`。

## 材料与提交

- [离线指导书](comp-network-guide/index.html) / [全量目录](comp-network-guide/mirror-catalog.html)，更新工具为 [`tools/mirror_network_guide.py`](tools/mirror_network_guide.py)。
- 协议代码提交后，在仓库根目录执行 `python3 tools/export_lab_patch.py`，生成相对课程初始版本的 `private/submissions/commit.patch`。
- 报告按课程统一模板填写，目前覆盖 Lab 2、3；最终在 Lab 9 后统一提交。报告、截图、日志、模板和提交包均保存在被 Git 忽略的 `private/`，不上传 GitHub。
