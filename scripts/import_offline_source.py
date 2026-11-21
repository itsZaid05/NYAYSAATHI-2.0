"""Review-controlled import of an authentic official artifact obtained elsewhere.

A local file alone never establishes authenticity. Requires a reviewer attestation
of independently checked official origin, retrieval time, checksum and reuse basis.
"""

import argparse
import hashlib
import json
import os
import tempfile
import fcntl
from datetime import date, timedelta
from datetime import datetime, timezone
from pathlib import Path
from backend.config import ROOT
from backend.schemas import Source
from pydantic import ValidationError
from pypdf.errors import PyPdfError
from scripts.review_source import extract_text, normalize


def validate_reviewed(record, data, extracted_text=None):
    row = dict(record)
    from backend.services.source_rights import validate_reuse, PIPELINE_USES

    validate_reuse(row)
    if row.get("review_schema") != 2:
        raise ValueError(
            "New imports require review_schema 2 and explicit reuse/version evidence"
        )
    if not PIPELINE_USES.issubset(set(row.get("permitted_uses", []))):
        raise ValueError(
            "Rights review must explicitly cover retention, search, external embeddings, LLM context and quoted exports"
        )
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
        "rights_evidence",
        "version_evidence",
        "reviewed_at",
    ]
    if any(
        not row.get(k) or (isinstance(row[k], str) and not row[k].strip())
        for k in required
    ):
        raise ValueError(
            "Complete provenance, rights and reviewer metadata are required"
        )
    if any(
        len(row[k].strip()) < 20
        for k in ("provenance_evidence", "rights_evidence", "version_evidence")
    ):
        raise ValueError(
            "Substantive provenance, version and reuse evidence is required"
        )
    if row["jurisdiction"] != "IN" or row["reuse_rights"] == "pending review":
        raise ValueError("Jurisdiction and reuse basis not approved")
    checksum = hashlib.sha256(data).hexdigest()
    if checksum != row["expected_sha256"]:
        raise ValueError("Artifact does not match independently recorded checksum")
    retrieved = datetime.fromisoformat(row["retrieved_at"])
    if retrieved.tzinfo is None or retrieved > datetime.now(timezone.utc):
        raise ValueError("Invalid retrieval timestamp")
    reviewed = datetime.fromisoformat(row["reviewed_at"])
    now = datetime.now(timezone.utc)
    if reviewed.tzinfo is None or not now - timedelta(days=90) <= reviewed <= now:
        raise ValueError(
            "Review must be timezone-aware, not future-dated and within 90 days"
        )
    review_times = [reviewed]
    for decision in row.get("document_reviews", {}).values():
        checked = datetime.fromisoformat(decision["reviewed_at"])
        if checked.tzinfo is None or not now - timedelta(days=90) <= checked <= now:
            raise ValueError("Document reviews must also be current and timezone-aware")
        review_times.append(checked)
    start = date.fromisoformat(row["valid_from"])
    end = date.fromisoformat(row["valid_until"]) if row.get("valid_until") else None
    if start > now.date() or (end and (end < start or end < now.date())):
        raise ValueError(
            "Version validity interval is inverted, expired or not yet effective"
        )
    mime = row.get("artifact_mime", "")
    if mime == "application/pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("Artifact is not a PDF")
    if mime not in ("application/pdf", "text/html", "text/plain"):
        raise ValueError("Unsupported artifact format")
    if not row["exact_text"].strip() or normalize(row["exact_text"]) not in normalize(
        extracted_text if extracted_text is not None else extract_text(data, mime)
    ):
        raise ValueError("Passage not present in retained authoritative artifact")
    row.update(
        status="reviewed",
        # Rerunning an importer must not extend the manual review's freshness.
        checked_at=min(review_times).isoformat(),
        artifact_checked_at=now.isoformat(),
        artifact_sha256=checksum,
        verification_method="reviewer attestation + independently recorded artifact checksum + exact passage verification",
    )
    try:
        Source(
            id=row["source_id"],
            title=row["title"],
            url=row["official_url"],
            provision=row["provision"],
            version=row["effective_version"],
            quote=row["exact_text"],
            checked_at=row["checked_at"],
        )
    except ValidationError as exc:
        fields = [
            ".".join(map(str, e["loc"])) or "record"
            for e in exc.errors(include_input=False, include_url=False)[:10]
        ]
        raise ValueError(
            "Invalid approved-source fields: " + ", ".join(fields)
        ) from None
    return row


def read_artifact(artifact):
    path = Path(artifact)
    if not path.is_file() or not 0 < path.stat().st_size <= 20 * 1024 * 1024:
        raise ValueError("Artifact must be a file containing 1 byte to 20 MB")
    with path.open("rb") as stream:
        data = stream.read(20 * 1024 * 1024 + 1)
    if not 0 < len(data) <= 20 * 1024 * 1024:
        raise ValueError("Artifact exceeds the allowed size")
    return data


def _atomic_write(path, data):
    fd, temporary = tempfile.mkstemp(prefix=".source-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def import_reviewed_batch(
    records, artifact, root=ROOT, *, replace_existing=False, dry_run=False
):
    """Validate the entire batch before an atomic registry replacement; never auto-approve."""
    data = read_artifact(artifact)
    if not records:
        raise ValueError("No approved passages to import")
    mime = records[0].get("artifact_mime", "")
    if any(row.get("artifact_mime") != mime for row in records):
        raise ValueError("One batch must reference one artifact format")
    if mime == "application/pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("Artifact is not a PDF")
    if mime not in ("application/pdf", "text/html", "text/plain"):
        raise ValueError("Unsupported artifact format")
    try:
        text = extract_text(data, mime)
    except PyPdfError:
        raise ValueError("Artifact cannot be parsed; no source admitted") from None
    validated = [validate_reviewed(row, data, text) for row in records]
    ids = {row["source_id"] for row in validated}
    if len(ids) != len(validated):
        raise ValueError("Duplicate source IDs in batch")
    folder = Path(root) / "knowledge"
    path = folder / "reviewed_sources.json"

    def merged():
        existing = json.loads(path.read_text()) if path.exists() else []
        if not isinstance(existing, list) or len(
            {r["source_id"] for r in existing}
        ) != len(existing):
            raise ValueError("Existing corpus is malformed or has duplicate IDs")
        if not replace_existing and ids & {r["source_id"] for r in existing}:
            raise ValueError("Source ID already exists; review replacement explicitly")
        return [r for r in existing if r["source_id"] not in ids] + validated

    if dry_run:
        merged()
        return validated
    folder.mkdir(parents=True, exist_ok=True)
    # Serialise operator imports, not public requests; readers see either complete registry.
    with (folder / ".ingest.lock").open("a") as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = merged()
        artifacts = folder / "artifacts"
        artifacts.mkdir(exist_ok=True)
        target = artifacts / validated[0]["artifact_sha256"]
        if target.exists():
            if target.is_symlink() or target.read_bytes() != data:
                raise ValueError("Retained artifact conflicts with its checksum")
        else:
            _atomic_write(target, data)
        _atomic_write(
            path, (json.dumps(rows, ensure_ascii=False, indent=2) + "\n").encode()
        )
    return validated


def import_reviewed(record, artifact, root=ROOT):
    return import_reviewed_batch([record], artifact, root)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record")
    parser.add_argument("artifact")
    parser.add_argument("--attest-official-provenance-and-rights", action="store_true")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate only; never change the corpus"
    )
    args = parser.parse_args()
    if not args.attest_official_provenance_and_rights:
        parser.error(
            "An identified reviewer must independently verify official origin, version and reuse basis first"
        )
    try:
        row = import_reviewed_batch(
            [json.loads(Path(args.record).read_text())],
            args.artifact,
            dry_run=args.dry_run,
        )[0]
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(
        "Validated without importing:"
        if args.dry_run
        else "Imported reviewed official passage:",
        row["source_id"],
    )


if __name__ == "__main__":
    main()
