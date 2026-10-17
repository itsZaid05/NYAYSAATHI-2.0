"""Stdlib HTTP server: static UI + JSON API. Secrets server-side only; narratives never logged."""
import json, os, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from .core import build_case_state, verify_and_explain, audit_event
from .providers import LegislationProvider, CaseLawProvider
from .pipeline import run as pipeline_run
ROOT = Path(__file__).parent.parent
AUDIT, HANDOFFS = [], []
LEG, CASE = LegislationProvider(), CaseLawProvider()

def ranking(query, sources):  # transparent lexical relevance over provider results
    terms = set(query.lower().split())
    return sorted(sources, key=lambda s: -sum(t in (s.title + s.passage).lower() for t in terms))

class H(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass  # no request-path logging of user content
    def _json(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _body(self):
        try: return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except Exception: return {}
    def do_GET(self):
        p = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(p.query)
        if p.path == "/api/health": return self._json({"status": "ok", "jurisdiction": "England and Wales", "legislation": "enabled (OGL v3.0)", "caselaw_live": CASE.enabled()})
        if p.path == "/api/search/legislation":
            try:
                src = ranking(q.get("q", [""])[0], LEG.search(q.get("q", [""])[0]))
                AUDIT.append(audit_event("legislation_search", {"n": len(src)})); return self._json({"sources": [s.to_dict() for s in src], "attribution": LEG.attribution})
            except Exception as e: return self._json({"error": "Legislation service unavailable. Your work is saved in this browser; please retry.", "detail": type(e).__name__}, 502)
        if p.path == "/api/search/caselaw":
            try:
                src = CASE.search(q.get("q", [""])[0]); return self._json({"sources": [s.to_dict() for s in src]})
            except PermissionError as e: return self._json({"error": str(e), "sources": []}, 403)
            except Exception as e: return self._json({"error": "Case law service unavailable; no substitute cases shown.", "sources": []}, 502)
        if p.path == "/api/lawyers": return self._json({"lawyers": [], "notice": "No verified lawyer directory is connected yet. We will not show invented profiles. You can find regulated solicitors via the Law Society 'Find a Solicitor' service or a local Citizens Advice."})
        if p.path == "/api/audit": return self._json({"events": AUDIT[-50:]})  # content-free
        return super().do_GET()
    def do_POST(self):
        p = urllib.parse.urlparse(self.path); b = self._body()
        if p.path == "/api/case-state":
            if not str(b.get("narrative", "")).strip(): return self._json({"error": "Please describe your situation first."}, 400)
            return self._json(build_case_state(str(b["narrative"]), str(b.get("category", ""))))
        if p.path == "/api/explain":
            cs = b.get("case_state", {})
            out = pipeline_run(cs, [LEG.search, CASE.search])  # case law traces provider_refused until licence granted
            AUDIT.append(audit_event("explain", {"status": out["status"], "n_sources": len(out.get("sources", []))}))
            return self._json(out)
        if p.path == "/api/packet":
            cs = b.get("case_state", {}); return self._json({"packet": {"summary": "Lawyer-ready case preparation pack (not a court filing)", "facts_user_stated": cs.get("facts", []), "timeline": cs.get("timeline", []), "candidate_issues": cs.get("candidate_issues", []), "missing_information": cs.get("missing_information", []), "sources": b.get("sources", []), "questions_for_lawyer": cs.get("missing_information", [])}})
        if p.path == "/api/handoff":
            if b.get("consent") is not True: return self._json({"error": "Explicit consent is required before anything is shared. Nothing has been sent."}, 400)
            h = {"id": f"H-{len(HANDOFFS)+1}", "status": "pending — no lawyer has accepted this yet", "lawyer_id": b.get("lawyer_id", "")}
            HANDOFFS.append(h); AUDIT.append(audit_event("handoff_consent", {"id": h["id"]})); return self._json(h)
        return self._json({"error": "not found"}, 404)

def main():
    os.chdir(ROOT); ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8000"))), H).serve_forever()
if __name__ == "__main__": main()
