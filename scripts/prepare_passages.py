"""Prepare section-aware candidates from a local authentic artifact; every item remains unapproved."""

import argparse, json, hashlib
from pathlib import Path
from scripts.review_source import extract_text
from backend.services.source_chunking import section_candidates

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact")
    p.add_argument("--mime", choices=["application/pdf", "text/plain"], required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    data = Path(args.artifact).read_bytes()
    if len(data) > 20 * 1024 * 1024:
        p.error("Artifact exceeds 20 MB")
    rows = section_candidates(extract_text(data, args.mime))
    for row in rows:
        row["artifact_sha256"] = hashlib.sha256(data).hexdigest()
    target = Path(args.output)
    if target.exists():
        p.error("Output already exists; choose a fresh review file")
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    print("Prepared unapproved review candidates:", len(rows))
