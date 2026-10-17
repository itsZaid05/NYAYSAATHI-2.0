"""Accuracy pipeline: plan -> retrieve -> rank -> verify -> explain/abstain.

Design rules (docs/REBUILD_MASTER_PLAN.md):
- Only allow-listed official source URLs may ever be cited. Anything else is
  dropped BEFORE ranking, so a model/provider can never inject a citation.
- A source is only cited for a proposition if it passes a passage-relevance
  check (distinct query/issue terms present in title or passage).
- Similarity/relevance scores are retrieval signals, NEVER outcome odds.
- Zero verified sources => explicit abstention, zero legal propositions.
Retrievers are injectable callables(query)->list[Source] for offline tests.
"""
import re
from .core import Source

ALLOWED_HOSTS = ("https://www.legislation.gov.uk/", "https://caselaw.nationalarchives.gov.uk/")
STOP = set("the a an and or of to in for on my i was is are with from at by".split())
GENERIC = {"act","acts","rights","duties","legislation","law","legal","section"}  # never sufficient to ground a proposition

def terms(text):
    return {w for w in re.findall(r"[a-z0-9]{3,}", (text or "").lower()) if w not in STOP}

def plan_queries(case_state):
    """One primary + one statute-oriented query per candidate issue."""
    qs = []
    for issue in case_state.get("candidate_issues", []):
        area = issue.get("area", "")
        matched = " ".join(issue.get("matched_terms", [])[:3])
        qs.append({"issue": area, "query": f"{matched} {area}".strip(), "purpose": "provider search"})
        qs.append({"issue": area, "query": f"{area} act rights duties", "purpose": "legislation discovery"})
    if not qs and case_state.get("original_narrative"):
        qs.append({"issue": "general", "query": " ".join(sorted(terms(case_state["original_narrative"]))[:6]), "purpose": "fallback discovery"})
    return qs

def relevance(query_terms, source):
    t, p = terms(source.title), terms(source.passage)
    return 2 * len(query_terms & t) + len(query_terms & p)

def passes_relevance(query_terms, source):
    # Distinctive (non-generic) support: >=2 distinct terms overall, at least 1 in passage.
    qt = query_terms - GENERIC
    return len(qt & (terms(source.title) | terms(source.passage))) >= 2 and len(qt & terms(source.passage)) >= 1

def run(case_state, retrievers, top_k=5):
    """retrievers: list of callable(query)->list[Source]. Returns grounded output."""
    queries = plan_queries(case_state)
    seen, ranked, trace = {}, [], []
    for q in queries:
        qt = terms(q["query"]) | terms(q["issue"]) | terms(case_state.get("original_narrative",""))
        for retriever in retrievers:
            try:
                results = retriever(q["query"])
            except PermissionError as e:
                trace.append({"query": q["query"], "status": "provider_refused", "detail": str(e)[:160]}); continue
            except Exception as e:
                trace.append({"query": q["query"], "status": "provider_error", "detail": type(e).__name__}); continue
            for s in results:
                if not s.url.startswith(ALLOWED_HOSTS):
                    trace.append({"query": q["query"], "status": "dropped_untrusted_url", "detail": s.url[:80]}); continue
                if s.source_id in seen: continue
                seen[s.source_id] = s
                ranked.append({"source": s, "issue": q["issue"], "score": relevance(qt, s), "verified": passes_relevance(qt, s)})
            trace.append({"query": q["query"], "status": "ok", "n": len(results)})
    # Hybrid rerank over the full candidate pool (BM25 needs corpus stats)
    from .ranking import bm25, hybrid_score, _tok
    docs=[_tok(r["source"].title+" "+r["source"].passage) for r in ranked]
    all_terms=set()
    for q in queries: all_terms |= terms(q["query"]) | terms(case_state.get("original_narrative",""))
    scores=bm25(all_terms, docs) if docs else []; mx=max(scores) if scores else 0
    for r, sc in zip(ranked, scores):
        hs, sent, hits = hybrid_score(all_terms, r["source"], sc, mx)
        r["score"]=hs; r["supporting_sentence"]=sent; r["sentence_hits"]=hits
        r["verified"]=bool(r["verified"] and hits>=1)  # must have a quotable supporting sentence
    ranked.sort(key=lambda r: -r["score"])
    verified = [r for r in ranked if r["verified"]][:top_k]
    base = {"queries_planned": queries, "retrieval_trace": trace,
            "disclaimer": "General legal information for England and Wales, not legal advice. Whether a source applies to you depends on your confirmed facts; a qualified solicitor/adviser should review them."}
    if not verified:
        reason = "no_sources_returned" if not ranked else "sources_failed_relevance_check"
        return {**base, "status": "insufficient_sources", "abstention_reason": reason, "sources": [], "propositions": [],
                "explanation": "I could not verify sufficiently relevant official sources for your situation, so I will not summarise the law here. You have not been given substitute or invented cases. Try adding details (dates, letters received, who is involved), or speak to Citizens Advice or a qualified solicitor."}
    props, srcs = [], []
    for r in verified:
        s = r["source"]; srcs.append(s.to_dict())
        props.append({"proposition": f"Official source relevant to '{r['issue']}' — read it and compare its requirements with your confirmed facts before relying on it.",
                      "supporting_source_ids": [s.source_id], "passage": r.get("supporting_sentence") or s.passage[:500], "support_type": "exact_source_sentence" if r.get("supporting_sentence") else "provider_summary",
                      "retrieval_relevance": r["score"], "note": "Retrieval relevance only — not a prediction of any outcome."})
    return {**base, "status": "grounded_information", "sources": srcs, "propositions": props,
            "explanation": "Verified official sources were retrieved for your candidate issue(s) and are cited below with the passages that matched. Anything I could not verify has been left out rather than guessed.",
            "evidence_gaps": [c for i in case_state.get("candidate_issues", []) for c in i.get("evidence_checklist", [])],
            "next_questions": case_state.get("missing_information", [])}
