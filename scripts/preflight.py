"""Fast source-level guardrails; this does not replace GenVM validation."""

from pathlib import Path
import ast
import sys


CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "truth_lease.py"
REQUIRED = (
    "class TruthLease(gl.Contract)", "run_nondet_unsafe", "def validator_fn",
    "def _normalize_assessment", "def _effective_status", "MAX_SOURCE_CHARS",
    "DATA_START", "DATA_END",
)


def main() -> int:
    source = CONTRACT.read_text(encoding="utf-8")
    ast.parse(source, filename=str(CONTRACT))
    failures = [item for item in REQUIRED if item not in source]
    if source.count("class TruthLease(gl.Contract)") != 1:
        failures.append("exactly one TruthLease contract")
    register_body = source[source.index("def register_fact"):source.index("def revalidate")]
    if register_body.index("assessment = self._consensus_assessment") > register_body.index("self.leases[lease_id] = LeaseRecord"):
        failures.append("consensus must precede state write")
    if failures:
        print("PREFLIGHT FAIL: " + "; ".join(failures))
        return 1
    print("PREFLIGHT PASS: 11 checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
