#!/bin/bash

# Configuration
STACK_IP="192.168.254.2"
NET_PREFIX="192.168.254"
VETH_USER="veth0"
VETH_KERNEL="veth1"

VETH_USER_IP="${NET_PREFIX}.3/24"
VETH_KERNEL_IP="${NET_PREFIX}.1/24"
SUBNET="${NET_PREFIX}.0/24"

echo "=== Setting up veth pair for Net-Lab ==="
echo "Configuration:"
echo "  Stack IP:   $STACK_IP"
echo "  Prefix:     $NET_PREFIX"
echo "  Interfaces: $VETH_USER <-> $VETH_KERNEL"

if ip link show "$VETH_USER" > /dev/null 2>&1; then
    echo "Removing existing $VETH_USER..."
    sudo ip link del "$VETH_USER"
fi

echo "Creating veth pair: $VETH_USER <-> $VETH_KERNEL"
sudo ip link add "$VETH_USER" type veth peer name "$VETH_KERNEL"

echo "Bringing up interfaces..."
sudo ip link set "$VETH_USER" up
sudo ip link set "$VETH_KERNEL" up

echo "Assigning IP $VETH_USER_IP to $VETH_USER"
sudo ip addr add "$VETH_USER_IP" dev "$VETH_USER"

echo "Assigning IP $VETH_KERNEL_IP to $VETH_KERNEL"
sudo ip addr add "$VETH_KERNEL_IP" dev "$VETH_KERNEL"

echo "Deleting kernel route for $VETH_USER..."
sudo ip route del "$SUBNET" dev "$VETH_USER"

echo "Disabling checksum offload..."
sudo ethtool -K "$VETH_USER" rx off tx off
sudo ethtool -K "$VETH_KERNEL" rx off tx off

echo "Configuring IPv6..."
sudo sysctl -w "net.ipv6.conf.$VETH_USER.disable_ipv6=0" > /dev/null
sudo sysctl -w "net.ipv6.conf.$VETH_KERNEL.disable_ipv6=0" > /dev/null

VETH_KERNEL_IP6="fd00::1/64"
echo "Assigning IPv6 $VETH_KERNEL_IP6 to $VETH_KERNEL"
sudo ip -6 addr add "$VETH_KERNEL_IP6" dev "$VETH_KERNEL"

echo "Disabling ARP on $VETH_USER..."
sudo ip link set dev "$VETH_USER" arp off

echo "=== Setup Complete ==="
echo "User Stack Interface: $VETH_USER"
echo "Kernel Interface:     $VETH_KERNEL (IP: $VETH_KERNEL_IP)"
echo "UDP/TCP Test:         nc $STACK_IP 60000"
echo "Web Test:             curl http://$STACK_IP/"
