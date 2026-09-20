# Scope clarification before any outcome analysis

The user's follow-up asks specifically about the data needed for the earlier IV
versions, excluding MAD. Complete the existing signal-rule rerun first. Historical
MAD calibration and the newly proposed ≥1/≥2 magnitude cutoffs in PROTOCOL.md are
not part of this comparison and no additional MAD history will be fetched for it.
They remain explicitly inventoried as untested here. Balanced quote recovery can
be compared as a measurement sensitivity without computing historical MAD.

The initial protocol listed a broader future inventory; this narrows the executable
scope without looking at new outcomes. Collection runs only `inputs.py research`.
The calendar's earlier sessions also support prior-session weight lookup and are
not evidence that their option histories were fetched. The first collection version
also lacked the adapter from inherited `expirations` to `selected`; version two fixes
that naming mismatch without changing the expiry rule or any captured observation.

Operational amendment: four independent native requests may run concurrently instead
of two. No request parameters, data budget, retries or statistical rules change. This
reduces elapsed time for the outstanding 2024 collection. Restart the first collector
only after its in-flight requests finish; already captured responses are reused.

Inference settings: 5,000 whole-date bootstrap draws, seed 20260919. Exploratory
intervals are not adjusted for the many reported comparisons. First-per-day and
spaced rules filter before thinning and can move the chosen entry; winner retention
therefore counts actual shared winning date/minute identities, not a ratio falsely
implying that different timed entries were retained.
