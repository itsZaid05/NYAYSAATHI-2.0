import sys; sys.path.insert(0, ".")
from server.core import build_case_state, verify_and_explain
from server.providers import CaseLawProvider
def test_safety_and_issues():
    cs = build_case_state("I was sacked on 3 March 2025 and I am in danger at home")
    assert cs["safety_signals"] and any(i["area"]=="employment" for i in cs["candidate_issues"]) and cs["timeline"]
def test_abstains_without_sources():
    out = verify_and_explain({}, []); assert out["status"]=="insufficient_sources" and out["propositions"]==[]
def test_caselaw_gated_by_default():
    try: CaseLawProvider().search("test"); assert False
    except PermissionError: pass
def test_no_win_probability():
    import json; assert "success_percentage" not in json.dumps(build_case_state("landlord eviction"))
