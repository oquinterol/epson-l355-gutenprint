# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'tools/build.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
PROFILE = json.loads((ROOT / 'profile/l355.json').read_text())


def xml(body):
    return ET.ElementTree(ET.fromstring('<gutenprint xmlns="' + b.NS + '">' + body + '</gutenprint>'))


class ProfileTests(unittest.TestCase):
    def source(self):
        return xml('<escp2Model id="80" base="escp2/model/base/baseline_360.xml">'
                   '<borderless>Yes</borderless><verticalBorderlessSequence>unsafe</verticalBorderlessSequence>'
                   '<headConfiguration type="default"><Nozzles>59</Nozzles></headConfiguration>'
                   '<headConfiguration type="black"><Nozzles>180</Nozzles></headConfiguration>'
                   '<margins interleave="soft" media="sheet">9 9 0 9</margins>'
                   '<margins interleave="printer" media="sheet">9 9 0 9</margins>'
                   '</escp2Model>')

    def model(self, tree):
        return tree.getroot().find(b.tag('escp2Model'))

    def test_independent_model_and_no_mutation(self):
        source = self.source()
        result = b.modify_model(source, PROFILE)
        self.assertEqual(self.model(source).get('id'), '80')
        self.assertEqual(self.model(result).get('id'), '355')
        self.assertEqual(self.model(source).find(b.tag('borderless')).text, 'Yes')

    def test_disable_borderless_and_sequence(self):
        model = self.model(b.modify_model(self.source(), PROFILE))
        self.assertEqual(model.find(b.tag('borderless')).text, 'No')
        self.assertIsNone(model.find(b.tag('verticalBorderlessSequence')))

    def test_margins_and_conservative_limits(self):
        model = self.model(b.modify_model(self.source(), PROFILE))
        for node in model.findall(b.tag('margins')):
            self.assertEqual([float(x) for x in node.text.split()], PROFILE['sheet_margins_pt'])
        self.assertEqual(model.find(b.tag('maximumMediaSize')).text, '612 1008')
        self.assertEqual(model.find(b.tag('maximumResolution')).text, '2880 1440')

    def test_nozzle_geometry_preserved(self):
        model = self.model(b.modify_model(self.source(), PROFILE))
        self.assertEqual([n.find(b.tag('Nozzles')).text for n in model.findall(b.tag('headConfiguration'))], ['59', '180'])

    def test_fail_closed_on_wrong_model(self):
        tree = self.source()
        self.model(tree).set('id', '129')
        with self.assertRaises(ValueError): b.modify_model(tree, PROFILE)

    def test_registry_preserves_upstream_and_color_parameters(self):
        tree = xml('<printdef><family name="escp2"><printer name="Epson L130" driver="escp2-l130" model="80" parameters="cx3500_params" deviceid="not-validated"/></family></printdef>')
        result = b.modify_registry(tree, PROFILE)
        entries = result.getroot().findall('.//' + b.tag('printer'))
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].get('driver'), 'escp2-l130')
        self.assertEqual(entries[1].get('parameters'), 'cx3500_params')
        self.assertIsNone(entries[1].get('deviceid'))
        with self.assertRaises(ValueError): b.modify_registry(result, PROFILE)


if __name__ == '__main__': unittest.main()
