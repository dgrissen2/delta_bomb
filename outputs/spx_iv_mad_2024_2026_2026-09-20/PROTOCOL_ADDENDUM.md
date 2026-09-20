# Additive endpoint-pairing repair — June 9, 2026

After all native responses were captured, the unchanged key-equality check stopped
derivation on one date. The IV endpoint returned 79,200 rows, versus 36,000 first-
order Greek rows for the same request parameters and expiry. Every Greek key is
present in IV; 43,200 IV-only rows have no requested Greek counterpart.

Before deriving this date, freeze this narrow preprocessing repair and its inputs:
retain every native Greek key and its unchanged IV counterpart, reject duplicate
keys or any missing Greek counterpart, and require the observed strict-superset
shape. Do not apply an arbitrary inner join, infer a Greek, synthesize a quote,
expand strikes, or change any scientific/quality function. The original endpoint
responses, day manifest and collection manifest remain immutable. Store the paired
IV view separately, with a receipt linking it back to both original native hashes.

Run the unchanged endpoint price/timestamp checks and IV/recovery rules on that
paired view, then the original window and MAD code. The derived day's input hashes
reference the paired IV view and original Greek response; the pairing receipt
supplies the upstream provenance. The full runner reuses this verified per-date
output. Its original collection ledger continues to describe the native responses.

Six boundary tests cover exact value preservation, no dropped Greek keys,
duplicates, unsupported asymmetry, non-superset refusal and retained quote checks.
This fixes input alignment, not a trading rule. No outcomes were inspected and
no extra provider request was made. The original protocol remains preserved;
endpoint_pairing_freeze.json records this additive exception explicitly.
