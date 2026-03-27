"""
Evaluator - Evaluates experiment results and determines hypothesis validity.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from hypothesis_generator import ScientificHypothesis, HypothesisStatus
from experiment_executor import Experiment, ExperimentStatus


class EvaluationVerdict(Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"
    INCONCLUSIVE = "inconclusive"
    CONTRADICTED = "contradicted"


class EvidenceStrength(Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


@dataclass
class EvaluationResult:
    hypothesis_id: str
    hypothesis_title: str
    verdict: str
    evidence_strength: str
    effect_size: float
    p_value: float
    confidence_interval: Dict[str, float]
    key_findings: List[str]
    limitations: List[str]
    alternative_explanations: List[str]
    recommendation: str
    evaluated_at: str
    experiments_analyzed: int
    supporting_experiments: int
    contradicting_experiments: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        return cls(**data)


class Evaluator:
    def __init__(self, workspace_path: str = "./workspace"):
        self.workspace_path = workspace_path
        self.evaluation_history: List[EvaluationResult] = []

    def evaluate_hypothesis(
        self,
        hypothesis: ScientificHypothesis,
        experiments: List[Experiment]
    ) -> EvaluationResult:
        if not experiments:
            return self._create_inconclusive_result(
                hypothesis,
                ["No experiments were conducted"]
            )

        completed_experiments = [
            e for e in experiments
            if e.status == ExperimentStatus.COMPLETED.value
        ]

        if not completed_experiments:
            return self._create_inconclusive_result(
                hypothesis,
                ["All experiments failed or were cancelled"]
            )

        effect_sizes = []
        p_values = []
        supporting = 0
        contradicting = 0
        inconclusive = 0

        for exp in completed_experiments:
            results = exp.results
            if not results:
                inconclusive += 1
                continue

            effect = results.get("effect_size", 0)
            p_val = results.get("p_value", 1.0)

            effect_sizes.append(effect)
            p_values.append(p_val)

            if p_val < 0.05:
                if abs(effect) > 0.5:
                    if effect > 0:
                        supporting += 1
                    else:
                        contradicting += 1
                elif abs(effect) > 0.2:
                    if effect > 0:
                        supporting += 0.5
                    else:
                        contradicting += 0.5
                else:
                    inconclusive += 1
            else:
                inconclusive += 1

        avg_effect = sum(effect_sizes) / len(effect_sizes) if effect_sizes else 0
        avg_p = sum(p_values) / len(p_values) if p_values else 1.0

        verdict = self._determine_verdict(
            avg_effect, avg_p, supporting, contradicting, inconclusive
        )

        evidence_strength = self._assess_evidence_strength(
            avg_effect, avg_p, len(completed_experiments)
        )

        key_findings = self._extract_key_findings(completed_experiments, avg_effect, avg_p)
        limitations = self._identify_limitations(completed_experiments)
        alt_explanations = self._generate_alternative_explanations(
            hypothesis, avg_effect, completed_experiments
        )
        recommendation = self._generate_recommendation(
            verdict, evidence_strength, hypothesis
        )

        ci_lower = min([r.get("confidence_interval", {}).get("lower", 0) for r in [e.results for e in completed_experiments] if r], default=0)
        ci_upper = max([r.get("confidence_interval", {}).get("upper", 0) for r in [e.results for e in completed_experiments] if r], default=0)

        result = EvaluationResult(
            hypothesis_id=hypothesis.id,
            hypothesis_title=hypothesis.title,
            verdict=verdict.value,
            evidence_strength=evidence_strength.value,
            effect_size=round(avg_effect, 4),
            p_value=round(avg_p, 4),
            confidence_interval={"lower": round(ci_lower, 4), "upper": round(ci_upper, 4)},
            key_findings=key_findings,
            limitations=limitations,
            alternative_explanations=alt_explanations,
            recommendation=recommendation,
            evaluated_at=datetime.now().isoformat(),
            experiments_analyzed=len(completed_experiments),
            supporting_experiments=int(supporting),
            contradicting_experiments=int(contradicting)
        )

        self.evaluation_history.append(result)
        self._save_evaluation_result(result)

        return result

    def _create_inconclusive_result(
        self,
        hypothesis: ScientificHypothesis,
        reasons: List[str]
    ) -> EvaluationResult:
        return EvaluationResult(
            hypothesis_id=hypothesis.id,
            hypothesis_title=hypothesis.title,
            verdict=EvaluationVerdict.INCONCLUSIVE.value,
            evidence_strength=EvidenceStrength.NONE.value,
            effect_size=0.0,
            p_value=1.0,
            confidence_interval={"lower": 0, "upper": 0},
            key_findings=[],
            limitations=reasons,
            alternative_explanations=["Unable to determine due to lack of valid experiments"],
            recommendation="More experimental work needed",
            evaluated_at=datetime.now().isoformat(),
            experiments_analyzed=0,
            supporting_experiments=0,
            contradicting_experiments=0
        )

    def _determine_verdict(
        self,
        avg_effect: float,
        avg_p: float,
        supporting: float,
        contradicting: float,
        inconclusive: int
    ) -> EvaluationVerdict:
        total = supporting + contradicting + inconclusive

        if total == 0:
            return EvaluationVerdict.INCONCLUSIVE

        support_ratio = supporting / total
        contradict_ratio = contradicting / total

        if avg_p >= 0.05:
            return EvaluationVerdict.INCONCLUSIVE

        if support_ratio > 0.7 and avg_effect > 0.3:
            return EvaluationVerdict.SUPPORTED
        elif support_ratio > 0.5 and avg_effect > 0.2:
            return EvaluationVerdict.PARTIALLY_SUPPORTED
        elif contradict_ratio > 0.7 and avg_effect < -0.3:
            return EvaluationVerdict.CONTRADICTED
        elif contradict_ratio > 0.5 and avg_effect < -0.2:
            return EvaluationVerdict.PARTIALLY_SUPPORTED
        else:
            return EvaluationVerdict.NOT_SUPPORTED

    def _assess_evidence_strength(
        self,
        effect_size: float,
        p_value: float,
        num_experiments: int
    ) -> EvidenceStrength:
        if p_value >= 0.05:
            return EvidenceStrength.NONE

        score = 0

        if abs(effect_size) > 0.8:
            score += 3
        elif abs(effect_size) > 0.5:
            score += 2
        elif abs(effect_size) > 0.2:
            score += 1

        if p_value < 0.001:
            score += 2
        elif p_value < 0.01:
            score += 1

        if num_experiments >= 5:
            score += 2
        elif num_experiments >= 3:
            score += 1

        if score >= 6:
            return EvidenceStrength.STRONG
        elif score >= 4:
            return EvidenceStrength.MODERATE
        elif score >= 2:
            return EvidenceStrength.WEAK
        else:
            return EvidenceStrength.NONE

    def _extract_key_findings(
        self,
        experiments: List[Experiment],
        avg_effect: float,
        avg_p: float
    ) -> List[str]:
        findings = []

        if avg_effect > 0.5:
            findings.append(f"Strong positive effect observed (d={avg_effect:.2f})")
        elif avg_effect > 0.2:
            findings.append(f"Moderate positive effect observed (d={avg_effect:.2f})")
        elif avg_effect < -0.5:
            findings.append(f"Strong negative effect observed (d={avg_effect:.2f})")
        elif avg_effect < -0.2:
            findings.append(f"Moderate negative effect observed (d={avg_effect:.2f})")
        else:
            findings.append(f"Negligible effect size (d={avg_effect:.2f})")

        if avg_p < 0.001:
            findings.append("Result is highly statistically significant (p<0.001)")
        elif avg_p < 0.01:
            findings.append("Result is statistically significant (p<0.01)")
        elif avg_p < 0.05:
            findings.append("Result is statistically significant (p<0.05)")
        else:
            findings.append("Result is not statistically significant (p>=0.05)")

        successful = len([e for e in experiments if e.status == ExperimentStatus.COMPLETED.value])
        findings.append(f"{successful}/{len(experiments)} experiments completed successfully")

        return findings

    def _identify_limitations(self, experiments: List[Experiment]) -> List[str]:
        limitations = []

        if len(experiments) < 3:
            limitations.append("Limited number of experiments - results may not be robust")

        for exp in experiments:
            if exp.duration_seconds < 60:
                limitations.append(f"Experiment {exp.id} had very short duration ({exp.duration_seconds:.1f}s)")

        if not limitations:
            limitations.append("No major limitations identified")

        return limitations

    def _generate_alternative_explanations(
        self,
        hypothesis: ScientificHypothesis,
        effect_size: float,
        experiments: List[Experiment]
    ) -> List[str]:
        alternatives = []

        if abs(effect_size) < 0.2:
            alternatives.append("Effect may be due to measurement error or noise")
            alternatives.append("Sample size may have been insufficient to detect real effect")

        if effect_size > 0:
            alternatives.append("Confounding variables may have influenced the results")
            alternatives.append("Selection bias in sample preparation")

        if not alternatives:
            alternatives.append("No strong alternative explanations identified")

        return alternatives

    def _generate_recommendation(
        self,
        verdict: EvaluationVerdict,
        evidence: EvidenceStrength,
        hypothesis: ScientificHypothesis
    ) -> str:
        if verdict == EvaluationVerdict.SUPPORTED and evidence == EvidenceStrength.STRONG:
            return f"Hypothesis '{hypothesis.title}' is strongly supported by evidence. Recommend further investigation and potential publication."
        elif verdict == EvaluationVerdict.SUPPORTED:
            return f"Hypothesis is supported. Consider replication with larger sample size."
        elif verdict == EvaluationVerdict.PARTIALLY_SUPPORTED:
            return f"Hypothesis shows partial support. Refine and test specific aspects."
        elif verdict == EvaluationVerdict.NOT_SUPPORTED:
            return f"Hypothesis not supported by current evidence. Consider modifying theoretical framework."
        elif verdict == EvaluationVerdict.CONTRADICTED:
            return f"Hypothesis contradicted by evidence. Reject and develop alternative hypotheses."
        else:
            return "Results are inconclusive. More experimental data needed."

    def _save_evaluation_result(self, result: EvaluationResult):
        os.makedirs(os.path.join(self.workspace_path, "evaluation"), exist_ok=True)
        filename = os.path.join(
            self.workspace_path,
            "evaluation",
            f"evaluation_{result.hypothesis_id}_{result.evaluated_at.replace(':', '-').replace('.', '-')}.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    def compare_hypotheses(
        self,
        hypotheses: List[ScientificHypothesis],
        results: Dict[str, EvaluationResult]
    ) -> List[EvaluationResult]:
        sorted_results = sorted(
            results.values(),
            key=lambda x: (
                0 if x.evidence_strength == EvidenceStrength.STRONG.value else
                1 if x.evidence_strength == EvidenceStrength.MODERATE.value else
                2 if x.evidence_strength == EvidenceStrength.WEAK.value else 3,
                x.p_value
            )
        )
        return sorted_results

    def generate_summary_report(
        self,
        hypotheses: List[ScientificHypothesis],
        results: List[EvaluationResult]
    ) -> str:
        report = []
        report.append("="*70)
        report.append("SCIENTIFIC HYPOTHESIS EVALUATION SUMMARY")
        report.append("="*70)
        report.append(f"\nGenerated: {datetime.now().isoformat()}")
        report.append(f"Total hypotheses evaluated: {len(results)}")

        supported = [r for r in results if r.verdict == EvaluationVerdict.SUPPORTED.value]
        partially = [r for r in results if r.verdict == EvaluationVerdict.PARTIALLY_SUPPORTED.value]
        not_supported = [r for r in results if r.verdict == EvaluationVerdict.NOT_SUPPORTED.value]
        contradicted = [r for r in results if r.verdict == EvaluationVerdict.CONTRADICTED.value]
        inconclusive = [r for r in results if r.verdict == EvaluationVerdict.INCONCLUSIVE.value]

        report.append(f"\nResults breakdown:")
        report.append(f"  - Supported: {len(supported)}")
        report.append(f"  - Partially Supported: {len(partially)}")
        report.append(f"  - Not Supported: {len(not_supported)}")
        report.append(f"  - Contradicted: {len(contradicted)}")
        report.append(f"  - Inconclusive: {len(inconclusive)}")

        report.append("\n" + "-"*70)
        report.append("DETAILED RESULTS")
        report.append("-"*70)

        for result in sorted(results, key=lambda x: x.p_value):
            report.append(f"\n[{result.verdict.upper()}] {result.hypothesis_title}")
            report.append(f"  Evidence Strength: {result.evidence_strength}")
            report.append(f"  Effect Size: d={result.effect_size:.4f}")
            report.append(f"  P-value: {result.p_value:.4f}")
            report.append(f"  Recommendation: {result.recommendation}")

        return "\n".join(report)
