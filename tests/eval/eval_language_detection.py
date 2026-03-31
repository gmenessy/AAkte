"""Evaluation suite for language detection quality.

Measures precision and recall of the heuristic language detector
against a curated test corpus. This is not a pass/fail test but
a quality benchmark that reports metrics.
"""

import pytest

from backend.app.services.ingestion_service import _detect_language

# Curated test corpus: (text, expected_language)
GERMAN_CORPUS = [
    ("Der Vertrag wurde am 15. Maerz 2024 unterzeichnet.", "de"),
    ("Die Geschaeftsfuehrung hat beschlossen, die Investition fortzusetzen.", "de"),
    ("Auf Grundlage der vorliegenden Analyse empfehlen wir folgende Massnahmen.", "de"),
    ("Das Unternehmen ist verpflichtet, die Datenschutzverordnung einzuhalten.", "de"),
    ("Im Folgenden werden die wesentlichen Ergebnisse zusammengefasst.", "de"),
    ("Die Parteien vereinbaren, dass saemtliche Streitigkeiten vor dem Landgericht verhandelt werden.", "de"),
    ("Gemaess Paragraph 12 Absatz 3 des Gesellschaftsvertrags ist die Zustimmung erforderlich.", "de"),
    ("Der Jahresabschluss wurde durch den Wirtschaftspruefer testiert.", "de"),
    ("Hiermit wird die ordnungsgemaesse Durchfuehrung der Massnahme bestaetigt.", "de"),
    ("Die Kuendigungsfrist betraegt drei Monate zum Quartalsende.", "de"),
]

ENGLISH_CORPUS = [
    ("The annual report has been reviewed and approved by the board.", "en"),
    ("All contractual obligations shall be fulfilled within 30 days.", "en"),
    ("This agreement supersedes all prior negotiations and representations.", "en"),
    ("The company reported strong revenue growth in Q4 of fiscal year 2024.", "en"),
    ("Risk mitigation strategies should be implemented before the end of March.", "en"),
    ("The board of directors has unanimously approved the merger proposal.", "en"),
    ("Intellectual property rights remain with the original creator.", "en"),
    ("Performance metrics indicate a significant improvement year over year.", "en"),
    ("The arbitration clause requires disputes to be settled in London.", "en"),
    ("Quarterly financial statements must be submitted by the fifteenth of each month.", "en"),
]

MIXED_CORPUS = [
    ("Meeting Notes: Der CEO hat die neue Strategie vorgestellt.", "de"),
    ("Summary: Die Ergebnisse der Analyse sind positiv.", "de"),
    ("Note: This document is confidential and proprietary.", "en"),
    ("Warning: Unauthorized access is strictly prohibited.", "en"),
]

ALL_SAMPLES = GERMAN_CORPUS + ENGLISH_CORPUS + MIXED_CORPUS


@pytest.mark.eval
class EvalLanguageDetection:
    """Evaluation metrics for language detection."""

    def eval_german_corpus_accuracy(self):
        """Measure accuracy on German-language texts."""
        correct = sum(1 for text, expected in GERMAN_CORPUS if _detect_language(text) == expected)
        accuracy = correct / len(GERMAN_CORPUS)
        print(f"\n  German accuracy: {correct}/{len(GERMAN_CORPUS)} = {accuracy:.0%}")
        assert accuracy >= 0.8, f"German accuracy {accuracy:.0%} below 80% threshold"

    def eval_english_corpus_accuracy(self):
        """Measure accuracy on English-language texts."""
        correct = sum(1 for text, expected in ENGLISH_CORPUS if _detect_language(text) == expected)
        accuracy = correct / len(ENGLISH_CORPUS)
        print(f"\n  English accuracy: {correct}/{len(ENGLISH_CORPUS)} = {accuracy:.0%}")
        assert accuracy >= 0.8, f"English accuracy {accuracy:.0%} below 80% threshold"

    def eval_mixed_corpus_accuracy(self):
        """Measure accuracy on mixed-language texts."""
        correct = sum(1 for text, expected in MIXED_CORPUS if _detect_language(text) == expected)
        accuracy = correct / len(MIXED_CORPUS)
        print(f"\n  Mixed accuracy: {correct}/{len(MIXED_CORPUS)} = {accuracy:.0%}")
        # Lower threshold for mixed content
        assert accuracy >= 0.5, f"Mixed accuracy {accuracy:.0%} below 50% threshold"

    def eval_overall_accuracy(self):
        """Report overall accuracy across all samples."""
        correct = sum(1 for text, expected in ALL_SAMPLES if _detect_language(text) == expected)
        accuracy = correct / len(ALL_SAMPLES)
        print(f"\n  Overall accuracy: {correct}/{len(ALL_SAMPLES)} = {accuracy:.0%}")
        assert accuracy >= 0.75, f"Overall accuracy {accuracy:.0%} below 75% threshold"

    def eval_detailed_report(self):
        """Print detailed per-sample results for debugging."""
        errors = []
        for text, expected in ALL_SAMPLES:
            detected = _detect_language(text)
            if detected != expected:
                errors.append((text[:60], expected, detected))

        print(f"\n  Total errors: {len(errors)}/{len(ALL_SAMPLES)}")
        for snippet, expected, detected in errors:
            print(f"    MISS: expected={expected} got={detected} | \"{snippet}...\"")

        # This test always passes — it's a diagnostic report
        assert True
