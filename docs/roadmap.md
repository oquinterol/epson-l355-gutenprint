# Development and test roadmap

## Objective

Develop a dedicated Epson L355 Gutenprint profile with verified configuration
options, reproducible results, and isolated installation.

This roadmap orders the remaining work. Check a task when its implementation or
experiment record satisfies the stated completion criterion. Link the supporting
commit, test result, or report when updating its status.

## Starting point

The project includes an isolated profile builder, a native capability probe,
unit tests, sandboxed filter capture, and raster diagnostics. Historical Letter
trials identified automatic raster scaling and partial edge clipping.

See the [validation plan](validation.md) for current results and the physical
test procedure, [profile evidence](evidence.md) for model decisions, and
[offline testing](offline-testing.md) for existing commands.

## Sequence

| Stage | Work | Prerequisite |
|---|---|---|
| 1 | Reproducible baseline | Current profile and tools |
| 2 | Automated capability coverage | Stage 1 |
| 3 | Physical geometry and feed | Stages 1–2; agreed measurement tolerances |
| 4 | Black output and quality modes | Stage 3 |
| 5 | Color output | Stages 3–4 |
| 6 | Isolated installation | Offline packaging work can run alongside stages 3–5 |
| 7 | Validated release | Evidence for the advertised capability matrix and stage 6 |

Stabilize geometry before changing density, head offsets, or feed parameters.
Apply the physical test procedure before each hardware trial. Set numerical
acceptance tolerances and page budgets before printing.

## 1. Reproducible baseline

- [ ] **BASE-01** Build from a clean source extraction and run `make test`.
- [ ] **BASE-02** Record the source revision, profile and fixture hashes, and
  versions of Gutenprint, CUPS, Ghostscript, filters, and build tools.
- [ ] **BASE-03** Generate new L130 and experimental L355 reference captures
  using the identified fixtures and explicit settings.
- [ ] **BASE-04** Store commands, manifests, diagnostics, and outputs in new run
  directories, keeping historical artifacts associated with their original inputs.

**Completion criterion:** a clean-source run produces a traceable build and
reference captures with passing checks. Record reproducibility differences
separately from expected timestamp or environment-dependent output changes.

## 2. Automated capability coverage

- [ ] **AUTO-01** Parameterize the native probe for Letter, A4, and Legal;
  assert page dimensions, effective margins, and media limits.
- [ ] **AUTO-02** Inventory inherited paper sizes, quality modes, resolutions,
  media types, and relevant option constraints.
- [ ] **AUTO-03** Define the candidate capability matrix and remove or disable
  inherited options that lack a supported L355 use case.
- [ ] **AUTO-04** Add L130 regression checks to verify that generating and
  loading the experimental profile preserves the source model and registry entries.
- [ ] **AUTO-05** Extend inspector and raster-diagnostic tests with empty,
  truncated, unsupported, and boundary-case inputs.

**Completion criterion:** the candidate matrix has automated checks for digital
properties and explicit expected failures for unsupported inputs. Identify
physical properties separately for hardware validation.

## 3. Physical geometry and feed

- [ ] **GEOM-01** Prepare the current margin fixture and verify raster page
  count, actual-size scaling, and pixels near every expected mark center.
- [ ] **GEOM-02** Define measurement tools, tolerances, repeat count, paper
  conditions, and the approved page budget.
- [ ] **GEOM-03** Measure the printed 100 mm scale, both sides of the 20 mm
  square, and paper-edge-to-mark-center distances on all four edges.
- [ ] **GEOM-04** Record clipped marks, horizontal and vertical displacement,
  and sheet skew; repeat identical settings to assess consistency.
- [ ] **GEOM-05** Compare missing or shortened printed features with their
  raster counterparts and test one explanation at a time.
- [ ] **GEOM-06** Extend the accepted geometry checks to A4 and Legal with
  format-specific fixtures and approved trials.

**Completion criterion:** repeated measurements satisfy the agreed tolerances
for each validated format. Record digital clipping, positioning error, and feed
variation as separate findings where the evidence supports that distinction.

## 4. Black output and quality modes

- [ ] **BLACK-01** Prepare fixtures for text, thin lines, grayscale ramps,
  and small coverage patches at the validated geometry.
- [ ] **BLACK-02** Compare the experimental profile, L130, and official driver
  using identical content and paper; record effective settings for each pipeline.
- [ ] **BLACK-03** Evaluate stroke continuity, fine detail, tonal transitions,
  banding, and print duration using a defined assessment procedure.
- [ ] **BLACK-04** Change one setting per comparison and repeat candidate
  configurations before selecting defaults.

**Completion criterion:** a reproducible black-output configuration meets the
specified checks. Document quality and time trade-offs alongside the settings;
keep input raster DPI, configured modes, and physical measurements distinct.

## 5. Color output

- [ ] **COLOR-01** Verify digital channel codes and prepare low-coverage cyan,
  magenta, yellow, mixed-color, and neutral patterns.
- [ ] **COLOR-02** Evaluate printed channel registration, banding, and tonal
  transitions under fixed paper and quality settings.
- [ ] **COLOR-03** Repeat cross-profile comparisons and investigate inherited
  color or media parameters through controlled changes.
- [ ] **COLOR-04** Define a calibration workflow, including measurement
  equipment and ICC profiling requirements, after geometry and modes stabilize.

**Completion criterion:** supported color configurations have repeatable test
results and documented limitations. Require instrumental measurements for
quantitative color-accuracy claims.

## 6. Isolated installation and rollback

- [ ] **PKG-01** Design the filter or wrapper to select the project XML tree
  through process-local configuration.
- [ ] **PKG-02** Test permissions, dependency versions, data paths, and failure
  behavior before connecting the package to a print queue.
- [ ] **PKG-03** Install an approved experimental queue alongside the existing
  queue and verify representative application print paths.
- [ ] **PKG-04** Test package removal and restoration of the previous setup.

**Completion criterion:** installation and removal are reproducible, the existing
queue remains usable, and application output preserves the validated settings.

## 7. Validated release

- [ ] **REL-01** Consolidate a matrix of validated formats, media, modes, and
  options, linking each advertised capability to its test evidence.
- [ ] **REL-02** Run automated tests in CI with explicit dependency versions
  and separate optional vendor-driver comparisons from core tests.
- [ ] **REL-03** Align requirements, installation steps, experiment records,
  known issues, and release scope with the validated matrix.
- [ ] **REL-04** Publish a tagged release after the checks pass; evaluate an
  upstream Gutenprint contribution and coordinate model ID allocation.

**Completion criterion:** a release can be built, tested, installed, and evaluated
against its published capability matrix.

## Initial work batch

1. Complete **BASE-01** and **BASE-02** to identify the working baseline.
2. Complete **BASE-03** and **BASE-04** to capture comparable reference runs.
3. Complete **AUTO-01** and **AUTO-02** to establish format checks and the option
   inventory.
4. Define **GEOM-02** before scheduling the first new physical trial.
