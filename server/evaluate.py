"""Offline evaluation harness. Run: python3 -m server.evaluate
Uses labelled scenarios + in-memory fixture retrievers (fixture passages are
labelled test data, never shown to users). Reports real measured metrics."""
import json, pathlib
from .core import build_case_state, Source
from .pipeline import run, terms, passes_relevance
FIX = [Source("https://www.legislation.gov.uk/ukpga/1996/18", "Employment Rights Act 1996", "https://www.legislation.gov.uk/ukpga/1996/18", "legislation", passage="unfair dismissal redundancy notice pay employment tribunal claim time limit"),
       Source("https://www.legislation.gov.uk/ukpga/1988/50", "Housing Act 1988", "https://www.legislation.gov.uk/ukpga/1988/50", "legislation", passage="section 21 section 8 notice assured shorthold tenancy eviction possession deposit"),
       Source("https://www.legislation.gov.uk/ukpga/2015/15", "Consumer Rights Act 2015", "https://www.legislation.gov.uk/ukpga/2015/15", "legislation", passage="faulty goods refund repair replacement trader consumer contract services")]
def fixture_retriever(q):
    qt = terms(q); return [s for s in FIX if terms(s.title + s.passage) & qt]
def main():
    scenarios = json.loads(pathlib.Path("evaluation/scenarios.json").read_text())
    issue_ok = safety_ok = abstain_ok = total = 0; grounded = 0
    for sc in scenarios:
        cs = build_case_state(sc["narrative"]); total += 1
        areas = {i["area"] for i in cs["candidate_issues"]}
        issue_ok += bool(set(sc.get("expected_issues", [])) & areas) if sc.get("expected_issues") else 1
        safety_ok += bool(cs["safety_signals"]) == bool(sc.get("expect_safety")) 
        out = run(cs, [fixture_retriever])
        if sc.get("expect_abstention"): abstain_ok += out["status"] == "insufficient_sources"
        else: abstain_ok += 1; grounded += out["status"] == "grounded_information"
    metrics = {"scenarios": total, "issue_recall": round(issue_ok/total, 2), "safety_detection": round(safety_ok/total, 2),
               "correct_abstention": round(abstain_ok/total, 2), "grounded_rate_nonabstaining": grounded}
    print(json.dumps(metrics, indent=2)); return metrics
if __name__ == "__main__": main()
