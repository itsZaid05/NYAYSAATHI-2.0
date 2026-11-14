"""Canonical facts and provenance; deterministic local support is explicitly labelled."""

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.schemas import Entity, Event, IntakeIntelligence, Question

TIMEZONE = ZoneInfo("Asia/Kolkata")


def structured_local(text, language, reference_at):
    hi = language == "hi"
    parties = []
    amounts = []
    events = []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if s.strip()]
    for sentence in sentences:
        for m in re.finditer(
            r"(?:from\s+|seller\s*[:=-]\s*)([A-Z][\w ]{1,65}?)(?=\s+on\b|\s+for\b|[.,;]|$)",
            sentence,
            re.I,
        ):
            value = m.group(1).strip()
            if value:
                parties.append(
                    Entity(
                        value=value, quote=sentence[:1500], role="seller, as alleged"
                    )
                )
        for m in re.finditer(
            r"(?:₹\s*|INR\s*|Rs\.?\s*)(\d[\d,]*(?:\.\d{1,2})?)|\b(\d[\d,]*)\s*(?:रुपये|रुपए)",
            sentence,
            re.I,
        ):
            amounts.append(
                Entity(
                    value=m.group(0),
                    quote=sentence[:1500],
                    role="amount stated by user",
                )
            )
        for value in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", sentence):
            try:
                datetime.fromisoformat(value)
            except ValueError:
                continue
            events.append(Event(date=value, description=sentence[:1500]))
        # Resolve only explicitly supported relative phrases using a visible trusted case reference.
        ref = reference_at.astimezone(TIMEZONE).date()
        for match in re.finditer(
            r"\b(yesterday|today|last (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
            sentence,
            re.I,
        ):
            phrase = match.group(0).lower()
            if phrase == "today":
                resolved = ref
            elif phrase == "yesterday":
                resolved = ref - timedelta(days=1)
            else:
                weekday = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ].index(phrase[5:])
                resolved = ref - timedelta(days=(ref.weekday() - weekday) % 7 or 7)
            events.append(
                Event(
                    date=resolved.isoformat(),
                    description=sentence[:1500],
                    date_basis=f'Resolved "{match.group(0)}" against {ref.isoformat()} Asia/Kolkata; confirm with user',
                )
            )
    remedy_match = re.search(
        r"(?:I (?:want|requested|asked for|would like)|मुझे|मैंने).{0,100}?(?:refund|replacement|repair|रिफंड|बदल|मरम्मत|पैसे वापस)",
        text,
        re.I,
    )
    remedy_quote = remedy_match.group(0) if remedy_match else ""
    questions = []

    def question(key, en, hindi, reason):
        questions.append(Question(key=key, question=hindi if hi else en, reason=reason))

    if not parties:
        question(
            "seller",
            "Who was the seller, and which platform or service provider was involved?",
            "विक्रेता और प्लेटफॉर्म या सेवा प्रदाता कौन था?",
            "Identifies the parties without guessing responsibility.",
        )
    if not events:
        question(
            "dates",
            "When did you purchase, receive and first notice the problem?",
            "खरीद, डिलीवरी और समस्या की तारीखें क्या थीं?",
            "Dates are unknown; no deadline can be calculated.",
        )
    if not amounts:
        question(
            "amount",
            "How much did you pay, and was this a personal purchase or for resale/business?",
            "आपने कितना भुगतान किया? खरीद निजी उपयोग के लिए थी या व्यापार/पुनर्विक्रय के लिए?",
            "Transaction amount and purpose may affect legal conditions.",
        )
    if not remedy_quote:
        question(
            "remedy",
            "What resolution would you like, and what has the seller said so far?",
            "आप क्या समाधान चाहते हैं और विक्रेता ने अब तक क्या कहा?",
            "Requested remedy and seller response remain unclear.",
        )
    if re.search(
        r"last (?:week|month)|recently|some time|पिछले महीने|हाल ही", text, re.I
    ):
        question(
            "ambiguous_date",
            "Could you confirm the actual dates? Relative phrases such as “last month” are ambiguous.",
            "कृपया सही तारीखें बताएं; “पिछले महीने” जैसे शब्द अस्पष्ट हैं।",
            "Ambiguous dates remain unresolved.",
        )
    return IntakeIntelligence(
        assistant_message="यह परेशानी तनावपूर्ण हो सकती है। आपके बताए तथ्यों को व्यवस्थित करते हैं; कोई नतीजा तय नहीं माना गया है।"
        if hi
        else "That sounds frustrating. Let’s organise what you have told us and identify the missing details, without assuming an outcome.",
        parties=parties[:15],
        amounts=amounts[:15],
        desired_remedy=remedy_quote,
        remedy_quote=remedy_quote,
        questions=questions[:6],
    ), sorted(events, key=lambda e: e.date)


def validate_intelligence(result, narrative):
    for entity in result.parties + result.amounts:
        if entity.quote not in narrative or entity.value not in entity.quote:
            raise ValueError("Entity lacks verbatim narrative provenance")
    if result.desired_remedy and (
        result.remedy_quote not in narrative or not result.remedy_quote
    ):
        raise ValueError("Remedy lacks source excerpt")
    return result


def narrative_segments(text):
    """Stable selection IDs for the current canonical narrative, never generated facts."""
    pieces = [
        part.strip() for part in re.split(r"(?<=[.!?।])\s+|\n+", text) if part.strip()
    ]
    return {f"f{i}": piece for i, piece in enumerate(pieces)}


def ground_dynamic_extraction(result, narrative):
    """Only deterministic selection/alignment creates factual provenance."""
    segments = narrative_segments(narrative)
    if result.scope is None:
        # Preserve the strict legacy adapter contract; new dynamic output uses segment selection.
        if any(f not in narrative for f in result.facts) or any(
            e.description not in narrative or e.date not in e.description
            for e in result.timeline
        ):
            raise ValueError("AI fact provenance rejected")
    for entity in result.parties + result.amounts:
        if entity.segment_id:
            if entity.segment_id not in segments:
                raise ValueError("Entity selected unknown narrative segment")
            segment = segments[entity.segment_id]
            index = segment.find(entity.value)
            if index < 0:
                raise ValueError("Entity value is absent from selected source segment")
            start = max(0, index - 100)
            entity.quote = segment[start : start + 1500]
    for issue in result.issue_details:
        if issue.fact_segment_ids:
            if any(sid not in segments for sid in issue.fact_segment_ids):
                raise ValueError("AI issue selected an unknown narrative segment")
            issue.fact_quotes = list(
                dict.fromkeys(segments[sid] for sid in issue.fact_segment_ids)
            )
        if not issue.fact_quotes or any(q not in narrative for q in issue.fact_quotes):
            raise ValueError("AI issue lacks exact narrative provenance")
    if (
        result.scope is not None
        and result.desired_remedy
        and (not result.remedy_quote or result.remedy_quote not in narrative)
    ):
        result.desired_remedy = ""
        result.remedy_quote = ""
    # Model-generated prose summaries are never promoted into canonical facts or dates.
    result.facts = [f for f in result.facts if f in narrative]
    result.timeline = [
        e
        for e in result.timeline
        if e.description in narrative and e.date in e.description
    ]
    return result
