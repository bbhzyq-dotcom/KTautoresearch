# KTautoresearch - Scientific Hypothesis Generation Agent

This is an experiment to have the AI autonomously generate scientific hypotheses, have humans validate them, and then autonomously design and execute experiments to test validated hypotheses.

## The Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                         HUMAN                                    │
│  1. Define research question                                     │
│  2. Validate/filter AI-generated hypotheses                       │
│  3. Judge final results                                          │
└─────────────────────────────────────────────────────────────────┘
           │                            ▲
           ▼                            │
┌─────────────────────────────────────────────────────────────────┐
│                         AI AGENT                                 │
│  1. Generate multiple candidate hypotheses                       │
│  2. Design experiments for validated hypotheses                   │
│  3. Execute experiments autonomously                             │
│  4. Evaluate and interpret results                               │
└─────────────────────────────────────────────────────────────────┘
```

## Setup

To set up a new research session:

1. **Agree on a research question**: Work with the human to define the scientific question to investigate.
2. **Create a new branch**: `git checkout -b research/<topic>-<date>`
3. **Initialize workspace**: Create necessary directories
4. **Confirm and begin**: Confirm setup looks good

## Phase 1: Hypothesis Generation

### What you CAN do:
- Generate multiple candidate hypotheses (5-10) based on the research question
- Consider multiple angles: direct, inverse, synergistic, threshold-based, novel mechanisms
- Provide detailed rationale for each hypothesis
- Suggest specific experiments to test each hypothesis

### What you CANNOT do:
- Modify the core system files (`core/hypothesis_generator.py`, `core/experiment_executor.py`, `core/evaluator.py`)
- Install new packages or dependencies
- Skip human validation phase

### Output format:

Save each hypothesis to `workspace/hypotheses/hypothesis_<id>.json`:

```json
{
  "id": "unique-id",
  "title": "Hypothesis title",
  "description": "Detailed description",
  "rationale": "Why this hypothesis makes sense",
  "predicted_mechanism": "Expected mechanism",
  "potential_evidence": ["list of evidence to look for"],
  "potential_counter_evidence": ["list of counter-evidence"],
  "expected_effect_direction": "Positive/Negative/None",
  "estimated_feasibility": "High/Medium/Low",
  "suggested_experiments": ["experiment ideas"],
  "created_at": "ISO timestamp",
  "status": "pending_validation"
}
```

## Phase 2: Human Validation

After generating hypotheses, present them to the human for validation.

**Validation Options:**
1. **Worthy** - This hypothesis is worth exploring
2. **Unworthy** - This hypothesis is not promising
3. **Needs Refinement** - This hypothesis needs modification
4. **Defer** - Need more information

**For each hypothesis, the human will:**
- Review the scientific rationale
- Assess feasibility
- Consider potential impact
- Provide feedback

**Only "Worthy" hypotheses proceed to experimentation.**

## Phase 3: Autonomous Experimentation

For each validated hypothesis, the AI will:

1. **Design Experiment**: Create detailed experimental protocol
2. **Execute**: Run experiments (up to 10 iterations per hypothesis)
3. **Evaluate**: Assess results against hypothesis predictions
4. **Iterate**: Refine approach if results are inconclusive
5. **Report**: Generate comprehensive report

### Experiment Design Requirements:
- Define independent and dependent variables
- Specify control groups
- Estimate sample size requirements
- Outline statistical analysis plan
- Identify potential confounders

### Experiment Execution:
- Use fixed time budget per experiment (configurable)
- Track all parameters and outcomes
- Document any deviations from protocol
- Collect sufficient data for statistical analysis

### Evaluation Criteria:
- Effect size (Cohen's d)
- Statistical significance (p-value)
- Consistency across iterations
- Strength of evidence

## Logging and Results

### Results Format:
Save experiment results to `workspace/experiments/experiment_<id>.json`:

```json
{
  "id": "unique-id",
  "hypothesis_id": "ref-to-hypothesis",
  "status": "completed/failed",
  "results": {
    "effect_size": 0.45,
    "p_value": 0.023,
    "confidence_interval": {"lower": 0.12, "upper": 0.78}
  },
  "interpretation": "Hypothesis supported/not supported"
}
```

### Evaluation Summary:
After all experiments, generate summary report:
- Which hypotheses were supported
- Which were contradicted
- Recommendations for future research

## Experiment Loop

```
FOR each validated hypothesis:
    LOOP up to max_iterations:
        1. Design experiment based on hypothesis
        2. Execute experiment
        3. Evaluate results
        4. If conclusive: BREAK
        5. If not conclusive: Refine and retry
    Generate final report
```

## Ethical Considerations

- Always respect human validation decisions
- Report null results and negative findings
- Acknowledge limitations in conclusions
- Do not overstate evidence strength
- Recommend replication for surprising findings

## The Goal

Advance scientific understanding by:
1. Generating diverse hypothesis space
2. Using human intuition to filter promising directions
3. Executing rigorous experimental tests
4. Providing honest evaluation of evidence

This is a tool to augment human scientific reasoning, not replace it.
