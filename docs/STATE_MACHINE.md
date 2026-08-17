# TruthLease State Machine

TruthLease distinguishes **semantic invalidation** from **time expiry**.

## States

### `UNVERIFIED`
The registered evidence does not currently establish the proposition strongly enough for downstream consumption.

### `CONFIRMED`
Current registered evidence materially supports the proposition without a material credible contradiction.

A `CONFIRMED` record receives a deterministic `valid_until = verified_at + ttl_seconds`.

### `CONFLICTED`
Credible registered sources materially disagree.

### `SUPERSEDED`
Current evidence indicates that the proposition is no longer true, especially when the proposition may previously have been correct.

### `STALE`
A previously `CONFIRMED` result has passed its `valid_until` time.

This state is deterministic. `get_lease()` and `is_usable()` derive it even before `mark_stale()` materializes it into storage.

## Transition table

| From | Trigger | To | Consensus? |
|---|---|---|---|
| none | `register_fact` | `CONFIRMED` / `CONFLICTED` / `SUPERSEDED` / `UNVERIFIED` | Yes |
| any existing | `revalidate` | `CONFIRMED` / `CONFLICTED` / `SUPERSEDED` / `UNVERIFIED` | Yes |
| `CONFIRMED` | time > `valid_until` | effective `STALE` | No |
| expired `CONFIRMED` | `mark_stale` | stored `STALE` | No |
| any | owner `update_sources` | `UNVERIFIED` | No |
| `STALE` | `revalidate` | consensus state | Yes |

## Source update invariant

A source change cannot inherit an old verdict.

```text
old evidence + CONFIRMED
        │
        └── update_sources()
                 │
                 ▼
             UNVERIFIED
                 │
                 └── revalidate() ── consensus ──> new state
```

This prevents an owner from replacing a strong evidence set with a weak one while preserving a previous confirmation.

## Freshness invariant

A lease is consumable only when its **effective** state is `CONFIRMED`.

```text
usable = stored_status == CONFIRMED
         AND valid_until > 0
         AND current_transaction_time <= valid_until
```

## Version invariant

Every state-changing lifecycle operation increments `version`:

- initial registration creates version `1`,
- revalidation increments it,
- source updates increment it,
- materializing expiry increments it.

Each transition also appends a `LeaseEvent` containing the lease ID, version, transition type, from/to states, timestamp and reason code.

## Why `SUPERSEDED` is different from `CONFLICTED`

`CONFLICTED` means credible sources currently disagree.

`SUPERSEDED` means current evidence materially overturns the proposition. This is useful for facts that age naturally, such as roles, certifications, published capabilities or organizational metadata.

## Why `STALE` is different from `SUPERSEDED`

`STALE` does **not** mean the proposition became false. It means TruthLease refuses to keep treating an old confirmation as fresh without new consensus.

That distinction is the core primitive:

```text
expired evidence != false proposition
```
