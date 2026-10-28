# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_comparison import margin_marks


class MarginFixtureTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT/'tests/fixtures/letter-margin-marks.ps').read_text()

    def test_one_letter_page_and_no_color_patches(self):
        self.assertIn('/PageSize [612 792]', self.source)
        self.assertEqual(self.source.splitlines().count('showpage'), 1)
        self.assertNotIn('setrgbcolor', self.source)
        self.assertNotIn('rectfill', self.source)

    def test_all_sides_have_exact_expected_distances(self):
        for name, sx, sy in margin_marks(self.source):
            side, distance = name.split('-')
            x, y, d = float(sx), float(sy), float(distance)*72/25.4
            actual = {'left': x, 'right': 612-x, 'top': 792-y, 'bottom': y}[side]
            self.assertAlmostEqual(actual, d, places=5)

    def test_missing_or_duplicate_mark_rejected(self):
        line = next(x for x in self.source.splitlines() if x.startswith('%%MarginMark:'))
        for source in (self.source.replace(line, '', 1), self.source+'\n'+line+'\n'):
            with self.assertRaises(ValueError): margin_marks(source)

    def test_out_of_page_mark_rejected(self):
        source = self.source.replace('top-3.2 72.000000', 'top-3.2 700.000000')
        self.assertNotEqual(source, self.source)
        with self.assertRaises(ValueError): margin_marks(source)

    def test_unknown_mark_name_rejected(self):
        with self.assertRaises(ValueError): margin_marks(self.source.replace('top-3.2', 'top-2.5', 1))


if __name__ == '__main__': unittest.main()
