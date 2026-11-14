"""Reuse clearance is a provenance requirement, never inferred from public access."""

from urllib.parse import urlparse

PERMISSION_POLICIES = {
    "consumerhelpline.gov.in": "https://consumerhelpline.gov.in/public/disclaimer",
    "nalsa.gov.in": "https://nalsa.gov.in/website-policies/",
}

# These are the pipeline's actual uses; a reviewer must clear all before a new import.
PIPELINE_USES = {
    "retention",
    "local_search",
    "external_embeddings",
    "llm_context",
    "quotation_and_export",
}


def validate_reuse(record):
    host = (urlparse(record.get("official_url", "")).hostname or "").removeprefix(
        "www."
    )
    status = record.get("reuse_status")
    if status in ("permission_required", "unknown", "denied", "pending_review"):
        raise ValueError("Source reuse is not cleared")
    if host in PERMISSION_POLICIES:
        # These portal policies were actually inspected; prior approval cannot be assumed.
        if status != "documented_permission" or not record.get("rights_evidence"):
            raise ValueError(
                "This portal requires documented prior permission: "
                + PERMISSION_POLICIES[host]
            )
    if record.get("review_schema") == 2:
        if status not in (
            "documented_permission",
            "public_licence",
            "reviewed_statutory_basis",
        ) or not record.get("rights_evidence"):
            raise ValueError(
                "Version-2 review needs an explicit reuse basis and evidence"
            )
    return True
