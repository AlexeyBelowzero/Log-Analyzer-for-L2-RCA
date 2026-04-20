from __future__ import annotations

from backend.app.analyzer.classifier import RuleSet
from backend.app.models import ErrorGroup, Insight


class InsightGenerator:
    def __init__(self, ruleset: RuleSet | None = None) -> None:
        self.ruleset = ruleset or RuleSet()

    def generate(self, groups: list[ErrorGroup]) -> list[Insight]:
        insights: list[Insight] = []
        seen: set[str] = set()
        for group in groups:
            rule = self.ruleset.match(group.pattern)
            if not rule:
                continue
            classification = str(rule.get("classification", "UNKNOWN"))
            if classification in seen:
                continue
            seen.add(classification)
            title = str(rule.get("insight") or rule.get("name") or f"{classification} detected")
            insights.append(
                Insight(
                    title=title,
                    classification=classification,
                    possible_causes=[str(item) for item in rule.get("possible_causes", [])],
                    recommended_actions=[str(item) for item in rule.get("actions", [])],
                )
            )
        return insights
