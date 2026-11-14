"""Prepare local section candidates; parsing never authenticates or approves an artifact."""

import argparse, hashlib
from pathlib import Path
from scripts.review_source import extract_text
from backend.services.source_chunking import section_candidates
from backend.services.offline_review import inspect_pdf, write_new_json
from scripts.import_offline_source import read_artifact

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact")
    p.add_argument("--mime", choices=["application/pdf", "text/plain"], required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        if args.mime == "application/pdf":
            data, pages = inspect_pdf(args.artifact)
            text = "\n".join(pages)
        else:
            data = read_artifact(args.artifact)
            text = extract_text(data, args.mime)
        rows = section_candidates(text)
    except (ValueError, OSError) as exc:
        p.error(str(exc))
    for row in rows:
        row["artifact_sha256"] = hashlib.sha256(data).hexdigest()
    target = Path(args.output)
    if target.exists():
        p.error("Output already exists; choose a fresh review file")
    write_new_json(target, rows)
    print("Prepared unapproved review candidates:", len(rows))
