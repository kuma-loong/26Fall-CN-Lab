#!/usr/bin/env python3
"""Compare packet contents with course samples, ignoring capture timestamps."""

import argparse
from pathlib import Path
import struct


def read_pcap(path):
    data = path.read_bytes()
    endian = {b'\xd4\xc3\xb2\xa1': '<', b'\xa1\xb2\xc3\xd4': '>',
              b'\x4d\x3c\xb2\xa1': '<', b'\xa1\xb2\x3c\x4d': '>'}[data[:4]]
    link_type = struct.unpack_from(endian + 'I', data, 20)[0]
    packets = []
    offset = 24
    while offset < len(data):
        _, _, captured, original = struct.unpack_from(endian + 'IIII', data, offset)
        offset += 16
        packet = data[offset:offset + captured]
        if len(packet) != captured:
            raise ValueError(f'{path}: truncated packet')
        packets.append((original, packet))
        offset += captured
    return link_type, packets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'testing/data')
    parser.add_argument('tests', nargs='*', default=['eth_in', 'eth_out', 'arp_test'])
    args = parser.parse_args()
    failed = False
    for name in args.tests:
        folder = args.data_root / name
        actual_type, actual = read_pcap(folder / 'out.pcap')
        expected_type, expected = read_pcap(folder / 'demo_out.pcap')
        if (actual_type, actual) != (expected_type, expected):
            print(f'{name}: FAIL (actual {len(actual)}, expected {len(expected)} packets)')
            for number, (got, want) in enumerate(zip(actual, expected), 1):
                if got != want:
                    print(f'  packet {number}: content or original length differs')
                    break
            failed = True
        else:
            size = sum(len(packet) for _, packet in actual)
            print(f'{name}: PASS ({len(actual)} packets, {size} bytes match exactly)')
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
