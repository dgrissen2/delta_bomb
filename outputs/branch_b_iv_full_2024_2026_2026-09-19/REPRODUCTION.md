# Reproducing the previous-rule IV comparison

Project directory:
`/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19`.
Central data directory:
`/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1`.

Use `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B` from the project
root. Tests use `python -B -m pytest -q` against this directory; Ruff checks the
same directory. Python optimization mode is deliberately rejected.

The native collection is complete. Do not redownload existing responses, replace
the collection namespace, or run MAD history for this experiment. Existing input
parameters, native hashes and source-code versions are recorded in the central
manifests. Earlier source versions and a copy of the execution dependencies are
preserved under `source_snapshots/`. Shared dependencies still live in the earlier
research directories; their exact expected hashes are in execution_freeze.json.

The computation order is:

1. `inputs.py research` collects only missing dated sector inputs. This is a
   resumable acquisition step, not a request to repeat completed downloads.
2. `features.py derive` constructs cached sector-day minute series and balanced
   nearby-recovery windows. A captured day is not a claim that every minute is valid.
3. Freeze the execution dependencies with `provenance.execution_freeze()` before
   assembling entry features or attaching any new outcomes.
4. `features.py events` builds the strictly prior reference, separate contemporaneous
   breakout update, and separately labeled post-entry measurements. Three local
   processes handle independent dates; results retain deterministic date order.
5. `baskets.py` constructs every fixed rule and the yes/no/unknown states.
6. `match_features.py` freezes comparable-price pair identities without reading scores.
7. `analyze.py` joins unchanged +5/−10 scores and produces full tables, unions,
   matching summaries, price-context diagnostics and whole-date uncertainty.
8. `checkpoint.py` evaluates genuinely new T+15 entries with fresh VT admission
   and their own sixty-minute target/stop window.
9. `verify.py` audits native provenance, original measurements, independent feature
   arithmetic, every reported summary row, and deduplicated opportunity unions.
10. `report.py` renders only the exact tables whose hashes passed verification.

Numerical outputs are immutable. An unchanged rerun must reproduce them. A changed
source, table or input fails its checks; a substantive future correction needs a
new version or an explicitly documented, preserved correction, not deletion of a
freeze to make the run succeed. Rendering the Markdown/plot does not authorize a
new strategy rule or threshold.

`weights.py` is the separately completed historical issuer retrieval/validation
step. Its accepted weights are in the parser-versioned validation directory. The
raw response body being present does not make it accepted. Missing classifications
remain unknown; do not substitute current weights or drop missing sectors from
the eleven-sector denominator.

For Markdown rendering, the working Python environment lacks the optional
`tabulate` package. Append the existing
`/Users/dgrissen/Dev/virtualenvs/trade_catalog/lib/python3.13/site-packages` directory
to `sys.path` after the working environment before importing `report`. This finds
tabulate 0.10.0 and its version metadata without changing either environment.
The source/version is recorded in rendering_dependency_v2.json. Then run
`additive_audit.py` and `delivery_tables.py` for the final review disclosures.

`register_data_safe.py` is the one-time final inventory/journal entry point after
completed review and verification. The original reviewed `register_data.py` is
preserved for source provenance and is superseded for execution by the safe writer.
The replacement stages a durable roll-forward plan, writes each file atomically,
detects intervening registry edits and writes the completion inventory last.
Interrupted registration resumes from that plan. The root data dictionary and
changelog must be committed together with the namespace inventory.

This remains a research comparison of frozen recipes. No dashboard, strategy
engine, execution service, order, or original historical score is changed.
