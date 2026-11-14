"""One-document, explicit review import. Never bulk scrape or auto-approve passages."""

import argparse
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse
import httpx
from pypdf import PdfReader
from backend.config import ROOT
from backend.schemas import Source

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
        return "\n".join(p.extract_text() or "" for p in reader.pages)

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
    ]:
        if not row.get(field):
            parser.error(f"Missing {field}")
    if row["jurisdiction"] != "IN" or row["reuse_rights"] == "pending review":
        parser.error("Indian jurisdiction and documented reuse permission are required")
    current = row["official_url"]
    # Validate every redirect before network access (no private hosts or unapproved ingestion).
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        for _ in range(4):
            if urlparse(current).hostname not in ALLOWED or not current.startswith(
                "https://"
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
    row.update(
        status="reviewed",
        checked_at=datetime.now(timezone.utc).isoformat(),
        artifact_sha256=hashlib.sha256(data).hexdigest(),
        artifact_mime=mime,
    )
    Source(
        id=row["source_id"],
        title=row["title"],
        url=row["official_url"],
        provision=row["provision"],
        version=row["effective_version"],
        checked_at=row["checked_at"],
        quote=row["exact_text"],
    )
    folder = ROOT / "knowledge/artifacts"
    folder.mkdir(exist_ok=True)
    (folder / row["artifact_sha256"]).write_bytes(data)
    path = ROOT / "knowledge/reviewed_sources.json"
    records = json.loads(path.read_text())
    records = [r for r in records if r["source_id"] != row["source_id"]] + [row]
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    print("Imported reviewed passage:", row["source_id"])


if __name__ == "__main__":
    main()
