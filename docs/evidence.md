# Profile design and evidence

Initial investigation: 2026-10-27. This document records the public specifications,
Gutenprint source observations, and native-library tests used to define the profile.
Physical trial results are recorded separately under `docs/experiments/`.

## Sources

1. [Epson EcoTank L355 specifications](https://www.epson.eu/en_EU/products/printers/inkjet/consumer/ecotank-l355/p/15690):
   180 black nozzles, 59 nozzles per color, four colors, a minimum drop size of
   3 pl, an advertised resolution of 5760 × 1440, 3 mm margins, and manual duplex.
2. [Gutenprint 5.3.5 source](https://downloads.sourceforge.net/project/gimp-print/gutenprint-5.3/5.3.5/gutenprint-5.3.5.tar.xz)
   and [supported printers](https://gimp-print.sourceforge.io/p_Supported_Printers.php).
   Inspected files: `src/xml/printers/escp2.xml`,
   `src/xml/escp2/model/model_80.xml`, `model_129.xml`,
   `src/main/print-escp2-data.c`, `print-escp2.c`, and `path.c`.
3. Installed L355 PPD from `epson-inkjet-printer-201207w` 1.0.1-7:
   `/usr/share/cups/model/epson-inkjet-printer-201207w/EPSON_L355.ppd`.
   Its Letter `ImageableArea` is `8.4 8.4 603.6 783.6` pt, approximately
   3 mm from each paper edge.

## Model selection

Gutenprint maps `escp2-l130` to model 80 and `cx3500_params`. Model 80
defines 180 black nozzles, 59 nozzles per color, four channels, and variable
drop sizes. This nozzle count matches the published L355 specification.

The L310 profile uses model 129, with `FirstNozzle=1` for color; model 80
uses `FirstNozzle=0`. The prototype retains model 80's geometry pending
comparative hardware measurements.

Model 80 inherits media and color data from `c82.xml`. Calibration of these
parameters for L355 inks, head offsets, and drop volumes remains pending.

## Margin representation

In `src/main/print-escp2-data.c`, the margin parser stores the result of
`stp_xmlstrtodim` in `unsigned long data[4]`. Consequently, a 3 mm margin
(8.503937 pt) becomes 8 pt.

The native probe confirmed an effective 8 pt margin in the initial variant.
The current profile rounds upward to **9 pt (3.175 mm)** and verifies all four
Letter margins through `stp_get_imageable_area`.

## Independent model definition

The parser accumulates capability flags with bitwise OR. Disabling borderless
printing therefore requires transforming a copy of the complete model 80
definition rather than inheriting its enabled flag.

The profile uses local model ID 355, retains `baseline_360.xml`, disables
borderless printing, and removes `verticalBorderlessSequence`. The builder
rejects existing model IDs and registry collisions.

## Resolution and media limits

The profile limits inherited modes to 2880 × 1440. Gutenprint validates modes
against nozzle geometry, supported drop sizes, media, and pass counts.

Maximum media dimensions are 612 × 1008 pt, corresponding to Letter width and
Legal length. Inherited media names and options, including CD-related entries,
still require filtering against L355 capabilities.

## Data isolation and provenance

`STP_DATA_PATH` selects the generated XML tree for each build or test process.
The builder writes its outputs under `build/artifacts/`.

The manifest records the Gutenprint version, profile hash, source XML hashes,
generated XML hashes, and PPD hash. These identify the inputs and outputs of
each build; cross-platform bitwise reproducibility remains untested.

The tested library version is Gutenprint 5.3.5. The builder rejects other versions.
