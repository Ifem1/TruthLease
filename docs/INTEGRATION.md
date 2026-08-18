# Integrating TruthLease

Treat TruthLease as a specification-bound freshness oracle. Pin the expected digest at consumer deployment and use the stable view surface:

```python
if not truthlease.view().is_usable_for(lease_id, expected_spec_hash):
    raise gl.vm.UserError("matching fresh confirmed TruthLease required")
```

`is_usable_for` is the recommended machine-readable gate. It additionally requires the stored `spec_hash` to equal the consumer-pinned hash. The hash canonically binds proposition, context, sorted source set, and source policy. TTL is deliberately excluded: it controls how long a confirmation remains fresh, not which factual specification is being trusted. `is_usable` is only appropriate when the consumer has already pinned the corresponding specification by some other means. Do not use confidence, source coverage, or free-form evidence summaries as settlement inputs.

See `examples/truth_lease_consumer.py` for a minimal interface-only composition example.
