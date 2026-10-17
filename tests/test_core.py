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

def test_clml_provisions_ranked_and_no_inforce_claim():
    import pathlib
    from server.legislation import parse_clml
    out=parse_clml(pathlib.Path("tests/fixtures/sample_clml.xml").read_text(),"unfair dismissal time limit claim")
    assert out["title"] and out["in_force_claim"] is None and "time limits" in out["provisions"][0]["heading"].lower() or "unfair" in out["provisions"][0]["heading"].lower()
def test_confirm_case_state_user_wins():
    from server.core import build_case_state, confirm_case_state
    cs=build_case_state("landlord eviction section 21")
    out=confirm_case_state(cs,{"confirmed_facts":["Landlord served notice on 3 March"],"evidence_statuses":{"tenancy agreement":"available"}})
    assert out["facts"][0]["provenance"]=="user-confirmed" and out["candidate_issues"][0]["evidence_checklist"][0]["status"]=="available"
def test_llm_polish_rejects_new_citation_and_probability():
    from server.llm import polish
    v={"propositions":[{"supporting_source_ids":["https://www.legislation.gov.uk/1"],"proposition":"x"}]}
    assert "explanation_polished" not in polish(v, client=lambda p:"You have a 90% chance of winning [https://fake.example]")
    assert polish(v, client=lambda p:"See the cited source. [https://www.legislation.gov.uk/1]")["generation"].startswith("llm-polished")

def test_gemini_parse_and_minimisation():
    import json
    from server.gemini import parse_response, gemini_client
    assert parse_response({"candidates":[{"content":{"parts":[{"text":"Hello "},{"text":"world"}]}}]})=="Hello world"
    assert parse_response({})==""
    import inspect; src=inspect.getsource(gemini_client)
    assert "propositions_json" in src and "original_narrative" not in src  # narrative never sent

def test_sentence_level_grounding():
    from server.core import Source, build_case_state
    from server.pipeline import run
    real = Source("https://www.legislation.gov.uk/ukpga/1996/18","Employment Rights Act 1996","https://www.legislation.gov.uk/ukpga/1996/18","legislation",
                  passage="Catering rules govern salmon fishing licences. An employee has the right not to be unfairly dismissed by their employer. Tea breaks are customary in offices.")
    out = run(build_case_state("I was sacked, unfair dismissal by my employer"), [lambda q: [real]])
    assert out["status"]=="grounded_information" and "unfairly dismissed" in out["propositions"][0]["passage"]
    assert out["propositions"][0]["support_type"]=="exact_source_sentence"
def test_ranking_prefers_relevant_source():
    from server.core import Source, build_case_state
    from server.pipeline import run
    good = Source("https://www.legislation.gov.uk/a","Housing Act 1988","https://www.legislation.gov.uk/a","legislation",passage="A landlord must follow the section 21 notice procedure for an assured shorthold tenancy eviction.")
    bad = Source("https://www.legislation.gov.uk/b","Fisheries Act","https://www.legislation.gov.uk/b","legislation",passage="Salmon fishing licences and river nets are regulated annually in Scotland.")
    out = run(build_case_state("landlord eviction section 21 tenancy notice"), [lambda q: [bad, good]])
    assert out["sources"][0]["source_id"].endswith("/a")

def test_story_and_packet_only_from_verified():
    from server.story import build_story, build_packet
    assert build_story({"status":"insufficient_sources"})["status"]=="unavailable"
    st=build_story({"status":"grounded_information","propositions":[{"supporting_source_ids":["https://www.legislation.gov.uk/1"],"passage":"Exact sentence."}]})
    assert "Fictional" in st["label"] and st["steps"][0]["source_passage"]=="Exact sentence."
    pk=build_packet({"facts":[{"text":"f","provenance":"user-confirmed"}]},{"status":"insufficient_sources","sources":[{"x":1}]})
    assert pk["verified_sources"]==[]  # unverified sources never enter the packet
