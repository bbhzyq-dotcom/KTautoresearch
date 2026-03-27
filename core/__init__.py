"""
KTautoresearch - Scientific Hypothesis Generation and Autonomous Experimentation
"""

from core.hypothesis_generator import (
    HypothesisGenerator,
    ScientificHypothesis,
    HypothesisStatus,
    ExperimentResult
)
from core.human_validator import (
    HumanValidator,
    ValidationRecord,
    ValidationDecision
)
from core.experiment_executor import (
    ExperimentExecutor,
    Experiment,
    ExperimentDesign,
    ExperimentStatus,
    ExperimentType
)
from core.evaluator import (
    Evaluator,
    EvaluationResult,
    EvaluationVerdict,
    EvidenceStrength
)

__all__ = [
    "HypothesisGenerator",
    "ScientificHypothesis",
    "HypothesisStatus",
    "ExperimentResult",
    "HumanValidator",
    "ValidationRecord",
    "ValidationDecision",
    "ExperimentExecutor",
    "Experiment",
    "ExperimentDesign",
    "ExperimentStatus",
    "ExperimentType",
    "Evaluator",
    "EvaluationResult",
    "EvaluationVerdict",
    "EvidenceStrength",
]
