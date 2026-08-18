# TruthLease

**Consensus-backed facts with expiry, revalidation, contradiction handling, and auditable lifecycle state.**

TruthLease is a standalone GenLayer Intelligent Contract primitive. It lets other contracts register a factual proposition against an explicit evidence set and consume the result only while that result remains current.

There is intentionally **no frontend**. TruthLease is infrastructure for builders, not a product UI.

## Why TruthLease exists

Most oracle-style designs answer a question once and then persist that answer as if truth never changes. But many useful facts are time-sensitive:

- an organization has a particular officer,
- a software project currently supports a feature,
- a certification is presently valid,
- a public policy currently contains a requirement,
- a service currently publishes a stated capability.

A proposition can be well-supported today and wrong next month. TruthLease models that lifecycle explicitly.

## The primitive

A lease binds five things:

1. **Proposition** — the factual statement being evaluated.
2. **Context** — optional disambiguating information.
3. **Evidence set** — 1-5 explicit HTTPS sources that every validator independently inspects.
4. **Source policy** — guidance about what counts as authoritative/relevant evidence.
5. **TTL** — how long a `CONFIRMED` result may be consumed before it becomes `STALE`.

The contract produces one semantic state:

```text
UNVERIFIED
    │
    ├───────────────┐
    ▼               ▼
CONFIRMED       CONFLICTED
    │               │
    │               └──── revalidate ────┐
    │                                     │
    ├── time expiry ──> STALE             │
    │                    │                │
    └── revalidate ──────┼──────> SUPERSEDED
                         │
                         └──── revalidate ──> CONFIRMED / CONFLICTED / UNVERIFIED
```

`STALE` is not an LLM opinion. It is derived deterministically from the transaction timestamp and `valid_until`.

## Why this is GenLayer-native

TruthLease separates deterministic and non-deterministic work.

### Non-deterministic consensus work

For registration and revalidation:

1. The leader independently renders every registered source.
2. The leader asks its LLM to classify the proposition under a strict semantic schema.
3. Each validator independently renders the same sources and performs the same classification task.
4. A custom validator compares stable semantic fields rather than prose wording.
5. Only an accepted result is written to blockchain state.

The validator requires exact agreement on:

- lifecycle status,
- reason code,
- whether credible contradiction exists,
- whether a material change exists.

It tolerates only bounded differences in:

- source coverage (difference of at most one source, accounting for transient web availability),
- confidence (one adjacent confidence band).

The evidence summary is intentionally **not** used as an equality key because equivalent validators may phrase the same reasoning differently.

### Deterministic work

Normal contract logic handles:

- lease IDs,
- ownership,
- source-set validation,
- duplicate-source rejection,
- TTL limits,
- expiry,
- version increments,
- owner-only evidence updates,
- event history,
- consumer usability checks.

This keeps consensus focused on the part that actually requires judgment.

## Status semantics

| Status | Meaning |
|---|---|
| `UNVERIFIED` | Evidence is insufficient, unavailable, or too ambiguous to establish the proposition. |
| `CONFIRMED` | Credible current evidence materially supports the proposition without material credible contradiction. |
| `CONFLICTED` | Credible current sources materially disagree. |
| `SUPERSEDED` | Current evidence materially indicates the proposition is no longer true. |
| `STALE` | A previously confirmed lease has exceeded its deterministic TTL and needs revalidation. |

## State design

Each `LeaseRecord` stores:

```text
lease_id
owner
proposition
context
sources_json
source_policy
ttl_seconds
status
previous_status
reason_code
evidence_summary
confidence
contradiction
material_change
source_coverage
verified_at
valid_until
version
```

A separate append-only `LeaseEvent` history records lifecycle transitions.

## Public API

### `register_fact(...) -> str`

Registers a proposition and immediately runs GenLayer consensus.

```python
lease_id = truthlease.register_fact(
    proposition="Example Foundation currently lists Jane Doe as executive director.",
    context="Use the organization's current leadership information.",
    sources_json='["https://example.org/about","https://example.org/team"]',
    source_policy="Prefer first-party current leadership pages over archived or third-party summaries.",
    ttl_seconds=604800,
)
```

### `revalidate(lease_id) -> str`

Anyone may trigger a fresh adjudication using the exact registered evidence universe.

This is intentional: the lease owner cannot quietly swap evidence at revalidation time.

### `update_sources(lease_id, sources_json, source_policy)`

Owner-only. A source change immediately invalidates the old semantic result and moves the lease to `UNVERIFIED` until fresh consensus runs.

### `mark_stale(lease_id)`

Persists deterministic expiry into storage for indexers. Consumers do **not** need to call this first: `get_lease()` and `is_usable()` derive staleness automatically.

### `get_lease(lease_id)`

Returns the stored record plus its current effective status.

### `is_usable(lease_id) -> bool`

The simplest integration surface for another contract:

```python
if not truthlease.view().is_usable(lease_id):
    raise gl.vm.UserError("fresh confirmed evidence required")
```

### `get_event_count()` / `get_event(index)`

Expose append-only lifecycle history for auditing and educational inspection.

## Evidence-set security model

TruthLease does **not** claim that arbitrary user-selected URLs are automatically authoritative.

Instead it makes the evidence universe explicit and auditable:

- maximum five sources,
- HTTPS only,
- duplicate URLs rejected,
- a source policy is passed into every adjudication,
- validators independently fetch the sources,
- changing the source set invalidates the current lease.

A consuming protocol should decide what source policy/evidence set it accepts for its own use case.

## Important invariant

A confirmed lease is usable only when:

```text
stored_status == CONFIRMED
AND
current_transaction_time <= valid_until
```

No LLM gets to extend a lease merely by describing old evidence as trustworthy.

## Repository structure

```text
contracts/
  truth_lease.py             # reusable Intelligent Contract
examples/
  truth_lease_consumer.py    # minimal composition example
tests/direct/
  test_truth_lease.py        # storage, lifecycle and validator tests
docs/
  CONSENSUS.md               # validator/equivalence rationale
  SECURITY.md                # trust boundaries and fail-closed behavior
  INTEGRATION.md             # stable consumer interface
  DEPLOYMENT.md              # canonical live evidence (when available)
  STATE_MACHINE.md           # state-transition specification
scripts/
  preflight.py               # zero-dependency structural checks
SUBMISSION.md                # contribution-portal summary
```

## Development

Requirements:

- Python 3.12+
- current GenLayer tooling listed in `requirements.txt`

Install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Lint:

```bash
genvm-lint check contracts/truth_lease.py
```

Fast structural preflight:

```bash
python scripts/preflight.py
```

Direct tests:

```bash
pytest tests/direct/ -v
```

The direct suite uses mocked web/LLM responses and explicitly exercises the custom validator path with `direct_vm.run_validator()`.

## Deployment status

No canonical Studionet deployment is currently recorded. The repository does not claim live runtime evidence that it cannot prove; see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the evidence required before portal submission.

## Example use cases

TruthLease is intentionally domain-neutral. A consuming Intelligent Contract can use it for:

- expiring organization metadata,
- current certification claims,
- software/project capability attestations,
- public registry facts,
- governance prerequisites,
- time-sensitive compliance assertions,
- agent workflows that require fresh external facts before acting.

## What TruthLease is not

- It is not permanent truth storage.
- It is not a generic `AI decides X` wrapper.
- It is not a frontend application.
- It is not a replacement for deterministic oracles when exact machine-readable data is available.
- It does not hide source selection; source provenance is part of state.

## Design principles

1. **Consensus must be load-bearing.** Remove GenLayer consensus and the semantic classification cannot safely become shared state.
2. **Do not ask AI to decide deterministic facts.** Expiry, ownership, versions and bounds are normal code.
3. **Validators verify independently.** They do not merely check that the leader returned valid JSON.
4. **Equivalence is semantic.** Stable decision fields matter; prose wording does not.
5. **Freshness is first-class state.** A true fact can age out without becoming false.
6. **Evidence changes are state changes.** Swapping sources cannot silently inherit an old verdict.

## License

MIT
