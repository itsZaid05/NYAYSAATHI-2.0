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


class Event(StrictModel):
    date: str
    description: str


class Source(StrictModel):
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
    label: Literal["Fictional illustration — not a judgment"] = (
        "Fictional illustration — not a judgment"
    )
    text: str


class Draft(StrictModel):
    id: str
    kind: Literal["seller_representation"] = "seller_representation"
    content: str = Field(max_length=24000)
    status: Literal["Editable draft — not filed"] = "Editable draft — not filed"


class CaseAssessment(StrictModel):
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
        if self.options and self.jurisdiction != "IN":
            raise ValueError(
                "Indian legal options cannot be used for another jurisdiction"
            )
        return self


class Extracted(StrictModel):
    facts: list[str] = Field(max_length=30)
    timeline: list[Event] = Field(max_length=30)
    unknowns: list[str] = Field(max_length=20)
    follow_up: str = Field(max_length=1500)


class Grounded(StrictModel):
    source_id: str
    quote: str = Field(min_length=1, max_length=4000)


class Reasoning(StrictModel):
    claims: list[Grounded] = Field(max_length=8)


class DraftRequest(StrictModel):
    content: str | None = Field(default=None, max_length=24000)


class ShareRequest(StrictModel):
    consent: bool


class LawyerLogin(StrictModel):
    password: str = Field(min_length=1, max_length=256)
