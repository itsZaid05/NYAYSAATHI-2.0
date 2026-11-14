import re
import uuid
from datetime import date
from backend.providers import (
    GeminiProvider,
    ProviderUnavailable,
    ReviewedLegalSources,
)
from backend.config import settings
from backend.schemas import (
    Question,
    CaseAssessment,
    Consent,
    Draft,
    Event,
    Evidence,
    Fact,
    Option,
)

SENSITIVE = [
    r"\b[A-Z]{5}\d{4}[A-Z]\b",
    r"\b\d{4}[ -]\d{4}[ -]\d{4}\b",
    r"\b\d{12,16}\b",
    r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
    r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)",
]


def redact(text):
    for pattern in SENSITIVE:
        text = re.sub(pattern, "[redacted identifier]", text, flags=re.I)
    return text


def classify(text, jurisdiction):
    low = text.casefold()
    if jurisdiction != "IN":
        return "unsupported_jurisdiction"
    unrelated = [
        "divorce",
        "custody",
        "inheritance",
        "arrest",
        "criminal",
        "domestic violence",
        "तलाक",
        "विरासत",
        "गिरफ्तार",
        "घरेलू हिंसा",
        "sexual assault",
        "eviction",
        "tenant",
        "employment",
        "salary",
        "land dispute",
    ]
    if any(w in low for w in unrelated):
        return "unsupported_domain"
    groups = [
        ("defective_product", ["defect", "broken", "fault", "laptop", "खराब", "लैपटॉप"]),
        ("refund_refusal", ["refund", "रिफंड", "पैसे वापस"]),
        ("warranty", ["warranty", "वारंटी"]),
        ("online_shopping", ["online", "delivery", "ऑनलाइन", "डिलीवरी"]),
        ("service_deficiency", ["service", "repair", "सेवा", "मरम्मत"]),
    ]
    for name, words in groups:
        if any(w in low for w in words):
            return name
    return "needs_clarification"


def local_extract(text, language):
    facts = []
    timeline = []
    for sentence in re.split(r"(?<=[.!?।])\s+|\n+", text):
        if sentence.strip():
            facts.append(Fact(text=sentence.strip()[:1500]))
            for value in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", sentence):
                try:
                    date.fromisoformat(value)
                except ValueError:
                    continue
                timeline.append(Event(date=value, description=sentence.strip()[:1500]))
    return facts[:30], sorted(timeline, key=lambda e: e.date)[:30]


def assess(
    case_id,
    text,
    jurisdiction,
    language,
    consent,
    evidence_rows=(),
    old=None,
    use_ai=True,
):
    import hashlib, json
    from datetime import datetime, timezone
    from backend.schemas import ClaimVerdict, IntakeIntelligence, ReadinessFinding
    from backend.services.case_state import structured_local, validate_intelligence
    from backend.services.citation_verification import verify
    from backend.services.evidence_analysis import analyse_document
    from backend.services.scenario_engine import ScenarioEngine

    clean = redact(text)
    category = classify(clean, jurisdiction)
    facts, _ = local_extract(clean, language)
    reference = (
        old.reference_at if old and old.reference_at else datetime.now(timezone.utc)
    )
    context, timeline = structured_local(clean, language, reference)
    flags = [
        "Educational case preparation; user allegations and document excerpts are not verified facts. No complaint has been filed."
    ]
    if any(e.date_basis.startswith("Resolved") for e in timeline):
        flags.append(
            "Relative dates were resolved against the visible case reference date in Asia/Kolkata; confirm them before use."
        )
    if clean != text:
        flags.append(
            "Identifiers redacted. Automated redaction is incomplete; use fictional data only."
        )
    danger = any(
        w in clean.casefold()
        for w in ["suicide", "kill myself", "immediate danger", "धमकी", "जान का खतरा"]
    )
    supported = (
        category
        not in ("unsupported_domain", "unsupported_jurisdiction", "needs_clarification")
        and not danger
    )
    if danger:
        flags.append(
            "Urgent safety concern: contact local emergency services (112 in India). This is not an emergency service."
        )
    if not supported:
        flags.append(
            "Outside supported scope or insufficient information. Consult a qualified professional; NALSA information is in Help."
        )
    documents = [analyse_document(row, clean) for row in evidence_rows]
    for row in evidence_rows:
        if row["excerpt"]:
            facts.append(
                Fact(
                    text=row["excerpt"][:1500],
                    origin="document_excerpt",
                    document_id=row["id"],
                )
            )
    for doc in documents:
        flags.extend(doc.warnings)
    provider = ReviewedLegalSources()
    corpus_hash = hashlib.sha256(
        json.dumps(
            [r.model_dump(mode="json") for r in provider.records], sort_keys=True
        ).encode()
    ).hexdigest()
    fingerprint = hashlib.sha256(
        (
            clean
            + language
            + jurisdiction
            + corpus_hash
            + json.dumps(
                [(d.document_id, d.relevant_excerpts) for d in documents],
                ensure_ascii=False,
            )
        ).encode()
    ).hexdigest()
    unchanged = bool(old and old.analysis_fingerprint == fingerprint)
    ai_allowed = (
        use_ai
        and settings.processing_mode
        == "demonstration"
        and consent.ai_processing
        and consent.fictional_demo
        and clean == text
        and supported
    )
    ai_status = "Local structured preparation — Gemini not used"
    if ai_allowed:
        try:
            result = GeminiProvider().extract(
                clean, language, [q.question for q in context.questions]
            )
            if any(f not in clean for f in result.facts) or any(
                e.description not in clean or e.date not in e.description
                for e in result.timeline
            ):
                raise ProviderUnavailable("AI fact provenance rejected")
            validate_intelligence(result, clean)
            if re.search(
                r"section\s+\d|धारा\s*[०-९\d]|you (?:are entitled|must file)|guaranteed|file within",
                result.assistant_message,
                re.I,
            ):
                raise ProviderUnavailable(
                    "AI intake contained an unsupported legal assertion"
                )
            # Questions can be natural, but must not smuggle legal conclusions or instructions.
            questions = list(
                dict.fromkeys([q.strip() for q in result.unknowns if q.strip()])
            )[:5]
            if any(
                not q.endswith(("?", "？"))
                or re.search(
                    r"\bsection\b|धारा|guarantee|must file|entitled|\d+%", q, re.I
                )
                for q in questions
            ):
                raise ProviderUnavailable(
                    "AI question contains an unsupported assertion"
                )
            context = IntakeIntelligence(
                assistant_message=result.assistant_message or context.assistant_message,
                parties=result.parties or context.parties,
                amounts=result.amounts or context.amounts,
                desired_remedy=result.desired_remedy or context.desired_remedy,
                remedy_quote=result.remedy_quote or context.remedy_quote,
                questions=[
                    Question(
                        key="ai-" + str(i),
                        question=q,
                        reason="Factual gap identified from the case context",
                    )
                    for i, q in enumerate(questions)
                ],
            )
            if result.timeline:
                timeline = sorted(result.timeline, key=lambda x: x.date)
            ai_status = (
                "Gemini live structured intake; entity and fact provenance validated"
            )
        except (ProviderUnavailable, ValueError) as exc:
            ai_status = "Gemini unavailable or unverified — local preparation only"
            flags.append(str(exc))
    elif unchanged and old:
        context.assistant_message = old.assistant_message or context.assistant_message
        context.parties = old.parties or context.parties
        context.amounts = old.amounts or context.amounts
        context.desired_remedy = old.desired_remedy or context.desired_remedy
        # GET revalidation preserves accepted case intelligence; it never asks the model again.
        if old.ai_status.startswith("Gemini live"):
            context.questions = [
                Question(
                    key="saved-" + str(i),
                    question=q,
                    reason="Persisted factual question",
                )
                for i, q in enumerate(old.unknowns)
            ]
        ai_status = old.ai_status
    if not supported:
        context.questions = [
            Question(
                key="scope",
                question="Please describe an Indian consumer purchase/service dispute, or seek qualified legal-aid assistance.",
                reason="Scope gate",
            )
        ]
    sources, mode = (
        provider.search(
            clean,
            semantic=ai_allowed,
            event_date=timeline[0].date if timeline else None,
        )
        if supported
        else ([], "disabled for unsupported/urgent request")
    )
    if unchanged and old and supported:
        approved = {r.id: r for r in provider.records}
        if all(
            x.id in approved and x.quote == approved[x.id].quote for x in old.sources
        ):
            sources = [approved[x.id] for x in old.sources]
            mode = old.retrieval_mode
    options = []
    analysis = None
    verdicts = []
    if sources:
        selected = [(x, x.quote) for x in sources]
        if ai_allowed:
            try:
                result = GeminiProvider().reason(clean, sources)
                by_id = {x.id: x for x in sources}
                if any(
                    c.source_id not in by_id or c.quote not in by_id[c.source_id].quote
                    for c in result.claims
                ):
                    raise ProviderUnavailable(
                        "AI claim failed independent citation validation"
                    )
                selected = [(by_id[c.source_id], c.quote) for c in result.claims]
                if result.analysis:
                    analysis, verdicts = verify(
                        result.analysis, sources, clean, GeminiProvider()
                    )
                    ai_status += (
                        "; "
                        + str(len(analysis.claims))
                        + " legal propositions passed separate AI support checks"
                    )
            except ProviderUnavailable as exc:
                selected = []
                flags.append("AI legal output rejected or unavailable: " + str(exc))
        elif unchanged and old:
            analysis = old.legal_analysis
            verdicts = old.claim_verification
            ai_status = old.ai_status
        for source, quote in selected:
            options.append(
                Option(
                    action="Read the relevant official passage",
                    conditions="Applicability to your facts needs professional review.",
                    caveats="Current rules and legal interpretation need independent professional review.",
                    source_ids=[source.id],
                    proposition=quote,
                )
            )
    elif supported:
        flags.append(
            "Verified law unavailable: no reviewed official passages matched the case. Legal conclusions and deadlines are withheld."
        )
    if analysis and any(c.support_status != "supported" for c in analysis.claims):
        analysis = None
    items = []
    checks = [
        ("invoice", "Purchase invoice / payment record", "खरीद का बिल / भुगतान रिकॉर्ड"),
        ("fault", "Fault description / photographs", "खराबी का विवरण / तस्वीरें"),
        ("communication", "Seller correspondence", "विक्रेता से पत्राचार"),
        ("warranty", "Warranty / order terms", "वारंटी / ऑर्डर की शर्तें"),
    ]
    for kind, en, hi in checks:
        relevant = [d for d in documents if d.kind == kind and d.relevant_excerpts]
        items.append(
            Evidence(
                item=hi if language == "hi" else en,
                present=bool(relevant),
                reason="Readable uploaded document; relevance and authenticity require review."
                if relevant
                else "No readable supporting document uploaded. Mention in chat does not establish availability.",
            )
        )
    findings = [
        ReadinessFinding(
            dimension="transaction facts",
            status="available" if context.parties and timeline else "missing",
            finding="Seller and dated events are described."
            if context.parties and timeline
            else "Confirm parties and event dates before procedural analysis.",
        ),
        ReadinessFinding(
            dimension="evidence coverage",
            status="available" if all(e.present for e in items) else "missing",
            finding="; ".join(
                e.item + (": readable upload" if e.present else ": missing")
                for e in items
            ),
        ),
        ReadinessFinding(
            dimension="contradictions / reconciliation",
            status="needs_review"
            if any(d.warnings for d in documents)
            else "available",
            finding="; ".join(w for d in documents for w in d.warnings)
            or "No date discrepancy detected by the limited local checks; this is not proof of consistency.",
        ),
        ReadinessFinding(
            dimension="legal sources",
            status="available" if sources else "missing",
            finding="Reviewed source passages available; temporal/substantive applicability still needs professional review."
            if sources
            else "Approved source coverage unavailable.",
        ),
        ReadinessFinding(
            dimension="legal interpretation",
            status="needs_review",
            finding="AI support evaluation is not a qualified human legal opinion.",
        ),
    ]
    readiness = (
        "Strong"
        if all(e.present for e in items)
        and timeline
        and not context.questions
        and sources
        and not any(d.warnings for d in documents)
        else "Partial"
        if any(e.present for e in items)
        else "Needs information"
    )
    scenarios = (
        ScenarioEngine().select(clean, category, language, sources) if supported else []
    )
    if analysis and scenarios:
        scenarios[0].similarities = (
            analysis.story_similarity or scenarios[0].similarities
        )
        scenarios[0].differences = analysis.story_difference or scenarios[0].differences
    return CaseAssessment(
        case_id=case_id,
        jurisdiction=jurisdiction,
        category=category,
        consent=consent,
        language=language,
        facts=facts,
        unknowns=[q.question for q in context.questions],
        timeline=timeline,
        issues=[category.replace("_", " ")],
        sources=sources,
        options=options,
        evidence=items,
        readiness=readiness,
        readiness_flags=[
            "Evidence completeness only; not a probability of winning.",
            "Strong requires readable evidence, described events, resolved factual gaps and available legal sources; it does not establish legal strength.",
            "No authenticity or professional legal review is claimed.",
        ],
        illustrative_scenarios=scenarios,
        drafts=old.drafts if old else [],
        safety_flags=flags,
        handoff_status=old.handoff_status if old else "not_shared",
        ai_status=ai_status,
        retrieval_mode=mode,
        reference_at=reference,
        assistant_message=context.assistant_message,
        parties=context.parties,
        amounts=context.amounts,
        desired_remedy=context.desired_remedy,
        legal_analysis=analysis,
        claim_verification=verdicts,
        readiness_findings=findings,
        evidence_analysis=documents,
        conversation=old.conversation if old else [],
        analysis_fingerprint=fingerprint,
    )


def make_draft(assessment):
    facts = "\n".join(
        "- " + f.text for f in assessment.facts if f.origin == "user_allegation"
    )
    if assessment.language == "hi":
        content = f"""विक्रेता को प्रतिनिधित्व — संपादन योग्य मसौदा, दाखिल नहीं हुआ
प्रति: [विक्रेता का नाम/पता]
विषय: उपभोक्ता खरीद के संबंध में समाधान का अनुरोध

मेरे द्वारा बताया गया घटनाक्रम (सत्यापित तथ्य नहीं):
{facts}

ऑर्डर संख्या / कीमत: [भरें]
खरीद की तारीख: [भरें]
खराबी और संपर्क का विवरण: [जांचें और भरें]
मांगा गया समाधान: [मरम्मत / बदलना / रिफंड — चुनें और कारण बताएं]
संलग्न दस्तावेज: [केवल उपलब्ध दस्तावेज लिखें]
कृपया मेरे अनुरोध पर लिखित जवाब दें।
[नाम / संपर्क — भेजने से पहले स्वयं भरें]

यह मसौदा कोई कानूनी निष्कर्ष या निर्धारित समय-सीमा नहीं बताता। भेजने से पहले तथ्यों की समीक्षा करें।"""
    else:
        content = f"""SELLER REPRESENTATION — EDITABLE DRAFT, NOT FILED
To: [Seller name and address]
Subject: Request to resolve a consumer purchase issue

My account of events (user allegations, not independently verified):
{facts}

Order reference / amount paid: [complete]
Purchase date: [complete]
Fault and correspondence: [check and complete]
Requested resolution: [repair / replacement / refund — choose and explain]
Enclosures: [list only documents actually available]
Please provide a written response to this request.
[Name and contact details — add privately before sending]

This draft makes no finding of liability and sets no statutory deadline. Review all facts and attachments before sending. No official complaint has been filed."""
    return Draft(id=uuid.uuid4().hex, content=content)
