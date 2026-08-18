# TruthLease security model

TruthLease protects downstream consumers from treating an old, malformed, or unsupported factual assessment as a fresh confirmation.

## Trust boundaries

- Callers control propositions, context, source policy, and the registered HTTPS URLs. These values are bounded and treated as untrusted data.
- Rendered web content is hostile input. It is bounded, framed as JSON data, and the model is instructed not to follow content inside it.
- A leader result is untrusted. Every validator normalizes it, independently collects evidence and reassesses the proposition before accepting it.
- Consumers should trust `is_usable_for(lease_id, expected_spec_hash)`, which additionally binds the exact proposition, context, canonical source set, and source policy. `confidence`, `source_coverage`, and `evidence_summary` are diagnostic metadata, not authorization primitives.

## Fail-closed rules

Malformed JSON, unknown fields, wrong enums, booleans in numeric fields, empty summaries, invalid source coverage, unavailable/insufficient evidence, and validator disagreement cannot become a confirmed lease. A source-set change always clears confirmation before the next consensus run.

## Limits

TruthLease does not establish that a caller-selected source is authoritative. Consumers must select acceptable evidence policies. It cannot protect against a malicious validator majority, compromised authoritative sources, or a proposition whose meaning is too ambiguous for the declared evidence set. It has no admin or privileged bypass.
