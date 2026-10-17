# Feature Inventory (retain/adapt/replace/remove)
|#|Feature|Old location|Status|UK rebuild|
|1|Entry/consent|index login|cosmetic|Adapt: UK privacy/consent, guest mode, separate lawyer-sharing consent|
|2|Intake chat|intake-page, sendMessage|scripted|Adapt: POST /api/case-state, editable structured state|
|3|Safety|—|absent|New: deterministic urgency signals, 999/Samaritans/Refuge signposting|
|4|Case state|AppState.caseData|static|Replace: typed CaseState schema, user-correctable|
|5|Timeline|summary tab|static|Adapt: date extraction, uncertainty preserved|
|6|Issue ID|—|hardcoded verdict|Replace: candidate issues w/ confidence+uncertainty|
|7|Legislation search|—|absent|New: /api/search/legislation (OGL)|
|8|Past cases|story/DemoData|fabricated|Replace: /api/search/caselaw (licence-gated, abstains)|
|9|Grounded explanation|ai-insights|canned|Replace: /api/explain verification gate|
|10|Story mode|story-mode|Indian, fixed|Adapt: fictional labelled, source-linked|
|11|Evidence checklist|documents|cosmetic|Adapt: checklist from issue map, user status|
|12|Fact-to-law|—|absent|New: in explain output (supporting/missing)|
|13|Risk|risk widget|fake %|Replace: sourced deadlines only, no win %|
|14|Case packet|case-summary|static|Adapt: /api/packet export (JSON/print)|
|15|Lawyer discovery|marketplace|fake profiles|**Replace: empty verified-directory state**|
|16|Handoff|connectWithLawyer|instant fake|Replace: explicit consent, status=pending only|
|17|Privacy/security|policies text|false claims|Replace: server-side keys, no narrative logs|
|18|Auditability|—|absent|New: content-free audit events (source ids, consent)|
|19|Error/degradation|toasts|partial|Adapt: provider-down states, no synthetic fallback|
|20|Admin/QC|analytics page|fake|**Remove user analytics**; internal audit log only|
