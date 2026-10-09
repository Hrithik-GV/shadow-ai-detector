from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.ai_detector import AIDetector, default_detector

logger = logging.getLogger(__name__)

DEFAULT_DATASET_PATH = Path(__file__).parent.parent / "data" / "evaluation_dataset.json"


@dataclass
class EvaluationRecord:
    """A labeled ground-truth record for detector performance benchmarking."""
    id: str
    domain: str
    ground_truth_is_ai: bool
    ground_truth_provider: Optional[str] = None
    ground_truth_category: Optional[str] = None
    traffic_type: str = "unknown"
    notes: Optional[str] = None


@dataclass
class EvaluationResult:
    """Comprehensive evaluation metrics computed against ground truth records."""
    dataset_name: str
    dataset_version: str
    dataset_size: int
    evaluated_records_count: int
    total_evaluations: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: Optional[float]
    recall: Optional[float]
    false_positive_rate: Optional[float]
    provider_accuracy: Optional[float]
    detection_accuracy: Optional[float]
    evaluated_at: datetime
    is_illustrative: bool = False
    categories_breakdown: Dict[str, int] = field(default_factory=dict)
    detailed_discrepancies: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None


class EvaluationService:
    """Executes reproducible evaluation benchmarks using labeled ground-truth records."""

    def __init__(
        self,
        dataset_path: Optional[Path] = None,
        detector: Optional[AIDetector] = None,
    ) -> None:
        self.dataset_path = dataset_path or DEFAULT_DATASET_PATH
        self.detector = detector or default_detector

    def load_ground_truth_dataset(self) -> tuple[str, str, List[EvaluationRecord]]:
        """Loads versioned ground-truth dataset from disk."""
        if not self.dataset_path.exists():
            logger.warning("Ground-truth evaluation dataset not found at %s", self.dataset_path)
            return "unknown", "0.0.0", []

        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            dataset_name = data.get("dataset_name", "ground_truth_evaluation")
            dataset_version = data.get("version", "1.0.0")
            raw_records = data.get("records", [])

            records = [
                EvaluationRecord(
                    id=r["id"],
                    domain=r["domain"],
                    ground_truth_is_ai=bool(r["ground_truth_is_ai"]),
                    ground_truth_provider=r.get("ground_truth_provider"),
                    ground_truth_category=r.get("ground_truth_category"),
                    traffic_type=r.get("traffic_type", "unknown"),
                    notes=r.get("notes"),
                )
                for r in raw_records
            ]
            return dataset_name, dataset_version, records
        except Exception as exc:
            logger.error("Failed to parse evaluation dataset at %s: %s", self.dataset_path, exc)
            return "unknown", "0.0.0", []

    def evaluate_records(
        self,
        records: List[EvaluationRecord],
        dataset_name: str = "custom_test_dataset",
        dataset_version: str = "1.0.0",
        detector: Optional[AIDetector] = None,
    ) -> EvaluationResult:
        """Computes confusion matrix and metrics over a list of labeled records."""
        active_detector = detector or self.detector
        total = len(records)
        now = datetime.now(timezone.utc)

        # Handle empty dataset explicitly
        if total == 0:
            return EvaluationResult(
                dataset_name=dataset_name,
                dataset_version=dataset_version,
                dataset_size=0,
                evaluated_records_count=0,
                total_evaluations=0,
                true_positives=0,
                false_positives=0,
                true_negatives=0,
                false_negatives=0,
                precision=None,
                recall=None,
                false_positive_rate=None,
                provider_accuracy=None,
                detection_accuracy=None,
                evaluated_at=now,
                is_illustrative=False,
                categories_breakdown={},
                detailed_discrepancies=[],
                notes="Evaluation dataset is empty. Metrics are undefined (zero denominators).",
            )

        tp = 0
        fp = 0
        tn = 0
        fn = 0
        provider_correct = 0
        categories_breakdown: Dict[str, int] = {}
        discrepancies: List[Dict[str, Any]] = []

        for rec in records:
            classification = active_detector.classify_target(domain=rec.domain)
            is_predicted_ai = bool(classification.is_ai)
            predicted_provider = classification.provider

            if rec.ground_truth_is_ai:
                if is_predicted_ai:
                    tp += 1
                    # Track category counts for true positives
                    cat = rec.ground_truth_category or "Uncategorized AI"
                    categories_breakdown[cat] = categories_breakdown.get(cat, 0) + 1

                    # Check provider identification
                    if rec.ground_truth_provider and predicted_provider:
                        if rec.ground_truth_provider.replace(" ", "").lower() == predicted_provider.replace(" ", "").lower():
                            provider_correct += 1
                        else:
                            discrepancies.append({
                                "id": rec.id,
                                "domain": rec.domain,
                                "type": "provider_mismatch",
                                "ground_truth_provider": rec.ground_truth_provider,
                                "predicted_provider": predicted_provider,
                            })
                    elif rec.ground_truth_provider is None and predicted_provider is None:
                        provider_correct += 1
                else:
                    fn += 1
                    discrepancies.append({
                        "id": rec.id,
                        "domain": rec.domain,
                        "type": "false_negative",
                        "notes": "Actual AI flow missed by detector",
                    })
            else:
                if is_predicted_ai:
                    fp += 1
                    discrepancies.append({
                        "id": rec.id,
                        "domain": rec.domain,
                        "type": "false_positive",
                        "predicted_provider": predicted_provider,
                        "notes": "Benign flow misclassified as AI",
                    })
                else:
                    tn += 1

        # Calculate metrics with explicit zero-denominator protection
        # Precision: TP / (TP + FP) -> undefined if no positive predictions
        precision = (float(tp) / (tp + fp)) if (tp + fp) > 0 else None

        # Recall: TP / (TP + FN) -> undefined if no actual positive records in dataset
        recall = (float(tp) / (tp + fn)) if (tp + fn) > 0 else None

        # False-Positive Rate: FP / (FP + TN) -> undefined if no actual negative records
        false_positive_rate = (float(fp) / (fp + tn)) if (fp + tn) > 0 else None

        # Accuracy: (TP + TN) / Total
        detection_accuracy = (float(tp + tn) / total) if total > 0 else None

        # Provider Identification Accuracy: correct provider matches / TP
        provider_accuracy = (float(provider_correct) / tp) if tp > 0 else None

        return EvaluationResult(
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            dataset_size=total,
            evaluated_records_count=total,
            total_evaluations=1,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            false_positive_rate=false_positive_rate,
            provider_accuracy=provider_accuracy,
            detection_accuracy=detection_accuracy,
            evaluated_at=now,
            is_illustrative=False,
            categories_breakdown=categories_breakdown,
            detailed_discrepancies=discrepancies,
            notes=f"Evaluated against {total} ground-truth records ({tp} TP, {fp} FP, {tn} TN, {fn} FN).",
        )

    def run_ground_truth_evaluation(self) -> EvaluationResult:
        """Loads default ground-truth dataset and executes evaluation benchmark."""
        dataset_name, dataset_version, records = self.load_ground_truth_dataset()
        return self.evaluate_records(
            records=records,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
        )


default_evaluation_service = EvaluationService()
