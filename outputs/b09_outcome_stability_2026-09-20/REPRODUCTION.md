# Reproduce the two phases

From `/Users/dgrissen/Dev/delta_bomb`, use
`/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python` with `-B` and
`OPENBLAS_NUM_THREADS=1`.

```sh
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B -m unittest discover -s outputs/b09_outcome_stability_2026-09-20 -p test_stability.py
OPENBLAS_NUM_THREADS=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B outputs/b09_outcome_stability_2026-09-20/stability.py delete
```

The initial `stability.py ci` phase already ran and refuses to overwrite its
namespace. It froze source/code/persona hashes and published TABLES_WITH_CI.md
before the local Charlie interpretation was written. The deletion phase requires
those original hashes and the interpretation file, then verifies every recount.
Do not remove the original namespace to change this analysis. A changed question
or method needs a new namespace.

No new data or network connection is needed. The two source ledgers retain
their prior native-price verification. Bulk derived data stay locally in the
central data repository under its existing ignore policy; receipts/dictionaries
retain provenance. Dates without signals are included in both phases.
