from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.traffic_api import TestEvaluationMetricsResponse
from app.services.evaluation_service import default_evaluation_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/metrics",
    response_model=TestEvaluationMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get model detection and evaluation metrics",
    description="Returns measured precision, recall, false-positive rate, and provider identification accuracy benchmarks on versioned ground-truth dataset.",
)
def get_evaluation_metrics(
    db: Session = Depends(get_db),
) -> TestEvaluationMetricsResponse:
    """Calculates live detection performance and evaluation benchmarks against labeled ground truth."""
    eval_res = default_evaluation_service.run_ground_truth_evaluation()

    return TestEvaluationMetricsResponse(
        totalEvaluations=eval_res.total_evaluations,
        datasetSize=eval_res.dataset_size,
        evaluatedRecordsCount=eval_res.evaluated_records_count,
        precision=eval_res.precision,
        detectionPrecision=eval_res.precision,
        recall=eval_res.recall,
        detectionRecall=eval_res.recall,
        falsePositiveRate=eval_res.false_positive_rate,
        fpr=eval_res.false_positive_rate,
        providerAccuracy=eval_res.provider_accuracy,
        providerIdentificationAccuracy=eval_res.provider_accuracy,
        detectionAccuracy=eval_res.detection_accuracy,
        truePositives=eval_res.true_positives,
        true_positives=eval_res.true_positives,
        falsePositives=eval_res.false_positives,
        false_positives=eval_res.false_positives,
        trueNegatives=eval_res.true_negatives,
        true_negatives=eval_res.true_negatives,
        falseNegatives=eval_res.false_negatives,
        false_negatives=eval_res.false_negatives,
        datasetVersion=eval_res.dataset_version,
        dataset_version=eval_res.dataset_version,
        evaluationDatasetName=eval_res.dataset_name,
        evaluation_dataset_name=eval_res.dataset_name,
        isIllustrative=eval_res.is_illustrative,
        is_illustrative=eval_res.is_illustrative,
        status="completed",
        notes=eval_res.notes,
        timestamp=eval_res.evaluated_at,
        evaluatedAt=eval_res.evaluated_at,
        evaluated_at=eval_res.evaluated_at,
        categoriesBreakdown=eval_res.categories_breakdown,
    )

