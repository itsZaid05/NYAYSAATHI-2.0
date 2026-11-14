"""Opt-in live Gemini checks with synthetic data. Never logs credentials or thought signatures."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from backend.config import settings
from backend.db import init
from backend.providers import GeminiProvider, ProviderUnavailable, ReviewedLegalSources
from backend.engine import assess
from backend.schemas import Consent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--embedding-model", required=True)
    args = parser.parse_args()
    settings.gemini_model = args.model
    settings.embedding_model = args.embedding_model
    settings.runtime = settings.runtime / "live-validation"
    init()
    p = GeminiProvider()
    results = []

    def check(name, operation):
        try:
            detail = operation()
            results.append({"check": name, "status": "PASS", "detail": detail})
        except (ProviderUnavailable, ValueError) as exc:
            results.append({"check": name, "status": "FAIL", "detail": str(exc)})

    check(
        "model list",
        lambda: {
            "count": len(p.models()),
            "configured_generation": args.model,
            "configured_embedding": args.embedding_model,
        },
    )
    from backend.schemas import Extracted

    check(
        "minimal generation",
        lambda: {
            "validated": p.generate(
                "Return facts as the exact supplied fictional statement; no timeline/questions/follow_up needed.",
                {"text": "Fictional connectivity test."},
                Extracted,
            ).facts
        },
    )
    narrative = "Fictional: I purchased a laptop online from Demo Seller for INR 45000. It stopped working shortly after delivery. The seller refused a replacement. I have a synthetic invoice and warranty. I want a replacement."
    a = assess(
        "live-acceptance",
        narrative,
        "IN",
        "en",
        Consent(processing=True, fictional_demo=True, ai_processing=True),
    )
    results.append(
        {
            "check": "structured intake",
            "status": "PASS" if a.ai_status.startswith("Gemini live") else "FAIL",
            "detail": {
                "ai_status": a.ai_status,
                "parties": [x.value for x in a.parties],
                "amounts": [x.value for x in a.amounts],
                "questions": a.unknowns,
            },
        }
    )
    followup = (
        narrative
        + " I purchased it on 2026-10-01 and it was delivered on 2026-10-03. The problem began on 2026-10-04. The platform was Demo Shop."
    )
    b = assess("live-acceptance", followup, "IN", "en", a.consent, old=a)
    results.append(
        {
            "check": "multi-turn factual follow-up",
            "status": "PASS"
            if b.ai_status.startswith("Gemini live") and len(b.timeline) >= 3
            else "FAIL",
            "detail": {
                "ai_status": b.ai_status,
                "timeline_events": len(b.timeline),
                "questions": b.unknowns,
            },
        }
    )
    check(
        "real embedding",
        lambda: {
            "dimensions": len(p.embed(["Fictional defective laptop invoice refund"])[0])
        },
    )
    source_provider = ReviewedLegalSources()
    if source_provider.records:
        check(
            "hybrid retrieval",
            lambda: {"mode": source_provider.search(narrative, semantic=True)[1]},
        )
        results.append(
            {
                "check": "grounded reasoning",
                "status": "PASS"
                if b.legal_analysis and b.legal_analysis.claims
                else "FAIL",
                "detail": {
                    "accepted_claims": len(b.legal_analysis.claims)
                    if b.legal_analysis
                    else 0
                },
            }
        )
    else:
        for name in [
            "hybrid retrieval over official law",
            "official-source grounded reasoning",
        ]:
            results.append(
                {
                    "check": name,
                    "status": "BLOCKED",
                    "detail": "No authenticated, rights-reviewed official passages available; synthetic material is never substituted as law.",
                }
            )
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_data_only": True,
        "runtime_overrides_only": True,
        "results": results,
    }
    path = settings.runtime / "live-results.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    for r in results:
        print(r["status"], r["check"], r["detail"])
    print("Saved non-secret validation report:", path)
    if any(r["status"] == "FAIL" for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
