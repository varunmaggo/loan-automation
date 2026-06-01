"""Run evaluation suite."""

import json
import os
import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from deepeval import evaluate
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from deepeval.dataset import EvaluationDataset

from .metrics import (
    PolicyComplianceMetric,
    SchemaValidityMetric,
    ExactMatchMetric,
    slice_disparity
)
from ..config import config


def load_test_cases() -> List[LLMTestCase]:
    """Load test cases from dataset file."""
    dataset_path = Path(__file__).parent / "dataset.jsonl"
    
    if not dataset_path.exists():
        # Generate test cases if not exists
        generate_test_dataset()
    
    test_cases = []
    with open(dataset_path) as f:
        for line in f:
            data = json.loads(line.strip())
            test_case = LLMTestCase(
                input=data["input"],
                actual_output=data["actual_output"],
                expected_output=data["expected_output"],
                additional_metadata=data.get("additional_metadata", {})
            )
            test_cases.append(test_case)
    
    return test_cases


def generate_test_dataset():
    """Generate test dataset if not exists."""
    dataset_path = Path(__file__).parent / "dataset.jsonl"
    
    # Sample test cases
    test_cases = [
        {
            "input": "Process loan application for John Doe with credit score 750",
            "actual_output": json.dumps({
                "application_id": "app_001",
                "recommendation": "approve_fast_track",
                "status": "approved_fast_track",
                "risk_band": "prime",
                "reasons": ["Excellent credit score", "Low debt-to-income ratio"],
                "requires_human_review": False
            }),
            "expected_output": json.dumps({
                "application_id": "app_001",
                "recommendation": "approve_fast_track",
                "status": "approved_fast_track",
                "risk_band": "prime",
                "reasons": ["Excellent credit score"],
                "requires_human_review": False
            }),
            "additional_metadata": {"risk_band": "prime"}
        },
        {
            "input": "Process loan application for Jane Smith with credit score 600",
            "actual_output": json.dumps({
                "application_id": "app_002",
                "recommendation": "human_review",
                "status": "human_review",
                "risk_band": "high_risk",
                "reasons": ["Low credit score", "High debt-to-income ratio"],
                "requires_human_review": True
            }),
            "expected_output": json.dumps({
                "application_id": "app_002",
                "recommendation": "human_review",
                "status": "human_review",
                "risk_band": "high_risk",
                "reasons": ["Low credit score"],
                "requires_human_review": True
            }),
            "additional_metadata": {"risk_band": "high_risk"}
        }
    ]
    
    with open(dataset_path, "w") as f:
        for case in test_cases:
            f.write(json.dumps(case) + "\n")


def run_evaluations():
    """Run all evaluations."""
    print("Running DeepEval evaluation suite...")
    
    # Set telemetry opt out
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = config.DEEPEVAL_TELEMETRY_OPT_OUT
    
    # Load test cases
    test_cases = load_test_cases()
    
    # Create metrics
    metrics: List[BaseMetric] = [
        PolicyComplianceMetric(threshold=0.85),
        SchemaValidityMetric(threshold=0.90),
        ExactMatchMetric(threshold=0.90)
    ]
    
    # Create dataset
    dataset = EvaluationDataset()
    dataset.add_test_cases(test_cases)
    
    # Run evaluations
    try:
        result = evaluate(
            test_cases=dataset.test_cases,
            metrics=metrics,
            run_async=False
        )
    except TypeError:
        # Handle DeepEval v4 API change
        result = evaluate(
            test_cases=dataset.test_cases,
            metrics=metrics
        )
    
    # Print results
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    
    for metric in metrics:
        passed = sum(1 for tc in test_cases if metric.measure(tc) >= metric.threshold)
        total = len(test_cases)
        status = "PASSED" if metric.is_successful() else "FAILED"
        print(f"{metric.__name__}: {passed}/{total} {status}")
    
    # Calculate slice disparity
    disparity = slice_disparity(test_cases)
    print(f"\nslice_disparity: {disparity}")
    
    # Check all hard gates
    all_passed = all(m.is_successful() for m in metrics)
    
    print("\n" + "="*50)
    if all_passed:
        print("All hard gates: PASS")
    else:
        print("Some hard gates: FAIL")
    print("="*50)
    
    return all_passed


if __name__ == "__main__":
    success = run_evaluations()
    sys.exit(0 if success else 1)
