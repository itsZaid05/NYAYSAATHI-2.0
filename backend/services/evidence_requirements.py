"""Contextual suggestions, distinguished from legal document requirements and proof."""

import re
from backend.schemas import Evidence


def requirements_for_issues(issues, documents, language):
    items = []
    seen = set()
    for issue in issues:
        for suggestion in issue.evidence_needed:
            key = suggestion.strip().casefold()
            if not key or key in seen:
                continue
            seen.add(key)
            # This only identifies possible relevance. It never verifies sufficiency/authenticity.
            related = [
                d
                for d in documents
                if any(q in d.supports_fact_quotes for q in issue.fact_quotes)
            ]
            items.append(
                Evidence(
                    item=suggestion,
                    present=bool(related),
                    reason=(
                        "Possible supporting uploads: "
                        + ", ".join(d.filename for d in related)
                        + ". Content must be reviewed; this is not proof or a legal filing requirement."
                        if related
                        else "Suggested for this case issue: "
                        + issue.title
                        + ". No related upload has been established; this is not a mandatory legal-document finding."
                    ),
                )
            )
    return items[:16]
