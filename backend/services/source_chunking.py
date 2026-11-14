"""Review-candidate preparation, never automatic legal approval."""

import re


def section_candidates(text, max_chars=6000):
    # Collapse whitespace only after preserving statutory boundary positions.
    # No paraphrasing, deleted exceptions or generated legal text.
    starts = list(re.finditer(r"(?m)^\s*(\d{1,3})\.\s+(?=[A-Z])", text))
    results = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        original = text[match.start() : end].strip()
        if len(original) < 15:
            continue
        paragraphs = re.split(r"\n\s*\n", original)
        chunk = ""
        for paragraph in paragraphs:
            if chunk and len(chunk) + len(paragraph) > max_chars:
                results.append(
                    {
                        "provision_candidate": "Section " + match.group(1),
                        "exact_text": chunk.strip(),
                        "status": "pending_manual_review",
                    }
                )
                chunk = ""
            # Long indivisible clauses remain whole for a reviewer; never silently truncate law.
            chunk += paragraph + "\n\n"
        if chunk.strip():
            results.append(
                {
                    "provision_candidate": "Section " + match.group(1),
                    "exact_text": chunk.strip(),
                    "status": "pending_manual_review",
                }
            )
    return results
