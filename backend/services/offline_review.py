"""Local PDF staging and review gates. No fetches, model calls or automatic approvals."""

import hashlib
import io
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from backend.schemas import StrictModel
from backend.services.source_chunking import section_candidates
from scripts.import_offline_source import import_reviewed_batch, read_artifact


class Review(StrictModel):
    status: Literal["pending", "approved", "rejected"] = "pending"
    reviewed_by: str = ""
    reviewed_at: datetime | None = None
    evidence: str = ""


class Document(StrictModel):
    title: str = ""
    official_url: str = ""
    jurisdiction: Literal["IN"] = "IN"
    source_type: Literal[
        "unspecified", "statute", "rule", "notification", "official_guidance"
    ] = "unspecified"
    effective_version: str = ""
    valid_from: date | None = None
    valid_until: date | None = None
    retrieved_at: datetime | None = None
    reuse_status: Literal[
        "pending_review",
        "documented_permission",
        "public_licence",
        "reviewed_statutory_basis",
    ] = "pending_review"
    reuse_rights: str = ""
    permitted_uses: list[
        Literal[
            "retention",
            "local_search",
            "external_embeddings",
            "llm_context",
            "quotation_and_export",
        ]
    ] = Field(default_factory=list)


class Artifact(StrictModel):
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mime: Literal["application/pdf"] = "application/pdf"
    filename: str
    byte_count: int = Field(gt=0)
    page_count: int = Field(gt=0, le=500)


class Passage(StrictModel):
    source_id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,120}$")
    provision: str = ""
    exact_text: str = Field(min_length=5, max_length=200000)
    page_hints: list[int] = Field(default_factory=list)
    review: Review = Field(default_factory=Review)
    excluded: bool = False


class ReviewPack(StrictModel):
    format_version: Literal[1] = 1
    created_at: datetime
    artifact: Artifact
    document: Document = Field(default_factory=Document)
    provenance: Review = Field(default_factory=Review)
    version: Review = Field(default_factory=Review)
    reuse: Review = Field(default_factory=Review)
    passages: list[Passage] = Field(default_factory=list, max_length=500)
    notice: str = "Parsing alone does not establish authenticity, rights or legal authority; explicit review remains required."


def inspect_pdf(path):
    data = read_artifact(path)
    if not data.startswith(b"%PDF-"):
        raise ValueError("Not a PDF: an extension or HTML error page is insufficient")
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ValueError(
                "Encrypted PDFs are unsupported; supply an authorised readable copy"
            )
        if not 0 < len(reader.pages) <= 500:
            raise ValueError("PDF must contain 1 to 500 pages")
        pages = []
        length = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            length += len(text)
            if length > 3_000_000:
                raise ValueError("PDF extracted text exceeds the 3 MB review limit")
            pages.append(text)
    except PyPdfError:
        raise ValueError("PDF cannot be parsed; no review pack was created") from None
    if not any(text.strip() for text in pages):
        raise ValueError(
            "No searchable text; image-only PDFs need a separately verified accessible official copy"
        )
    return data, pages


def stage_pdf(path):
    data, pages = inspect_pdf(path)
    checksum = hashlib.sha256(data).hexdigest()
    text = "\n".join(pages)
    candidates = section_candidates(text)
    # Non-numbered guidance is staged by page, with no invented provision number.
    if not candidates:
        candidates = [
            {"exact_text": page.strip(), "provision_candidate": ""}
            for page in pages
            if len(page.strip()) >= 5
        ]
    offsets = []
    offset = 0
    for page in pages:
        offsets.append((offset, offset + len(page)))
        offset += len(page) + 1
    passages = []
    for index, candidate in enumerate(candidates):
        quote = candidate["exact_text"]
        start = text.find(quote)
        hints = [
            n + 1
            for n, (a, b) in enumerate(offsets)
            if start >= 0 and start < b and start + len(quote) > a
        ]
        passages.append(
            Passage(
                source_id=f"doc-{checksum[:12]}-{index + 1:03d}",
                provision=candidate["provision_candidate"],
                exact_text=quote,
                page_hints=hints,
            )
        )
    return ReviewPack(
        created_at=datetime.now(timezone.utc),
        artifact=Artifact(
            sha256=checksum,
            filename=Path(path).name,
            byte_count=len(data),
            page_count=len(pages),
        ),
        passages=passages,
    )


def write_new_json(path, value):
    """Private, exclusive output: never overwrite an existing review or corpus."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(
        path, "x", encoding="utf-8", opener=lambda p, flags: os.open(p, flags, 0o600)
    ) as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prepare_records(pack, artifact):
    data, pages = inspect_pdf(artifact)
    if (
        hashlib.sha256(data).hexdigest() != pack.artifact.sha256
        or len(data) != pack.artifact.byte_count
        or len(pages) != pack.artifact.page_count
    ):
        raise ValueError(
            "Artifact differs from the staged PDF; stage and review the correct version again"
        )
    now = datetime.now(timezone.utc)
    for name, review in [
        ("provenance", pack.provenance),
        ("version", pack.version),
        ("reuse", pack.reuse),
    ]:
        if (
            review.status != "approved"
            or not review.reviewed_by.strip()
            or len(review.evidence.strip()) < 20
            or not review.reviewed_at
            or review.reviewed_at.tzinfo is None
            or not now - timedelta(days=90) <= review.reviewed_at <= now
        ):
            raise ValueError(
                f"{name} review requires explicit approval, reviewer, recent aware timestamp and substantive evidence"
            )
    doc = pack.document.model_dump(mode="json")
    if doc["source_type"] == "unspecified":
        raise ValueError("Document type remains unspecified")
    ids = [p.source_id for p in pack.passages]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate passage source IDs in review pack")
    records = []
    for passage in pack.passages:
        if passage.excluded or passage.review.status != "approved":
            continue
        review = passage.review
        if (
            not review.reviewed_by.strip()
            or len(review.evidence.strip()) < 20
            or not review.reviewed_at
            or review.reviewed_at.tzinfo is None
            or not now - timedelta(days=90) <= review.reviewed_at <= now
        ):
            raise ValueError(
                f"Passage {passage.source_id} lacks a complete current review"
            )
        if passage.page_hints and any(
            p < 1 or p > len(pages) for p in passage.page_hints
        ):
            raise ValueError("Page hints are outside the PDF")
        records.append(
            {
                **doc,
                "review_schema": 2,
                "source_id": passage.source_id,
                "provision": passage.provision,
                "exact_text": passage.exact_text,
                "reviewed_by": review.reviewed_by,
                "reviewed_at": review.reviewed_at.isoformat(),
                "expected_sha256": pack.artifact.sha256,
                "artifact_mime": "application/pdf",
                "provenance_attestation": "Identified reviewer explicitly approved the provenance review in this pack",
                "provenance_evidence": pack.provenance.evidence,
                "rights_evidence": pack.reuse.evidence,
                "version_evidence": pack.version.evidence,
                "document_reviews": {
                    name: r.model_dump(mode="json")
                    for name, r in [
                        ("provenance", pack.provenance),
                        ("version", pack.version),
                        ("reuse", pack.reuse),
                    ]
                },
                "passage_review": review.model_dump(mode="json"),
                "review_pack_created_at": pack.created_at.isoformat(),
            }
        )
    return records


def check_pack(pack, artifact, root):
    counts = {"approved": 0, "pending": 0, "excluded": 0}
    for p in pack.passages:
        key = (
            "excluded"
            if p.excluded or p.review.status == "rejected"
            else "approved"
            if p.review.status == "approved"
            else "pending"
        )
        counts[key] += 1
    try:
        records = prepare_records(pack, artifact)
        validated = import_reviewed_batch(records, artifact, root, dry_run=True)
        return {
            "ready": True,
            "mutated_corpus": False,
            "counts": counts,
            "source_ids": [r["source_id"] for r in validated],
            "errors": [],
            "notice": "Technical and recorded-review checks only; authenticity, rights and legal correctness are not established by software.",
        }
    except ValidationError as exc:
        fields = [
            ".".join(map(str, e["loc"])) or "record"
            for e in exc.errors(include_input=False, include_url=False)[:10]
        ]
        return {
            "ready": False,
            "mutated_corpus": False,
            "counts": counts,
            "source_ids": [],
            "errors": ["Invalid approved-source fields: " + ", ".join(fields)],
        }
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return {
            "ready": False,
            "mutated_corpus": False,
            "counts": counts,
            "source_ids": [],
            "errors": [str(exc)],
        }
