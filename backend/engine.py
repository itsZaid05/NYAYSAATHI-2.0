import re
import uuid
from datetime import date
from backend.providers import (
    FictionalScenarioProvider,
    GeminiProvider,
    ProviderUnavailable,
    ReviewedLegalSources,
)
from backend.schemas import (
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
    clean = redact(text)
    category = classify(clean, jurisdiction)
    facts, timeline = local_extract(clean, language)
    flags = [
        "Educational case preparation; allegations are not proven facts. No complaint has been filed."
    ]
    if clean != text:
        flags.append(
            "Identifiers redacted. Automated redaction is incomplete; use fictional data only."
        )
    danger = any(
        w in clean.lower()
        for w in ["suicide", "kill myself", "immediate danger", "धमकी", "जान का खतरा"]
    )
    if danger:
        flags.append(
            "Urgent safety concern: contact local emergency services (112 in India); this workspace is not an emergency service."
        )
    supported = (
        category
        not in ("unsupported_domain", "unsupported_jurisdiction", "needs_clarification")
        and not danger
    )
    if not supported:
        flags.append(
            "Outside supported scope or insufficient information. Seek qualified advice; NALSA legal-aid information is linked in Help. No legal assessment generated."
        )
    checks = [
        ("invoice", "Purchase invoice / payment record", "खरीद का बिल / भुगतान रिकॉर्ड"),
        ("fault", "Fault description / photographs", "खराबी का विवरण / तस्वीरें"),
        ("communication", "Seller correspondence", "विक्रेता से पत्राचार"),
        ("warranty", "Warranty / order terms", "वारंटी / ऑर्डर की शर्तें"),
    ]
    items = []
    for kind, en, hi in checks:
        present = any(row["kind"] == kind for row in evidence_rows)
        items.append(
            Evidence(
                item=hi if language == "hi" else en,
                present=present,
                reason="Uploaded document classified by the user; authenticity and sufficiency are not verified."
                if present
                else "Not uploaded. Mentioning a document in chat does not establish its availability.",
            )
        )
    questions = []
    for condition, en, hi in [
        (
            not timeline,
            "What were the purchase, delivery and fault dates? Use YYYY-MM-DD where known.",
            "खरीद, डिलीवरी और खराबी की तारीखें क्या हैं? ज्ञात तारीख YYYY-MM-DD में लिखें।",
        ),
        (
            not re.search(r"\bseller\s*[:=-]|\bfrom\b|विक्रेता\s*[:=-]", clean, re.I),
            "Who sold the item, and through which platform?",
            "विक्रेता कौन था और किस प्लेटफॉर्म से खरीदा?",
        ),
        (
            not items[2].present,
            "What did you ask the seller for, and how did they respond? Upload fictional correspondence if available.",
            "आपने विक्रेता से क्या समाधान मांगा और उनका जवाब क्या था? उपलब्ध हो तो काल्पनिक पत्राचार अपलोड करें।",
        ),
    ]:
        if condition:
            questions.append(hi if language == "hi" else en)
    if not supported:
        questions = [
            "Please describe an Indian consumer purchase or service dispute. For other matters, consult a qualified professional."
            if language == "en"
            else "कृपया भारतीय उपभोक्ता खरीद या सेवा विवाद बताएं। अन्य मामलों के लिए योग्य पेशेवर से सलाह लें।"
        ]
    ai_status = "Local structured preparation — Gemini not used"
    ai_allowed = (
        use_ai
        and consent.ai_processing
        and consent.fictional_demo
        and clean == text
        and supported
    )
    if ai_allowed:
        try:
            result = GeminiProvider().extract(clean, language, questions)
            # Independent fact provenance: reject every invented fact/date.
            if any(f not in clean for f in result.facts) or any(
                e.description not in clean or e.date not in e.description
                for e in result.timeline
            ):
                raise ProviderUnavailable(
                    "AI extraction failed fact-provenance validation"
                )
            if result.follow_up and result.follow_up not in questions:
                raise ProviderUnavailable(
                    "AI follow-up was outside the approved missing-fact questions"
                )
            if any(q not in questions for q in result.unknowns):
                raise ProviderUnavailable(
                    "AI question not grounded in missing information"
                )
            if result.follow_up:
                questions = [result.follow_up] + [
                    q for q in questions if q != result.follow_up
                ]
            facts = [Fact(text=f) for f in result.facts]
            timeline = []
            for event in result.timeline:
                date.fromisoformat(event.date)
                timeline.append(event)
            timeline.sort(key=lambda e: e.date)
            # Required missing-information checks are deterministic; model cannot suppress them.
            ai_status = (
                "Gemini structured extraction validated against the supplied narrative"
            )
        except (ProviderUnavailable, ValueError) as exc:
            ai_status = "Gemini unavailable or unverified — local preparation only"
            flags.append(
                "AI extraction not accepted. No generated legal reasoning is displayed."
            )
    elif consent.ai_processing and clean != text:
        flags.append(
            "AI transmission blocked because identifiers were detected. Use a wholly fictional narrative."
        )
    if len(clean) > sum(len(f.text) for f in facts) + 300:
        flags.append(
            "Summary excerpts may be abbreviated; the complete redacted narrative is retained for follow-up processing."
        )
    provider = ReviewedLegalSources()
    sources, mode = (
        provider.search(
            clean,
            semantic=ai_allowed,
            event_date=timeline[0].date if timeline else None,
        )
        if supported
        else ([], "disabled for unsupported/urgent request")
    )
    options = []
    if sources:
        selected = [(s, s.quote) for s in sources]
        if ai_allowed:
            try:
                result = GeminiProvider().reason(clean, sources)
                by_id = {s.id: s for s in sources}
                if any(
                    c.source_id not in by_id or c.quote not in by_id[c.source_id].quote
                    for c in result.claims
                ):
                    raise ProviderUnavailable(
                        "AI claim failed independent citation validation"
                    )
                selected = [(by_id[c.source_id], c.quote) for c in result.claims]
                ai_status += "; Gemini passage selection verified"
            except ProviderUnavailable:
                selected = []
                flags.append(
                    "AI legal output rejected or unavailable; reviewed source cards remain available without AI conclusions."
                )
        for source, quote in selected:
            options.append(
                Option(
                    action="Read the relevant official passage",
                    conditions="Applicability to your facts needs professional review.",
                    caveats="Current rules, amendments, dates and forum requirements must be checked before action.",
                    source_ids=[source.id],
                    proposition=quote,
                )
            )
    elif supported:
        flags.append(
            "Verified law unavailable: no reviewed official passages are loaded. Legal conclusions, statutory citations and filing deadlines are withheld."
        )
    for row in evidence_rows:
        if row["excerpt"]:
            facts.append(Fact(text=row["excerpt"][:1500], origin="document_excerpt"))
    count = sum(e.present for e in items)
    readiness = (
        "Strong"
        if count == 4 and timeline and not questions
        else "Partial"
        if count
        else "Needs information"
    )
    scenario = FictionalScenarioProvider().scenario(language)
    from backend.schemas import Scenario

    if not use_ai and old:
        ai_status = (
            old.ai_status + "; source pack revalidated locally"
            if "revalidated" not in old.ai_status
            else old.ai_status
        )
    return CaseAssessment(
        case_id=case_id,
        jurisdiction=jurisdiction,
        category=category,
        consent=consent,
        language=language,
        facts=facts,
        unknowns=questions,
        timeline=timeline,
        issues=[category.replace("_", " ")],
        sources=sources,
        options=options,
        evidence=items,
        readiness=readiness,
        readiness_flags=[
            "Evidence completeness only; not a probability of winning.",
            "No document authenticity, legal merit or outcome verification.",
            "Dates are only reconstructed when explicitly supplied in ISO format.",
        ],
        illustrative_scenarios=[Scenario(text=scenario)] if supported else [],
        drafts=old.drafts if old else [],
        safety_flags=flags,
        handoff_status=old.handoff_status if old else "not_shared",
        ai_status=ai_status,
        retrieval_mode=mode,
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
