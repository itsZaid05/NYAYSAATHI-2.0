"""Stage -> check -> explicitly import a reviewed official PDF. No network or Gemini calls."""

import argparse
import json
from pathlib import Path
from pydantic import ValidationError

from backend.config import ROOT
from backend.services.offline_review import (
    ReviewPack,
    stage_pdf,
    write_new_json,
    check_pack,
    prepare_records,
)
from scripts.import_offline_source import import_reviewed_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser(
        "stage", help="Prepare private unapproved candidates; never modify retrieval"
    )
    stage.add_argument("artifact")
    stage.add_argument("--output", required=True)
    for command in ("check", "import"):
        p = sub.add_parser(command)
        p.add_argument("pack")
        p.add_argument("artifact")
        p.add_argument("--report", help="Write a fresh private validation report")
        if command == "import":
            p.add_argument(
                "--attest-reviewed-provenance-version-and-rights", action="store_true"
            )
    args = parser.parse_args()
    try:
        if args.command == "stage":
            pack = stage_pdf(args.artifact)
            write_new_json(args.output, pack.model_dump(mode="json"))
            print(
                f"Prepared {len(pack.passages)} UNAPPROVED candidates; corpus unchanged."
            )
            return 0
        pack = ReviewPack.model_validate_json(Path(args.pack).read_text())
        report = check_pack(pack, args.artifact, ROOT)
        if args.report:
            write_new_json(args.report, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report["ready"]:
            return 2
        if args.command == "check":
            return 0
        if not args.attest_reviewed_provenance_version_and_rights:
            parser.error(
                "Import requires explicit attestation by the responsible reviewer; a passing technical check is insufficient"
            )
        records = prepare_records(pack, args.artifact)
        imported = import_reviewed_batch(records, args.artifact, ROOT)
        print(
            f"Imported {len(imported)} reviewed passages. Existing retrieval loads them on its next request; semantic vectors remain consent-dependent."
        )
        return 0
    except ValidationError as exc:
        fields = [
            ".".join(map(str, e["loc"]))
            for e in exc.errors(include_input=False, include_url=False)[:10]
        ]
        print("Invalid review fields: " + ", ".join(fields))
        return 2
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("Review workflow blocked: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
