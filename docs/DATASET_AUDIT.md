# Dataset Audit — data/nyaysaathi_complete_dataset.json (656KB)
306 records (metadata claims 305): consumer 106, family/DV 110, property 90. All Indian jurisdiction.
## Field-by-field
Every record has: success_percentage (e.g. 75/85/95 cycling), lawyer_success_rate (0.49–0.95 sequential patterns), estimated_litigation_cost, time_estimate_months, evidence_strength, opponent_power, risk_level — **no methodology, no source per value; sequential/cycling distributions indicate synthetic generation**. Citations like "2021 HC 1", "2023 SCC (1) 456", generic courts ("High Court"×86) are unverifiable as stored; `source` is a bare label ("Indian Kanoon"). Cannot verify representative records from sandbox (no egress to Indian Kanoon); treat **all as unverified**.
## Decision
Quarantined: moved conceptually to dev-fixture only (file retained in repo for audit, **excluded from production retrieval**; server never loads it). Never present as precedent. UK production path = legislation.gov.uk (OGL) + Find Case Law (licence-gated) only.
