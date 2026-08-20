"""Sparse official gltest Studionet proof (run explicitly, never normal CI)."""
import hashlib
import json

import pytest
from gltest import get_contract_factory, get_default_account

pytestmark = pytest.mark.integration

ADDRESS = "0x706Dba371c2E7907c4da395C6345f636b438c09e"
SOURCE = "https://www.iana.org/domains/reserved"
PROPOSITION = "IANA maintains a Reserved Domains page."
CONTEXT = "Use the current first-party IANA documentation page."
POLICY = "Prefer the current first-party IANA page."


def expected_hash():
    canonical = json.dumps({"proposition": PROPOSITION, "context": CONTEXT,
                            "sources": [SOURCE], "source_policy": POLICY},
                           sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def receipt_field(receipt, field, default=...):
    """Support the mapping receipts returned by current genlayer-py."""
    if isinstance(receipt, dict):
        if field in receipt:
            return receipt[field]
        if default is not ...:
            return default
        raise KeyError(field)
    return getattr(receipt, field)


def receipt_return_data(receipt):
    """Read the return value from legacy or current simplified receipts."""
    if isinstance(receipt, dict) and "return_data" in receipt:
        return receipt["return_data"]
    leader = receipt["consensus_data"]["leader_receipt"][0]
    readable = leader["result"]["payload"]["readable"]
    return json.loads(readable)


@pytest.fixture(scope="module")
def contract():
    factory = get_contract_factory(contract_file_path="truth_lease.py")
    return factory.build_contract(ADDRESS, account=get_default_account())


def test_studionet_registration_readback_and_revalidation(contract):
    hash_args = [PROPOSITION, CONTEXT, json.dumps([SOURCE]), POLICY]
    args = hash_args + [3600]
    spec = expected_hash()
    assert contract.compute_spec_hash(args=hash_args).call() == spec

    receipt = contract.register_fact(args=args).transact(
        # genlayer-py expresses this value in milliseconds.  Ten seconds gives
        # Studionet validators time to render evidence and reach consensus.
        wait_interval=10_000, wait_retries=18,
    )
    assert receipt_field(receipt, "status_name") == "ACCEPTED"
    assert receipt_field(receipt, "result_name") == "MAJORITY_AGREE"
    # Older gltest receipts expose execution_result; current simplified
    # receipts omit it once status/result already prove accepted execution.
    assert receipt_field(receipt, "execution_result", None) in (None, "SUCCESS")
    print("LIVE_REGISTER_RECEIPT", receipt)
    lease_id = receipt_return_data(receipt)
    lease = contract.get_lease(args=[lease_id]).call()
    assert lease["status"] == "CONFIRMED"
    assert lease["stored_status"] == "CONFIRMED"
    assert lease["spec_hash"] == spec
    assert contract.is_usable(args=[lease_id]).call() is True
    assert contract.is_usable_for(args=[lease_id, spec]).call() is True
    assert contract.is_usable_for(args=[lease_id, "0" * 64]).call() is False

    before_version = lease["version"]
    refreshed = contract.revalidate(args=[lease_id]).transact(
        wait_interval=10_000, wait_retries=18,
    )
    assert receipt_field(refreshed, "status_name") == "ACCEPTED"
    assert receipt_field(refreshed, "result_name") == "MAJORITY_AGREE"
    assert receipt_field(refreshed, "execution_result", None) in (None, "SUCCESS")
    print("LIVE_REVALIDATE_RECEIPT", refreshed)
    after = contract.get_lease(args=[lease_id]).call()
    assert after["status"] == "CONFIRMED"
    assert after["version"] == before_version + 1
    assert after["spec_hash"] == spec
