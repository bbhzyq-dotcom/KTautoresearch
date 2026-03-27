#!/usr/bin/env python3
"""
KTautoresearch CLI - Command Line Interface
"""

import json
import os
from typing import List, Optional

from core import (
    HypothesisGenerator,
    ScientificHypothesis,
    HumanValidator,
    ValidationDecision,
    ExperimentExecutor,
    ExperimentDesign,
    Evaluator,
    EvaluationResult,
    EvaluationVerdict,
    HypothesisStatus
)


class KTAutoResearchCLI:
    def __init__(
        self,
        workspace_path: str = "./workspace",
        research_question: str = None
    ):
        self.workspace_path = workspace_path
        self.research_question = research_question
        self.hypothesis_generator = HypothesisGenerator()
        self.human_validator = HumanValidator(
            workspace_path=os.path.join(workspace_path, "validation")
        )
        self.experiment_executor = ExperimentExecutor(
            workspace_path=os.path.join(workspace_path, "experiments"),
            max_iterations=5,
            time_budget_per_experiment=60
        )
        self.evaluator = Evaluator(workspace_path=workspace_path)
        self.hypotheses: List[ScientificHypothesis] = []

    def setup_workspace(self):
        os.makedirs(os.path.join(self.workspace_path, "hypotheses"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_path, "experiments"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_path, "validation"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_path, "evaluation"), exist_ok=True)
        print(f"Workspace initialized at: {self.workspace_path}")

    def generate_hypotheses(
        self,
        num_hypotheses: int = 5,
        domain_knowledge: str = ""
    ) -> List[ScientificHypothesis]:
        if not self.research_question:
            print("Error: No research question set.")
            return []

        print("\n" + "="*60)
        print("PHASE 1: HYPOTHESIS GENERATION")
        print("="*60)
        print(f"Research Question: {self.research_question}")
        print(f"Generating {num_hypotheses} hypotheses...\n")

        hypotheses = self.hypothesis_generator.generate_hypotheses(
            research_question=self.research_question,
            domain_knowledge=domain_knowledge,
            num_hypotheses=num_hypotheses
        )

        self.hypotheses = hypotheses

        for h in hypotheses:
            self._save_hypothesis(h)
            print(f"Generated: [{h.id}] {h.title}")

        print(f"\n{len(hypotheses)} hypotheses generated and saved.")
        return hypotheses

    def validate_hypotheses(
        self,
        validator_name: str = "researcher"
    ) -> List[ScientificHypothesis]:
        if not self.hypotheses:
            self._load_hypotheses()

        print("\n" + "="*60)
        print("PHASE 2: HUMAN VALIDATION")
        print("="*60)

        worthy_hypotheses = []

        for h in self.hypotheses:
            print(f"\n[Validation] {h.title}")
            print(f"Description: {h.description[:100]}...")

            decision = self._get_validation_decision(h)

            if decision == ValidationDecision.WORTHY:
                self.human_validator.validate_hypothesis(
                    hypothesis=h,
                    validator_name=validator_name,
                    decision=ValidationDecision.WORTHY,
                    confidence_level=5,
                    reasoning="Human expert validation"
                )
                worthy_hypotheses.append(h)
                print("  -> Approved for experimentation")
            elif decision == ValidationDecision.UNWORTHY:
                self.human_validator.validate_hypothesis(
                    hypothesis=h,
                    validator_name=validator_name,
                    decision=ValidationDecision.UNWORTHY,
                    confidence_level=5,
                    reasoning="Human expert rejected"
                )
                print("  -> Rejected")
            else:
                print(f"  -> Deferred (decision: {decision.value})")

        print(f"\n{len(worthy_hypotheses)} hypotheses approved for experimentation.")
        return worthy_hypotheses

    def _get_validation_decision(self, hypothesis: ScientificHypothesis) -> ValidationDecision:
        print("\nValidation options:")
        print("  1. Worthy (approve for experiments)")
        print("  2. Unworthy (reject)")
        print("  3. Defer (skip for now)")

        while True:
            choice = input("\nEnter decision (1-3): ").strip()
            if choice in ['1', '2', '3']:
                break
            print("Invalid choice. Try again.")

        decision_map = {
            '1': ValidationDecision.WORTHY,
            '2': ValidationDecision.UNWORTHY,
            '3': ValidationDecision.DEFER
        }
        return decision_map[choice]

    def run_experiments(
        self,
        hypotheses: List[ScientificHypothesis] = None
    ):
        if hypotheses is None:
            if not self.hypotheses:
                self._load_hypotheses()
            hypotheses = [h for h in self.hypotheses
                        if h.status == HypothesisStatus.VALIDATED_WORTHY.value]

        if not hypotheses:
            print("No validated hypotheses to experiment on.")
            return []

        print("\n" + "="*60)
        print("PHASE 3: AUTONOMOUS EXPERIMENTATION")
        print("="*60)

        all_experiments = []

        for h in hypotheses:
            print(f"\n--- Experiment for: {h.title} ---")

            design = self.experiment_executor.design_experiment(h)
            print(f"Designed: {design.title}")

            experiment = self.experiment_executor.execute_experiment(
                hypothesis=h,
                experiment_design=design,
                iteration=1
            )

            all_experiments.append(experiment)

            print(f"Result: {experiment.actual_outcome}")
            print(f"Effect size: {experiment.results.get('effect_size', 'N/A')}")
            print(f"P-value: {experiment.results.get('p_value', 'N/A')}")

        print(f"\n{len(all_experiments)} experiments completed.")
        return all_experiments

    def evaluate_results(
        self,
        hypotheses: List[ScientificHypothesis] = None,
        experiments=None
    ):
        if hypotheses is None:
            self._load_hypotheses()
            hypotheses = self.hypotheses

        if experiments is None:
            experiments = []
            for h in hypotheses:
                exp_files = os.listdir(os.path.join(self.workspace_path, "experiments"))
                for f in exp_files:
                    if h.id in f:
                        with open(os.path.join(self.workspace_path, "experiments", f)) as fp:
                            experiments.append(json.load(fp))

        print("\n" + "="*60)
        print("PHASE 4: EVALUATION")
        print("="*60)

        evaluation_results = []

        for h in hypotheses:
            h_experiments = [e for e in experiments if isinstance(e, dict) and e.get('hypothesis_id') == h.id]
            if not h_experiments:
                continue

            from core.experiment_executor import Experiment
            exp_objects = [Experiment.from_dict(e) for e in h_experiments]

            result = self.evaluator.evaluate_hypothesis(h, exp_objects)
            evaluation_results.append(result)

            print(f"\n{result.hypothesis_title}")
            print(f"  Verdict: {result.verdict}")
            print(f"  Evidence: {result.evidence_strength}")
            print(f"  Effect Size: {result.effect_size}")
            print(f"  P-value: {result.p_value}")
            print(f"  Recommendation: {result.recommendation}")

        summary = self.evaluator.generate_summary_report(hypotheses, evaluation_results)
        print(f"\n{summary}")

        return evaluation_results

    def run_full_workflow(self, num_hypotheses: int = 5):
        self.setup_workspace()
        self.generate_hypotheses(num_hypotheses=num_hypotheses)
        worthy = self.validate_hypotheses()
        if worthy:
            self.run_experiments(worthy)
            self.evaluate_results(worthy)

    def run_demo(self):
        print("\n" + "="*60)
        print("KTautoresearch CLI Demo")
        print("="*60)

        self.research_question = "How does sleep quality affect cognitive performance?"
        print(f"\nDemo research question: {self.research_question}")

        self.setup_workspace()

        hypotheses = self.generate_hypotheses(num_hypotheses=3)

        worthy = []
        for h in hypotheses:
            self.human_validator.validate_hypothesis(
                hypothesis=h,
                validator_name="demo",
                decision=ValidationDecision.WORTHY,
                confidence_level=5,
                reasoning="Demo approval"
            )
            worthy.append(h)

        experiments = []
        for h in worthy:
            design = self.experiment_executor.design_experiment(h)
            exp = self.experiment_executor.execute_experiment(h, design, iteration=1)
            experiments.append(exp)

        self.evaluate_results(worthy, experiments)

        print("\n" + "="*60)
        print("Demo Complete!")
        print("="*60)

    def _save_hypothesis(self, hypothesis: ScientificHypothesis):
        filename = os.path.join(
            self.workspace_path,
            "hypotheses",
            f"hypothesis_{hypothesis.id}.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hypothesis.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_hypotheses(self):
        hypotheses_dir = os.path.join(self.workspace_path, "hypotheses")
        if not os.path.exists(hypotheses_dir):
            return

        self.hypotheses = []
        for filename in os.listdir(hypotheses_dir):
            if filename.endswith('.json'):
                with open(os.path.join(hypotheses_dir, filename)) as f:
                    self.hypotheses.append(ScientificHypothesis.from_dict(json.load(f)))
