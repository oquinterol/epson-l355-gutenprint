#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Inspect framed ESC/P2 graphics commands using public Gutenprint documentation.

Skip the preamble, walk framed commands, and advance over raster payloads using
declared sizes and bounded PackBits lengths. Coverage ends at the remote trailer.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

MAX_DECODED_BAND = 64 * 1024 * 1024


def skip_packbits(data, offset, expected):
    if expected < 0 or expected > MAX_DECODED_BAND:
        raise ValueError('Unreasonable decoded raster band length')
    produced = 0
    while produced < expected:
        if offset >= len(data):
            raise ValueError('Truncated PackBits control')
        control = data[offset]
        offset += 1
        if control <= 127:
            count = control + 1
            offset += count
        elif control >= 129:
            count = 257 - control
            offset += 1
        else:
            count = 0
        if offset > len(data):
            raise ValueError('Truncated PackBits payload')
        produced += count
        if produced > expected:
            raise ValueError('PackBits exceeds declared band length')
    return offset


def inspect(data):
    start = data.find(b'\x1b(G\x01\x00\x01')
    if start < 0:
        raise ValueError('No supported graphics-body start found')
    result = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
              'preamble_bytes_not_decoded': start, 'graphics_start_is_pattern_inference': True,
              'raster_bands': 0, 'page_ejects_in_graphics_body': 0, 'first_parameters': {},
              'decoded_raster_bytes': 0}
    commands = Counter()
    channels = Counter()
    depths = Counter()
    compressions = Counter()
    offset = start
    status = 'end-of-file'
    while offset < len(data):
        if data[offset] in (0, 10, 13):
            offset += 1
            continue
        if data[offset] == 12:
            result['page_ejects_in_graphics_body'] += 1
            offset += 1
            continue
        if data[offset:offset+2] == b'\x1bi':
            if offset + 9 > len(data):
                raise ValueError('Truncated ESC i header')
            color, compression, bits = data[offset+2:offset+5]
            rowbytes = int.from_bytes(data[offset+5:offset+7], 'little')
            rows = int.from_bytes(data[offset+7:offset+9], 'little')
            size = rowbytes * rows
            if size > MAX_DECODED_BAND or bits not in (1, 2, 4, 8):
                raise ValueError('Unsupported raster dimensions or bit depth')
            offset += 9
            if compression == 0:
                offset += size
                if offset > len(data):
                    raise ValueError('Truncated uncompressed band')
            elif compression == 1:
                offset = skip_packbits(data, offset, size)
            else:
                status = 'unsupported-raster-compression-' + str(compression)
                break
            result['raster_bands'] += 1
            result['decoded_raster_bytes'] += size
            channels[str(color)] += 1
            depths[str(bits)] += 1
            compressions[str(compression)] += 1
            continue
        if data[offset:offset+2] == b'\x1b(':
            if offset + 5 > len(data):
                raise ValueError('Truncated parenthesized command')
            cmd = chr(data[offset+2])
            length = int.from_bytes(data[offset+3:offset+5], 'little')
            end = offset + 5 + length
            if end > len(data):
                raise ValueError('Truncated parenthesized payload')
            if cmd == 'R':
                status = 'remote-trailer-not-decoded'
                break
            payload = data[offset+5:end]
            commands['ESC (' + cmd] += 1
            result['first_parameters'].setdefault(cmd, payload.hex())
            if cmd == 'U' and len(payload) == 5 and 'positioning_units_per_inch' not in result:
                base = int.from_bytes(payload[3:], 'little')
                result['positioning_units_per_inch'] = {
                    key: base / divisor if divisor else None
                    for key, divisor in zip(('page', 'vertical', 'horizontal'), payload[:3])}
            offset = end
            continue
        if data[offset:offset+1] == b'\x1b' and offset+1 < len(data):
            cmd = chr(data[offset+1])
            length = {'@': 2, 'U': 3, '$': 4, '\\': 4, 'r': 3}.get(cmd)
            if length is not None and offset+length <= len(data):
                commands['ESC ' + cmd] += 1
                offset += length
                continue
        status = 'unknown-command-or-trailer'
        break
    result.update(parsed_until_offset=offset, stopped_because=status,
                  command_counts=dict(commands), channel_code_band_counts=dict(channels),
                  bits_per_pixel_band_counts=dict(depths), compression_band_counts=dict(compressions),
                  complete_protocol_validation=False)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    reports = {}
    for path in args.files:
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('Input too large for bounded inspector')
        reports[path.name] = inspect(path.read_bytes())
    print(json.dumps(reports, indent=2, sort_keys=True))
