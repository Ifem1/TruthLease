# Deployment evidence

| Field | Value |
|---|---|
| Date | 2026-08-18 |
| Network | GenLayer Studionet (chain 61999) |
| Source commit | `cc1b4db6f8546bcf1958b227d8c1644966248d81` |
| Contract | `0x706Dba371c2E7907c4da395C6345f636b438c09e` |
| Deployment transaction | `0x58ba24897decd2a163653862c726ffbed063892047ca89687d00feec3fd3eee8` |
| Lifecycle | `ACCEPTED` |
| Consensus | `MAJORITY_AGREE` (3 agree; remaining validators idle after quorum) |
| Deployer | `0xf8531058e0a3df4ae1d58c11529bcdecb9aa4487` |

The deployed `contracts/truth_lease.py` blob is `7d55700ca4350ec3a2161b1a3cc5bbb18c855b58` at the deployment commit. Later commits must retain this exact blob or a new canonical deployment is required. The prior deployment `0xd638D12370b30877Bdc531E0aD6c2D48a90e520d` is superseded.

## Runtime evidence

The first runtime call intentionally demonstrated a fail-closed argument-validation path:

- Transaction: `0x80b3e0b0ebdc3b3065c8003a32b962589052f44e5e65a191c9ae51f7b3131b0d`
- Lifecycle: `ACCEPTED`; consensus: `MAJORITY_AGREE`
- Result: rollback, `sources_json must be valid JSON`

The CLI encoded the JSON-string argument without quotation marks, so no lease was created. This is valid negative evidence only; it is not a successful consensus assessment. A separate successful `register_fact` runtime path remains required before final portal submission.
