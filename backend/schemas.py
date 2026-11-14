from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from urllib.parse import urlparse
from pydantic import BaseModel, Field, model_validator


class StrictModel(BaseModel):
    model_config = {"extra": "forbid"}


class Consent(StrictModel):
    processing: bool
    fictional_demo: bool
    ai_processing: bool = False
    sharing: bool = False


class Intake(StrictModel):
    narrative: str = Field(min_length=10, max_length=12000)
    jurisdiction: str = Field(default="IN", max_length=10)
    language: Literal["en", "hi"] = "en"
    consent: Consent


class Message(StrictModel):
    text: str = Field(min_length=2, max_length=6000)


class Fact(StrictModel):
    text: str = Field(max_length=1500)
    origin: Literal["user_allegation", "document_excerpt"] = "user_allegation"
    document_id: str | None = None


class Event(StrictModel):
    date: str
    description: str
    date_basis: str = "explicit ISO date"
    document_id: str | None = None


class Source(StrictModel):
    jurisdiction: Literal["IN"] = "IN"
    artifact_sha256: str | None = None
    source_type: str = "unspecified"
    reuse_rights: str = "See retained source review record"
    verification_method: str = "Artifact checksum and exact passage verification"
    valid_from: str | None = None
    valid_until: str | None = None
    legal_review_status: str = "Technical source verification only; qualified interpretation review not established"
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1)
    url: str
    provision: str = Field(min_length=1)
    version: str = Field(min_length=1)
    checked_at: datetime
    quote: str = Field(min_length=5, max_length=16000)

    @model_validator(mode="after")
    def official(self):
        host = urlparse(self.url).hostname or ""
        if not (
            host.endswith(".gov.in") or host.endswith(".nic.in")
        ) or not self.url.startswith("https://"):
            raise ValueError("Only official Indian HTTPS legal sources are permitted")
        return self


class Option(StrictModel):
    action: str
    conditions: str
    caveats: str
    source_ids: list[str] = Field(min_length=1)
    # Only verbatim source propositions are displayed as legal claims.
    proposition: str = Field(min_length=1)


class Evidence(StrictModel):
    item: str
    present: bool
    reason: str


class Scenario(StrictModel):
    id: str = "legacy"
    title: str = "Fictional consumer illustration"
    category: str = "consumer"
    source_ids: list[str] = Field(default_factory=list)
    lessons: list[str] = Field(default_factory=list)
    similarities: str = ""
    differences: str = ""
    label: Literal["Fictional illustration — not a judgment"] = (
        "Fictional illustration — not a judgment"
    )
    text: str


class Draft(StrictModel):
    id: str
    kind: Literal[
        "seller_representation",
        "refund_request",
        "grievance_summary",
        "chronology",
        "evidence_inventory",
        "lawyer_brief",
    ] = "seller_representation"
    content: str = Field(max_length=24000)
    status: Literal["Editable draft — not filed"] = "Editable draft — not filed"


class CaseAssessment(StrictModel):
    reference_at: datetime | None = None
    assistant_message: str = ""
    parties: list[Entity] = Field(default_factory=list)
    amounts: list[Entity] = Field(default_factory=list)
    desired_remedy: str = ""
    legal_analysis: LegalAnalysis | None = None
    claim_verification: list[ClaimVerdict] = Field(default_factory=list)
    readiness_findings: list[ReadinessFinding] = Field(default_factory=list)
    evidence_analysis: list[EvidenceAnalysis] = Field(default_factory=list)
    conversation: list[ConversationTurn] = Field(default_factory=list)
    analysis_fingerprint: str = ""
    precedent_status: str = "Disabled: no authorised, validated judgment corpus"
    case_id: str
    jurisdiction: str
    category: str
    consent: Consent
    language: Literal["en", "hi"]
    facts: list[Fact]
    unknowns: list[str]
    timeline: list[Event]
    issues: list[str]
    sources: list[Source]
    options: list[Option]
    evidence: list[Evidence]
    readiness: Literal["Strong", "Partial", "Needs information"]
    readiness_flags: list[str]
    illustrative_scenarios: list[Scenario]
    drafts: list[Draft]
    safety_flags: list[str]
    handoff_status: Literal[
        "not_shared", "shared_with_demo_lawyer", "reviewed_by_demo_lawyer"
    ]
    ai_status: str
    retrieval_mode: str

    @model_validator(mode="after")
    def citations(self):
        sources = {s.id: s for s in self.sources}
        if len(sources) != len(self.sources):
            raise ValueError("Duplicate source IDs")
        for opt in self.options:
            if any(s not in sources for s in opt.source_ids):
                raise ValueError("Unknown source reference")
            if not any(opt.proposition in sources[s].quote for s in opt.source_ids):
                raise ValueError(
                    "Legal proposition must be supported by a verbatim retrieved passage"
                )
        if self.legal_analysis:
            for claim in self.legal_analysis.claims:
                if claim.support_status != "supported" or len(claim.source_ids) != len(
                    claim.supporting_quotes
                ):
                    raise ValueError("Unverified legal interpretation")
                for sid, quote in zip(claim.source_ids, claim.supporting_quotes):
                    if (
                        sid not in sources
                        or not quote.strip()
                        or quote not in sources[sid].quote
                    ):
                        raise ValueError("Unsupported legal interpretation citation")
        if self.options and self.jurisdiction != "IN":
            raise ValueError(
                "Indian legal options cannot be used for another jurisdiction"
            )
        return self


class Extracted(StrictModel):
    assistant_message: str = ""
    parties: list[Entity] = Field(default_factory=list, max_length=15)
    amounts: list[Entity] = Field(default_factory=list, max_length=15)
    desired_remedy: str = ""
    remedy_quote: str = ""
    facts: list[str] = Field(max_length=30)
    timeline: list[Event] = Field(max_length=30)
    unknowns: list[str] = Field(max_length=20)
    follow_up: str = Field(max_length=1500)


class Grounded(StrictModel):
    source_id: str
    quote: str = Field(min_length=1, max_length=4000)


class Reasoning(StrictModel):
    analysis: LegalAnalysis | None = None
    claims: list[Grounded] = Field(max_length=8)


class DraftRequest(StrictModel):
    kind: Literal[
        "seller_representation",
        "refund_request",
        "grievance_summary",
        "chronology",
        "evidence_inventory",
        "lawyer_brief",
    ] = "seller_representation"
    content: str | None = Field(default=None, max_length=24000)


class ShareRequest(StrictModel):
    consent: bool


class LawyerLogin(StrictModel):
    password: str = Field(min_length=1, max_length=256)


# Additive canonical intelligence contracts; legacy cases migrate with safe defaults.
class Entity(StrictModel):
    value: str = Field(min_length=1, max_length=300)
    quote: str = Field(min_length=1, max_length=1500)
    role: str = Field(default="", max_length=80)
    origin: Literal["user_allegation", "document_excerpt"] = "user_allegation"
    document_id: str | None = None


class Question(StrictModel):
    key: str = Field(max_length=80)
    question: str = Field(min_length=3, max_length=600)
    reason: str = Field(max_length=600)


class IntakeIntelligence(StrictModel):
    assistant_message: str = Field(max_length=1200)
    parties: list[Entity] = Field(default_factory=list, max_length=15)
    amounts: list[Entity] = Field(default_factory=list, max_length=15)
    desired_remedy: str = Field(default="", max_length=300)
    remedy_quote: str = Field(default="", max_length=1500)
    questions: list[Question] = Field(default_factory=list, max_length=6)


class LegalClaim(StrictModel):
    id: str = Field(max_length=80)
    proposition: str = Field(min_length=5, max_length=1000)
    source_ids: list[str] = Field(min_length=1, max_length=3)
    supporting_quotes: list[str] = Field(min_length=1, max_length=3)
    application: str = Field(max_length=1200)
    fact_quotes: list[str] = Field(default_factory=list, max_length=5)
    conditions: list[str] = Field(max_length=6)
    unknowns: list[str] = Field(max_length=6)
    suggested_action: str = Field(max_length=600)
    qualification: str = Field(min_length=10, max_length=600)
    support_status: Literal["pending", "supported", "rejected"] = "pending"


class LegalAnalysis(StrictModel):
    overview: str = Field(max_length=1400)
    claims: list[LegalClaim] = Field(default_factory=list, max_length=6)
    story_similarity: str = Field(default="", max_length=800)
    story_difference: str = Field(default="", max_length=800)


class ClaimVerdict(StrictModel):
    claim_id: str
    supported: bool
    reason: str = Field(max_length=600)


class SupportEvaluation(StrictModel):
    verdicts: list[ClaimVerdict] = Field(max_length=8)


class ConversationTurn(StrictModel):
    role: Literal["user", "assistant", "correction"]
    text: str = Field(max_length=12000)
    at: datetime


class ReadinessFinding(StrictModel):
    dimension: str
    status: Literal["available", "missing", "needs_review"]
    finding: str


class EvidenceAnalysis(StrictModel):
    document_id: str
    filename: str
    kind: str
    extraction_method: str
    dates: list[str]
    amounts: list[str]
    transaction_references: list[str]
    relevant_excerpts: list[str]
    supports_fact_quotes: list[str]
    warnings: list[str]


class CaseContextUpdate(StrictModel):
    narrative: str | None = Field(default=None, min_length=10, max_length=30000)
    language: Literal["en", "hi"] | None = None


class ConsentUpdate(StrictModel):
    ai_processing: bool


CaseAssessment.model_rebuild()

Extracted.model_rebuild()
Reasoning.model_rebuild()


class AuthenticJudgment(StrictModel):
    id: str
    title: str
    court: str
    decision_date: date
    citation: str
    authoritative_url: str
    relevant_facts: str
    legal_principle: str
    comparison_limits: str
    reuse_rights: str
    verified_at: datetime
