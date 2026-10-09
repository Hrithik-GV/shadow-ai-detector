from datetime import datetime, timezone
import pytest

from app.services.ai_detector import AIDetector, AIDetectionResult
from app.services.evaluation_service import (
    EvaluationRecord,
    EvaluationService,
    default_evaluation_service,
)


def test_ground_truth_benchmark_dataset_loads_and_evaluates():
    """Verify default ground-truth dataset loads correctly and yields reproducible metrics."""
    service = default_evaluation_service
    dataset_name, version, records = service.load_ground_truth_dataset()

    assert dataset_name == "shadow_ai_ground_truth_benchmark_v1"
    assert version == "1.0.0"
    assert len(records) == 20

    res = service.run_ground_truth_evaluation()
    assert res.dataset_size == 20
    assert res.true_positives == 10
    assert res.true_negatives == 10
    assert res.false_positives == 0
    assert res.false_negatives == 0
    assert res.precision == 1.0
    assert res.recall == 1.0
    assert res.false_positive_rate == 0.0
    assert res.provider_accuracy == 1.0
    assert res.detection_accuracy == 1.0
    assert res.is_illustrative is False
    assert len(res.categories_breakdown) >= 4


def test_evaluation_empty_dataset_zero_denominators():
    """Empty dataset returns None for all metric ratios and handles zero denominators safely."""
    service = EvaluationService()
    res = service.evaluate_records(records=[])

    assert res.dataset_size == 0
    assert res.true_positives == 0
    assert res.false_positives == 0
    assert res.true_negatives == 0
    assert res.false_negatives == 0
    assert res.precision is None
    assert res.recall is None
    assert res.false_positive_rate is None
    assert res.provider_accuracy is None
    assert res.detection_accuracy is None
    assert "empty" in res.notes.lower()


def test_evaluation_imperfect_dataset():
    """Verify mathematical calculation on dataset with intentional false positives and false negatives."""
    # Custom mock detector
    class MockDetector:
        def classify_target(self, domain: str) -> AIDetectionResult:
            if domain == "real-ai.com":
                return AIDetectionResult(is_ai=True, is_uncertain=False, provider="OpenAI", confidence=0.99)
            elif domain == "missed-ai.com":
                # False negative: actual AI classified as non-AI
                return AIDetectionResult(is_ai=False, is_uncertain=False, provider=None, confidence=0.0)
            elif domain == "false-ai.com":
                # False positive: benign classified as AI
                return AIDetectionResult(is_ai=True, is_uncertain=False, provider="Anthropic", confidence=0.8)
            else:
                # True negative
                return AIDetectionResult(is_ai=False, is_uncertain=False, provider=None, confidence=0.0)

    records = [
        EvaluationRecord(id="1", domain="real-ai.com", ground_truth_is_ai=True, ground_truth_provider="OpenAI"),
        EvaluationRecord(id="2", domain="missed-ai.com", ground_truth_is_ai=True, ground_truth_provider="Google"),
        EvaluationRecord(id="3", domain="false-ai.com", ground_truth_is_ai=False, ground_truth_provider=None),
        EvaluationRecord(id="4", domain="benign-1.com", ground_truth_is_ai=False, ground_truth_provider=None),
        EvaluationRecord(id="5", domain="benign-2.com", ground_truth_is_ai=False, ground_truth_provider=None),
    ]

    service = EvaluationService()
    res = service.evaluate_records(records=records, detector=MockDetector())

    assert res.dataset_size == 5
    assert res.true_positives == 1   # real-ai.com
    assert res.false_negatives == 1  # missed-ai.com
    assert res.false_positives == 1  # false-ai.com
    assert res.true_negatives == 2   # benign-1, benign-2

    # Precision: TP / (TP + FP) = 1 / (1 + 1) = 0.50 (50%)
    assert res.precision == 0.5
    # Recall: TP / (TP + FN) = 1 / (1 + 1) = 0.50 (50%)
    assert res.recall == 0.5
    # False-positive rate: FP / (FP + TN) = 1 / (1 + 2) = 1/3 (~0.333)
    assert pytest.approx(res.false_positive_rate, rel=1e-2) == 0.333
    # Detection accuracy: (TP + TN) / Total = (1 + 2) / 5 = 0.60 (60%)
    assert res.detection_accuracy == 0.6
    # Provider accuracy: TP matched provider "OpenAI" == "OpenAI" -> 1/1 = 1.0
    assert res.provider_accuracy == 1.0
    assert len(res.detailed_discrepancies) == 2


def test_evaluation_imbalanced_all_positives():
    """When dataset has only positive records, FPR is undefined (None) without zero division error."""
    class AllAIDetector:
        def classify_target(self, domain: str) -> AIDetectionResult:
            return AIDetectionResult(is_ai=True, is_uncertain=False, provider="OpenAI", confidence=0.99)

    records = [
        EvaluationRecord(id="1", domain="ai1.com", ground_truth_is_ai=True, ground_truth_provider="OpenAI"),
        EvaluationRecord(id="2", domain="ai2.com", ground_truth_is_ai=True, ground_truth_provider="OpenAI"),
    ]

    service = EvaluationService()
    res = service.evaluate_records(records=records, detector=AllAIDetector())

    assert res.true_positives == 2
    assert res.precision == 1.0
    assert res.recall == 1.0
    # Zero negative records -> FP + TN = 0 -> FPR must be None
    assert res.false_positive_rate is None


def test_evaluation_imbalanced_all_negatives():
    """When dataset has only negative records, Precision & Recall are undefined (None)."""
    class NonAIDetector:
        def classify_target(self, domain: str) -> AIDetectionResult:
            return AIDetectionResult(is_ai=False, is_uncertain=False, provider=None, confidence=0.0)

    records = [
        EvaluationRecord(id="1", domain="benign1.com", ground_truth_is_ai=False),
        EvaluationRecord(id="2", domain="benign2.com", ground_truth_is_ai=False),
    ]

    service = EvaluationService()
    res = service.evaluate_records(records=records, detector=NonAIDetector())

    assert res.true_negatives == 2
    # Zero positive predictions -> Precision is None
    assert res.precision is None
    # Zero positive ground truth -> Recall is None
    assert res.recall is None
    assert res.false_positive_rate == 0.0
    assert res.detection_accuracy == 1.0


def test_evaluation_provider_misclassification():
    """When detector identifies AI but assigns wrong provider, provider accuracy drops."""
    class MisclassifyingDetector:
        def classify_target(self, domain: str) -> AIDetectionResult:
            # Always identifies AI correctly, but always attributes to OpenAI
            return AIDetectionResult(is_ai=True, is_uncertain=False, provider="OpenAI", confidence=0.99)


    records = [
        EvaluationRecord(id="1", domain="api.openai.com", ground_truth_is_ai=True, ground_truth_provider="OpenAI"),
        EvaluationRecord(id="2", domain="api.anthropic.com", ground_truth_is_ai=True, ground_truth_provider="Anthropic"),
    ]

    service = EvaluationService()
    res = service.evaluate_records(records=records, detector=MisclassifyingDetector())

    assert res.true_positives == 2
    assert res.precision == 1.0
    assert res.recall == 1.0
    # Only 1 out of 2 matched the correct provider ("OpenAI" matched, "Anthropic" was misclassified as "OpenAI")
    assert res.provider_accuracy == 0.5
    assert any(d["type"] == "provider_mismatch" for d in res.detailed_discrepancies)


def test_unknown_and_ambiguous_domains_handled_safely():
    """Ambiguous synthetic and general web domains must be correctly classified as non-AI (TN)."""
    service = default_evaluation_service
    records = [
        EvaluationRecord(id="1", domain="unverified-ai-test.invalid", ground_truth_is_ai=False),
        EvaluationRecord(id="2", domain="google.com", ground_truth_is_ai=False),
        EvaluationRecord(id="3", domain="internal-proxy.local", ground_truth_is_ai=False),
        EvaluationRecord(id="4", domain="example.com", ground_truth_is_ai=False),
    ]

    res = service.evaluate_records(records=records)
    assert res.true_negatives == 4
    assert res.false_positives == 0
    assert res.false_positive_rate == 0.0
