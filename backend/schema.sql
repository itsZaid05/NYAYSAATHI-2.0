PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES (1);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, role TEXT NOT NULL CHECK(role IN ('guest','lawyer')),
 expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, created_at REAL NOT NULL,
 updated_at REAL NOT NULL, expires_at REAL NOT NULL, state TEXT NOT NULL,
 FOREIGN KEY(owner) REFERENCES sessions(token_hash) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS evidence (
 id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
 filename TEXT NOT NULL, kind TEXT NOT NULL, mime TEXT NOT NULL,
 content BLOB NOT NULL, excerpt TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
 actor TEXT NOT NULL, action TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS handoffs (
 case_id TEXT PRIMARY KEY REFERENCES cases(id) ON DELETE CASCADE,
 packet BLOB NOT NULL, created_at REAL NOT NULL, reviewed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS download_tokens (
 token_hash TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
 owner TEXT NOT NULL, expires_at REAL NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(source_id UNINDEXED, text);
CREATE TABLE IF NOT EXISTS embeddings (
 source_id TEXT NOT NULL, model TEXT NOT NULL, content_hash TEXT NOT NULL,
 vector TEXT NOT NULL, PRIMARY KEY(source_id,model)
);
CREATE TABLE IF NOT EXISTS narratives (
 case_id TEXT PRIMARY KEY REFERENCES cases(id) ON DELETE CASCADE,
 text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS login_attempts (actor TEXT NOT NULL, at REAL NOT NULL);
-- Version 2 is additive: canonical intelligence/history remains in validated case JSON.
INSERT OR IGNORE INTO schema_version VALUES (2);
CREATE TABLE IF NOT EXISTS request_budget (
 actor TEXT NOT NULL REFERENCES sessions(token_hash) ON DELETE CASCADE,
 bucket TEXT NOT NULL, at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS request_budget_actor ON request_budget(actor,bucket,at);
