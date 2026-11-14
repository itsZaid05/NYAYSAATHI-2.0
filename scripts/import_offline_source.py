"""Review-controlled import of an authentic official artifact obtained elsewhere.

A local file alone never establishes authenticity. Requires a reviewer attestation
of independently checked official origin, retrieval time, checksum and reuse basis.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from backend.config import ROOT
from backend.schemas import Source
from scripts.review_source import extract_text, normalize


def import_reviewed(record, artifact, root=ROOT):
    row = dict(record)
    data = Path(artifact).read_bytes()
    if not 0 < len(data) <= 20 * 1024 * 1024:
        raise ValueError("Artifact must contain 1 byte to 20 MB")
    required = [
        "source_id",
        "title",
        "provision",
        "exact_text",
        "official_url",
        "jurisdiction",
        "effective_version",
        "valid_from",
        "reuse_rights",
        "reviewed_by",
        "retrieved_at",
        "source_type",
        "provenance_attestation",
        "expected_sha256",
        "provenance_evidence",
    ]
    if any(not row.get(k) for k in required):
        raise ValueError(
            "Complete provenance, rights and reviewer metadata are required"
        )
    if row["jurisdiction"] != "IN" or row["reuse_rights"] == "pending review":
        raise ValueError("Jurisdiction and reuse basis not approved")
    checksum = hashlib.sha256(data).hexdigest()
    if checksum != row["expected_sha256"]:
        raise ValueError("Artifact does not match independently recorded checksum")
    retrieved = datetime.fromisoformat(row["retrieved_at"])
    if retrieved.tzinfo is None or retrieved > datetime.now(timezone.utc):
        raise ValueError("Invalid retrieval timestamp")
    mime = row.get("artifact_mime", "")
    if mime == "application/pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("Artifact is not a PDF")
    if mime not in ("application/pdf", "text/html", "text/plain"):
        raise ValueError("Unsupported artifact format")
    if not row["exact_text"].strip() or normalize(row["exact_text"]) not in normalize(
        extract_text(data, mime)
    ):
        raise ValueError("Passage not present in retained authoritative artifact")
    row.update(
        status="reviewed",
        checked_at=datetime.now(timezone.utc).isoformat(),
        artifact_sha256=checksum,
        verification_method="reviewer attestation + independently recorded artifact checksum + exact passage verification",
    )
    Source(
        id=row["source_id"],
        title=row["title"],
        url=row["official_url"],
        provision=row["provision"],
        version=row["effective_version"],
        quote=row["exact_text"],
        checked_at=row["checked_at"],
    )
    folder = root / "knowledge/artifacts"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / checksum).write_bytes(data)
    path = root / "knowledge/reviewed_sources.json"
    rows = json.loads(path.read_text()) if path.exists() else []
    path.write_text(
        json.dumps(
            [r for r in rows if r["source_id"] != row["source_id"]] + [row],
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record")
    parser.add_argument("artifact")
    parser.add_argument("--attest-official-provenance-and-rights", action="store_true")
    args = parser.parse_args()
    if not args.attest_official_provenance_and_rights:
        parser.error(
            "An identified reviewer must independently verify official origin, version and reuse basis first"
        )
    try:
        row = import_reviewed(json.loads(Path(args.record).read_text()), args.artifact)
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))
    print("Imported reviewed official passage:", row["source_id"])


if __name__ == "__main__":
    main()
