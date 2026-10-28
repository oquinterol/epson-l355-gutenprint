#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Capture synthetic filter output in a bubblewrap sandbox.

Run installed Epson and Gutenprint filters in isolated network, PID, and mount
namespaces. Store inputs, streams, and manifests under build/.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = Path('/usr/share/cups/model/epson-inkjet-printer-201207w/EPSON_L355.ppd')
LIBRARY = Path('/usr/lib/libEpson_201207w.so.1.0.1')
FILTER = Path('/usr/lib/cups/filter/epson_inkjet_printer_filter')
RESOURCE = Path('/usr/share/epson-inkjet-printer-filter/resource/Epson_201207w.1.data')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sandbox(work, extra_env=None):
    # Use read-only system mounts, synthetic devices, and an isolated /run.
    command = ['bwrap', '--unshare-all', '--new-session', '--die-with-parent',
            '--cap-drop', 'ALL', '--ro-bind', '/usr', '/usr',
            '--ro-bind', '/lib', '/lib', '--ro-bind', '/lib64', '/lib64',
            '--ro-bind', '/bin', '/bin',
            '--ro-bind', '/etc', '/etc', '--proc', '/proc', '--dev', '/dev',
            '--tmpfs', '/tmp', '--dir', '/run', '--bind', str(work), '/work',
            '--ro-bind', str(ROOT / 'build/artifacts/xml'), '/gutenprint-xml',
            '--chdir', '/work', '--clearenv', '--setenv', 'PATH', '/usr/bin',
            '--setenv', 'LC_ALL', 'C', '--setenv', 'HOME', '/tmp',
            '--setenv', 'STP_DATA_PATH', '/gutenprint-xml']
    for name, value in (extra_env or {}).items():
        command += ['--setenv', name, value]
    return command + ['--']


def execute(command, output, log, timeout=120):
    # Create exclusive output and log files; propagate execution failures.
    with output.open('xb') as out, log.open('xb') as err:
        result = subprocess.run(command, stdout=out, stderr=err, timeout=timeout,
                                stdin=subprocess.DEVNULL)
    if result.returncode:
        raise RuntimeError('Capture failed; inspect ' + str(log))


def capture():
    for tool in ('bwrap', 'cupsfilter', 'cups-genppd.5.3'):
        if not shutil.which(tool):
            raise RuntimeError('Missing sandbox requirement: ' + tool)
    artifacts = ROOT / 'build/artifacts'
    ppds = list((artifacts / 'ppd').glob('*.ppd'))
    if len(ppds) != 1 or not (artifacts / 'manifest.json').is_file():
        raise RuntimeError('Run make build first')
    work = ROOT / 'build/captures'
    if (ROOT / 'build').is_symlink() or work.is_symlink():
        raise RuntimeError('Refusing symlinked output directory')
    work.mkdir(exist_ok=False)
    shutil.copyfile(ROOT / 'tests/fixtures/probe.ps', work / 'probe.ps')
    shutil.copyfile(OFFICIAL, work / 'epson.ppd')
    shutil.copyfile(ppds[0], work / 'prototype.ppd')
    subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                    str(ROOT / 'tools/ppd_shim.c'), '-o', str(work / 'ppd_shim.so')],
                   check=True, timeout=30)
    prefix = sandbox(work)
    isolation_command = prefix + ['/usr/bin/python3', '-c',
        'import os,json; print(json.dumps({"network_namespace":os.readlink("/proc/self/ns/net"),'
        '"cups_socket_visible":os.path.exists("/run/cups/cups.sock"),'
        '"device_entries":sorted(os.listdir("/dev"))}))']
    isolation = json.loads(subprocess.check_output(isolation_command, timeout=15))
    isolation['host_network_namespace'] = os.readlink('/proc/self/ns/net')
    if (isolation['network_namespace'] == isolation['host_network_namespace'] or
            isolation['cups_socket_visible']):
        raise RuntimeError('Isolation verification failed')
    generated = subprocess.run(prefix + ['/usr/bin/cups-genppd.5.3', '-q', '-p', '/work',
                                        'escp2-l130'], capture_output=True, timeout=30)
    if generated.returncode:
        raise RuntimeError('Could not generate baseline L130 PPD')
    import gzip
    baseline_gz = work / 'stp-escp2-l130.5.3.ppd.gz'
    (work / 'baseline.ppd').write_bytes(gzip.decompress(baseline_gz.read_bytes()))
    runs = [
        ('epson-standard', 'epson.ppd', ['PrintQuality=Standard', 'Color=Color']),
        ('epson-high', 'epson.ppd', ['PrintQuality=High', 'Color=Color']),
        ('l130-standard', 'baseline.ppd', ['StpQuality=Standard', 'ColorModel=RGB']),
        ('prototype-standard', 'prototype.ppd', ['StpQuality=Standard', 'ColorModel=RGB']),
    ]
    manifest = {'fixture_sha256': sha(work / 'probe.ps'), 'isolation': isolation,
                'vendor_inputs': {str(path): sha(path) for path in (OFFICIAL, LIBRARY, FILTER, RESOURCE)},
                'runs': [], 'submitted_jobs': False, 'physical_validation': False}
    for name, ppd, options in runs:
        command = prefix + ['/usr/bin/cupsfilter', '-p', '/work/' + ppd,
                            '-i', 'application/postscript', '-m', 'application/vnd.cups-raster',
                            '-o', 'PageSize=Letter']
        for option in options:
            command += ['-o', option]
        command += ['/work/probe.ps']
        raster = work / (name + '.raster')
        raster_log = work / (name + '.raster.stderr.log')
        execute(command, raster, raster_log)
        extra_env = {'PPD': '/work/' + ppd}
        vendor = name.startswith('epson-')
        if vendor:
            extra_env.update(LD_PRELOAD='/work/ppd_shim.so', L355_TEST_PPD='/work/' + ppd)
        executable = '/usr/lib/cups/filter/' + ('epson_inkjet_printer_filter' if vendor else 'rastertogutenprint.5.3')
        render_command = sandbox(work, extra_env) + [executable, '1', 'offline',
            'L355 synthetic probe', '1', 'PageSize=Letter ' + ' '.join(options), '/work/' + raster.name]
        output = work / (name + '.prn')
        log = work / (name + '.stderr.log')
        execute(render_command, output, log)
        if not output.stat().st_size:
            raise RuntimeError('Empty filter output for ' + name)
        manifest['runs'].append({'name': name, 'raster_command': command,
                                 'render_command': render_command, 'test_ppd_shim': vendor,
                                 'raster_sha256': sha(raster), 'raster_bytes': raster.stat().st_size,
                                 'ppd_sha256': sha(work / ppd),
                                 'output_sha256': sha(output), 'output_bytes': output.stat().st_size,
                                 'stderr_sha256': sha(log)})
        (work / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(name, ':', output.stat().st_size, 'bytes captured in sandbox', flush=True)
    return work


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-offline', action='store_true', required=True,
                        help='Run installed filters in a network and device sandbox')
    parser.parse_args()
    capture()
