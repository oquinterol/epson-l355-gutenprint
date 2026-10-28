#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build an isolated Gutenprint data tree and experimental PPD."""
import argparse
import copy
import ctypes
import ctypes.util
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://gimp-print.sourceforge.net/xsd/gp.xsd-1.0'
ET.register_namespace('', NS)
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')


def tag(name):
    return '{' + NS + '}' + name


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def modify_model(tree, profile):
    """Apply profile overrides to an independent copy of the source model."""
    tree = copy.deepcopy(tree)
    model = tree.getroot().find(tag('escp2Model'))
    if model is None or model.get('id') != str(profile['source_model_id']):
        raise ValueError('Unexpected upstream model')
    model.set('id', str(profile['model_id']))
    for name in profile['remove']:
        for child in model.findall(tag(name)):
            model.remove(child)
    for name, value in profile['overrides'].items():
        child = model.find(tag(name))
        if child is None:
            child = ET.SubElement(model, tag(name))
        child.text = value
    for interleave in ('soft', 'printer'):
        matches = [node for node in model.findall(tag('margins'))
                   if node.get('media') == 'sheet' and node.get('interleave') == interleave]
        if len(matches) != 1:
            raise ValueError('Expected exactly one sheet margin definition')
        matches[0].text = ' '.join(str(v) for v in profile['sheet_margins_pt'])
    return tree


def modify_registry(tree, profile):
    tree = copy.deepcopy(tree)
    family = tree.getroot().find('.//' + tag('family'))
    if family is None or family.get('name') != 'escp2':
        raise ValueError('Unexpected printer registry')
    printers = family.findall(tag('printer'))
    if any(p.get('driver') == profile['driver'] or p.get('model') == str(profile['model_id'])
           for p in printers):
        raise ValueError('Experimental model ID or driver name already exists upstream')
    source = next((p for p in printers if p.get('driver') == profile['source_driver']), None)
    if source is None or source.get('model') != str(profile['source_model_id']):
        raise ValueError('Unexpected upstream L130 mapping')
    entry = copy.deepcopy(source)
    entry.set('name', profile['name'])
    entry.set('driver', profile['driver'])
    entry.set('model', str(profile['model_id']))
    # Keep device auto-detection disabled pending hardware validation.
    entry.attrib.pop('deviceid', None)
    family.append(entry)
    return tree


def library_version():
    name = ctypes.util.find_library('gutenprint')
    if not name:
        raise RuntimeError('Install Gutenprint first')
    lib = ctypes.CDLL(name)
    lib.stp_get_version.restype = ctypes.c_char_p
    return lib.stp_get_version().decode('ascii')


def command(args, env):
    result = subprocess.run(args, env=env, capture_output=True, text=True, errors='replace', timeout=90)
    if result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args) + '\n' + result.stdout + result.stderr)
    return result.stdout + result.stderr


def build(data_dir):
    profile_path = ROOT / 'profile/l355.json'
    profile = json.loads(profile_path.read_text())
    version = library_version()
    if version != profile['gutenprint_version']:
        raise RuntimeError('Tested Gutenprint version is ' + profile['gutenprint_version'] + ', found ' + version)
    data_dir = data_dir.resolve(strict=True)
    inputs = {'registry': data_dir / 'printers/escp2.xml',
              'model': data_dir / ('escp2/model/model_' + str(profile['source_model_id']) + '.xml')}
    model_id = profile['model_id']
    if (data_dir / f'escp2/model/model_{model_id}.xml').exists():
        raise RuntimeError('Experimental model ID collision')
    build_dir = ROOT / 'build'
    if build_dir.is_symlink():
        raise RuntimeError('Refusing symlinked build directory')
    build_dir.mkdir(exist_ok=True)
    destination = build_dir / 'artifacts'
    if destination.exists() or destination.is_symlink():
        raise RuntimeError('build/artifacts already exists; move it aside before rebuilding')
    with tempfile.TemporaryDirectory(prefix='staging-', dir=build_dir) as staging:
        work = Path(staging) / 'artifacts'
        xml_dir = work / 'xml'
        shutil.copytree(data_dir, xml_dir)
        modify_registry(ET.parse(inputs['registry']), profile).write(
            xml_dir / 'printers/escp2.xml', encoding='utf-8', xml_declaration=True)
        modify_model(ET.parse(inputs['model']), profile).write(
            xml_dir / f'escp2/model/model_{model_id}.xml', encoding='utf-8', xml_declaration=True)
        env = {**os.environ, 'LC_ALL': 'C', 'STP_DATA_PATH': str(xml_dir),
               'SOURCE_DATE_EPOCH': '0'}
        ppd_dir = work / 'ppd'
        ppd_dir.mkdir()
        generator = command(['cups-genppd.5.3', '-q', '-p', str(ppd_dir), profile['driver']], env)
        ppds = list(ppd_dir.glob('*.ppd.gz')) + list(ppd_dir.glob('*.ppd'))
        if len(ppds) != 1:
            raise RuntimeError('Expected one PPD')
        ppd = ppds[0]
        if ppd.suffix == '.gz':
            raw = gzip.decompress(ppd.read_bytes())
            uncompressed = ppd.with_suffix('')
            uncompressed.write_bytes(raw)
            ppd.unlink()
            ppd = uncompressed
        validation = command(['cupstestppd', str(ppd)], env)
        (work / 'validation.log').write_text(generator + validation)
        manifest = {
            'gutenprint_version': version,
            'profile_sha256': digest(profile_path),
            'upstream_inputs': {key: {'path': str(path), 'sha256': digest(path)} for key, path in inputs.items()},
            'xml_files': {str(path.relative_to(xml_dir)): digest(path)
                          for path in sorted(xml_dir.rglob('*')) if path.is_file()},
            'ppd': {'name': ppd.name, 'sha256': digest(ppd)},
            'hardware_validated': False,
        }
        (work / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        work.rename(destination)
    print('Built:', destination)
    print('Profile build and offline validation complete.')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('/usr/share/gutenprint/5.3/xml'))
    args = parser.parse_args()
    build(args.data_dir)
