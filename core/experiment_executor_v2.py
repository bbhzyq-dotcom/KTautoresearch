"""
Experiment Executor V2 - LLM-Driven Autonomous Experimentation
支持多种实验类型的统一执行框架
"""

import json
import os
import uuid
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from hypothesis_generator import ScientificHypothesis, HypothesisStatus


class ExperimentStatus(Enum):
    DESIGNING = "designing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentType(Enum):
    DATA_ANALYSIS = "data_analysis"
    LITERATURE_SEARCH = "literature_search"
    SURVEY_DESIGN = "survey_design"
    CASE_STUDY = "case_study"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    TEXT_GENERATION = "text_generation"
    CRITICAL_REVIEW = "critical_review"
    INTERVIEW_ANALYSIS = "interview_analysis"
    SIMULATION = "simulation"


@dataclass
class ExperimentConfig:
    experiment_type: str
    research_question: str
    hypothesis: str
    resources: List[str] = field(default_factory=list)
    time_budget: int = 300
    max_iterations: int = 3


@dataclass
class ExperimentResult:
    id: str
    hypothesis_id: str
    experiment_type: str
    status: str
    design: Dict[str, Any]
    execution_log: List[str]
    findings: List[str]
    evidence: List[Dict[str, Any]]
    assessment: Dict[str, Any]
    raw_output: str
    created_at: str
    completed_at: str
    duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentResult':
        return cls(**data)


class LLMExperimentExecutor:
    """
    LLM驱动的实验执行器
    支持多种研究类型的实验执行
    """

    def __init__(self, llm_provider=None, workspace_path: str = "./workspace"):
        self.llm_provider = llm_provider
        self.workspace_path = workspace_path
        self.experiment_history: List[ExperimentResult] = []

    def set_llm_provider(self, llm_provider):
        self.llm_provider = llm_provider

    def is_llm_available(self) -> bool:
        return self.llm_provider is not None and self.llm_provider.is_available()

    def design_experiment(
        self,
        hypothesis: ScientificHypothesis,
        experiment_type: ExperimentType = ExperimentType.LITERATURE_SEARCH
    ) -> Dict[str, Any]:
        """
        LLM 设计实验方案
        """
        if not self.is_llm_available():
            return self._default_design(hypothesis, experiment_type)

        system_prompt = """You are an expert research methodologist. Design a detailed experimental plan to test the given hypothesis.

Your output must be a JSON object with:
{
    "research_question": "Refined research question",
    "methodology": "Overall research approach",
    "steps": ["Step 1 description", "Step 2 description", ...],
    "resources_needed": ["Resource 1", "Resource 2", ...],
    "success_criteria": ["Criterion 1", "Criterion 2", ...],
    "potential_challenges": ["Challenge 1", "Challenge 2", ...],
    "expected_timeline": "Estimated time",
    "evaluation_framework": "How to evaluate the results"
}"""

        user_prompt = f"""Hypothesis to test: {hypothesis.title}

Description: {hypothesis.description}
Predicted mechanism: {hypothesis.predicted_mechanism}
Expected effect direction: {hypothesis.expected_effect_direction}

Research type: {experiment_type.value}

Please design a comprehensive experiment plan that:
1. Has clear, actionable steps
2. Uses available LLM capabilities (literature search, text analysis, etc.)
3. Produces tangible evidence
4. Can be evaluated objectively

Return ONLY valid JSON."""

        try:
            response = self.llm_provider.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.7,
                max_tokens=2048
            )

            return self._parse_design_response(response)

        except Exception as e:
            print(f"LLM design failed: {e}")
            return self._default_design(hypothesis, experiment_type)

    def _default_design(
        self,
        hypothesis: ScientificHypothesis,
        experiment_type: ExperimentType
    ) -> Dict[str, Any]:
        return {
            "research_question": hypothesis.description,
            "methodology": f"{experiment_type.value.replace('_', ' ').title()} approach",
            "steps": [
                f"Review relevant {experiment_type.value.replace('_', ' ')}",
                "Formulate findings based on evidence",
                "Evaluate hypothesis consistency"
            ],
            "resources_needed": ["Academic databases", "Research papers", "LLM analysis"],
            "success_criteria": ["Clear evidence found", "Logical consistency"],
            "potential_challenges": ["Limited evidence", "Ambiguous results"],
            "expected_timeline": "30 minutes",
            "evaluation_framework": "Qualitative assessment by LLM"
        }

    def _parse_design_response(self, response: str) -> Dict[str, Any]:
        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            return json.loads(json_str.strip())
        except:
            return {"methodology": "Analysis", "steps": ["Analyze", "Evaluate"], "raw_response": response}

    def execute_experiment(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        experiment_type: ExperimentType = ExperimentType.LITERATURE_SEARCH,
        iteration: int = 1,
        progress_callback: Optional[Callable] = None
    ) -> ExperimentResult:
        """
        执行实验 - 由 LLM 驱动
        """
        result_id = str(uuid.uuid4())[:8]
        started_at = datetime.now().isoformat()

        result = ExperimentResult(
            id=result_id,
            hypothesis_id=hypothesis.id,
            experiment_type=experiment_type.value,
            status=ExperimentStatus.RUNNING.value,
            design=design,
            execution_log=[],
            findings=[],
            evidence=[],
            assessment={},
            raw_output="",
            created_at=started_at,
            completed_at="",
            duration_seconds=0.0
        )

        self._log(result, f"Starting experiment {iteration} for hypothesis: {hypothesis.title}")

        if progress_callback:
            progress_callback("Initializing...", 10)

        try:
            if experiment_type == ExperimentType.LITERATURE_SEARCH:
                raw_output = self._execute_literature_search(hypothesis, design, result, progress_callback)
            elif experiment_type == ExperimentType.CASE_STUDY:
                raw_output = self._execute_case_study(hypothesis, design, result, progress_callback)
            elif experiment_type == ExperimentType.COMPARATIVE_ANALYSIS:
                raw_output = self._execute_comparative_analysis(hypothesis, design, result, progress_callback)
            elif experiment_type == ExperimentType.CRITICAL_REVIEW:
                raw_output = self._execute_critical_review(hypothesis, design, result, progress_callback)
            elif experiment_type == ExperimentType.TEXT_GENERATION:
                raw_output = self._execute_text_generation(hypothesis, design, result, progress_callback)
            elif experiment_type == ExperimentType.SURVEY_DESIGN:
                raw_output = self._execute_survey_design(hypothesis, design, result, progress_callback)
            elif experiment_type == ExperimentType.INTERVIEW_ANALYSIS:
                raw_output = self._execute_interview_analysis(hypothesis, design, result, progress_callback)
            else:
                raw_output = self._execute_generic_analysis(hypothesis, design, result, progress_callback)

            result.raw_output = raw_output

            if progress_callback:
                progress_callback("Analyzing findings...", 80)

            result.assessment = self._assess_results(hypothesis, raw_output, result.findings)

            if progress_callback:
                progress_callback("Finalizing...", 90)

            result.status = ExperimentStatus.COMPLETED.value
            self._log(result, "Experiment completed successfully")

        except Exception as e:
            result.status = ExperimentStatus.FAILED.value
            result.assessment = {"error": str(e)}
            self._log(result, f"Experiment failed: {e}")

        completed_at = datetime.now().isoformat()
        result.completed_at = completed_at
        result.duration_seconds = (
            datetime.fromisoformat(completed_at) -
            datetime.fromisoformat(started_at)
        ).total_seconds()

        self._save_result(result)
        self.experiment_history.append(result)

        return result

    def _log(self, result: ExperimentResult, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        result.execution_log.append(log_entry)
        print(log_entry)

    def _execute_literature_search(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        result: ExperimentResult,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        执行文献搜索实验
        """
        if not self.is_llm_available():
            return self._simulate_literature_search(hypothesis, result)

        self._log(result, "Executing literature search...")

        system_prompt = """You are an expert academic researcher conducting a literature review.

Your task is to:
1. Identify key concepts and search terms related to the hypothesis
2. Synthesize findings from multiple perspectives
3. Provide evidence supporting or refuting the hypothesis
4. Identify gaps in current research

Be thorough, critical, and cite relevant theories and studies."""

        user_prompt = f"""Hypothesis: {hypothesis.title}
Description: {hypothesis.description}
Predicted mechanism: {hypothesis.predicted_mechanism}

Research methodology: {design.get('methodology', 'Literature review')}

Please conduct a comprehensive literature review that:
1. Summarizes existing research on this topic
2. Provides key evidence (supporting or refuting)
3. Identifies 3-5 major findings
4. Notes any contradictions or gaps
5. Assesses the overall strength of evidence

Format your response as a detailed research summary with clear sections."""

        if progress_callback:
            progress_callback("Searching literature...", 30)

        response = self.llm_provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=4096
        )

        self._log(result, f"Generated {len(response)} characters of analysis")

        findings = self._extract_findings_from_text(response, hypothesis)
        result.findings = findings

        evidence = [
            {"type": "literature_review", "content": response[:500] + "...", "source": "LLM synthesis"},
            {"type": "key_finding", "content": findings[0] if findings else "See full analysis"}
        ]
        result.evidence = evidence

        return response

    def _execute_case_study(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        result: ExperimentResult,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        执行案例分析实验
        """
        if not self.is_llm_available():
            return self._simulate_case_study(hypothesis, result)

        self._log(result, "Executing case study analysis...")

        system_prompt = """You are an expert case study analyst. Analyze the given case/phenomenon to test the hypothesis.

Your analysis should:
1. Present the case with sufficient context
2. Analyze relevant variables and their relationships
3. Draw connections to the hypothesis
4. Provide nuanced conclusions

Be thorough, objective, and analytically rigorous."""

        user_prompt = f"""Hypothesis to test: {hypothesis.title}
Description: {hypothesis.description}

Please create a detailed case study that:
1. Describes a relevant real-world case or scenario
2. Analyzes the case in relation to the hypothesis
3. Provides specific examples and evidence
4. Draws conclusions about the hypothesis

Make the case study detailed and informative (800-1200 words)."""

        if progress_callback:
            progress_callback("Analyzing case...", 40)

        response = self.llm_provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=2048
        )

        findings = self._extract_findings_from_text(response, hypothesis)
        result.findings = findings

        result.evidence = [
            {"type": "case_description", "content": response[:800] + "..."},
            {"type": "analysis", "content": findings[0] if findings else "See full analysis"}
        ]

        return response

    def _execute_comparative_analysis(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        result: ExperimentResult,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        执行比较分析实验
        """
        if not self.is_llm_available():
            return self._simulate_comparative_analysis(hypothesis, result)

        self._log(result, "Executing comparative analysis...")

        system_prompt = """You are an expert comparative analyst. Compare and contrast different approaches, theories, or cases to test the hypothesis.

Your comparative analysis should:
1. Define clear comparison dimensions
2. Present each approach/case fairly
3. Draw meaningful comparisons to the hypothesis
4. Identify patterns and differences

Be analytical and objective."""

        user_prompt = f"""Hypothesis: {hypothesis.title}
Description: {hypothesis.description}

Conduct a comparative analysis that:
1. Compares 2-3 different approaches, theories, or cases
2. Analyzes each in relation to the hypothesis
3. Identifies which best supports or explains the hypothesis
4. Provides specific comparison points

Format as a structured comparative essay (600-1000 words)."""

        if progress_callback:
            progress_callback("Comparing approaches...", 40)

        response = self.llm_provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=2048
        )

        findings = self._extract_findings_from_text(response, hypothesis)
        result.findings = findings

        result.evidence = [
            {"type": "comparison", "content": response[:600] + "...", "dimensions": ["approach", "theory", "case"]}
        ]

        return response

    def _execute_critical_review(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        result: ExperimentResult,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        执行批判性评论实验
        """
        if not self.is_llm_available():
            return self._simulate_critical_review(hypothesis, result)

        self._log(result, "Executing critical review...")

        system_prompt = """You are an expert critical thinker and academic reviewer.

Your task is to:
1. Critically examine the hypothesis from multiple angles
2. Identify strengths and weaknesses
3. Consider counterarguments and alternative perspectives
4. Evaluate the logical consistency and evidence

Be fair, rigorous, and intellectually honest."""

        user_prompt = f"""Hypothesis: {hypothesis.title}
Description: {hypothesis.description}
Rationale: {hypothesis.rationale}

Please provide a critical review that:
1. Evaluates the hypothesis strengths
2. Identifies potential weaknesses or limitations
3. Presents counterarguments
4. Assesses overall validity (600-1000 words)"""

        if progress_callback:
            progress_callback("Critically reviewing...", 40)

        response = self.llm_provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=2048
        )

        findings = self._extract_findings_from_text(response, hypothesis)
        result.findings = findings

        result.evidence = [
            {"type": "critical_review", "content": response[:600] + "..."}
        ]

        return response

    def _execute_text_generation(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        result: ExperimentResult,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        执行文本生成实验 (如散文、故事、诗歌)
        """
        if not self.is_llm_available():
            return self._simulate_text_generation(hypothesis, result)

        self._log(result, "Executing creative text generation...")

        system_prompt = """You are a creative writer. Write a piece of text (essay, story, poem, etc.) that explores and illustrates the hypothesis.

Your writing should:
1. Be creative and engaging
2. Illustrate the hypothesis concepts through narrative or argument
3. Provide insights related to the hypothesis theme
4. Be of high literary quality"""

        user_prompt = f"""Hypothesis: {hypothesis.title}
Description: {hypothesis.description}
Theme: {hypothesis.predicted_mechanism}

Write a creative piece (essay, story, or narrative) that explores this hypothesis.

Requirements:
1. Length: 800-1200 words
2. Must engage with the hypothesis theme
3. Should provide insight or illustration of the hypothesis
4. Literary quality required"""

        if progress_callback:
            progress_callback("Generating creative text...", 40)

        response = self.llm_provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.8,
            max_tokens=2048
        )

        findings = [
            f"Creative exploration of: {hypothesis.title}",
            f"Theme: {hypothesis.predicted_mechanism}",
            "Narrative successfully illustrates hypothesis concepts"
        ]
        result.findings = findings

        result.evidence = [
            {"type": "creative_text", "content": response[:500] + "...", "word_count": len(response.split())}
        ]

        return response

    def _execute_survey_design(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        result: ExperimentResult,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        执行问卷设计实验
        """
        if not self.is_llm_available():
            return self._simulate_survey_design(hypothesis, result)

        self._log(result, "Designing survey instrument...")

        system_prompt = """You are an expert research methodologist specializing in survey design.

Your task is to design a survey questionnaire that can empirically test the hypothesis.

The survey should:
1. Have clear, measurable variables
2. Use appropriate question types (Likert, multiple choice, open-ended)
3. Be logically organized
4. Have proper scales and measurements
5. Be unbiased and ethical"""

        user_prompt = f"""Hypothesis: {hypothesis.title}
Description: {hypothesis.description}
Expected effect: {hypothesis.expected_effect_direction}

Design a comprehensive survey questionnaire (10-15 questions) that:
1. Covers all key aspects of testing this hypothesis
2. Uses appropriate question formats
3. Includes demographic questions where relevant
4. Has clear instructions
5. Is ready for pilot testing

Format as a structured questionnaire with question numbers and scales."""

        if progress_callback:
            progress_callback("Designing survey...", 40)

        response = self.llm_provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=2048
        )

        findings = [
            f"Survey designed for: {hypothesis.title}",
            "10-15 questions covering key variables",
            "Ready for pilot testing and validation"
        ]
        result.findings = findings

        result.evidence = [
            {"type": "survey", "content": response[:500] + "...", "questions": "10-15"}
        ]

        return response

    def _execute_interview_analysis(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        result: ExperimentResult,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        执行访谈分析实验
        """
        if not self.is_llm_available():
            return self._simulate_interview_analysis(hypothesis, result)

        self._log(result, "Designing interview protocol...")

        system_prompt = """You are an expert qualitative researcher specializing in interview-based studies.

Your task is to:
1. Design an interview protocol to test the hypothesis
2. Create semi-structured interview questions
3. Provide probing strategies
4. Suggest analysis approaches (thematic analysis, etc.)"""

        user_prompt = f"""Hypothesis: {hypothesis.title}
Description: {hypothesis.description}

Design an interview protocol (8-12 questions) that:
1. Explores the phenomenon related to the hypothesis
2. Uses semi-structured format
3. Includes probing questions
4. Covers all relevant dimensions
5. Is ethical and respectful

Format as an organized interview guide."""

        if progress_callback:
            progress_callback("Designing interview protocol...", 40)

        response = self.llm_provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=2048
        )

        findings = [
            f"Interview protocol for: {hypothesis.title}",
            "Semi-structured format with probing strategies",
            "Ready for qualitative validation"
        ]
        result.findings = findings

        result.evidence = [
            {"type": "interview_guide", "content": response[:500] + "...", "questions": "8-12"}
        ]

        return response

    def _execute_generic_analysis(
        self,
        hypothesis: ScientificHypothesis,
        design: Dict[str, Any],
        result: ExperimentResult,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        执行通用分析实验
        """
        if not self.is_llm_available():
            return self._simulate_generic_analysis(hypothesis, result)

        self._log(result, "Executing generic analysis...")

        system_prompt = """You are an expert research analyst. Analyze and provide insights related to the hypothesis.

Be thorough, evidence-based, and analytical."""

        user_prompt = f"""Hypothesis: {hypothesis.title}
Description: {hypothesis.description}
Predicted mechanism: {hypothesis.predicted_mechanism}

Provide a comprehensive analysis that:
1. Explores the hypothesis from multiple angles
2. Provides evidence and reasoning
3. Draws meaningful conclusions
4. Identifies implications (600-1000 words)"""

        if progress_callback:
            progress_callback("Analyzing...", 40)

        response = self.llm_provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=2048
        )

        findings = self._extract_findings_from_text(response, hypothesis)
        result.findings = findings

        result.evidence = [{"type": "analysis", "content": response[:400] + "..."}]

        return response

    def _assess_results(
        self,
        hypothesis: ScientificHypothesis,
        raw_output: str,
        findings: List[str]
    ) -> Dict[str, Any]:
        """
        LLM 评估实验结果
        """
        if not self.is_llm_available():
            return self._default_assessment(hypothesis, findings)

        system_prompt = """You are an expert research evaluator. Assess the experimental results against the original hypothesis.

Evaluate:
1. SUPPORT: Does the evidence support the hypothesis?
2. CONTRADICT: Does the evidence contradict the hypothesis?
3. INCONCLUSIVE: Is the evidence mixed or insufficient?
4. NOVEL: Does it reveal new insights?

Provide a rigorous, objective assessment."""

        user_prompt = f"""Hypothesis: {hypothesis.title}
Description: {hypothesis.description}
Expected effect: {hypothesis.expected_effect_direction}

Experimental findings:
{chr(10).join(f"- {f}" for f in findings[:5])}

Raw output excerpt:
{raw_output[:1000]}

Please assess:
1. Overall verdict (SUPPORT / CONTRADICT / INCONCLUSIVE / NOVEL_INSIGHT)
2. Evidence strength (Strong / Moderate / Weak)
3. Key insights discovered
4. Limitations of the experiment
5. Recommendations for future research

Return as JSON:
{{"verdict": "...", "evidence_strength": "...", "key_insights": [...], "limitations": [...], "recommendations": [...]}}"""

        try:
            response = self.llm_provider.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.5,
                max_tokens=1024
            )

            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            assessment = json.loads(json_str.strip())
            return assessment

        except Exception as e:
            return self._default_assessment(hypothesis, findings)

    def _extract_findings_from_text(
        self,
        text: str,
        hypothesis: ScientificHypothesis
    ) -> List[str]:
        """从文本中提取关键发现"""
        findings = []

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                findings.append(line.lstrip('-•* '))
            elif any(keyword in line.lower() for keyword in ['finding', 'conclusion', 'key', 'result', 'evidence']):
                findings.append(line)

        if not findings:
            sentences = text.split('. ')
            for sent in sentences[:5]:
                if len(sent) > 50:
                    findings.append(sent.strip())

        return findings[:5]

    def _default_assessment(
        self,
        hypothesis: ScientificHypothesis,
        findings: List[str]
    ) -> Dict[str, Any]:
        """默认评估（无 LLM 时）"""
        return {
            "verdict": "INCONCLUSIVE",
            "evidence_strength": "Cannot assess without LLM",
            "key_insights": findings[:3] if findings else ["No findings extracted"],
            "limitations": ["LLM not configured for detailed assessment"],
            "recommendations": ["Configure LLM for full assessment capabilities"]
        }

    def _save_result(self, result: ExperimentResult):
        os.makedirs(os.path.join(self.workspace_path, "experiments"), exist_ok=True)
        filename = os.path.join(
            self.workspace_path,
            "experiments",
            f"experiment_{result.id}.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    def autonomous_experiment_loop(
        self,
        hypothesis: ScientificHypothesis,
        experiment_type: ExperimentType = ExperimentType.LITERATURE_SEARCH,
        max_iterations: int = 3
    ) -> List[ExperimentResult]:
        """
        自主实验循环
        """
        print(f"\n{'='*60}")
        print(f"AUTONOMOUS EXPERIMENT LOOP")
        print(f"{'='*60}")
        print(f"Hypothesis: {hypothesis.title}")
        print(f"Experiment type: {experiment_type.value}")
        print(f"Max iterations: {max_iterations}")
        print()

        if not self.is_llm_available():
            print("WARNING: No LLM configured. Using simulation mode.")
            print("Results will be limited. Configure LLM for real experiments.")

        results = []

        for iteration in range(1, max_iterations + 1):
            print(f"\n--- Iteration {iteration}/{max_iterations} ---")

            design = self.design_experiment(hypothesis, experiment_type)
            print(f"Designed: {design.get('methodology', 'Unknown')}")
            print(f"Steps: {len(design.get('steps', []))} steps planned")

            def progress_callback(msg, pct):
                print(f"  [{pct:3d}%] {msg}")

            result = self.execute_experiment(
                hypothesis=hypothesis,
                design=design,
                experiment_type=experiment_type,
                iteration=iteration,
                progress_callback=progress_callback
            )

            results.append(result)

            print(f"\nResults:")
            print(f"  Status: {result.status}")
            print(f"  Verdict: {result.assessment.get('verdict', 'N/A')}")
            print(f"  Evidence: {result.assessment.get('evidence_strength', 'N/A')}")

            if result.assessment.get('verdict') == 'SUPPORT':
                print(f"\nHypothesis SUPPORTED! Stopping early.")
                break

        return results

    # ===== Simulation methods (when no LLM) =====

    def _simulate_literature_search(self, hypothesis, result):
        findings = [
            f"Literature review for: {hypothesis.title}",
            "Simulated evidence from academic sources",
            "Analysis suggests further investigation needed"
        ]
        result.findings = findings
        return f"Literature search simulation for: {hypothesis.description[:200]}..."

    def _simulate_case_study(self, hypothesis, result):
        findings = [f"Case study exploring: {hypothesis.title}"]
        result.findings = findings
        return f"Case study simulation - configure LLM for real analysis"

    def _simulate_comparative_analysis(self, hypothesis, result):
        findings = [f"Comparative analysis of: {hypothesis.title}"]
        result.findings = findings
        return f"Comparative analysis simulation - configure LLM for real analysis"

    def _simulate_critical_review(self, hypothesis, result):
        findings = [f"Critical review of: {hypothesis.title}"]
        result.findings = findings
        return f"Critical review simulation - configure LLM for real analysis"

    def _simulate_text_generation(self, hypothesis, result):
        findings = [f"Creative exploration of: {hypothesis.title}"]
        result.findings = findings
        return f"Text generation simulation - configure LLM for real creative writing"

    def _simulate_survey_design(self, hypothesis, result):
        findings = [f"Survey design for: {hypothesis.title}"]
        result.findings = findings
        return f"Survey design simulation - configure LLM for real instrument design"

    def _simulate_interview_analysis(self, hypothesis, result):
        findings = [f"Interview protocol for: {hypothesis.title}"]
        result.findings = findings
        return f"Interview analysis simulation - configure LLM for real protocol design"

    def _simulate_generic_analysis(self, hypothesis, result):
        findings = [f"Analysis of: {hypothesis.title}"]
        result.findings = findings
        return f"Generic analysis simulation - configure LLM for real analysis"
