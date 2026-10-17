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

def test_pipeline_rejects_fabricated_url_and_grounds_real():
    from server.core import Source, build_case_state
    from server.pipeline import run
    fake = Source("x","Made Up Act 2099","https://evil.example/act","legislation",passage="unfair dismissal employment")
    real = Source("https://www.legislation.gov.uk/ukpga/1996/18","Employment Rights Act 1996","https://www.legislation.gov.uk/ukpga/1996/18","legislation",passage="unfair dismissal claim employment tribunal notice")
    out = run(build_case_state("I was sacked, unfair dismissal, no notice"), [lambda q: [fake, real]])
    assert out["status"]=="grounded_information" and all(s["url"].startswith("https://www.legislation.gov.uk") for s in out["sources"])
def test_pipeline_abstains_on_irrelevant():
    from server.core import Source, build_case_state
    from server.pipeline import run
    src = Source("https://www.legislation.gov.uk/1","Fishing Act","https://www.legislation.gov.uk/1","legislation",passage="salmon rivers nets")
    out = run(build_case_state("I was sacked by my employer"), [lambda q: [src]])
    assert out["status"]=="insufficient_sources" and out["propositions"]==[]
