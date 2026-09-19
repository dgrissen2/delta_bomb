# Third tranche: every remaining verifiable above-VT date

Written before third-tranche signal generation or outcome scoring on19 September2026.
Window: every completed NYSE session from2025-01-01 through2026-09-18. Future2026
sessions are unavailable, not missing historical data. No random sample or date cap.

## Selection and the publication-format correction

Audit the full429-session calendar. Require positive same-date SPX Vol Trigger,
supported by saved same-date preopen note labels, a complete valid390-minute native
SPX session, and09:30 open strictly above VT. Preserve all excluded dates/reasons.
If a dated corrected CSV record exists, every usable preopen note VT must agree
with it. A conflict is excluded, never resolved by choosing a favorable value.
If the CSV has no date, a unique consistent directly observed preopen-note VT may
supply that day's level; mark this provenance separately. No next-day shift,
carried-forward level, after-open note or inferred VT is allowed.

The previous parser required a `Date` metadata field and exact first-heading time
equality. Many older saved notes instead contain `Published`, an explicit Eastern
outer heading and a sometimes earlier preopen content heading. The new parser
reads both metadata formats and every publication heading before article content
within the first14 lines. Require at least one explicit Eastern heading, every
publication label on the requested date, correct EST/EDT calendar usage, and the
latest label strictly before09:30. Preserve every timestamp discrepancy. An after-
open revision label, different-day label or malformed publication metadata fails.
Scraped-at is not publication time. Source labels still do not prove contemporaneous
capture or absence of later revisions. Record old and corrected acceptance side
by side; this is an explicit evidence-ingestion correction, not an unchanged sampler.

Keep original50 and added100 memberships unchanged. All qualifying dates outside
those150 and the ten original dashboard-development dates form `third_tranche`.
The ten development dates are rerun as a separate descriptive group, included only
in the separately labeled all-qualifying total. They are never new validation.
Report third-tranche legacy-eligible versus recovered-publication-format dates
separately. Do not substitute dates after seeing signals or outcomes.

Use available immutable native price caches first. If essential coverage is missing,
use ThetaData Python SDK `index_history_ohlc` at1m, preserve raw responses, timestamps,
request metadata and errors under this new central namespace. At most two concurrent
calls; one logged retry for a transient transport error. No synthetic observations,
no repaired bad OHLC and no partial-session promotion to390minutes. No option-IV
fetch is necessary for these price-only B01–B10 recipes.

## Frozen experiment

Import the exact eight rule snapshots and causal scoring helpers from the committed
150-date replay; hash them before outcomes. Reproduce that replay's7,313 distinct
opportunities and7,465 raw records on its original150 dates before trusting extension
results. Use complete available chronological warmup, preserve previously selected
sources, append later sessions, and disclose any changes before scoring. Keep all
thirteen rows, original clocks, state machines, EMA/ATR/RSI conventions and knobs.

Primary gate: all prior minute lows from09:30 strictly above that day's VT and entry
open above VT. A prior breach blocks remaining entries that day. Never inspect the
entry bar's subsequent low or future full-day status. Entry-above and opening-only
populations remain diagnostics, clearly distinguished from primary strict VT.

Success: +5 before−15 within60 native minute intervals starting at entry open.
Both first barriers in one minute are ambiguous; neither/ambiguous stay in N.
Later reversal after +5 is irrelevant. Count unique variant/date/entry-minute
opportunities while preserving all overlapping setup records.

Report original50, added100, third tranche, each third-tranche year, original150,
all non-development dates, development10 and all qualifying dates. Show N, targets,
adverse, neither, active dates and95% whole-date bootstrap intervals (10,000 draws,
seed20260919), with zero-event dates retained. Show first-per-day and fixed60-minute
spacing; no cooldown optimization. Reuse the earlier diagnostic cut points rather
than fitting new ones. No IV overlay and no selective reporting of the prior top rows.

The inherited earlier-hour B01 comparison is only a selected-path timing diagnostic:
the later trigger selects information after the control's entry. Do not call its
difference causal uplift or use it to promote a rule. The third tranche is a
historical extension with a different date mix, not a randomized or guaranteed
unseen holdout. Even successful rows remain subject to dependence and prior reuse.

## Storage and completion

Project source and findings:
`/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_third_tranche_2026-09-19/`.
New data:
`/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_third_tranche_2026-09-19-v1/`.
Preserve previous studies and dashboard files. Freeze population, provenance,
input hashes and event identities before outcomes. Independently check every new
native score and prior-only VT gate; reconcile all rows. Journal dataset creation,
update namespace/root dictionaries and commit only this isolated work.
