# TruthLease Consensus Model

TruthLease treats consensus as a semantic verification protocol, not a formatting check.

## What validators are deciding

Given:

- a proposition,
- context,
- an explicit set of 1-5 HTTPS sources,
- a source policy,
- the lease's previous effective status,

validators independently answer one question:

> What lifecycle state is justified by the current registered evidence?

The consensus-produced states are:

- `CONFIRMED`
- `CONFLICTED`
- `SUPERSEDED`
- `UNVERIFIED`

`STALE` is deliberately excluded because expiry is deterministic.

## Leader path

The leader:

1. renders each registered source,
2. labels unavailable sources explicitly,
3. supplies bounded source text to its LLM,
4. asks for a strict structured assessment,
5. proposes the parsed assessment as the nondeterministic result.

The assessment schema is:

```json
{
  "status": "CONFIRMED",
  "reason_code": "CURRENTLY_SUPPORTED",
  "confidence": "HIGH",
  "contradiction": false,
  "material_change": false,
  "source_coverage": 2,
  "evidence_summary": "Current first-party sources support the proposition."
}
```

## Validator path

A validator does **not** merely validate that the leader returned legal enum values.

It independently performs the evidence fetch and assessment again, then compares the leader's semantic result with its own.

### Exact-match fields

These must agree exactly:

- `status`
- `reason_code`
- `contradiction`
- `material_change`

These fields determine the actual lifecycle meaning written to state.

### Bounded-tolerance fields

`source_coverage` may differ by at most one registered source. This accounts for temporary availability differences between validator web requests without allowing radically different evidence bases to be called equivalent.

`confidence` may differ by one adjacent band:

```text
LOW <-> MEDIUM <-> HIGH
```

`LOW` versus `HIGH` is rejected as a material difference.

### Non-equivalence field

`evidence_summary` is stored for auditability but is not compared for textual equality. Two validators can reach the same lifecycle conclusion with materially equivalent reasoning expressed in different words.

## Why not `strict_eq`

Both web rendering and LLM output are nondeterministic. Exact byte equality would be brittle and would incorrectly reject semantically equivalent results.

## Why not leader-output-only validation

A validator that checks only:

```text
status in allowed_statuses
summary != empty
confidence in range
```

would establish only that the leader formatted its answer correctly. It would not establish that the answer is supported by evidence.

TruthLease therefore re-runs the evidence collection and assessment on every validator.

## Why a custom validator

The lifecycle classification has several fields with different equivalence requirements:

- some require exact semantic equality,
- some allow bounded tolerance,
- free-form prose should not be an equality key.

A custom `gl.vm.run_nondet_unsafe` leader/validator pair makes those rules explicit in code.

## Failure behavior

A validator rejects when:

- the leader result is an exception,
- the leader result cannot be normalized,
- lifecycle classification differs,
- contradiction/material-change semantics differ,
- source coverage diverges by more than one,
- confidence differs by more than one band.

Network consensus then determines whether the transaction's proposed nondeterministic result is accepted.

## Deterministic boundary

After consensus, only deterministic code may mutate lease state.

The LLM does not control:

- lease identifiers,
- ownership,
- source count/URL validation,
- TTL bounds,
- timestamps,
- expiry,
- version numbers,
- event indexing,
- source-update permissions.

This separation is a core TruthLease invariant.
