"""Sparse Studionet proof tests.

These tests use genlayer-py's typed ``args`` transport. They are opt-in because
the signer must be supplied by the operator through ``GENLAYER_PRIVATE_KEY``;
ordinary CI never contacts public Studionet.
"""
import hashlib
import json
import os
import pytest

pytestmark = pytest.mark.integration


ADDRESS = os.getenv("TRUTHLEASE_STUDIONET_ADDRESS", "0x706Dba371c2E7907c4da395C6345f636b438c09e")
SOURCE = "https://www.iana.org/domains/reserved"
PROPOSITION = "IANA maintains a Reserved Domains page."
CONTEXT = "Use the current first-party IANA documentation page."
POLICY = "Prefer the current first-party IANA page."


def _client():
    key = os.getenv("GENLAYER_PRIVATE_KEY")
    if not key:
        pytest.skip("set GENLAYER_PRIVATE_KEY to run sparse Studionet integration tests")
    from eth_account import Account
    from genlayer_py.client import create_client
    from genlayer_py.chains import studionet
    return create_client(studionet, endpoint=os.getenv("GENLAYER_RPC", "https://studio.genlayer.com/api"), account=Account.from_key(key))


def _expected_hash():
    canonical = json.dumps({"proposition": PROPOSITION, "context": CONTEXT,
                            "sources": [SOURCE], "source_policy": POLICY},
                           sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def test_studionet_spec_hash_and_registration_readback():
    client = _client()
    args = [PROPOSITION, CONTEXT, json.dumps([SOURCE]), POLICY, 3600]
    expected = _expected_hash()
    assert client.read_contract(ADDRESS, "compute_spec_hash", args=args) == expected
    tx = client.write_contract(ADDRESS, "register_fact", args=args)
    receipt = client.wait_for_transaction_receipt(tx)
    assert receipt.status_name == "ACCEPTED"
    lease_id = receipt.return_data
    lease = client.read_contract(ADDRESS, "get_lease", args=[lease_id])
    assert lease["spec_hash"] == expected
    assert lease["status"] == "CONFIRMED"
    assert client.read_contract(ADDRESS, "is_usable", args=[lease_id]) is True
    assert client.read_contract(ADDRESS, "is_usable_for", args=[lease_id, expected]) is True
    assert client.read_contract(ADDRESS, "is_usable_for", args=[lease_id, "0" * 64]) is False
