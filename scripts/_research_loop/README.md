# Native Codex research artifact adapter

This project uses the canonical Charlie McElligott and Quant personas inside the current
Codex task. Both are Codex primary responses. Their participation is **not** an independent
cross-model review. There are no model calls, subprocess launches, fallback engines, twin
blocks, or generated agreement labels in this adapter.

`contracts.py`, `verify_round.py`, `synthesize.py`, and `promote.py` were vendored from the
global research-loop helpers. Only contracts and verification were adapted. Synthesis and
promotion remain byte-for-byte copies. The canonical findings and memo templates were
copied unchanged into `hypothesis_tracking`. `source_manifest.json` records the original
absolute source paths, SHA256 hashes, and adapted file hashes.

The original seed, findings sections, note backlinks, commentary, proposal count/coverage,
synthesis traceability, promotion-ledger materialization, and memo timeline/finalization
gates remain. This adds successful Codex-primary provenance, exact configured-persona
coverage, round/ID consistency, raw-file hashes, and equality with the saved raw response.
Hashes detect changed bytes; they do not independently attest which model produced text.
The operator must save the actual agent response, never a fabricated response attributed
to an agent.

## Configuration

The task owner maintains `hypothesis_tracking/research_loop.yml`:

```yaml
prefix: PNDR
engine_mode: codex_only
personas: [charlie-mcelligott, quant]
persona_source: global
round_cap: 3
K: 2
```

Both persona IDs are mandatory, with no other personas allowed. The optional
`persona_paths` mapping may specify absolute definition paths; defaults are the canonical
global files under `/Users/dgrissen/.config/skillshare/personas`. Omit the legacy `codex`
twin flag. `codex: true` is rejected because it would incorrectly request a second engine.
No config, seed hypothesis, index, findings note, or protocol is authored by `emit.py`.

## Save the actual raw responses

Each phase reads exactly these files, without rewriting them:

```text
outputs/persona_raw/roundN/PHASE/charlie-mcelligott.json
outputs/persona_raw/roundN/PHASE/quant.json
```

`PHASE` is `seed`, `commentary`, or `proposals`. Seed expansion belongs to round 1.
Preserve the agent's response bytes when saving JSON, including its original whitespace.
The expected schemas are:

```json
{
  "hypotheses": [{
    "claim": "A falsifiable claim",
    "target": "Measured outcome",
    "pass_criterion": "Frozen pass rule",
    "controls": "Fixed comparison"
  }],
  "simple_protocol": {"selection": "Frozen rule"}
}
```

Seed responses contain one to three hypotheses; additional fields such as
`minimal_feasible_dataset` and `data_stopping_rules` are preserved in full.
The original `outcome` spelling is accepted in place of `target`; neither the raw
response nor its emitted copy is normalized or rewritten.

```json
{
  "by_hid": {
    "H-PNDR-001": {
      "interpret": "What the actual evidence establishes.",
      "act": "What should happen next."
    }
  }
}
```

Both commentary responses must cover the same IDs. The verifier requires commentary
for every active findings note in the requested round.

```json
{
  "candidates": [{
    "candidate_key": "audit-forward-support",
    "kind": "experiment",
    "title": "Audit historical forward support",
    "priority": "high",
    "parent": "H-PNDR-001",
    "rationale": "A missing input prevents the proposed measurement.",
    "falsification": "The archived snapshots cannot establish the required input.",
    "decision_impact": "Determine whether the measurement can proceed."
  }],
  "reprioritize": []
}
```

Proposal `kind` is `hypothesis` or `experiment`; experiments require a parent ID.
`reprioritize` entries use `id`, `action` (`deprioritize` or `drop`), and `why`.
Two distinct candidate keys are required when `K: 2`, unless the synthesis records
an explicit deferred round and reason. Both raw persona responses remain mandatory.

## Assemble and verify

All commands accept `--project`, defaulting to the current working directory:

```sh
python3 scripts/_research_loop/emit.py --project /Users/dgrissen/Dev/delta_bomb --phase seed --round 1
python3 scripts/_research_loop/emit.py --project /Users/dgrissen/Dev/delta_bomb --phase commentary --round 1
python3 scripts/_research_loop/emit.py --project /Users/dgrissen/Dev/delta_bomb --phase proposals --round 1
python3 scripts/_research_loop/synthesize.py --project /Users/dgrissen/Dev/delta_bomb --round 1
python3 scripts/_research_loop/promote.py --project /Users/dgrissen/Dev/delta_bomb --round 1
python3 scripts/_research_loop/verify_round.py --project /Users/dgrissen/Dev/delta_bomb --round 1
```

Emission writes canonical `outputs/seed_expansion.json`,
`outputs/commentary/roundN/H-PNDR-001.json`, and `outputs/proposals/roundN.json`.
Seed/commentary persona blocks use a `primary` object with `engine: codex`,
`producer_status: ok`, `raw_path`, and `raw_sha256`. Seeds preserve the whole response
in `primary.response`; commentary preserves `primary.interpret` and `primary.act`.
Proposal blocks retain the upstream flat layout with the same native producer metadata,
so synthesis and promotion do not need a second compatibility layer.

Synthesis groups proposals by candidate key. The task owner reviews its classifications
and records any decision to defer or drop before promotion. Promotion materializes the
retained decisions and keeps an idempotence ledger. The round cannot close until findings,
commentary, proposals, synthesis, required materialization and the memo pass verification.
At the configured final round, the memo must be finalized; an inconclusive result is valid.

## Targeted checks

```sh
/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -m pytest tests/test_pandar_research_framework.py -q
```

The tests were written first and confirmed failing before this adapter existed. They
cover provenance and payload tampering, missing personas/raw inputs, wrong rounds/fake
twins, the retained back-half failures, and a complete native round with real idempotent
materialization.
