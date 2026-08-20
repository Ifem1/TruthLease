# TruthLease — standalone Intelligent Contract

- **Category:** Standalone Intelligent Contract
- **Purpose:** Consensus-backed, expiring factual leases for contracts that need a fresh external claim before acting.
- **Repository:** https://github.com/Ifem1/TruthLease
- **Canonical Studionet address:** `0x706Dba371c2E7907c4da395C6345f636b438c09e`
- **Deployment transaction:** `0x58ba24897decd2a163653862c726ffbed063892047ca89687d00feec3fd3eee8` (`ACCEPTED`, `MAJORITY_AGREE`)

TruthLease uses GenLayer consensus for the load-bearing semantic task: independent validators retrieve the registered evidence set and assess whether it currently supports, conflicts with, overturns, or cannot establish a proposition. Exact lifecycle semantics are compared; bounded source-availability and confidence differences are tolerated. Deterministic code controls IDs, ownership, bounds, expiry, state mutation, and downstream usability.

It is not a thin LLM wrapper: the leader result is treated as untrusted, parsed against a closed schema, and independently re-derived by validators. Malformed output and disagreement fail closed. Its reusable surface is `is_usable(lease_id)` plus the auditable `get_lease` view.

Reviewer fast path: run `python scripts/preflight.py`, `pytest tests/direct -v`, and `genvm-lint check contracts/truth_lease.py`; then read `docs/CONSENSUS.md`, `docs/SECURITY.md`, and `docs/INTEGRATION.md`.

Limitations: evidence authority remains a consumer policy decision; a malicious validator majority or compromised source cannot be eliminated by the contract. The canonical deployment and current-source live registration/revalidation are verified; the recorded negative evidence remains the fail-closed input-validation transaction.
