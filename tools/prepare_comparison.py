#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Prepare two Letter grayscale comparison streams in an offline sandbox."""
import argparse
import json
import re
import shutil
import subprocess

from capture_streams import ROOT, OFFICIAL, FILTER, LIBRARY, RESOURCE, sandbox, execute, sha
from inspect_stream import inspect


FIXTURES = {
    'comparison': 'letter-black-comparison.ps',
    'margins': 'letter-margin-marks.ps',
}


def margin_marks(source):
    marks = re.findall(r'^%%MarginMark: ([A-Za-z0-9_.-]+) ([0-9.]+) ([0-9.]+)$', source, re.M)
    expected = {side+'-'+distance for side in ('top', 'bottom', 'left', 'right')
                for distance in ('3.2', '4', '5', '7')}
    if len(marks) != 16 or {m[0] for m in marks} != expected:
        raise ValueError('Expected 16 uniquely identified margin marks')
    for _, x, y in marks:
        if not (0 <= float(x) <= 612 and 0 <= float(y) <= 792):
            raise ValueError('Margin mark outside Letter page')
    return marks


def prepare(run_name='comparison-letter-actual-size', fixture_kind='comparison'):
    artifacts = ROOT / 'build/artifacts'
    build = json.loads((artifacts / 'manifest.json').read_text())
    if build['profile_sha256'] != sha(ROOT / 'profile/l355.json'):
        raise RuntimeError('Profile has changed since build')
    for relative, expected in build['xml_files'].items():
        if sha(artifacts / 'xml' / relative) != expected:
            raise RuntimeError('Changed XML: ' + relative)
    ppd = artifacts / 'ppd' / build['ppd']['name']
    if sha(ppd) != build['ppd']['sha256']:
        raise RuntimeError('Changed prototype PPD')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_name):
        raise ValueError('Run name must be a simple directory name')
    work = ROOT / 'build' / run_name
    if (ROOT / 'build').is_symlink() or work.is_symlink():
        raise RuntimeError('Refusing symlinked output directory')
    work.mkdir(exist_ok=False)
    fixture = ROOT / 'tests/fixtures' / FIXTURES[fixture_kind]
    marks = margin_marks(fixture.read_text()) if fixture_kind == 'margins' else []
    shutil.copyfile(fixture, work / 'probe.ps')
    shutil.copyfile(OFFICIAL, work / 'epson.ppd')
    shutil.copyfile(ppd, work / 'prototype.ppd')
    for source, target, libs in [('ppd_shim.c', 'ppd_shim.so', ['-shared', '-fPIC']),
                                  ('raster_info.c', 'raster_info', ['-lcups']),
                                  ('measure_raster_scale.c', 'measure_scale', ['-lcups']),
                                  ('raster_mark_report.c', 'mark_report', ['-lcups', '-lm'])]:
        subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', str(ROOT/'tools'/source),
                        '-o', str(work/target)] + libs, check=True, timeout=30)
    prefix = sandbox(work)
    manifest = {'fixture_kind': fixture_kind, 'fixture_sha256': sha(fixture), 'prepared_page_count': 2,
        'page_size': 'Letter', 'print_scaling': 'none', 'physical_validation': 'pending', 'print_submitted': False,
        'prototype_manifest_sha256': sha(artifacts / 'manifest.json'),
        'vendor_inputs': {str(p): sha(p) for p in (OFFICIAL, LIBRARY, FILTER, RESOURCE)}, 'runs': []}
    for name, ppd_name, options in [
        ('official-black', 'epson.ppd', ['PrintQuality=Standard', 'Color=Grayscale']),
        ('prototype-black', 'prototype.ppd', ['StpQuality=Standard', 'ColorModel=Black'])]:
        raster_command = prefix + ['/usr/bin/cupsfilter', '-p', '/work/'+ppd_name,
            '-i', 'application/postscript', '-m', 'application/vnd.cups-raster',
            '-o', 'PageSize=Letter', '-o', 'print-scaling=none']
        for option in options:
            raster_command += ['-o', option]
        raster_command += ['/work/probe.ps']
        raster = work / (name+'.raster')
        execute(raster_command, raster, work/(name+'.raster.log'))
        info = json.loads(subprocess.check_output(prefix + ['/work/raster_info', '/work/'+raster.name], timeout=30))
        if info['count'] != 1 or info['pages'][0]['page_points'] != [612, 792]:
            raise RuntimeError('Expected exactly one Letter raster page')
        scale_check = subprocess.check_output(prefix + ['/work/measure_scale',
            '/work/'+raster.name, '--expect-100mm'], timeout=30, text=True).strip()
        mark_report = None
        if marks:
            check = subprocess.run(prefix + ['/work/mark_report', '/work/'+raster.name],
                input=''.join(' '.join(m)+'\n' for m in marks),
                capture_output=True, text=True, timeout=30)
            (work/(name+'.marks.json')).write_text(check.stdout)
            if check.returncode:
                raise RuntimeError('Expected margin mark absent or invalid raster; inspect '+name+'.marks.json')
            mark_report = json.loads(check.stdout)
        extra = {'PPD': '/work/'+ppd_name}
        vendor = name == 'official-black'
        if vendor:
            extra.update(LD_PRELOAD='/work/ppd_shim.so', L355_TEST_PPD='/work/'+ppd_name)
        filter_name = 'epson_inkjet_printer_filter' if vendor else 'rastertogutenprint.5.3'
        render_command = sandbox(work, extra) + ['/usr/lib/cups/filter/'+filter_name,
            '1', 'offline', 'Letter black comparison', '1',
            'PageSize=Letter print-scaling=none '+' '.join(options), '/work/'+raster.name]
        output = work / (name+'.prn')
        execute(render_command, output, work/(name+'.render.log'))
        report = inspect(output.read_bytes())
        channels = set(report['channel_code_band_counts'])
        if (report['page_ejects_in_graphics_body'] != 1 or report['raster_bands'] < 1 or
            report['stopped_because'] != 'remote-trailer-not-decoded' or
            not channels or not channels <= {'0', '5', '6'}):
            raise RuntimeError('Stream failed single-page/black-channel checks: '+name+' '+str(report))
        manifest['runs'].append({'name': name, 'raster_sha256': sha(raster),
            'raster_info': info, 'raster_scale_check': scale_check, 'margin_mark_report': mark_report,
            'output_sha256': sha(output), 'output_bytes': output.stat().st_size,
            'stream_report': report, 'raster_command': raster_command, 'render_command': render_command,
            'vendor_test_shim': vendor})
        print(name, ': one Letter page, black codes', sorted(channels), 'bytes', output.stat().st_size)
    (work/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('Comparison artifacts prepared:', work)
    return work


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-name', default='comparison-letter-actual-size')
    parser.add_argument('--fixture', choices=FIXTURES, default='comparison')
    args = parser.parse_args()
    prepare(args.run_name, args.fixture)
