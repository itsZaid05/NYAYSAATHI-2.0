"""One-document, explicit review import. Never bulk scrape or auto-approve passages."""

import argparse
import hashlib
import io
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlparse
import httpx
from pypdf import PdfReader
from backend.config import ROOT

ALLOWED = {
    "www.indiacode.nic.in",
    "indiacode.gov.in",
    "www.indiacode.gov.in",
    "consumeraffairs.gov.in",
    "www.consumeraffairs.gov.in",
    "indiacode.nic.in",
    "consumerhelpline.gov.in",
    "e-jagriti.gov.in",
    "nalsa.gov.in",
    "consumeraffairs.nic.in",
}


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def extract_text(data, mime):
    if mime == "application/pdf":
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted or not 0 < len(reader.pages) <= 500:
            raise ValueError(
                "Encrypted PDFs and documents outside 1-500 pages are unsupported"
            )
        pages = []
        size = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            size += len(text)
            if size > 3_000_000:
                raise ValueError("Extracted source text exceeds the 3 MB limit")
            pages.append(text)
        return "\n".join(pages)
    if mime == "text/plain":
        return data.decode("utf-8", errors="replace")

    class Text(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []

        def handle_data(self, data):
            self.parts.append(data)

    parser = Text()
    parser.feed(data.decode("utf-8", errors="replace"))
    return " ".join(parser.parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "record",
        help="JSON object with exact_text, provenance, validity dates and rights review",
    )
    parser.add_argument("--confirm-manual-review", action="store_true")
    args = parser.parse_args()
    if not args.confirm_manual_review:
        parser.error(
            "Read the source and applicable terms before confirming manual review"
        )
    row = json.loads(open(args.record).read())
    if row.get("review_schema") != 2:
        parser.error(
            "New imports require review_schema 2 with explicit provenance, version and reuse review"
        )
    for field in [
        "source_id",
        "title",
        "provision",
        "exact_text",
        "official_url",
        "jurisdiction",
        "effective_version",
        "reuse_rights",
        "reviewed_by",
        "valid_from",
        "provenance_attestation",
        "provenance_evidence",
        "rights_evidence",
        "version_evidence",
        "reviewed_at",
        "retrieved_at",
        "source_type",
        "permitted_uses",
    ]:
        if not row.get(field):
            parser.error(f"Missing {field}")
    if row["jurisdiction"] != "IN" or row["reuse_rights"] == "pending review":
        parser.error("Indian jurisdiction and documented reuse permission are required")
    from backend.services.source_rights import validate_reuse, PIPELINE_USES

    try:
        validate_reuse(row)
        if not PIPELINE_USES.issubset(set(row["permitted_uses"])):
            parser.error("Reuse review must cover all required pipeline uses")
    except ValueError as exc:
        parser.error(str(exc))
    current = row["official_url"]
    # Validate every redirect before network access (no private hosts or unapproved ingestion).
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        for _ in range(4):
            parsed = urlparse(current)
            if (
                parsed.username
                or parsed.password
                or parsed.port not in (None, 443)
                or parsed.hostname not in ALLOWED
                or not current.startswith("https://")
            ):
                parser.error(
                    "Only explicitly approved official HTTPS hosts are allowed"
                )
            with client.stream("GET", current) as response:
                if response.is_redirect:
                    from urllib.parse import urljoin

                    current = urljoin(current, response.headers["location"])
                    continue
                response.raise_for_status()
                chunks = []
                size = 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 20 * 1024 * 1024:
                        parser.error("Official artifact exceeds 20 MB")
                    chunks.append(chunk)
                data = b"".join(chunks)
                mime = response.headers.get("content-type", "").split(";")[0]
                break
        else:
            parser.error("Too many redirects")
    if mime not in ("application/pdf", "text/html", "text/plain"):
        parser.error("Unsupported official document format")
    if normalize(row["exact_text"]) not in normalize(extract_text(data, mime)):
        parser.error("Exact passage not present in fetched official artifact")
    # Use the same complete validation and atomic admission path as offline review.
    # HTTPS retrieval establishes a fetch observation, not permission or version approval.
    import tempfile
    from scripts.import_offline_source import import_reviewed_batch
    from backend.config import settings

    row.update(expected_sha256=hashlib.sha256(data).hexdigest(), artifact_mime=mime)
    settings.runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with tempfile.NamedTemporaryFile(dir=settings.runtime) as artifact:
            artifact.write(data)
            artifact.flush()
            import_reviewed_batch([row], artifact.name, ROOT)
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))
    print("Imported reviewed passage:", row["source_id"])


if __name__ == "__main__":
    main()
