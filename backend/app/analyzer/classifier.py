from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from backend.app.models import ErrorGroup


class RuleSet:
    def __init__(self, rules_path: Path | None = None) -> None:
        self.rules_path = rules_path or Path(__file__).resolve().parents[1] / "rules" / "rules.yaml"
        self.rules = self._load_rules()

    def _load_rules(self) -> list[dict[str, Any]]:
        with self.rules_path.open("r", encoding="utf-8") as file:
            payload = yaml.safe_load(file) or {}
        rules = payload.get("rules", [])
        if not isinstance(rules, list):
            raise ValueError("rules.yaml must contain a list under the 'rules' key.")
        return rules

    def match(self, pattern: str) -> dict[str, Any] | None:
        for rule in self.rules:
            rule_pattern = str(rule.get("pattern", ""))
            if rule_pattern and re.search(rule_pattern, pattern, re.IGNORECASE):
                return rule
        return None


class ErrorClassifier:
    def __init__(self, ruleset: RuleSet | None = None) -> None:
        self.ruleset = ruleset or RuleSet()

    def classify(self, groups: list[ErrorGroup]) -> list[ErrorGroup]:
        classified: list[ErrorGroup] = []
        for group in groups:
            rule = self.ruleset.match(group.pattern)
            classification = str(rule.get("classification", "UNKNOWN")) if rule else "UNKNOWN"
            classified.append(group.model_copy(update={"classification": classification}))
        return classified
