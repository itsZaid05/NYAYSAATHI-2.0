"""Independent structural/provenance checks plus a separately prompted support evaluation."""

from backend.schemas import LegalAnalysis
from backend.providers import ProviderUnavailable


def structurally_valid(claim, sources, narrative):
    import re

    by_id = {s.id: s for s in sources}
    if re.search(
        r"guaranteed (?:refund|win|success)|(?:100|99|95)\s*%|you will win",
        claim.proposition + " " + claim.application,
        re.I,
    ):
        return False, "Unqualified outcome guarantees are prohibited"
    if not claim.source_ids or len(claim.source_ids) != len(claim.supporting_quotes):
        return False, "Source/quote mapping is incomplete"
    if any(
        i not in by_id or not quote.strip() or quote not in by_id[i].quote
        for i, quote in zip(claim.source_ids, claim.supporting_quotes)
    ):
        return (
            False,
            "Citation is absent or quote does not occur in the approved passage",
        )
    if any(f not in narrative for f in claim.fact_quotes):
        return False, "Application relies on facts absent from the narrative"
    if not claim.qualification or not claim.conditions:
        return False, "Applicability/conditions are not qualified"
    return True, "Structural provenance checks passed"


def verify(analysis, sources, narrative, provider):
    from backend.schemas import ClaimVerdict

    candidates = []
    verdicts = []
    for claim in analysis.claims:
        valid, reason = structurally_valid(claim, sources, narrative)
        if valid:
            candidates.append(claim)
        else:
            verdicts.append(
                ClaimVerdict(claim_id=claim.id, supported=False, reason=reason)
            )
    accepted = []
    if candidates:
        try:
            evaluated = provider.evaluate_support(candidates, sources, narrative)
            results = {v.claim_id: v for v in evaluated.verdicts}
            for claim in candidates:
                verdict = results.get(
                    claim.id,
                    ClaimVerdict(
                        claim_id=claim.id,
                        supported=False,
                        reason="Independent evaluator did not return a verdict",
                    ),
                )
                verdicts.append(verdict)
                if verdict.supported:
                    claim.support_status = "supported"
                    accepted.append(claim)
        except ProviderUnavailable:
            verdicts.extend(
                ClaimVerdict(
                    claim_id=c.id,
                    supported=False,
                    reason="Support evaluation unavailable; conclusion withheld",
                )
                for c in candidates
            )
    import re

    def factual_comparison(value):
        return (
            ""
            if re.search(
                r"section|\bAct\b|धारा|must|entitled|guarantee|deadline|\d+\s*%",
                value,
                re.I,
            )
            else value
        )

    return LegalAnalysis(
        overview="AI interpretation, checked for source support; applicability still requires professional review."
        if accepted
        else "No AI legal proposition passed all support checks; review official source cards and prepare facts.",
        claims=accepted,
        story_similarity=factual_comparison(analysis.story_similarity)
        if accepted
        else "",
        story_difference=factual_comparison(analysis.story_difference)
        if accepted
        else "",
    ), verdicts
