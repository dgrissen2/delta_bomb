# Reproduction and artifact ownership

Runtime used: `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python`.
Working directory: `/Users/dgrissen/Dev/delta_bomb`.

The executed sequence was test_logic.py (expected failure before logic existed),
logic implementation and passing tests, prepare.py, analyze.py, verify.py,
gap_detail.py, report.py and register.py. No fetched market data.

Safe repeat verification:

```sh
/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B -m unittest discover -s outputs/mad_transfer_spx_2026-09-20 -p test_logic.py
/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B -m ruff check outputs/mad_transfer_spx_2026-09-20
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/mad_transfer_spx_2026-09-20/verify.py
```

The verifier writes its verification receipt in this derived namespace only.
prepare.py refuses to replace an existing namespace; analyze.py refuses to replace
a completed analysis. A deliberate new execution must use a new versioned namespace
and its own freeze. Do not delete/overwrite a frozen run to change a rule.

The protocol and four initial Python files were hashed before outcome attachment.
Verification/report/registration/support-inspection scripts were added afterward;
their receipts hash their own implementations. They do not change rules or fit
thresholds. Full initial memberships, source hashes and pre-outcome participation
remain intact. Existing B09 counts and the two reviewer-inspected sign controls
were already known and are explicitly disclosed.

All data and output tables live at:
`/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1`.
Its inventory includes every local payload's hash/size and Parquet row/schema
metadata. Source measurements and price outcomes remain in their original namespaces.

Project code, protocol, findings, review compliance and learning notes are versioned
in this slug; central metadata/dictionary/changelog are versioned in central_trade_data.
Bulk data stay local under that repository's normal ignore policy. Commits do not
imply a new independent review or prospective validation.
