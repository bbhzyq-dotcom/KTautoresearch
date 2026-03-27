"""
Human Validator - Interface for humans to validate/filter hypotheses.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from hypothesis_generator import ScientificHypothesis, HypothesisStatus


class ValidationDecision(Enum):
    WORTHY = "worthy"
    UNWORTHY = "unworthy"
    NEEDS_REFINEMENT = "needs_refinement"
    NEEDS_MORE_INFO = "needs_more_info"
    DEFER = "defer"


@dataclass
class ValidationRecord:
    hypothesis_id: str
    validator_name: str
    decision: str
    confidence_level: int
    reasoning: str
    strengths: List[str]
    weaknesses: List[str]
    suggested_modifications: List[str]
    validated_at: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRecord':
        return cls(**data)


class HumanValidator:
    def __init__(self, workspace_path: str = "./workspace/validation"):
        self.workspace_path = workspace_path
        self.validation_records: List[ValidationRecord] = []
        self._ensure_workspace()

    def _ensure_workspace(self):
        os.makedirs(self.workspace_path, exist_ok=True)

    def validate_hypothesis(
        self,
        hypothesis: ScientificHypothesis,
        validator_name: str,
        decision: ValidationDecision,
        confidence_level: int,
        reasoning: str,
        strengths: Optional[List[str]] = None,
        weaknesses: Optional[List[str]] = None,
        suggested_modifications: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> ValidationRecord:
        if strengths is None:
            strengths = []
        if weaknesses is None:
            weaknesses = []
        if suggested_modifications is None:
            suggested_modifications = []
        if tags is None:
            tags = []

        record = ValidationRecord(
            hypothesis_id=hypothesis.id,
            validator_name=validator_name,
            decision=decision.value,
            confidence_level=confidence_level,
            reasoning=reasoning,
            strengths=strengths,
            weaknesses=weaknesses,
            suggested_modifications=suggested_modifications,
            validated_at=datetime.now().isoformat(),
            tags=tags
        )

        self.validation_records.append(record)
        self._save_validation_record(record)
        self._update_hypothesis_status(hypothesis, decision, reasoning)

        return record

    def _save_validation_record(self, record: ValidationRecord):
        filename = os.path.join(
            self.workspace_path,
            f"validation_{record.hypothesis_id}_{record.validated_at.replace(':', '-').replace('.', '-')}.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)

    def _update_hypothesis_status(
        self,
        hypothesis: ScientificHypothesis,
        decision: ValidationDecision,
        reasoning: str
    ):
        if decision == ValidationDecision.WORTHY:
            hypothesis.status = HypothesisStatus.VALIDATED_WORTHY.value
        elif decision == ValidationDecision.UNWORTHY:
            hypothesis.status = HypothesisStatus.VALIDATED_UNWORTHY.value
        elif decision == ValidationDecision.NEEDS_REFINEMENT:
            hypothesis.status = HypothesisStatus.DRAFT.value
        elif decision == ValidationDecision.DEFER:
            hypothesis.status = HypothesisStatus.PENDING_VALIDATION.value

        hypothesis.validation_notes = f"[{decision.value}] {reasoning}"

        hypothesis_file = os.path.join(
            "./workspace/hypotheses",
            f"hypothesis_{hypothesis.id}.json"
        )
        with open(hypothesis_file, 'w', encoding='utf-8') as f:
            json.dump(hypothesis.to_dict(), f, indent=2, ensure_ascii=False)

    def batch_validate(
        self,
        hypotheses: List[ScientificHypothesis],
        validator_name: str,
        decisions: Dict[str, ValidationDecision],
        reasoning_map: Dict[str, str]
    ) -> List[ValidationRecord]:
        records = []
        for hypothesis in hypotheses:
            if hypothesis.id in decisions:
                record = self.validate_hypothesis(
                    hypothesis=hypothesis,
                    validator_name=validator_name,
                    decision=decisions[hypothesis.id],
                    confidence_level=5,
                    reasoning=reasoning_map.get(hypothesis.id, "Batch validation"),
                )
                records.append(record)
        return records

    def get_validation_history(
        self,
        hypothesis_id: Optional[str] = None,
        validator_name: Optional[str] = None
    ) -> List[ValidationRecord]:
        history = self.validation_records

        if hypothesis_id:
            history = [r for r in history if r.hypothesis_id == hypothesis_id]

        if validator_name:
            history = [r for r in history if r.validator_name == validator_name]

        return history

    def get_worthy_hypotheses(
        self,
        hypotheses: List[ScientificHypothesis]
    ) -> List[ScientificHypothesis]:
        return [
            h for h in hypotheses
            if h.status == HypothesisStatus.VALIDATED_WORTHY.value
        ]

    def generate_validation_summary(
        self,
        hypotheses: List[ScientificHypothesis]
    ) -> Dict[str, Any]:
        total = len(hypotheses)
        worthy = len(self.get_worthy_hypotheses(hypotheses))
        unworthy = len([h for h in hypotheses if h.status == HypothesisStatus.VALIDATED_UNWORTHY.value])
        pending = len([h for h in hypotheses if h.status == HypothesisStatus.PENDING_VALIDATION.value])
        draft = len([h for h in hypotheses if h.status == HypothesisStatus.DRAFT.value])

        return {
            "total_hypotheses": total,
            "worthy": worthy,
            "unworthy": unworthy,
            "pending_validation": pending,
            "draft": draft,
            "approval_rate": worthy / total if total > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }

    def interactive_validate(self, hypothesis: ScientificHypothesis) -> ValidationRecord:
        print("\n" + "="*60)
        print("HYPOTHESIS VALIDATION")
        print("="*60)
        print(f"\nHypothesis ID: {hypothesis.id}")
        print(f"Title: {hypothesis.title}")
        print(f"\nDescription:\n{hypothesis.description}")
        print(f"\nRationale:\n{hypothesis.rationale}")
        print(f"\nPredicted Mechanism:\n{hypothesis.predicted_mechanism}")
        print(f"\nExpected Effect: {hypothesis.expected_effect_direction}")
        print(f"\nSuggested Experiments:")
        for i, exp in enumerate(hypothesis.suggested_experiments, 1):
            print(f"  {i}. {exp}")

        print("\n" + "-"*60)
        print("Validation Options:")
        print("  1. Worthy    - This hypothesis is worth exploring")
        print("  2. Unworthy  - This hypothesis is not promising")
        print("  3. Refine    - Needs modification before approval")
        print("  4. Defer     - Need more information")
        print("-"*60)

        while True:
            choice = input("\nEnter your decision (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                break
            print("Invalid choice. Please try again.")

        decision_map = {
            '1': ValidationDecision.WORTHY,
            '2': ValidationDecision.UNWORTHY,
            '3': ValidationDecision.NEEDS_REFINEMENT,
            '4': ValidationDecision.DEFER
        }

        reasoning = input("\nEnter your reasoning (required): ").strip()
        if not reasoning:
            reasoning = "No reasoning provided"

        strengths_input = input("\nStrengths (comma-separated, optional): ").strip()
        strengths = [s.strip() for s in strengths_input.split(',')] if strengths_input else []

        weaknesses_input = input("\nWeaknesses (comma-separated, optional): ").strip()
        weaknesses = [w.strip() for w in weaknesses_input.split(',')] if weaknesses_input else []

        validator_name = input("\nYour name (optional): ").strip() or "anonymous"

        return self.validate_hypothesis(
            hypothesis=hypothesis,
            validator_name=validator_name,
            decision=decision_map[choice],
            confidence_level=5,
            reasoning=reasoning,
            strengths=strengths,
            weaknesses=weaknesses
        )
