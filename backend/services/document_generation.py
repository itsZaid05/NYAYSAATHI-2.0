"""Fact-based preparation documents, not court pleadings or filing automation."""

import uuid
from backend.schemas import Draft

KINDS = {
    "seller_representation": "Seller representation",
    "refund_request": "Refund / replacement request",
    "grievance_summary": "Consumer grievance summary",
    "chronology": "Case chronology",
    "evidence_inventory": "Evidence inventory",
    "lawyer_brief": "Lawyer consultation brief",
}


def generate(assessment, kind):
    if kind not in KINDS:
        raise ValueError("Unsupported document template")
    a = assessment
    hi = a.language == "hi"
    facts = "\n".join("- " + f.text for f in a.facts if f.origin == "user_allegation")
    parties = "; ".join(f"{x.role}: {x.value}" for x in a.parties) or (
        "[पक्षों का नाम भरें]" if hi else "[complete parties]"
    )
    amount = "; ".join(x.value for x in a.amounts) or (
        "[राशि भरें]" if hi else "[complete amount]"
    )
    remedy = a.desired_remedy or (
        "[मांगा गया समाधान भरें]" if hi else "[complete requested resolution]"
    )
    dates = (
        "\n".join(f"{x.date} — {x.description} ({x.date_basis})" for x in a.timeline)
        or "[No confirmed dates / तारीखें पुष्टि करें]"
    )
    docs = (
        "\n".join(
            f"- {x.filename} ({x.kind}) — unverified document {x.document_id}"
            for x in a.evidence_analysis
        )
        or "[No uploaded documents / कोई दस्तावेज़ नहीं]"
    )
    issue_notes = "\n".join(
        "- " + i.title + " [AI factual issue; not a legal finding]"
        for i in a.issue_details
    )
    evidence_gaps = "\n".join("- " + e.item + ": " + e.reason for e in a.evidence)
    missing = "\n".join("- " + x for x in a.unknowns) or (
        "अतिरिक्त तथ्यों की स्वतंत्र समीक्षा करें।"
        if hi
        else "Independently review any further missing information."
    )
    header = (
        "संपादन योग्य मसौदा — दाखिल नहीं हुआ; वकील द्वारा समीक्षा नहीं हुई।"
        if hi
        else "EDITABLE DRAFT — NOT FILED; NOT REVIEWED BY A LAWYER."
    )
    intro = f"{KINDS[kind]}\n{header}\nCase: {a.case_id}\n\n"
    summary = f"{'पक्ष' if hi else 'Parties'}: {parties}\n{'राशि' if hi else 'Amount'}: {amount}\n{'मांगा समाधान' if hi else 'Requested resolution'}: {remedy}\n"
    if kind in ("seller_representation", "refund_request"):
        body = (
            (
                "प्रति: [विक्रेता का सही पता भरें]\nविषय: उपभोक्ता खरीद का समाधान अनुरोध\n\n"
                if hi
                else "To: [confirm seller address]\nSubject: Request to resolve a consumer purchase\n\n"
            )
            + summary
            + "\n"
            + facts
            + "\n\n"
            + (
                "कृपया मेरे अनुरोध पर लिखित जवाब दें। यह पत्र दोष/दायित्व का कानूनी निष्कर्ष नहीं है।\n"
                if hi
                else "Please respond in writing to my request. This letter does not make a legal finding of fault or liability.\n"
            )
            + "\nEnclosures / संलग्नक:\n"
            + docs
        )
    elif kind == "chronology":
        body = summary + "\n" + dates
    elif kind == "evidence_inventory":
        body = docs + "\n\n" + missing
    else:
        body = (
            summary
            + "\nUser allegations / उपयोगकर्ता के आरोप:\n"
            + facts
            + "\n\nTimeline / घटनाक्रम:\n"
            + dates
            + "\n\nEvidence / साक्ष्य:\n"
            + docs
            + "\n\nUnresolved questions / अधूरे सवाल:\n"
            + missing
        )
    if kind in ("grievance_summary", "lawyer_brief", "evidence_inventory"):
        body += (
            "\n\nIssues to examine / विचार योग्य मुद्दे:\n"
            + issue_notes
            + "\n\nEvidence gaps / साक्ष्य की कमी:\n"
            + evidence_gaps
        )
    body += "\n\n" + (
        "भेजने से पहले तथ्यों, खाली स्थानों और संलग्नकों को जांचें। कोई कानूनी समय-सीमा या जीत की गारंटी नहीं दी गई।"
        if hi
        else "Review facts, placeholders and enclosures before use. No statutory deadline, guaranteed remedy or outcome is asserted."
    )
    return Draft(id=uuid.uuid4().hex, kind=kind, content=(intro + body)[:24000])
