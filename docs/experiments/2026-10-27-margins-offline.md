# Letter raster margin analysis

Date: 2026-10-27.

Raster analysis used the existing model, density, feed, and head settings.

## Question and method

The analysis tests whether input raster clipping contributes to the top and
bottom edge loss in the [actual-size trial](2026-10-27-letter-black-002.md).

`tools/raster_edge_report.c` projects dark pixels from the central image
region and locates long contour bands near the raster edges. The analysis
targets the synthetic frame fixture.

## Existing raster observations

Artifact: `build/comparison-letter-actual-size-checked/prototype-black.raster`.

| Property | Value |
|---|---|
| Raster dimensions | 5940 × 3870 pixels |
| Input DPI | 720 × 360 |
| Page dimensions | 612 × 792 pt |
| Imaging box | `[9.014175, 9.014175, 602.985840, 782.985840]` pt |
| Horizontal row bands, inclusive | `[0,0]`, `[25,26]`, `[95,97]`, `[3772,3773]`, `[3843,3844]`, `[3869,3869]` |

The outer top and bottom contours occupy a single pixel row each;
inner contours occupy two or three rows. Outer vertical contours occupy two
columns, compared with four for inner contours at the higher horizontal DPI.

The actual-size official raster has outer horizontal bands at rows `[2,3]`
and `[3872,3873]`, within an approximately 8.39 pt margin. It serves as an
offline reference for this analysis.

The 0.3 pt outer stroke is centered at 9 pt, partly outside the experimental
imaging box. These observations establish partial digital clipping. The
remaining contribution of physical positioning and feed requires printed
measurements.

Diagnostic results and hashes:
`build/comparison-letter-actual-size-checked/edge-diagnostic.json` (local).

## Margin fixture

`tests/fixtures/letter-margin-marks.ps` defines one Letter page with 16
isolated marks at 3.2, 4, 5, and 7 mm from each paper edge. It also includes a
100 mm scale and a 20 × 20 mm square.

Rendering uses `print-scaling=none`. The 3.2 mm mark remains close enough to
the imageable-area boundary for partial stroke clipping to occur.

Official and experimental variants were prepared under
`build/letter-margins-offline-001/`.

## Digital checks

- Each raster contained one Letter page, verified with libcups.
- Scale runs measured 100.259 mm for the official raster and 100.189 mm for the
  experimental raster, within the fixture's 0.5 mm tolerance.
- Graphics-body inspection found one page eject and black channel codes.
- The mark diagnostic transformed all 16 PostScript centers using the imaging
  box and nominal DPI, then counted dark pixels within a ±1 pt region.
- All 16 regions contained dark pixels in both rasters.
- An empty region at (400, 400) returned zero pixels and exit code 7.
- All five margin-fixture unit tests passed.

These checks establish nearby raster-pixel presence. Full mark extent and
printed visibility require separate evaluation.

## Reproduction

Use a new output directory:

```sh
make test
python3 tools/prepare_comparison.py --fixture margins --run-name letter-margins-new
```

The preparation manifest contains `margin_mark_report` and
`raster_scale_check` for both variants.

## Follow-up

[Physical margin trials](2026-10-27-margins-physical-001.md) use the isolated
marks to measure edge-to-center distances with paper, scaling, density, and feed
settings held fixed.
