"""Register the new derived study without modifying prior data namespaces."""
from __future__ import annotations

import pyarrow.parquet as pq

from prepare import DATA, OUT, ROOT, digest, save_json

DICTIONARY_ENTRY = f"""

## MAD-TRANSFER-SPX-2026-09-20 — reviewed B07/B05 transfers and B09 index IV

Namespace: `{DATA}`. Producer and findings: `{OUT}`.
Additive derived study; original measurements/outcomes unchanged; no provider calls.
Scope: 2025–September 18, 2026; 239 non-development research dates. Strict causal
above-VT B09 (3,141), B07 (415), B05 (1,537); +5 before −10 in 60 native minute bars.
Four fixed S4/F4 transfer cells, six sign controls, existing B09 S4/F4 references,
one SPXW falling-MAD rule and its OR with F4. No threshold/tenor/parent sweep.

Event keys, 55,? sector observations (exact rows in inventory.json), SPX entry
observations, frozen three-valued memberships, outcomes and coverage tables;
full/all-eleven/common cohorts; three execution policies; half-year/pooled results;
whole-date uncertainty; matched date/block diagnostics; B09 overlap; SPX nine-way
cross; gap receipts/support and source/code/output hashes. Namespace dictionary
defines exact row grains, units, sentinel values and interpretation limits.

Main raw counts: B09 F4 OR SPX 198/318 (62.3%), F4 115/188 (61.2%);
B05 F4 70/112 (62.5%), B07 F4 14/21 (66.7%, underpowered). OR spacing107/175;
SPX-alone first/day38/79. Gains are policy-dependent and overlap/date selection
matter; no established edge or normalization-specific causal attribution.

Validation: ten boundary tests, 26,654 scalar memberships, 2,592 summary rows,
5,093 native VT/outcome replays, 36 prior baseline cells, 204 date/block and
324 SPX cross rows. Independent strategy review preceded execution; new code
has local verification only. Full payload hashes and row counts in inventory.json.
"""

CHANGELOG_ENTRY = f"""

## 2026-09-20 — derive — reviewed MAD transfers and SPX disagreement

- **operator:** Codex / delta_bomb side conversation
- **operation:** additive derived experiment, no collection or source edits
- **namespace:** `{DATA}`
- **project:** `{OUT}`
- **inputs:** frozen eleven-sector MAD histories, completed SPXW MAD, native SPX prices and unchanged +5/−10 event outcomes
- **scope:** 2025–September18,2026; 239 dates; B09/B07/B05, strict causal above-VT only
- **calls:** ThetaData0; ORATS0; other market-data0
- **results:** OR198/318, B05F4 70/112, B07F4 14/21; all variants/policies/halves retained
- **limits:** reused dates/search history, sparse B07, overlap/date selection, policy sensitivity, informative unknowns
- **coverage:** all3141 B09 SPX endpoints available;2742 missing sector-entry slots diagnosed, no refetch or imputation
- **verification:**26654memberships;2592summaries;5093nativeVT/outcomes;10boundarytests; inherited counts and cross tables reconcile
- **dictionary_reconciled:** true; full namespace field definitions and per-file hashes/rows recorded
- **reversibility:** new namespace only; all prior raw, derived, measurement and outcome inputs unchanged
"""


def main() -> None:
    sector_rows = pq.ParquetFile(DATA / "sector_at_entry.parquet").metadata.num_rows
    dictionary_entry = DICTIONARY_ENTRY.replace("55,?", f"{sector_rows:,}")
    dictionary = f"""# Reviewed MAD transfer/SPX data dictionary

Path: `{DATA}`. Scope: 2025–September18,2026. No raw provider download.
This directory contains derived research artifacts, not production trade signals.

| File | Row grain and meaning |
|---|---|
| event_keys.parquet | One distinct variant/date/entry minute; outcome-free, causal above-VT only |
| sector_at_entry.parquet | One parent entry × ETF, exactly eleven per entry; preserves exact T−1 score/source support |
| spx_at_entry.parquet | One B09 entry; exact T−1 SPXW measurement |
| memberships.parquet | One entry × applicable fixed rule; yes/no/unknown and observed vote counts |
| spx_cross_keys.parquet | One B09 entry; sector F4/SPX states before outcomes |
| events_with_outcomes.parquet | Same keys joined one-to-one to unchanged price path labels |
| sector_gap_entries.parquet | One unavailable ETF-entry slot; collection/day/window reason retained |
| research_dates.csv | All239 selected non-development dates, including zero-entry dates; native price paths/hashes/VT |
| native_vt_checks.csv | Candidate date/minute eligibility, including excluded candidates; prior lows and entry open |
| pre_outcome_participation.csv | Parent × half × endpoint block × rule; yes/no/unknown counts before outcome join |
| valid_sector_counts.csv | Parent × half × block × observed-sector count, with entries/dates |
| instrument_coverage.csv | Parent × half × block × instrument; measured and expected entry observations |
| summary.csv | Parent/cohort/period/policy/rule/state; four outcome counts, rate, dates, retention and selected-date reference |
| uncertainty.csv | Pooled whole-date intervals by parent/cohort/policy/rule/reference |
| within_date_block.csv | Equal-date mean of equal-block yes-minus-no contrasts and bootstrap intervals; overlap support |
| within_date_block_strata.csv | Every date/block used or discarded in those diagnostics |
| b09_overlap.csv | Transfer outcomes within/without a corresponding B09 qualifying block and at exact coincident entry minutes |
| spx_cross.csv | All nine sector/SPX state combinations, including empty and unknown cells |
| spx_incremental.csv | SPX-positive/sector-no additions, SPX-positive/sector-unknown recovery, and two negative references |
| spx_incremental_uncertainty.csv | Pooled date-bootstrap contrasts of definite additions versus corresponding negative references |
| gap_causes.csv | Missing ETF-entry counts/dates by parent, ETF, half and recorded cause |
| gap_source_support.csv | Each missing ETF-entry reconciled to the unchanged expiry selection and minute support; not a new fill |
| half_year_results.png | Descriptive all-entry fixed-rule plot; exact N in project report |
| freeze.json | Input/code/protocol hashes and outcome-free artifact hashes before outcome attachment |
| analysis_receipt.json | Analysis outputs, outcome hash, bootstrap settings |
| verification.json | Scalar/native/summary reconciliation counts and status |
| gap_support_receipt.json | Source-table/day-receipt hashes for missing-entry diagnostics |
| report_receipt.json | Findings, complete table and chart hashes |

## Keys, units and state meanings

- `entry_id`: variant|ISOdate|known_min. `known_min`: local Eastern minute after
  midnight at the entry open. `signal_min` remains the original trigger minute.
- `end_min=known_min−1`, `start_min=end_min−29`. `block=(end_min−570)//60`:
  five calibration blocks anchored at09:30; current endpoints09:59–14:29.
- `half`: YYYY_H1/H2. 2026_H2 is partial through September18. `completed` pools
  2025_H1,2025_H2,2026_H1; `pooled` also includes the partial half.
- Original IV series uses IV percentage points; slopes `b1/b2` are points/minute,
  acceleration is points/minute². `scale` has the same units; signed_score M is
  dimensionless and zero-anchored. It is not a probability or Gaussian z-score.
- S4:M>1 in≥4 of11. F4:each of≥4 ETFs has M>1 AND b2<−1e−12.
  sign4:a<0 in≥4; sign_falling4 adds the same-sector b2 condition. Sign controls
  require the same finite scored-M source eligibility as magnitude rules.
- SPX_F uses the F4 single-instrument conjunction on SPXW. OR_F4_SPX is a
  three-valued union. `qualifying_votes/unknown_votes=-1` is an explicit **not
  applicable** sentinel for OR, not a negative sector count; other rules use
  actual observed votes. Unknown never counts as a negative vote by imputation.
- `all11`: all eleven ETFs have finite scored M, acceleration and b2.
  `joint_measurable`: B09 F4 and SPX states are both definite; false for other
  parents, which are not part of the SPX comparison. Cohorts:full/all11/common/
  common_all11, always with the corresponding restricted parent.
- Only target_first wins. adverse_first/neither/ambiguous remain in N. Barriers
  are +5/−10 price points,60 native minute bars including entry. No posttarget
  persistence score or inferred intraminute ordering.
- `rate`, `low`, `high`: percent,0–100. Deltas and uplift intervals:percentage
  points. NaN means unestimable/unavailable, not zero.
- Policies:all,first (first qualifying entry/date),spaced60 (greedy chronological
  ≥60minutes, reset per date). Filter before thinning. Cross-cell counts add to
  parent counts only in all-entry tables, because each thinned cell has its own
  chronological selections. OR portfolio policies are applied to the union itself.
- `parent_winner_overlap` is actual winning entry-ID intersection with that
  cohort's baseline policy. `parent_winners_excluded` is its set difference;
  first/spaced filters may choose different entries than a thinned parent.
- Date/hour and overlap diagnostics are retrospective controls, never new
  entry-time gates. A B09 block label may reference a later signal in that block.
- All uncertainty is descriptive,5000 shared whole-date draws,seed20260920;
  no adjustment for prior search or serial date dependence. Sparse/unestimable
  status and exact support must accompany any conclusion.
- Gap counts are ETF×parent-entry slots; different parents can share a physical
  ETF/date/endpoint. Missing bracket and rejected source window are separate
  causes. A captured source rejection does not prove the market lacked a quote.

## Provenance and interpretation

Read the project PROTOCOL.md,FINDINGS.md,ALL_RESULTS.md,REVIEW_COMPLIANCE.md and
LEARNING_NOTE.md for formulas, review conditions, search history and limitations.
Prior files are immutable. No global framework, dashboard or price trigger changed.
The source review was independent; the new execution's tests/replays are local.
"""
    (DATA / "DATA_DICTIONARY.md").write_text(dictionary)
    (DATA / "CHANGELOG.md").write_text(CHANGELOG_ENTRY.lstrip())
    for path, appendix in [(ROOT.parent / "DATA_DICTIONARY.md", dictionary_entry),
                            (ROOT.parent / "CHANGELOG.md", CHANGELOG_ENTRY)]:
        marker = "MAD-TRANSFER-SPX-2026-09-20" if path.name == "DATA_DICTIONARY.md" else \
            "## 2026-09-20 — derive — reviewed MAD transfers and SPX disagreement"
        if marker not in path.read_text():
            with path.open("a") as handle:
                handle.write(appendix)
    (OUT / "REGISTRY_DATA_DICTIONARY.md").write_text(dictionary_entry)
    (OUT / "REGISTRY_CHANGELOG.md").write_text(CHANGELOG_ENTRY)
    entries = []
    for path in sorted(DATA.iterdir()):
        if not path.is_file() or path.name == "inventory.json":
            continue
        entry = dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))
        if path.suffix == ".parquet":
            parquet = pq.ParquetFile(path)
            entry["rows"] = parquet.metadata.num_rows
            entry["schema"] = {f.name: str(f.type) for f in parquet.schema_arrow}
        entries.append(entry)
    save_json(DATA / "inventory.json", dict(files=len(entries),
        bytes=sum(x["bytes"] for x in entries), entries=entries,
        bulk_data_policy="local payload; commit metadata and source/report code",
        provider_calls=0))
    print(f"Registered {len(entries)} payload files in {DATA}", flush=True)


if __name__ == "__main__":
    main()
