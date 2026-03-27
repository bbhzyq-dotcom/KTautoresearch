"""
Hypothesis Generator - AI generates scientific hypotheses based on research questions.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class HypothesisStatus(Enum):
    DRAFT = "draft"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED_WORTHY = "validated_worthy"
    VALIDATED_UNWORTHY = "validated_unworthy"
    EXPERIMENTING = "experimenting"
    EXPERIMENT_COMPLETED = "experiment_completed"
    EXPERIMENT_FAILED = "experiment_failed"


class ExperimentResult(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    INCONCLUSIVE = "inconclusive"
    UNKNOWN = "unknown"


@dataclass
class ScientificHypothesis:
    id: str
    title: str
    description: str
    rationale: str
    predicted_mechanism: str
    potential_evidence: List[str]
    potential_counter_evidence: List[str]
    expected_effect_direction: str
    estimated_feasibility: str
    suggested_experiments: List[str]
    created_at: str
    status: str = HypothesisStatus.DRAFT.value
    validation_notes: str = ""
    experiment_results: Dict[str, Any] = field(default_factory=dict)
    ai_confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScientificHypothesis':
        return cls(**data)


class HypothesisGenerator:
    def __init__(
        self,
        model_name: str = "gpt-4",
        llm_provider=None
    ):
        self.model_name = model_name
        self.llm_provider = llm_provider
        self.generation_count = 0
        self._use_llm = llm_provider is not None

    def set_llm_provider(self, llm_provider):
        self.llm_provider = llm_provider
        self._use_llm = llm_provider is not None

    def generate_hypotheses(
        self,
        research_question: str,
        domain_knowledge: str = "",
        num_hypotheses: int = 5,
        existing_hypotheses: Optional[List[ScientificHypothesis]] = None
    ) -> List[ScientificHypothesis]:
        self.generation_count += 1

        if self._use_llm and self.llm_provider:
            return self._generate_with_llm(
                research_question, domain_knowledge, num_hypotheses, existing_hypotheses
            )
        else:
            return self._generate_with_templates(
                research_question, domain_knowledge, num_hypotheses
            )

    def _generate_with_llm(
        self,
        research_question: str,
        domain_knowledge: str,
        num_hypotheses: int,
        existing_hypotheses: Optional[List[ScientificHypothesis]] = None
    ) -> List[ScientificHypothesis]:
        system_prompt = """You are an expert scientific researcher. Your task is to generate innovative scientific hypotheses based on research questions.

For each hypothesis, you must provide:
1. title: A concise, descriptive title
2. description: Detailed explanation of the hypothesis
3. rationale: Why this hypothesis makes scientific sense
4. predicted_mechanism: The expected biological/physical/chemical mechanism
5. potential_evidence: List of evidence that would support this hypothesis
6. potential_counter_evidence: List of evidence that would refute this hypothesis
7. expected_effect_direction: Positive/Negative/Bidirectional/None
8. estimated_feasibility: High/Medium/Low (based on current technology and resources)
9. suggested_experiments: List of 2-3 specific experiments to test this hypothesis

Output format: Return a JSON array of hypotheses."""

        existing_context = ""
        if existing_hypotheses:
            existing_context = "\n\nPreviously generated hypotheses (for inspiration, do not repeat):\n"
            for h in existing_hypotheses[:3]:
                existing_context += f"- {h.title}: {h.description[:100]}...\n"

        user_prompt = f"""Research Question: {research_question}

Domain Knowledge: {domain_knowledge if domain_knowledge else "General scientific domain"}{existing_context}

Please generate exactly {num_hypotheses} diverse, scientifically sound hypotheses that explore different angles:
- Direct causal relationships
- Inverse relationships
- Synergistic/interaction effects
- Threshold effects
- Novel mechanisms

Ensure hypotheses are:
- Testable with current technology
- Specific enough to generate clear predictions
- Diverse in their theoretical foundations
- Relevant to the research question"""

        try:
            if not self.llm_provider.is_available():
                print("Warning: LLM provider not available, falling back to template generation")
                return self._generate_with_templates(research_question, domain_knowledge, num_hypotheses)

            response = self.llm_provider.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.8,
                max_tokens=4096
            )

            hypotheses = self._parse_llm_response(response, research_question)

            return hypotheses

        except Exception as e:
            print(f"LLM generation failed: {e}, falling back to templates")
            return self._generate_with_templates(research_question, domain_knowledge, num_hypotheses)

    def _parse_llm_response(self, response: str, research_question: str) -> List[ScientificHypothesis]:
        hypotheses = []

        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            json_str = json_str.strip()

            data = json.loads(json_str)

            if isinstance(data, dict) and "hypotheses" in data:
                data = data["hypotheses"]
            elif not isinstance(data, list):
                data = [data]

            for item in data:
                h = ScientificHypothesis(
                    id=str(uuid.uuid4())[:8],
                    title=item.get("title", f"Hypothesis about {research_question}"),
                    description=item.get("description", ""),
                    rationale=item.get("rationale", ""),
                    predicted_mechanism=item.get("predicted_mechanism", ""),
                    potential_evidence=item.get("potential_evidence", []),
                    potential_counter_evidence=item.get("potential_counter_evidence", []),
                    expected_effect_direction=item.get("expected_effect_direction", "Unknown"),
                    estimated_feasibility=item.get("estimated_feasibility", "Medium"),
                    suggested_experiments=item.get("suggested_experiments", []),
                    created_at=datetime.now().isoformat(),
                    ai_confidence=item.get("ai_confidence", 0.6)
                )
                hypotheses.append(h)

        except json.JSONDecodeError:
            hypotheses = self._parse_text_response(response, research_question)

        if not hypotheses:
            hypotheses = self._generate_with_templates(research_question, "", 3)

        return hypotheses

    def _parse_text_response(self, response: str, research_question: str) -> List[ScientificHypothesis]:
        hypotheses = []
        lines = response.split('\n')

        current_h = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('#') or line.startswith('**'):
                if current_h and 'title' in current_h:
                    current_h['title'] = line.lstrip('#* ').strip()
            elif ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                if key == 'potential_evidence' or key == 'suggested_experiments':
                    current_h[key] = [v.strip() for v in value.split(',')]
                else:
                    current_h[key] = value

            if len(current_h) >= 5:
                h = ScientificHypothesis(
                    id=str(uuid.uuid4())[:8],
                    title=current_h.get('title', f"Hypothesis {len(hypotheses)+1}"),
                    description=current_h.get('description', ''),
                    rationale=current_h.get('rationale', ''),
                    predicted_mechanism=current_h.get('predicted_mechanism', ''),
                    potential_evidence=current_h.get('potential_evidence', []),
                    potential_counter_evidence=current_h.get('potential_counter_evidence', []),
                    expected_effect_direction=current_h.get('expected_effect_direction', 'Unknown'),
                    estimated_feasibility=current_h.get('estimated_feasibility', 'Medium'),
                    suggested_experiments=current_h.get('suggested_experiments', []),
                    created_at=datetime.now().isoformat(),
                    ai_confidence=0.5
                )
                hypotheses.append(h)
                current_h = {}

        return hypotheses

        for h_data in base_hypotheses:
            hypothesis = ScientificHypothesis(
                id=str(uuid.uuid4())[:8],
                title=h_data["title"],
                description=h_data["description"],
                rationale=h_data["rationale"],
                predicted_mechanism=h_data["predicted_mechanism"],
                potential_evidence=h_data["potential_evidence"],
                potential_counter_evidence=h_data["potential_counter_evidence"],
                expected_effect_direction=h_data["expected_effect_direction"],
                estimated_feasibility=h_data["estimated_feasibility"],
                suggested_experiments=h_data["suggested_experiments"],
                created_at=datetime.now().isoformat(),
                ai_confidence=h_data.get("ai_confidence", 0.5)
            )
            hypotheses.append(hypothesis)

        return hypotheses

    def _generate_with_templates(
        self,
        research_question: str,
        domain_knowledge: str,
        num_hypotheses: int
    ) -> List[Dict[str, Any]]:
        templates = [
            {
                "title": f"Modulating {research_question.split()[0]} via {research_question.split()[-1]} pathway",
                "description": f"A systematic exploration of how {research_question}",
                "rationale": f"Based on domain knowledge: {domain_knowledge[:200]}..." if domain_knowledge else "Derived from first principles reasoning",
                "predicted_mechanism": "Direct interaction between target molecules altering reaction kinetics",
                "potential_evidence": ["Measurable change in output metric", "Dose-response relationship", "Reversible effect"],
                "potential_counter_evidence": ["No observed effect at any dose", "Effect only in specific conditions"],
                "expected_effect_direction": "Positive correlation expected",
                "estimated_feasibility": "Medium",
                "suggested_experiments": [
                    "Controlled experiment with varying parameters",
                    "Statistical analysis of dose-response",
                    "Replication in different conditions"
                ],
                "ai_confidence": 0.6
            },
            {
                "title": f"Inverse relationship in {research_question}",
                "description": f"Hypothesis that increasing X leads to decreasing Y in {research_question}",
                "rationale": "Contradictory mechanisms suggest bidirectional control",
                "predicted_mechanism": "Negative feedback loop compensation",
                "potential_evidence": ["Inverse correlation", "Compensatory response", "Threshold effect"],
                "potential_counter_evidence": ["Positive correlation observed", "No threshold found"],
                "expected_effect_direction": "Negative correlation expected",
                "estimated_feasibility": "Medium",
                "suggested_experiments": [
                    "Correlation analysis across samples",
                    "Time-series observation",
                    "Intervention studies"
                ],
                "ai_confidence": 0.55
            },
            {
                "title": f"Synergistic effect in {research_question}",
                "description": f"Combined factors A and B may produce enhanced effect in {research_question}",
                "rationale": "Multi-factor interactions often yield emergent properties",
                "predicted_mechanism": "Synergistic amplification through positive feedback",
                "potential_evidence": ["Combined effect > sum of individual effects", "Optimal ratio exists"],
                "potential_counter_evidence": ["Additive only", "No interaction observed"],
                "expected_effect_direction": "Non-linear enhancement",
                "estimated_feasibility": "Low",
                "suggested_experiments": [
                    "Factorial design experiment",
                    "Dose matrix analysis",
                    "Interaction term analysis"
                ],
                "ai_confidence": 0.45
            },
            {
                "title": f"Threshold behavior in {research_question}",
                "description": f"Effect only appears above/below certain threshold in {research_question}",
                "rationale": "Many biological and physical systems exhibit threshold dynamics",
                "predicted_mechanism": "Phase transition or critical point behavior",
                "potential_evidence": ["Sharp transition point", "Hysteresis", "All-or-none response"],
                "potential_counter_evidence": ["Gradual linear response", "No threshold found"],
                "expected_effect_direction": "Step function response",
                "estimated_feasibility": "Medium",
                "suggested_experiments": [
                    "Fine-grained parameter sweep",
                    "Threshold identification protocol",
                    "Reversibility tests"
                ],
                "ai_confidence": 0.5
            },
            {
                "title": f"Novel mechanism for {research_question}",
                "description": f"An unexplored mechanism may explain observations in {research_question}",
                "rationale": "Current models may be incomplete; novel pathways deserve investigation",
                "predicted_mechanism": "Alternative pathway or hidden variable",
                "potential_evidence": ["Unexplained variance", "Anomalous patterns", "Model residuals"],
                "potential_counter_evidence": ["Current model fully explains", "No anomalies found"],
                "expected_effect_direction": "To be determined",
                "estimated_feasibility": "Low",
                "suggested_experiments": [
                    "Exploratory data analysis",
                    "Model residual analysis",
                    "Literature review for similar phenomena"
                ],
                "ai_confidence": 0.4
            }
        ]

        selected = templates[:num_hypotheses]
        for i, h in enumerate(selected):
            h["title"] = h["title"].replace("{research_question}", research_question)
            h["description"] = h["description"].replace("{research_question}", research_question)
            h["title"] = h["title"].replace(f"{{research_question.split()[-1]}}", research_question.split()[-1])
            h["title"] = h["title"].replace(f"{{research_question.split()[0]}}", research_question.split()[0])
            h["predicted_mechanism"] = f"Exploring {research_question}: {h['predicted_mechanism']}"
            h["suggested_experiments"] = [f"For {research_question}: {exp}" for exp in h["suggested_experiments"]]

        return selected

    def refine_hypothesis(
        self,
        hypothesis: ScientificHypothesis,
        feedback: str,
        iteration: int = 1
    ) -> ScientificHypothesis:
        refined = ScientificHypothesis(
            id=hypothesis.id,
            title=f"{hypothesis.title} (v{iteration})",
            description=hypothesis.description,
            rationale=hypothesis.rationale + f"\n\nRefined based on: {feedback}",
            predicted_mechanism=hypothesis.predicted_mechanism,
            potential_evidence=hypothesis.potential_evidence,
            potential_counter_evidence=hypothesis.potential_counter_evidence,
            expected_effect_direction=hypothesis.expected_effect_direction,
            estimated_feasibility=hypothesis.estimated_feasibility,
            suggested_experiments=hypothesis.suggested_experiments,
            created_at=datetime.now().isoformat(),
            ai_confidence=min(hypothesis.ai_confidence + 0.1, 0.95)
        )
        return refined

    def combine_hypotheses(
        self,
        hypotheses: List[ScientificHypothesis],
        common_theme: str
    ) -> ScientificHypothesis:
        combined = ScientificHypothesis(
            id=str(uuid.uuid4())[:8],
            title=f"Integrated Hypothesis: {common_theme}",
            description="\n\n".join([h.description for h in hypotheses]),
            rationale="Synthesized from multiple validated hypotheses",
            predicted_mechanism="Multi-factorial mechanism integrating previous insights",
            potential_evidence=list(set([e for h in hypotheses for e in h.potential_evidence])),
            potential_counter_evidence=list(set([e for h in hypotheses for e in h.potential_counter_evidence])),
            expected_effect_direction="Complex, see description",
            estimated_feasibility="Medium",
            suggested_experiments=list(set([e for h in hypotheses for e in h.suggested_experiments])),
            created_at=datetime.now().isoformat(),
            ai_confidence=sum(h.ai_confidence for h in hypotheses) / len(hypotheses) * 1.1
        )
        return combined
