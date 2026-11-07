ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

ARG LAB_UID=1000
ARG LAB_GID=1000

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential ca-certificates cmake curl ethtool gdb gdbserver git \
        iproute2 iputils-ping libcap-dev libncurses-dev libpcap-dev \
        libreadline-dev netcat-openbsd python3 sudo tcpdump tshark vim-tiny \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "${LAB_GID}" lab \
    && useradd --uid "${LAB_UID}" --gid "${LAB_GID}" --create-home --shell /bin/bash lab \
    && printf 'lab ALL=(ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/lab \
    && chmod 0440 /etc/sudoers.d/lab

COPY setup-net-lab /usr/local/bin/setup-net-lab
RUN chmod 0755 /usr/local/bin/setup-net-lab

USER lab
WORKDIR /app
CMD ["/bin/bash"]
