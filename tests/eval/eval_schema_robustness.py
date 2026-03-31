"""Evaluation suite for schema validation robustness.

Tests the schema layer against edge cases, fuzzy inputs,
and adversarial payloads to verify hardening.
"""

import pytest
from pydantic import ValidationError

from backend.app.models.schemas import DocumentIngestRequest, IngestMetrics


def _make(filename="test.pdf", markdown="content", **metric_overrides):
    """Shorthand to build a request with metric overrides."""
    metrics = {
        "original_paragraphs": 10,
        "removed_boilerplate": 2,
        "textrank_retained": 6,
        "simhash_removed": 1,
        **metric_overrides,
    }
    return DocumentIngestRequest(
        filename=filename,
        raw_markdown=markdown,
        metrics=IngestMetrics(**metrics),
    )


@pytest.mark.eval
class EvalSchemaRobustness:
    """Stress-test input validation."""

    def eval_very_long_markdown(self):
        """Accept large but within-limit markdown."""
        text = "x" * 1_999_999  # Just under 2M limit
        req = _make(markdown=text)
        assert len(req.raw_markdown) == 1_999_999

    def eval_markdown_at_limit_rejected(self):
        """Reject markdown exceeding the 2M character limit."""
        text = "x" * 2_000_001
        with pytest.raises(ValidationError):
            _make(markdown=text)

    def eval_special_chars_in_filename(self):
        """Accept filenames with special but safe characters."""
        for name in [
            "report (final).pdf",
            "2024-Q4_report.pdf",
            "Geschaeftsbericht 2024.pdf",
        ]:
            req = _make(filename=name)
            assert req.filename == name

    def eval_null_byte_in_filename(self):
        """Null bytes should not corrupt filename processing."""
        req = _make(filename="test\x00.pdf")
        # Should at minimum not crash; the null byte stays since
        # it doesn't trigger path traversal
        assert req.filename is not None

    def eval_extreme_metric_values(self):
        """Accept very large metric values."""
        req = _make(
            original_paragraphs=999_999,
            removed_boilerplate=500_000,
            textrank_retained=400_000,
            simhash_removed=99_999,
            original_chars=100_000_000,
            reduced_chars=30_000_000,
            reduction_ratio=0.7,
        )
        assert req.metrics.original_paragraphs == 999_999

    def eval_zero_metrics(self):
        """Accept all-zero metrics (edge case for empty documents)."""
        req = _make(
            original_paragraphs=0,
            removed_boilerplate=0,
            textrank_retained=0,
            simhash_removed=0,
            original_chars=0,
            reduced_chars=0,
            reduction_ratio=0.0,
        )
        assert req.metrics.reduction_ratio == 0.0

    def eval_boundary_reduction_ratio(self):
        """Accept exact boundary values 0.0 and 1.0."""
        req_zero = _make(reduction_ratio=0.0)
        assert req_zero.metrics.reduction_ratio == 0.0

        req_one = _make(reduction_ratio=1.0)
        assert req_one.metrics.reduction_ratio == 1.0

    def eval_sql_injection_in_filename(self):
        """SQL injection attempts should be harmless strings."""
        req = _make(filename="'; DROP TABLE documents; --.pdf")
        assert "DROP" in req.filename  # It's just a string, no SQL execution

    def eval_html_injection_in_markdown(self):
        """HTML/script injection in markdown should be stored as-is."""
        payload = '<script>alert("xss")</script>'
        req = _make(markdown=payload)
        assert req.raw_markdown == payload  # Stored raw, frontend must escape

    def eval_metrics_type_coercion(self):
        """Pydantic should coerce string numbers to int."""
        metrics = IngestMetrics(
            original_paragraphs="10",
            removed_boilerplate="2",
            textrank_retained="6",
            simhash_removed="1",
        )
        assert metrics.original_paragraphs == 10
        assert isinstance(metrics.original_paragraphs, int)
