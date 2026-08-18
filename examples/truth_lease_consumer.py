# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


@gl.contract_interface
class TruthLeaseInterface:
    class View:
        def is_usable(self, lease_id: str) -> bool: ...
        def is_usable_for(self, lease_id: str, expected_spec_hash: str) -> bool: ...
        def get_lease(self, lease_id: str): ...

    class Write:
        pass


class FreshFactGate(gl.Contract):
    """Minimal composition example for builders.

    This contract does not know how TruthLease reaches consensus. It consumes the
    primitive through a tiny read interface and gates its own deterministic state
    transition on a fresh confirmed lease.
    """

    truthlease_address: Address
    expected_spec_hash: str
    accepted_payloads: TreeMap[str, str]

    def __init__(self, truthlease_address: Address, expected_spec_hash: str):
        self.truthlease_address = truthlease_address
        self.expected_spec_hash = expected_spec_hash

    @gl.public.write
    def accept_if_fresh(self, lease_id: str, payload: str) -> None:
        truthlease = TruthLeaseInterface(self.truthlease_address)
        if not truthlease.view().is_usable_for(lease_id, self.expected_spec_hash):
            raise gl.vm.UserError("matching fresh confirmed TruthLease required")

        self.accepted_payloads[lease_id] = payload

    @gl.public.view
    def get_accepted_payload(self, lease_id: str) -> str:
        return self.accepted_payloads.get(lease_id, "")
