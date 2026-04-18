# Generate Academic Paper

Generate a short academic paper (workshop / extended abstract style) about findings from the current repository's benchmark. The paper synthesizes code, results, lab notes, and development history into a coherent research narrative.

## Input

`$ARGUMENTS` — Optional instructions (e.g., "focus on adversarial noise findings", "target NeurIPS workshop format", "max 4 pages"). If empty, generate a complete paper covering all findings.

## Output Location

`paper/` directory in the current working directory. Creates:
- `paper/paper.md` — the paper in Markdown (primary output)
- `paper/figures/` — any generated figures or diagrams (ASCII/Mermaid/description)

## Workflow

### Step 1: Gather all evidence

Read these sources **in parallel** to build the complete picture:

**Code & data:**
- `src/generate.py` — how the dataset is constructed (passage generation, noise types, interleaving)
- `src/benchmark.py` — task definitions, evaluation metrics
- `src/analyze.py` — analysis methods and metrics
- `data/manifest.json` — dataset statistics
- `notebooks/kaggle_benchmark.ipynb` — the evaluation notebook (cell-by-cell)

**Results:**
- `results/` — all result directories. Read the `.run.json` files to extract actual numbers. Focus on the latest version (highest v-number).
- Parse results to build tables: accuracy by model × noise_type × noise_ratio, vigilance accuracy by model × task_type × position

**Documentation & context:**
- `geno-tools/labnotes/notes.md` — development history, bug discoveries, key findings, version evolution
- `geno-tools/labnotes/tasks.md` — what was planned vs completed
- `geno-tools/docs/` — existing documentation
- `CLAUDE.md` — project context and track description
- `README.md` — project overview

**Research context:**
- Walk up to 3 parent directories looking for `research/` folders
- Check for `../../research/attention/` and `../../research/concepts/` (paths from CLAUDE.md)
- Read any relevant research notes for theoretical grounding

**Git history:**
- `git log --oneline -30` — development trajectory and key milestones

### Step 2: Analyze and synthesize

Before writing, form a clear understanding of:

1. **The research question** — what gap does this benchmark fill?
2. **The methodology** — how was the benchmark constructed and why those choices?
3. **The results** — what did we actually find? Build precise tables from run data.
4. **The insights** — what do the results tell us about LLM attention?
5. **The limitations** — what doesn't the benchmark capture? What went wrong?
6. **The contribution** — what's novel here that others should know?

Compute any statistics not already in the notes:
- Effect sizes between model families
- Correlation between model size and adversarial threshold
- Statistical significance of key comparisons (if enough samples)

### Step 3: Write the paper

Write `paper/paper.md` following this structure:

```markdown
# [Paper Title]
[Short, specific, informative — not generic. Capture the key finding.]

## Abstract
[150-250 words. State the problem, method, key finding, and implication.
The abstract should make someone want to read the paper.]

## 1. Introduction
[Motivate the problem: why does LLM attention matter? What's missing from current benchmarks?
State the research question clearly. Preview the key finding.
Cite relevant prior work if found in research notes.
End with a paragraph summarizing contributions.]

## 2. Benchmark Design

### 2.1 Signal-in-Noise Titration (Selective Attention)
[Describe the task: passages, questions, noise types, noise ratios.
Explain WHY each design choice was made (not just what).
Include the interleaving strategy and its rationale.
Describe the three noise types and their purpose.]

### 2.2 Vigilance Decrement (Sustained Attention)
[Describe the task: repeated subtasks, oddball variant.
Explain what each measures and why it complements SIN.]

### 2.3 Dataset Construction
[How data was generated. Contamination resistance.
Key statistics: N items, noise ratio range, prompt sizes.
Answer verification method.]

### 2.4 Evaluation Setup
[Models tested (with rationale for selection).
Kaggle Benchmarks platform. Runtime constraints.
Any preprocessing (think-tag stripping, preamble handling).]

## 3. Results

### 3.1 Signal-in-Noise Results
[Main accuracy table: model × noise_type × noise_ratio.
Threshold table: the noise ratio where each model drops below 80%.
Key observation: adversarial noise as the sole discriminator.
The Gemma scaling ladder finding.]

### 3.2 Vigilance Results
[Accuracy by model × task_type.
Oddball detection results.
Notable anomalies and their explanations.]

### 3.3 Cross-Dimensional Analysis
[How selective and sustained attention correlate.
Do models that handle noise well also maintain vigilance?]

## 4. Discussion

### 4.1 Adversarial Noise as Cognitive Discriminator
[This is the paper's key insight. Develop it fully.
Why does adversarial noise separate models when other noise types don't?
What does this tell us about how LLMs process context?]

### 4.2 Scaling Laws for Attention
[The Gemma 1b→4b→12b→27b progression.
Does attention scale predictably with model size?]

### 4.3 Reasoning Models and Attention
[DeepSeek R1's behavior: chain-of-thought doesn't prevent adversarial distraction.
The preamble parsing discovery.]

### 4.4 Limitations
[Ceiling effect at frontier. Small sample sizes.
Vigilance task ambiguity (misspelling interpretation).
Platform constraints. What we'd do differently.]

## 5. Related Work
[Position relative to existing benchmarks (RULER, Needle-in-a-Haystack, etc.).
How this differs from long-context benchmarks.
Connection to cognitive science literature on attention.]

## 6. Conclusion
[Restate key findings. Emphasize the novel contribution.
Future directions: harder variants, more models, deeper analysis.]

## References
[Cite papers mentioned in research notes and related work.
Use numbered references.]

## Appendix
[Full results tables if they're too large for the main text.
Implementation details. Example prompts.]
```

### Step 4: Generate supporting materials

- Extract or generate key figures as descriptions in `paper/figures/`:
  - `sin_accuracy_curve.md` — description of the accuracy vs noise ratio plot
  - `threshold_table.md` — the attention threshold comparison
  - Any other visualizations that support the narrative

### Step 5: Review and polish

Re-read the paper and check:
- [ ] Every claim is supported by data from the results
- [ ] Tables contain actual numbers (not placeholders)
- [ ] The narrative flows logically from problem → method → results → insight
- [ ] The writing is concise and precise (no filler)
- [ ] Technical details are correct (noise ratios, model names, accuracy numbers)
- [ ] The paper honestly addresses limitations
- [ ] The contribution is clearly stated

### Step 6: Report

Print a summary:
```
Paper generated: paper/paper.md

Sections: [list]
Word count: ~N words
Key findings highlighted:
1. ...
2. ...
3. ...

Gaps/TODOs:
- [anything that needs user input or more data]
```

## Important Guidelines

- **Data-driven**: Every claim must trace back to actual run results. Parse the JSON files — don't rely solely on lab notes summaries.
- **Honest**: Report what we found, including surprises and failures. The bugs we found (think-tag parsing, preamble) are part of the story.
- **Specific**: Use exact numbers, model names, and noise ratios. "Several models" is worse than "5 of 8 models".
- **Novel framing**: Emphasize what's new — the adversarial noise finding, the separation of attention from reasoning, the scaling ladder.
- **Concise**: Aim for 3,000-5,000 words. Workshop paper length, not a full conference paper.
- **No fluff**: Every sentence should add information. Cut filler ruthlessly.
- **Version awareness**: Use the latest results (highest version number). Note if earlier versions revealed important methodological lessons.
