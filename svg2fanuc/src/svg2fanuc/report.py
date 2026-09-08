"""report.json builder (sections 4.3, 6.3, 10.2)."""

from __future__ import annotations

SAFETY_NOTICE = (
    "GENERATED != SAFE TO RUN. A qualified cell profile, integrator review and "
    "operator confirmation are required. This tool never asserts reachability, "
    "singularity-freedom, collision-freedom or visitor safety."
)

# section 6.3 job states
STATE_REJECTED = "REJECTED"
STATE_GENERATED_UNCOMPILED = "GENERATED_UNCOMPILED"
STATE_COMPILED_UNVERIFIED = "COMPILED_UNVERIFIED"


def build_report(
    *,
    command: str,
    job_id: str,
    profile_summary: dict,
    placement: dict,
    metrics: dict,
    validation: dict,
    emit: dict | None,
    maketp: dict | None,
    job_state: str,
    warnings: list[str],
) -> dict:
    return {
        "schema": "svg2fanuc/report@1",
        "command": command,
        "job_id": job_id,
        "job_state": job_state,
        "safety_notice": SAFETY_NOTICE,
        "profile": profile_summary,
        "placement": placement,
        "metrics": metrics,
        "validation": validation,
        "fanuc_ls": emit,
        "maketp": maketp,
        "warnings": warnings,
    }
