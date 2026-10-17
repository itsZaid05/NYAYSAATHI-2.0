"""NyaySaathi UK core: schemas, case-state extraction, verification gate.
Stdlib only. No LLM required; deterministic + source-grounded by design.
"""
import re, hashlib, datetime
from dataclasses import dataclass, field, asdict

JURISDICTION = "England and Wales"
SAFETY = [
 (r"\b(kill myself|suicide|self.?harm|end my life)\b", "urgent_self_harm",
  "If you may act on these thoughts, call 999 now or Samaritans free on 116 123 (24h). You do not have to go through this alone."),
 (r"\b(in danger|attacking me|hurt me tonight|afraid to go home|domestic abuse|hitting me)\b", "urgent_safety",
  "If you are in immediate danger call 999. Refuge National Domestic Abuse Helpline: 0808 2000 247 (free, 24h)."),
]
ISSUES = {
 "employment": (["sacked","dismissed","unfair dismissal","redundancy","employer","workplace","harassment at work","wages unpaid","discrimination at work"], ["contract of employment","payslips","dismissal/redundancy letter","grievance letters","ACAS Early Conciliation correspondence"]),
 "housing": (["eviction","landlord","tenancy","deposit not returned","rent arrears","disrepair","section 21","section 8"], ["tenancy agreement","deposit protection certificate","notices served (e.g. Section 21/8)","rent statements","photos of disrepair"]),
 "family": (["divorce","child arrangements","custody","domestic abuse","injunction","separation","hitting me","partner is hitting","afraid of my partner","my partner hit"], ["marriage/civil partnership certificate","children's documents (if relevant)","any court orders","safeguarding records"]),
 "consumer": (["refund refused","faulty goods","scam","trader","breach of contract","service not provided"], ["receipts/invoices","contract/terms","correspondence with trader","bank/card statements","photos"]),
 "benefits": (["benefit stopped","universal credit","pip refused","sanction","benefits appeal"], ["decision letters","medical evidence","benefit statements"]),
 "debt": (["debt collectors","ccj","county court claim","bailiffs","arrears"], ["claim form/judgment","creditor letters","income & expenditure details"]),
 "immigration": (["visa refused","asylum","home office","deportation","leave to remain"], ["Home Office decision letters","BRP/eVisa details","previous applications"]),
}
DATE_RE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|last (?:week|month|year)|yesterday|today)\b", re.I)

@dataclass
class Source:
    source_id: str; title: str; url: str; kind: str  # legislation|judgment
    court_or_body: str = ""; date: str = ""; citation: str = ""
    passage: str = ""; retrieved_at: str = ""; licence: str = ""
    verification: str = "verified_from_provider"  # only set after provider fetch+parse
    def to_dict(self): return asdict(self)

def build_case_state(narrative: str, category_hint: str = "") -> dict:
    text = narrative.strip()
    safety = [{"signal": s, "message": m} for pat, s, m in SAFETY if re.search(pat, text, re.I)]
    low = text.lower()
    issues = []
    for area, (kws, docs) in ISSUES.items():
        hits = [k for k in kws if k in low]
        if hits or category_hint.lower() == area:
            issues.append({"area": area, "confidence": "possible" if len(hits) < 2 else "likely-candidate",
                           "matched_terms": hits, "status": "candidate — not legally established",
                           "evidence_checklist": [{"item": d, "status": "unknown"} for d in docs]})
    events = [{"date_text": m.group(1), "date_certain": not m.group(1).lower().startswith("last"),
               "event": "Date mentioned in your account (please confirm what happened)", "status": "user-stated, unverified"}
              for m in DATE_RE.finditer(text)]
    return {"jurisdiction": JURISDICTION, "original_narrative": text,
            "facts": [{"text": text, "provenance": "user-stated", "verified": False}],
            "candidate_issues": issues, "timeline": events, "safety_signals": safety,
            "missing_information": (["What outcome are you hoping for?", "Have you received any letters, notices or court papers? If so, what dates do they show?"]
                                    if not issues else ["What outcome are you hoping for?", "Are there any deadlines mentioned in letters you have received?"]),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}

def verify_and_explain(case_state: dict, sources: list) -> dict:
    """Grounding gate: explanations may only cite source_ids actually retrieved.
    If no sources: explicit abstention, no legal propositions."""
    src = [s if isinstance(s, dict) else s.to_dict() for s in sources]
    base = {"sources": src, "disclaimer": "General legal information for England and Wales, not legal advice. A qualified solicitor or adviser should review your specific circumstances."}
    if not src:
        return {**base, "status": "insufficient_sources",
                "explanation": "I could not verify sufficiently relevant legal sources from the available official databases, so I should not summarise the law for your situation. You can try a more specific search, or speak to a qualified adviser (for example via Citizens Advice).",
                "propositions": []}
    props = [{"proposition": f"Source '{s['title']}' was retrieved from the official provider and may be relevant — open it to check it against your facts.",
              "supporting_source_ids": [s["source_id"]], "passage": s.get("passage", "")[:500]} for s in src]
    return {**base, "status": "grounded_information",
            "explanation": "The official sources below were retrieved for your candidate issue(s). They are listed with links so you can read them yourself. How they apply depends on your confirmed facts, which a qualified adviser can assess.",
            "propositions": props,
            "fact_to_law": {"supporting_facts_status": "Compare your confirmed timeline and documents against each source's requirements.",
                            "missing": case_state.get("missing_information", [])}}

def audit_event(kind: str, detail: dict) -> dict:
    """Content-free audit record: hashes, never narrative text."""
    return {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "kind": kind,
            "detail_hash": hashlib.sha256(repr(sorted(detail.items())).encode()).hexdigest()[:16],
            "detail_keys": sorted(detail.keys())}

def confirm_case_state(case_state, edits):
    """Phase 6: apply user corrections. User text always wins; provenance recorded."""
    out=dict(case_state); out["facts"]=[{"text":t,"provenance":"user-confirmed","verified":False} for t in edits.get("confirmed_facts",[])] or out.get("facts",[])
    for ev, upd in zip(out.get("timeline",[]), edits.get("timeline",[])):
        if isinstance(upd,dict): ev.update({k:v for k,v in upd.items() if k in ("date_text","event")}); ev["status"]="user-confirmed"
    statuses=edits.get("evidence_statuses",{})
    for issue in out.get("candidate_issues",[]):
        for item in issue.get("evidence_checklist",[]):
            if item["item"] in statuses and statuses[item["item"]] in ("available","missing","not_applicable","uncertain"): item["status"]=statuses[item["item"]]
    out["user_corrections_applied"]=True; return out
