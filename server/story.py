"""Phase 7: story-mode + lawyer packet, built ONLY from verified propositions.
Story characters are fictional and labelled; no proposition enters either
output unless it survived the pipeline verification gate."""
def build_story(explain_output):
    if explain_output.get("status") != "grounded_information":
        return {"status": "unavailable", "reason": "No verified sources, so no story will be generated rather than inventing one."}
    steps = []
    for p in explain_output["propositions"]:
        steps.append({"fictional_step": f"A fictional person, 'Alex', reads the official source below and compares its wording with their own documents before deciding anything.",
                      "source_id": p["supporting_source_ids"][0], "source_passage": p["passage"]})
    return {"status": "ok", "label": "Fictional educational story — not a real case, not your outcome",
            "steps": steps, "closing": "Alex's story teaches how to read the source; it does not predict what will happen in your situation."}
def build_packet(case_state, explain_output):
    verified = explain_output.get("status") == "grounded_information"
    return {"title": "Case preparation pack — not a court filing, not legal advice",
            "user_confirmed_facts": [f for f in case_state.get("facts", []) if f.get("provenance") == "user-confirmed"] or case_state.get("facts", []),
            "timeline_unverified_unless_confirmed": case_state.get("timeline", []),
            "candidate_issues_not_conclusions": case_state.get("candidate_issues", []),
            "verified_sources": explain_output.get("sources", []) if verified else [],
            "propositions": explain_output.get("propositions", []) if verified else [],
            "evidence_gaps": explain_output.get("evidence_gaps", []),
            "questions_for_lawyer": case_state.get("missing_information", []),
            "review_status": "Requires review by a qualified solicitor/adviser before reliance"}
