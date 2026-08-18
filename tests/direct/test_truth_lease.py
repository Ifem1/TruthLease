import json
import datetime


SOURCE_A = "https://example.com/source-a"
SOURCE_B = "https://example.com/source-b"


def assessment(
    status="CONFIRMED",
    reason_code="CURRENTLY_SUPPORTED",
    confidence="HIGH",
    contradiction=False,
    material_change=False,
    source_coverage=2,
    evidence_summary="Current registered evidence supports the proposition.",
):
    return json.dumps(
        {
            "status": status,
            "reason_code": reason_code,
            "confidence": confidence,
            "contradiction": contradiction,
            "material_change": material_change,
            "source_coverage": source_coverage,
            "evidence_summary": evidence_summary,
        }
    )


def install_confirmed_mocks(vm):
    vm.mock_web(r"example\.com/source-a", {"status": 200, "body": "Example Org lists Jane Doe as executive director."})
    vm.mock_web(r"example\.com/source-b", {"status": 200, "body": "Leadership: Jane Doe — Executive Director."})
    vm.mock_llm(r"Classify the proposition", assessment())


def register_confirmed(contract):
    return contract.register_fact(
        "Example Org currently lists Jane Doe as executive director.",
        "Current leadership role.",
        json.dumps([SOURCE_A, SOURCE_B]),
        "Prefer current first-party leadership pages.",
        3600,
    )


def test_rejects_invalid_source_sets(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/truth_lease.py")

    with direct_vm.expect_revert("sources_json must contain 1 to 5 URLs"):
        contract.register_fact(
            "A proposition long enough to validate.",
            "",
            "[]",
            "",
            3600,
        )

    with direct_vm.expect_revert("every source must be an HTTPS URL"):
        contract.register_fact(
            "A proposition long enough to validate.",
            "",
            json.dumps(["http://example.com"]),
            "",
            3600,
        )


def test_rejects_ttl_outside_bounds(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/truth_lease.py")

    with direct_vm.expect_revert("ttl_seconds must be between 60 and 31536000"):
        contract.register_fact(
            "A proposition long enough to validate.",
            "",
            json.dumps([SOURCE_A]),
            "",
            30,
        )


def test_rejects_unbounded_or_empty_prompt_inputs(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/truth_lease.py")

    with direct_vm.expect_revert("source_policy is required"):
        contract.register_fact(
            "A proposition long enough to validate.", "", json.dumps([SOURCE_A]), "", 3600
        )

    with direct_vm.expect_revert("context is too long"):
        contract.register_fact(
            "A proposition long enough to validate.", "x" * 2001,
            json.dumps([SOURCE_A]), "Use first-party evidence.", 3600,
        )

    with direct_vm.expect_revert("every source must be an HTTPS URL"):
        contract.register_fact(
            "A proposition long enough to validate.", "",
            json.dumps(["https://example.com/has a space"]), "Use first-party evidence.", 3600,
        )


def test_fails_closed_on_malformed_consensus_output(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/truth_lease.py")
    direct_vm.mock_web(r"example\.com/source-a", {"status": 200, "body": "Current leadership page."})
    direct_vm.mock_llm(r"Classify the proposition", '{"status":"CONFIRMED"}')

    with direct_vm.expect_revert("assessment fields are invalid"):
        contract.register_fact(
            "Example Org currently lists Jane Doe as executive director.",
            "Current leadership role.", json.dumps([SOURCE_A]),
            "Prefer current first-party leadership pages.", 3600,
        )


def test_registers_confirmed_lease_and_exposes_consumer_view(direct_vm, direct_deploy):
    direct_vm.check_pickling = True
    contract = direct_deploy("contracts/truth_lease.py")
    install_confirmed_mocks(direct_vm)

    lease_id = register_confirmed(contract)
    assert lease_id == "lease-1"

    lease = contract.get_lease(lease_id)
    assert lease["status"] == "CONFIRMED"
    assert lease["stored_status"] == "CONFIRMED"
    assert lease["version"] == 1
    assert lease["source_coverage"] == 2
    assert contract.is_usable(lease_id) is True
    assert contract.is_usable_for(lease_id, lease["spec_hash"]) is True
    assert contract.is_usable_for(lease_id, "0" * 64) is False
    assert contract.get_event_count() == 1


def test_spec_hash_is_source_order_stable_and_expiry_is_deterministic(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/truth_lease.py")
    install_confirmed_mocks(direct_vm)
    first = contract.compute_spec_hash(
        "Example Org currently lists Jane Doe as executive director.", "Current leadership role.",
        json.dumps([SOURCE_A, SOURCE_B]), "Prefer current first-party leadership pages.",
    )
    second = contract.compute_spec_hash(
        "Example Org currently lists Jane Doe as executive director.", "Current leadership role.",
        json.dumps([SOURCE_B, SOURCE_A]), "Prefer current first-party leadership pages.",
    )
    assert first == second
    lease_id = register_confirmed(contract)
    lease = contract.get_lease(lease_id)
    direct_vm.warp(datetime.datetime.fromtimestamp(lease["valid_until"] + 1, datetime.UTC).isoformat())
    assert contract.get_lease(lease_id)["status"] == "STALE"
    assert contract.is_usable_for(lease_id, first) is False
    contract.mark_stale(lease_id)
    assert contract.get_lease(lease_id)["stored_status"] == "STALE"


def test_custom_validator_accepts_matching_independent_assessment(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/truth_lease.py")
    install_confirmed_mocks(direct_vm)

    register_confirmed(contract)

    # Direct mode captures the custom validator from run_nondet_unsafe.
    # With independent web/LLM mocks reaching the same semantic decision,
    # the validator accepts even though summary wording need not be compared.
    assert direct_vm.run_validator() is True


def test_custom_validator_rejects_material_status_disagreement(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/truth_lease.py")
    install_confirmed_mocks(direct_vm)

    register_confirmed(contract)

    direct_vm.clear_mocks()
    direct_vm.mock_web(r"example\.com/source-a", {"status": 200, "body": "Example Org lists a different executive director."})
    direct_vm.mock_web(r"example\.com/source-b", {"status": 200, "body": "Leadership changed."})
    direct_vm.mock_llm(
        r"Classify the proposition",
        assessment(
            status="SUPERSEDED",
            reason_code="CURRENT_EVIDENCE_OVERTURNS",
            confidence="HIGH",
            contradiction=True,
            material_change=True,
            source_coverage=2,
            evidence_summary="Current sources indicate the role changed.",
        ),
    )

    assert direct_vm.run_validator() is False


def test_source_update_invalidates_old_confirmation(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    contract = direct_deploy("contracts/truth_lease.py")
    install_confirmed_mocks(direct_vm)
    lease_id = register_confirmed(contract)

    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("only lease owner may update sources"):
            contract.update_sources(
                lease_id,
                json.dumps([SOURCE_A]),
                "Prefer the current first-party source.",
            )

    contract.update_sources(
        lease_id,
        json.dumps([SOURCE_A]),
        "Prefer the current first-party source.",
    )

    lease = contract.get_lease(lease_id)
    assert lease["status"] == "UNVERIFIED"
    assert lease["reason_code"] == "EVIDENCE_SET_CHANGED"
    assert lease["version"] == 2
    assert contract.is_usable(lease_id) is False
