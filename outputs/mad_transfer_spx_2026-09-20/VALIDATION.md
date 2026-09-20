# Local validation

Ten boundary tests and Ruff passed after implementation.

```text
/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B -m unittest discover -s /Users/dgrissen/Dev/delta_bomb/outputs/mad_transfer_spx_2026-09-20 -p test_logic.py
..........
----------------------------------------------------------------------
Ran 10 tests in 0.015s

OK
```

```text
/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B -m ruff check /Users/dgrissen/Dev/delta_bomb/outputs/mad_transfer_spx_2026-09-20
All checks passed!
```
