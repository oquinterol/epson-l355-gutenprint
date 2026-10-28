# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stream', ROOT / 'tools/inspect_stream.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
START = b'\x1b(G\x01\x00\x01'
TRAILER = b'\x1b(R\x08\x00\x00REMOTE1'


def band(data, compression=0, width=None):
    width = len(data) if width is None else width
    return b'\x1bi\x00' + bytes([compression, 2]) + width.to_bytes(2, 'little') + b'\x01\x00' + data


class StreamTests(unittest.TestCase):
    def test_command_like_bytes_in_raw_raster_are_not_commands(self):
        report = s.inspect(START + band(b'\x1bi\x1b(G\x1b(R') + b'\x0c' + TRAILER)
        self.assertEqual(report['raster_bands'], 1)
        self.assertEqual(report['page_ejects_in_graphics_body'], 1)
        self.assertEqual(report['stopped_because'], 'remote-trailer-not-decoded')
        self.assertFalse(report['complete_protocol_validation'])

    def test_packbits_literal_repeat_and_noop(self):
        data = bytes([128, 2]) + b'ABC' + bytes([254, ord('X')])
        self.assertEqual(s.skip_packbits(data, 0, 6), len(data))
        report = s.inspect(START + band(data, compression=1, width=6) + TRAILER)
        self.assertEqual(report['decoded_raster_bytes'], 6)

    def test_rejects_truncated_packbits_and_overflow(self):
        for data, size in [(b'\x02A', 3), (b'\xfe', 3), (b'\xfeX', 2)]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                s.skip_packbits(data, 0, size)

    def test_declared_parenthetical_length_skips_fake_raster_header(self):
        payload = b'\x1bi' + b'\x00' * 7
        report = s.inspect(START + b'\x1b(X' + len(payload).to_bytes(2, 'little') + payload + TRAILER)
        self.assertEqual(report['raster_bands'], 0)
        self.assertEqual(report['command_counts']['ESC (X'], 1)

    def test_unknown_compression_reports_partial_coverage(self):
        report = s.inspect(START + band(b'A', compression=2))
        self.assertEqual(report['raster_bands'], 0)
        self.assertEqual(report['stopped_because'], 'unsupported-raster-compression-2')

    def test_positioning_units_are_not_claimed_as_print_resolution(self):
        report = s.inspect(START + b'\x1b(U\x05\x00\x04\x04\x04\xa0\x05' + TRAILER)
        self.assertEqual(report['positioning_units_per_inch']['horizontal'], 360)
        self.assertNotIn('print_resolution', report)

    def test_missing_start_and_truncated_commands(self):
        for data in (b'not a print stream', START + b'\x1bi', START + b'\x1b(X\xff\x7f'):
            with self.subTest(data=data), self.assertRaises(ValueError): s.inspect(data)

    def test_bounded_decoding(self):
        with self.assertRaises(ValueError): s.skip_packbits(b'', 0, s.MAX_DECODED_BAND + 1)


if __name__ == '__main__': unittest.main()
