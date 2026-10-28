# Physical Letter margin trials

Date: 2026-10-27.

Two single-copy jobs used the same experimental stream. The first print was
skewed; inspection of the repeat sheet remains pending.

## Configuration

- Paper: Letter/Carta, 75 g/m², actual size.
- Artifact: `build/letter-margins-offline-001/prototype-black.prn`.
- Stream bytes: 283657.
- SHA-256: `c208ce9c5851665de00bb431cdd9210230b0292eda7814aa6a9f02b0a621da15`.
- Digital checks: one 612 × 792 pt page, one inspected page eject, channel
  code 0, and dark pixels near all 16 margin-mark centers.
- Transport: existing `L355` queue, raw mode, one copy, separators disabled.
- Pre-submission state: idle queue and error-free SNMP status.

The model, density, head offsets, and feed settings remained fixed. The
official-driver comparison artifact remained unsubmitted.

## Submission log

| Job | Purpose | Local attempt record |
|---|---|---|
| L355-76 | Initial sheet; accepted at 17:37:15 UTC−05:00 | `prototype-submission.log` |
| L355-77 | Identical repeat | `prototype-reprint-001.log` |

Submission logs: `build/letter-margins-offline-001/` (local).

## Physical observations

The first print was skewed. Paper placement remains an untested hypothesis.

The repeat used the identical stream after verification of its hash, the idle
queue, and SNMP status.

## Open measurements

- Inspect the repeat sheet.
- Identify complete marks on each edge.
- Measure paper-edge-to-mark-center distances to evaluate printable margins and
  positioning accuracy.
