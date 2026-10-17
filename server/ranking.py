"""Hybrid lexical ranking: BM25 + sentence-level evidence selection.
Scores are retrieval signals only — never outcome odds. The supporting
sentence returned is the exact source text relied on, not a paraphrase."""
import math, re
from .pipeline import terms, GENERIC
def _tok(text): return [w for w in re.findall(r"[a-z0-9]{3,}", (text or "").lower())]
def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or "").replace("\n", " ")) if len(s.strip()) > 25]
def bm25(query_terms, docs, k1=1.5, b=0.75):
    N=len(docs) or 1; dl=[len(d) for d in docs]; avg=sum(dl)/N or 1
    df={t: sum(1 for d in docs if t in d) for t in query_terms}
    out=[]
    for d in docs:
        tf={}
        for w in d: tf[w]=tf.get(w,0)+1
        s=0.0
        for t in query_terms:
            if t not in tf: continue
            idf=math.log(1+(N-df[t]+0.5)/(df[t]+0.5)); s+=idf*(tf[t]*(k1+1))/(tf[t]+k1*(1-b+b*len(d)/avg))
        out.append(s)
    return out
def best_sentence(query_terms, text):
    qt=set(query_terms)-GENERIC; best, hits = "", 0
    for s in sentences(text):
        h=len(qt & terms(s))
        if h>hits: best, hits = s, h
    return best[:600], hits
def hybrid_score(query_terms, source, bm25_score, max_bm25):
    title_hits=len((set(query_terms)-GENERIC) & terms(source.title))
    sent, sent_hits = best_sentence(query_terms, source.passage)
    norm = (bm25_score/max_bm25) if max_bm25>0 else 0.0
    return round(0.55*(sent_hits/3 if sent_hits<3 else 1.0) + 0.25*(1.0 if title_hits else 0.0) + 0.20*norm, 4), sent, sent_hits
