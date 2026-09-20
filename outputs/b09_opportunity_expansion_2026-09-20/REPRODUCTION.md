# Reproduce the bounded expansion study

Python: `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python`.
Run from `/Users/dgrissen/Dev/delta_bomb`; set OPENBLAS_NUM_THREADS=1.

```sh
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B -m unittest discover -s outputs/b09_opportunity_expansion_2026-09-20 -p test_study.py
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/b09_opportunity_expansion_2026-09-20/analyze.py
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/b09_opportunity_expansion_2026-09-20/verify.py
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/b09_opportunity_expansion_2026-09-20/prepare_pilot.py
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/b09_opportunity_expansion_2026-09-20/report.py
```

Preparation already ran and is frozen. `prepare.py` intentionally refuses to
overwrite freeze.json. Do not delete the original freeze to rerun with altered
definitions. A changed experiment needs a new namespace/protocol. Analysis checks
all frozen inputs and prepared artifacts before attaching unchanged outcomes.
Source and output hashes live in the central namespace's receipts.

Central namespace:
`/Users/dgrissen/Dev/central_trade_data/thetadata/b09_opportunity_expansion_2026-09-20-v1`.
Bulk CSV/Parquet are local research data under existing git-ignore policy;
metadata, code and findings are committed. Original source datasets are untouched.
No service, browser, independent reviewer or provider connection is required.
