# KTautoresearch

**AI-Driven Scientific Hypothesis Generation and Autonomous Experimentation**

Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch), this project extends the autonomous experimentation paradigm to scientific hypothesis generation. The system uses AI to generate hypotheses, incorporates human validation for filtering, and then autonomously designs and executes experiments to test validated hypotheses.

## The Core Idea

```
Human defines the question
       │
       ▼
AI generates multiple hypotheses
       │
       ▼
Human filters/validates (optional step)
       │
       ▼
AI autonomously designs & runs experiments
       │
       ▼
AI evaluates results
       │
       ▼
Human judges final conclusions
```

This paradigm combines:
- **Human creativity** for defining research directions
- **AI's ability** to systematically explore the hypothesis space
- **Human judgment** for filtering promising directions
- **AI's persistence** for executing rigorous experiments

## Quick Start

### GUI Mode (Recommended)

```bash
python main.py --gui
```

The GUI provides a visual interface with:
- Research question input
- Hypothesis generation and browsing
- Human validation interface
- Real-time experiment execution
- Evaluation results display

### CLI Mode

```bash
# Run demo
python main.py --demo

# Full workflow with a research question
python main.py --question "How does sleep quality affect cognitive performance?" --all

# Generate hypotheses only
python main.py -q "Effect of caffeine on attention" --generate
```

## Architecture

```
KTautoresearch/
├── core/
│   ├── hypothesis_generator.py   # AI generates scientific hypotheses
│   ├── human_validator.py        # Human validation interface
│   ├── experiment_executor.py    # AI executes experiments
│   ├── evaluator.py              # AI evaluates results
│   └── llm_provider.py           # LLM API interface (OpenAI/Ollama/etc)
├── workspace/                    # Working directory
│   ├── hypotheses/               # Generated hypotheses
│   ├── experiments/              # Experiment results
│   ├── validation/               # Validation records
│   └── evaluation/               # Evaluation reports
├── program.md                    # AI agent instructions
├── main.py                       # Entry point (launches GUI or CLI)
├── gui.py                        # Graphical User Interface
├── ktcli.py                      # Command Line Interface
├── llm_config.py                 # LLM Configuration Dialog
└── llm_config.json               # LLM API configuration
```
```
```

## Workflow Phases

### Phase 1: Hypothesis Generation

The AI generates multiple candidate hypotheses based on a research question:

- **Direct effect hypotheses**: A leads to B
- **Inverse hypotheses**: Increasing A leads to decreasing B
- **Synergistic hypotheses**: Combined A+B produces enhanced effect
- **Threshold hypotheses**: Effect only appears above/below certain threshold
- **Novel mechanism hypotheses**: Unexplored pathways

Each hypothesis includes:
- Title and description
- Scientific rationale
- Predicted mechanism
- Potential evidence and counter-evidence
- Suggested experiments

### Phase 2: Human Validation

Humans review and filter the generated hypotheses:

| Decision | Meaning |
|----------|---------|
| **Worthy** | Proceed to experimentation |
| **Unworthy** | Discard hypothesis |
| **Needs Refinement** | AI should revise |
| **Defer** | Skip for now |

This step ensures human oversight and prevents wasted resources on low-quality hypotheses.

### Phase 3: Autonomous Experimentation

For validated hypotheses, the AI:

1. Designs detailed experiments (variables, controls, sample size)
2. Executes experiments with configurable time budget
3. Collects and analyzes data
4. Iterates if results are inconclusive
5. Generates comprehensive reports

### Phase 4: Evaluation

The AI evaluates evidence for each hypothesis:

- Statistical significance (p-value)
- Effect size (Cohen's d)
- Consistency across iterations
- Strength of evidence classification

Final verdicts:
- **Supported**: Strong evidence for hypothesis
- **Partially Supported**: Some evidence found
- **Not Supported**: Insufficient evidence
- **Contradicted**: Evidence against hypothesis
- **Inconclusive**: More data needed

## LLM Configuration (Optional)

The system can use LLM APIs for more creative hypothesis generation. By default, it uses template-based generation.

### Supported Providers

| Provider | Type | Example API URL |
|----------|------|----------------|
| Ollama | Local | `http://localhost:11434/v1` |
| LM Studio | Local | `http://localhost:1234/v1` |
| OpenAI | Cloud | `https://api.openai.com/v1` |
| Groq | Cloud | `https://api.groq.com/openai/v1` |
| Together AI | Cloud | `https://api.together.ai/v1` |
| Anthropic | Cloud | `https://api.anthropic.com/v1` |
| Custom | Other | Any OpenAI-compatible API |

### Configuration (GUI)

1. Click "LLM Config" button in the header
2. Select your provider
3. Enter API URL, Key (if required), and model name
4. Click "Test Connection" to verify
5. Click "Save"

### Configuration (Environment Variables)

```bash
export LLM_PROVIDER=ollama
export LLM_API_BASE=http://localhost:11434/v1
export LLM_MODEL=llama3
```

### Configuration (File)

Save to `llm_config.json`:

```json
{
  "provider": "ollama",
  "api_base": "http://localhost:11434/v1",
  "api_key": "not-needed",
  "model": "llama3",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

## Extending the System

### Adding New Experiment Types

Extend `ExperimentType` in `core/experiment_executor.py`:

```python
class ExperimentType(Enum):
    SIMULATION = "simulation"
    LITERATURE_SEARCH = "literature_search"
    DATA_ANALYSIS = "data_analysis"
    COMPUTATIONAL = "computational"
    EMPIRICAL = "empirical"
    THEORETICAL = "theoretical"
    # Add your custom type
    YOUR_CUSTOM_TYPE = "your_custom_type"
```

### Custom Hypothesis Templates

Modify `_generate_structured_hypotheses()` in `core/hypothesis_generator.py` to add domain-specific hypothesis templates.

### Integration with Real Data Sources

Replace simulated data generation in `_generate_simulated_data()` with actual data fetching from:
- Scientific databases (PubMed, arXiv)
- Experimental equipment APIs
- Simulation engines
- Computational chemistry packages

## Example Applications

### Materials Science

Research question: "What parameters optimize lithium-ion battery capacity?"

- Generate hypotheses about material combinations
- Validate based on feasibility
- Execute computational simulations
- Identify optimal compositions

### Drug Discovery

Research question: "What molecular modifications enhance drug efficacy?"

- Generate hypotheses about structure-activity relationships
- Validate based on synthesizability
- Execute molecular docking studies
- Identify promising candidates

### Ecology

Research question: "What environmental factors affect biodiversity?"

- Generate hypotheses about ecological relationships
- Validate based on measurability
- Execute analysis on existing datasets
- Identify key drivers

### Psychology

Research question: "What cognitive factors predict learning outcomes?"

- Generate hypotheses about cognitive mechanisms
- Validate based on ethical considerations
- Execute behavioral experiments
- Identify predictive factors

## Design Principles

1. **Human-in-the-loop**: Humans define questions and validate directions
2. **Autonomous execution**: AI handles repetitive experimental work
3. **Rigorous evaluation**: Statistical standards for evidence
4. **Transparent reporting**: Clear documentation of methods and limitations
5. **Iterative refinement**: Loop until conclusive or resources exhausted

## Related Work

- [Karpathy/autoresearch](https://github.com/karpathy/autoresearch) - The inspiration for this project
- [AlphaFold](https://www.deepmind.com/research/highlighted/alphafold) - AI-driven scientific discovery
- [Chemprop](https://github.com/chemprop/chemprop) - Message passing neural networks for molecular property prediction

## License

MIT License

## Contributing

Contributions welcome! Key areas for improvement:

- Real data source integrations
- Additional hypothesis templates
- Advanced statistical methods
- Visualization tools
- Report generation enhancements
