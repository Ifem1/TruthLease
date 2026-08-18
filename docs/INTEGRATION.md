# Integrating TruthLease

Treat TruthLease as a narrow freshness oracle. A consuming Intelligent Contract needs only the stable view surface:

```python
if not truthlease.view().is_usable(lease_id):
    raise gl.vm.UserError("fresh confirmed TruthLease required")
```

`is_usable` is the recommended machine-readable gate. It is true only for a `CONFIRMED` record whose `valid_until` has not passed. Use `get_lease` when an application needs the audit fields, current effective status, evidence URLs, version, or expiry. Do not use the free-form `evidence_summary` as a settlement input.

See `examples/truth_lease_consumer.py` for a minimal interface-only composition example.
