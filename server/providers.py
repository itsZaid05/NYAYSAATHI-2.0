"""Authorised source adapters. Legislation: OGL v3.0. Case law: licence-gated."""
import os, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET, datetime
from .core import Source
UA = {"User-Agent": "NyaySaathi/2.0 (legal-information research; contact via repo)"}
ATOM = "{http://www.w3.org/2005/Atom}"
def _get(url, timeout=12):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r: return r.read().decode("utf-8", "replace")
def _txt(html): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()

class LegislationProvider:
    name = "legislation.gov.uk"; licence = "Open Government Licence v3.0"
    attribution = "© Crown and database right. Derived from content available under the Open Government Licence v3.0 from legislation.gov.uk."
    def search(self, query, limit=5):
        url = "https://www.legislation.gov.uk/all/data.feed?" + urllib.parse.urlencode({"text": query, "results-count": limit})
        root = ET.fromstring(_get(url)); out = []
        for e in root.findall(f"{ATOM}entry")[:limit]:
            link = next((l.get("href") for l in e.findall(f"{ATOM}link") if l.get("rel") == "alternate"), "")
            out.append(Source(source_id=link or e.findtext(f"{ATOM}id", ""), title=_txt(e.findtext(f"{ATOM}title", "")),
                url=link, kind="legislation", court_or_body="legislation.gov.uk",
                date=(e.findtext(f"{ATOM}published", "") or "")[:10], passage=_txt(e.findtext(f"{ATOM}summary", ""))[:600],
                retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), licence=self.licence))
        return out

class CaseLawProvider:
    name = "Find Case Law — The National Archives"
    licence = "Open Justice Licence v2.0 (computational analysis excluded without separate licence)"
    def enabled(self):
        return os.getenv("CASELAW_LIVE_ENABLED") == "true" and os.getenv("CASELAW_COMPUTATIONAL_LICENCE_CONFIRMED") == "true"
    def search(self, query, limit=5):
        if not self.enabled():
            raise PermissionError("Find Case Law live retrieval is disabled: computational-analysis licence not confirmed (see docs/UK_LEGAL_DATA_RESEARCH.md). No substitute or synthetic cases are provided.")
        url = "https://caselaw.nationalarchives.gov.uk/judgments/search/data.xml?" + urllib.parse.urlencode({"query": query, "per_page": limit})
        root = ET.fromstring(_get(url)); out = []
        for e in root.findall(f"{ATOM}entry")[:limit]:
            link = next((l.get("href") for l in e.findall(f"{ATOM}link") if l.get("rel") == "alternate"), "")
            out.append(Source(source_id=link or e.findtext(f"{ATOM}id", ""), title=_txt(e.findtext(f"{ATOM}title", "")),
                url=link, kind="judgment", date=(e.findtext(f"{ATOM}published", "") or "")[:10],
                passage=_txt(e.findtext(f"{ATOM}summary", ""))[:600],
                retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), licence=self.licence))
        return out
