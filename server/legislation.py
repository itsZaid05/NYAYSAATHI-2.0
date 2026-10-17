"""Phase 3: provision-level legislation retrieval (CLML) with version honesty.
Only legislation.gov.uk URLs. In-memory TTL cache; OGL v3.0 attribution."""
import re, time, urllib.request, xml.etree.ElementTree as ET
UA={"User-Agent":"NyaySaathi/2.0 (legal-information; OGL reuse)"}
CACHE={}; TTL=3600
def _fetch(url):
    if not url.startswith("https://www.legislation.gov.uk/"): raise ValueError("untrusted legislation URL")
    if url in CACHE and time.time()-CACHE[url][0]<TTL: return CACHE[url][1]
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=15) as r: raw=r.read().decode("utf-8","replace")
    CACHE[url]=(time.time(),raw); return raw
def _local(tag): return tag.rsplit('}',1)[-1]
def parse_clml(xml_text, query=""):
    """Extract title, version dates (only if present), and best-matching provisions."""
    root=ET.fromstring(xml_text); title=""; dates={}
    provisions=[]; current={"heading":"","text":""}
    def flush():
        if current["text"].strip(): provisions.append({"heading":current["heading"],"text":re.sub(r"\s+"," ",current["text"]).strip()[:1200]})
    for el in root.iter():
        tag=_local(el.tag)
        if tag=="Title" and not title and el.text: title=el.text.strip()
        if tag in ("Enacted","Made","ComingIntoForce") and el.get("Date"): dates[tag]=el.get("Date")
        if tag in ("P1","P2","Section","Article"):
            flush(); current={"heading":"","text":""}
        if tag=="Title" and provisions is not None and el.text and current is not None:
            if not current["heading"] and len(provisions)>=0 and (el.text or "").strip(): current["heading"]=el.text.strip()[:160]
        if el.text and _local(el.tag) in ("Text","P","Para","Word"): current["text"]+=" "+el.text
    flush()
    qt={w for w in re.findall(r"[a-z0-9]{3,}",query.lower())}
    def score(p): return sum(w in (p["heading"]+" "+p["text"]).lower() for w in qt)
    provisions.sort(key=score,reverse=True)
    return {"title":title,"version_dates_reported_by_source":dates,
            "version_label":"latest version served by legislation.gov.uk" ,
            "in_force_claim": None,  # never asserted unless source metadata proves it
            "provisions":provisions[:5],
            "attribution":"© Crown and database right. Derived from content available under the Open Government Licence v3.0 from legislation.gov.uk."}
def fetch_provisions(url, query=""):
    if "/data.xml" not in url: url=url.rstrip("/")+"/data.xml"
    return parse_clml(_fetch(url),query)
