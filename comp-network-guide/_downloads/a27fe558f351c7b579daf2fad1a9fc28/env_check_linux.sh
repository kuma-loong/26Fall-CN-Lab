#!/usr/bin/env bash

set -u

ok() {
  printf '[OK]   %s\n' "$1"
}

warn() {
  printf '[WARN] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
}

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    ok "$1 found at $(command -v "$1")"
  else
    fail "$1 not found"
  fi
}

show_offload() {
  local iface="$1"
  if ! command -v ethtool >/dev/null 2>&1; then
    warn "ethtool not found; cannot inspect offload state"
    return
  fi

  if ! ip link show "$iface" >/dev/null 2>&1; then
    warn "$iface does not exist"
    return
  fi

  ok "$iface offload summary:"
  ethtool -k "$iface" 2>/dev/null | grep -E 'rx-checksumming|tx-checksum|generic-receive-offload|generic-segmentation-offload' | sed 's/^/       /'
}

printf '=== Net-Lab Linux/WSL Environment Check ===\n'

check_cmd gcc
check_cmd cmake
check_cmd gdb
check_cmd ip
check_cmd ethtool

if command -v sudo >/dev/null 2>&1; then
  ok "sudo found"
else
  warn "sudo not found; root-required setup steps may fail"
fi

if ip link show veth0 >/dev/null 2>&1; then
  ok "veth0 exists"
else
  warn "veth0 not found"
fi

if ip link show veth1 >/dev/null 2>&1; then
  ok "veth1 exists"
else
  warn "veth1 not found"
fi

if ip route show | grep -q ' dev veth1'; then
  ok "Found at least one route using veth1"
  ip route show | grep ' dev veth1' | sed 's/^/       /'
else
  warn "No route through veth1 found; confirm setup_veth.sh has been executed"
fi

show_offload veth0
show_offload veth1

printf '\nManual checks still required:\n'
printf '  1. Confirm include/config.h uses the same STACK_IP configured in setup_veth.sh.\n'
printf '  2. Confirm your experiment subnet is routed to veth1.\n'
printf '  3. If using WSL2, confirm ip/ethtool/sysctl all work correctly in the current distro.\n'
