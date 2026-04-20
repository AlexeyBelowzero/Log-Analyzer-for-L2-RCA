from __future__ import annotations

from collections import Counter

from backend.app.analyzer.classifier import ErrorClassifier, RuleSet
from backend.app.analyzer.deduplicator import ErrorDeduplicator
from backend.app.analyzer.insights import InsightGenerator
from backend.app.analyzer.normalizer import LogNormalizer
from backend.app.analyzer.parser import LogParser
from backend.app.models import AnalysisSummary, AnalyzeResponse


class LogAnalyzer:
    def __init__(self) -> None:
        ruleset = RuleSet()
        self.parser = LogParser()
        self.normalizer = LogNormalizer()
        self.deduplicator = ErrorDeduplicator()
        self.classifier = ErrorClassifier(ruleset)
        self.insights = InsightGenerator(ruleset)

    def analyze(self, text: str, source_type: str = "auto", max_groups: int = 10) -> AnalyzeResponse:
        total_lines = len([line for line in text.splitlines() if line.strip()])
        entries = self.parser.parse(text, source_type=source_type)
        normalized_entries = self.normalizer.normalize(entries)
        error_entries = self.normalizer.extract_error_entries(normalized_entries)
        groups = self.deduplicator.group(error_entries)
        classified_groups = self.classifier.classify(groups)
        insights = self.insights.generate(classified_groups)

        total_errors = sum(group.count for group in classified_groups)
        dominant = classified_groups[0] if classified_groups else None
        dominant_percentage = round((dominant.count / total_errors * 100), 1) if dominant and total_errors else 0

        summary = AnalysisSummary(
            total_lines=total_lines,
            parsed_lines=len(entries),
            error_events=total_errors,
            unique_patterns=len(classified_groups),
            dominant_issue=dominant.pattern if dominant else None,
            dominant_percentage=dominant_percentage,
            source_types=dict(Counter(entry.source_type for entry in entries)),
        )
        return AnalyzeResponse(
            summary=summary,
            groups=classified_groups[:max_groups],
            insights=insights,
        )
