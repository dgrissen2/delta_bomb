# Reproduce the combined expansion

From `/Users/dgrissen/Dev/delta_bomb`:

```sh
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B -m unittest discover -s outputs/b09_combined_expansion_2026-09-20 -p test_combined.py
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/b09_combined_expansion_2026-09-20/combined.py
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/b09_combined_expansion_2026-09-20/verify.py
```

`combined.py --prepare` already ran and refuses to overwrite freeze.json. Do not
remove the freeze to change the experiment; a changed rule needs another namespace.
The scoring step verifies all frozen inputs before attaching outcomes.

Data live in
`/Users/dgrissen/Dev/central_trade_data/thetadata/b09_combined_expansion_2026-09-20-v1`.
CSV/Parquet remain local under existing data-cache ignore policy; tracked metadata
contains hashes and table schemas. Earlier source memberships, outcomes and native
bars are unchanged. No network connection or new data collection is required.
