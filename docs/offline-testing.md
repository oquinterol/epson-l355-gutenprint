# Offline filter and raster testing

The tools render synthetic PostScript fixtures to local raster and ESC/P2 files.
They support comparison of the experimental profile, Gutenprint L130, and an
installed Epson L355 driver.

## Requirements

In addition to the build dependencies:

- bubblewrap (`bwrap`)
- Ghostscript and CUPS filters
- CUPS development headers and library
- An installed Epson L355 driver and its runtime resources

The current paths target the Arch Linux package
`epson-inkjet-printer-201207w`. Review its license before using its components.

## Isolation

The capture sandbox uses separate network, PID, and mount namespaces,
read-only system directories, a synthetic device tree, and an empty `/run`.
Only the output directory is writable on the host. Capture verifies network
namespace separation and CUPS socket isolation before running filters.

The official-filter test uses `tools/ppd_shim.c` to supply an explicit local
PPD through `cupsGetPPD`. This test configuration should be considered when
comparing results with a production CUPS pipeline.

## Capture a synthetic color fixture

Build the profile first, then run:

```sh
python3 tools/capture_streams.py --run-offline
python3 tools/inspect_stream.py build/captures/*.prn
```

The capture directory must be new. The run records input hashes, commands,
raster files, printer streams, and logs under `build/captures/`.

Four variants are generated: Epson Standard, Epson High, Gutenprint L130
Standard, and experimental L355 Standard. Each uses its profile's requested
raster settings; compare those settings alongside output differences.

## Prepare a grayscale comparison

```sh
python3 tools/prepare_comparison.py --run-name comparison-letter-new
python3 tools/prepare_comparison.py --fixture margins --run-name margins-letter-new
```

Each command prepares one official-driver stream and one experimental stream.
Checks cover:

- Build-manifest, XML, and PPD hashes.
- One Letter raster page per variant.
- `print-scaling=none` and a nominal 100 mm scale, with a 0.5 mm raster tolerance.
- One page eject and black channel codes in the inspected graphics body.
- Pixels near all 16 expected mark centers for the margin fixture.

Output directories must be new. Preparation writes files; physical trials are
a separate step described in the [validation plan](validation.md).

## Inspector coverage

The ESC/P2 inspector locates a graphics-mode pattern, walks length-framed
commands, and skips raster payloads by their declared size or PackBits length.
It reports bands, channel codes, bit depths, page ejects, and positioning units.

Coverage is limited to the graphics body. The preamble and remote trailer remain
unparsed. Positioning units and input raster DPI describe different stages of
the pipeline. Eight unit tests cover framing, truncation, bounded decoding,
command-like raster bytes, and unsupported compression.

## Interpretation

Raster checks establish properties of digital inputs. Physical dimensions,
registration, tone, and paper advance require measurements from printed sheets.
Output hashes may vary with filter versions, fonts, data, and job timestamps.
