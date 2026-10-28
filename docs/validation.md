# Validation plan

## Completed checks

- Isolated XML tree and SHA-256 manifest generation.
- Driver lookup and local model ID verification through libgutenprint.
- Letter margins, media limits, and borderless-option state.
- PPD structural validation.
- XML transformation, isolation, and collision tests.
- Sandboxed filter capture and bounded graphics-body inspection.
- Letter grayscale raster checks for page count, scale, and margin-mark presence.

See [offline testing](offline-testing.md) for commands and dependencies.

## Physical trial status

| Trial | Result |
|---|---|
| [Initial comparison](experiments/2026-10-27-letter-black-001.md) | Both variants printed; input raster scaling identified |
| [Actual-size prototype](experiments/2026-10-27-letter-black-002.md) | Actual-size stream printed; top and bottom edge clipping |
| [Margin analysis](experiments/2026-10-27-margins-offline.md) | Partial digital clipping identified; 16-mark fixture prepared |
| [Margin trials](experiments/2026-10-27-margins-physical-001.md) | First print skewed; identical repeat submitted; inspection pending |

## Open validation work

- Test A4, Legal, and the remaining supported modes.
- Filter inherited paper names and irrelevant options.
- Measure printed margins, scale, and registration repeatedly.
- Validate grayscale tone, color conversion, and channel mapping.
- Evaluate head offsets, drop sizes, interleaving, and paper advance.
- Expand prototype/L130 regression comparisons across media and modes.

## Experimental packaging

Develop a filter or package that selects the private XML tree for one experimental
queue. Keep data-path configuration process-local and retain the existing queue
as a rollback path.

Before installation, review wrapper permissions, pin compatible versions, save
the existing queue configuration, and agree on the queue name and destination.
Changing the default queue requires a separate decision.

## Physical test procedure

1. Confirm paper type, ink levels, and an acceptable nozzle-check pattern.
2. Agree on the fixture, page budget, and expected measurements before submission.
3. Start with a low-coverage Letter grayscale page at actual size.
4. Compare identical fixtures and paper across drivers; record scale, offsets,
   clipped marks, line continuity, and feed behavior.
5. Vary one setting at a time and retain hashes, commands, paper details,
   measurements, and acceptance criteria.
6. Extend testing to color and higher-quality modes after the basic checks pass.

Physical submissions require explicit approval for each page budget.
Service operations and unsupported borderless or CD modes remain outside this
test procedure.

## Upstream contribution

After hardware validation, prepare a Gutenprint patch containing the printer
entry, model definition, and supported calibration evidence. Coordinate model
ID allocation and patch format with maintainers. The margin-parser truncation
can be reported separately with a minimal reproducer.
