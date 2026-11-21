"""Explicit live evaluation of new synthetic narratives; never scores legal correctness from AI agreement."""

import argparse, json, time, hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from backend.config import ROOT, settings
from backend.db import init
from backend.engine import assess
from backend.schemas import Consent
from backend.services.model_configuration import verify_runtime_models


def evaluate_case(case):
    started = time.monotonic()
    try:
        a = assess(
            "unseen-" + case["id"],
            case["narrative"],
            case["jurisdiction"],
            case["language"],
            Consent(processing=True, fictional_demo=True, ai_processing=True),
        )
        got = {i.category for i in a.issue_details}
        expected = set(case["expected_issue_categories"])
        checks = {
            "live_dynamic_understanding": a.understanding_method.startswith("Gemini"),
            "consumer_scope": a.scope_status == "consumer",
            "expected_issue_coverage": expected.issubset(got),
            "no_forbidden_issue_inference": not (
                set(case.get("forbidden_categories", [])) & got
            ),
            "issue_fact_provenance": bool(a.issue_details)
            and all(
                q in case["narrative"] for i in a.issue_details for q in i.fact_quotes
            ),
            "no_source_fabrication": all(s.id for s in a.sources)
            and (bool(a.sources) or (not a.options and not a.legal_analysis)),
            "factual_evidence_suggestions": all(
                i.evidence_needed for i in a.issue_details
            ),
            "assistant_present": bool(a.assistant_message),
        }
        return {
            "id": case["id"],
            "language": case["language"],
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks,
            "expected_categories": sorted(expected),
            "actual_categories": sorted(got),
            "unexpected_categories": sorted(got - expected),
            "forbidden_categories": case.get("forbidden_categories", []),
            "scope": a.scope_status,
            "issues": [i.model_dump() for i in a.issue_details],
            "issue_review": {k: v.model_dump() for k, v in a.issue_review.items()},
            "followups": a.unknowns,
            "assistant": a.assistant_message,
            "source_ids": [s.id for s in a.sources],
            "retrieval_mode": a.retrieval_mode,
            "legal_validation": "NOT ASSESSED: requires authentic source corpus and independent legal review",
            "ai_status": a.ai_status,
            "diagnostics": a.safety_flags,
            "seconds": round(time.monotonic() - started, 2),
        }
    except Exception as exc:
        return {
            "id": case["id"],
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "legal_validation": "NOT ASSESSED",
        }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--limit", type=int)
    p.add_argument("--only")
    p.add_argument("--model")
    p.add_argument("--embedding-model")
    p.add_argument("--pause", type=float, default=4.5)
    p.add_argument("--output", default="runtime/unseen-evaluation.json")
    p.add_argument("--cases", default="tests/evaluation/unseen_consumer_cases.json")
    args = p.parse_args()
    if not args.live:
        p.error(
            "Explicit --live required: sends fictional narratives to the configured provider"
        )
    init()
    if args.model:
        settings.gemini_model = args.model
        if args.embedding_model:
            settings.embedding_model = args.embedding_model
        from backend.providers import GeminiProvider

        listed = GeminiProvider().models()
        if not any(
            m["name"] == "models/" + args.model
            and "generateContent" in m.get("supportedGenerationMethods", [])
            for m in listed
        ):
            raise SystemExit("Requested model is not listed for generation")
        profile = {
            "selected_generation": args.model,
            "selected_embedding": settings.embedding_model,
            "selection": "explicit evaluation override; actual case calls establish generation success",
        }
    else:
        profile = verify_runtime_models()
        if not profile["generation_verified"]:
            raise SystemExit("No generation model passed the actual startup probe")
    cases_path = (ROOT / args.cases).resolve()
    cases = json.loads(cases_path.read_text())
    if args.only:
        cases = [c for c in cases if c["id"] in args.only.split(",")]
    if args.limit:
        cases = cases[: args.limit]
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "model_configuration": profile,
        "synthetic_only": True,
        "cases_file": str(cases_path.relative_to(ROOT)),
        "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "source_count": 0,
        "results": [],
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    if args.workers == 1:
        for case in cases:
            result = evaluate_case(case)
            report["results"].append(result)
            target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print(
                result["id"],
                result["status"],
                ",".join(result.get("actual_categories", [])),
                flush=True,
            )
            if any(
                "HTTP 429" in d or "cooldown" in d
                for d in result.get("diagnostics", [])
            ):
                report["provider_blocker"] = (
                    "Quota cooldown reached; remaining cases not attempted in this run"
                )
                break
            if args.pause > 0:
                time.sleep(min(args.pause, 10))
    else:
        with ThreadPoolExecutor(max_workers=max(1, min(2, args.workers))) as pool:
            futures = {pool.submit(evaluate_case, c): c["id"] for c in cases}
            for future in as_completed(futures):
                result = future.result()
                report["results"].append(result)
                target.write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n"
                )
                print(
                    result["id"],
                    result["status"],
                    ",".join(result.get("actual_categories", [])),
                    flush=True,
                )
    report["results"].sort(key=lambda r: r["id"])
    report["passed"] = sum(r["status"] == "PASS" for r in report["results"])
    report["total"] = len(cases)
    report["unique_followup_sets"] = len(
        {tuple(r.get("followups", [])) for r in report["results"]}
    )
    report["unique_evidence_sets"] = len(
        {
            tuple(
                sorted(
                    e for i in r.get("issues", []) for e in i.get("evidence_needed", [])
                )
            )
            for r in report["results"]
        }
    )
    report["source_count"] = len(
        __import__("backend.providers", fromlist=["ReviewedLegalSources"])
        .ReviewedLegalSources()
        .records
    )
    report["legal_acceptance"] = (
        "BLOCKED: authentic approved corpus absent"
        if not report["source_count"]
        else "Independent legal applicability assessment still required"
    )
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Live triage checks: {report['passed']}/{report['total']}; legal correctness is not inferred from this score."
    )
    if report["passed"] != report["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
