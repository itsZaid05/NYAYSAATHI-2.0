# Evaluation Report (offline, 2026-10-18)
Harness: `python3 -m server.evaluate` (evaluation/scenarios.json, fixture retriever — labelled test data only, never user-facing).
Results: scenarios=12, issue_recall=1.0, safety_detection=1.0, correct_abstention=1.0, grounded on 3/4 non-abstaining scenarios.
Found & fixed during evaluation: (1) generic words ("rights/act") falsely grounded irrelevant Acts → distinctive-term verification; (2) domestic-abuse phrasing missed family issue → expanded signals. 6/6 unit tests pass incl. fabricated-URL rejection and irrelevant-source abstention.
NOT measured yet (require live licence/host + labelled relevance judgments): Recall@k/nDCG on real corpora, citation-to-passage human review, solicitor-reviewed accuracy. Do not claim legal accuracy until those exist.
