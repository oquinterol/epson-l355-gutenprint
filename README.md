# Epson L355 Gutenprint profile

Experimental Epson L355 printing support based on Gutenprint 5.3.5.

## Motivation and scope

This project grew from using Gutenprint's L130 profile with an Epson L355 on
GNU/Linux. In that setup, Gutenprint provided better print quality and more
configuration options than the official driver, motivating a dedicated L355
profile with hardware-based validation.

The objective is comprehensive L355 printing support through Gutenprint,
including paper geometry, margins, quality modes, grayscale, and color.

## Current implementation

| Property | Configuration |
|---|---|
| Driver identifier | `escp2-l355-experimental` |
| Local model ID | `355` |
| Base definition | Gutenprint L130, model `80` |
| Nozzle configuration | 180 black; 59 per color; four channels |
| Sheet margins | 9 pt (3.175 mm) |
| Maximum media dimensions | 612 × 1008 pt (Letter width, Legal length) |
| Resolution limit | 2880 × 1440 within inherited modes |
| Borderless printing | Disabled |

The build produces an isolated XML data tree, a PPD, and a SHA-256 manifest.
The filter must load the generated data tree through `STP_DATA_PATH` to use
the profile.

## Requirements

- GNU/Linux and Python 3.
- Gutenprint **5.3.5**, including its headers and library.
- `cups-genppd.5.3`, `cupstestppd`, a C compiler, GNU Make, and `pkg-config`.

The default XML data directory is `/usr/share/gutenprint/5.3/xml`.
The development environment uses Arch Linux with Gutenprint and CUPS installed.

## Build and test

```sh
make build
make test
```

To select another Gutenprint 5.3.5 data directory:

```sh
python3 tools/build.py --data-dir /path/to/gutenprint/5.3/xml
```

Outputs:

- `build/artifacts/xml/`: isolated printer data.
- `build/artifacts/ppd/stp-escp2-l355-experimental.5.3.ppd`: generated PPD.
- `build/artifacts/manifest.json`: input and output hashes.
- `build/artifacts/validation.log`: PPD generation and validation results.

The builder requires a new output directory. Move existing artifacts before
rebuilding:

```sh
mv build/artifacts build/artifacts-previous
make build
make test
```

`make test` runs 19 unit tests, a native libgutenprint capability probe, and
PPD validation. All test outputs remain local.

## Validation status

Initial Letter grayscale trials produced physical output. Raster diagnostics
identified automatic scaling and partial clipping at the printable-area boundary.
The preparation tool now fixes `print-scaling=none` and checks the fixture's
100 mm scale before generating printer streams.

Color calibration, inherited media options, head offsets, drop sizes,
interleaving, and paper advance require further validation. The current profile
is intended for controlled experiments; production packaging remains pending.

## Development tools

| Tool | Purpose |
|---|---|
| `tools/build.py` | Generate the profile and provenance manifest |
| `tools/capture_streams.py` | Capture filter output in a bubblewrap sandbox |
| `tools/inspect_stream.py` | Inspect framed ESC/P2 graphics commands |
| `tools/prepare_comparison.py` | Prepare Letter grayscale comparison streams |
| `tools/raster_info.c` | Report raster page count and dimensions |
| `tools/measure_raster_scale.c` | Check the fixture's nominal scale |
| `tools/raster_edge_report.c` | Locate long contours near raster edges |
| `tools/raster_mark_report.c` | Check pixels near expected margin marks |

Capture and comparison requirements and commands are documented in
[offline testing](docs/offline-testing.md).

## Technical documentation

- [Development and test roadmap](docs/roadmap.md)
- [Profile design and evidence](docs/evidence.md)
- [Validation plan](docs/validation.md)
- [Initial grayscale comparison](docs/experiments/2026-10-27-letter-black-001.md)
- [Actual-size grayscale trial](docs/experiments/2026-10-27-letter-black-002.md)
- [Raster margin analysis](docs/experiments/2026-10-27-margins-offline.md)
- [Physical margin trials](docs/experiments/2026-10-27-margins-physical-001.md)

## License

GPL-2.0-or-later. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
