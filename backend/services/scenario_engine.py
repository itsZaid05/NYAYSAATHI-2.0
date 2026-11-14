import json
import re
from backend.config import ROOT
from backend.schemas import Scenario


class ScenarioEngine:
    def select(self, text, category, language, sources, k=2):
        rows = json.loads((ROOT / "knowledge/scenarios/consumer.json").read_text())
        tokens = set(re.findall(r"\w+", text.casefold()))

        def score(row):
            words = set(
                re.findall(
                    r"\w+",
                    (
                        row["en"] + " " + row["hi"] + " " + " ".join(row["tags"])
                    ).casefold(),
                )
            )
            return len(tokens & words) + (5 if row["category"] == category else 0)

        ranked = sorted(rows, key=score, reverse=True)[:k]
        return [
            Scenario(
                id=r["id"],
                title=r["title_hi"] if language == "hi" else r["title"],
                category=r["category"],
                text=r[language],
                lessons=r["lessons_hi"] if language == "hi" else r["lessons"],
                source_ids=[
                    s.id
                    for s in sources
                    if any(
                        tag in (s.title + " " + s.provision + " " + s.quote).lower()
                        for tag in r["legal_terms"]
                    )
                ][:3],
                similarities="Selected because the problem category or described goods/service overlaps; this is an educational analogy."
                if language == "en"
                else "समस्या या वस्तु/सेवा की समानता के कारण चुना गया शैक्षिक उदाहरण।",
                differences="The people, transaction and events in this story are fictional. Your evidence and unresolved facts must be considered separately."
                if language == "en"
                else "कहानी के व्यक्ति, लेनदेन और घटनाएं काल्पनिक हैं। आपके साक्ष्य और अधूरे तथ्य अलग हैं।",
            )
            for r in ranked
        ]
