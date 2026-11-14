"""Decompose multi-issue research without inventing or approving legal authority."""


def retrieve_for_issues(provider, narrative, issues, *, semantic, event_date=None, k=8):
    if not issues:
        return provider.search(
            narrative, k=min(k, 6), semantic=semantic, event_date=event_date
        )
    candidates = {}
    ranks = {}
    modes = []
    # Bounded calls and per-issue diversity keep one verbose allegation from hiding the others.
    for issue in issues[:6]:
        query = (
            " ".join([issue.title] + issue.research_terms)
            + "\n"
            + "\n".join(issue.fact_quotes)
        )
        found, mode = provider.search(
            query, k=4, semantic=semantic, event_date=event_date
        )
        modes.append(mode)
        for rank, source in enumerate(found):
            candidates[source.id] = source
            ranks[source.id] = ranks.get(source.id, 0) + 1 / (60 + rank + 1)
    selected = [
        candidates[sid] for sid in sorted(ranks, key=ranks.get, reverse=True)[:k]
    ]
    modes = list(dict.fromkeys(modes))
    mode = (
        "; ".join(modes)
        + "; multi-issue research over "
        + str(min(len(issues), 6))
        + " issues"
    )
    return selected, mode
