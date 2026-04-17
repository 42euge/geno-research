# Deep Research — Multi-Resolution Knowledge Graph

Build a comprehensive, multi-resolution Obsidian knowledge graph for any research topic. Creates depth-linked notes (L0→L3), reference docs, and a navigable top-down canvas.

## Input

`$ARGUMENTS` — Either a research brief for a fresh run, OR empty/short to trigger the interactive menu.

### Interactive Menu (when no detailed brief is provided)

If `$ARGUMENTS` is empty or short (e.g., just a track name):

**Step 0 — Repo detection:** Check if the current directory is a git repo with `geno-tools/`. If so, read `CLAUDE.md` and `README.md` to extract the project's track and scope. Pre-fill the track selection and inform the user: "Detected repo: {repo name} — {track} track. Research will be saved to `geno-tools/docs/research/`."

Then use `AskUserQuestion` to present an interactive selection menu. Ask TWO questions in a single call:

**Question 1** — Research type (header: "Research"):
- **Benchmarks** — "Discover and catalog public benchmarks from Kaggle, arXiv, HuggingFace"
- **Literature** — "Find and summarize papers (2024-2026), download PDFs, create notes"
- **Track Research** — "Deep-dive into a track: new ideas, gaps, update analysis.md"
- **Full Research** — "Run the complete workflow (Steps 1-11) across all sub-areas"

**Question 2** — Track selection (header: "Track", multiSelect: true):
- **Attention** — "Can the model focus on relevant info and ignore distractions?"
- **Learning** — "Can the model acquire/apply new knowledge, not just recall training data?"
- **Metacognition** — "Does the model know what it knows and what it doesn't?"
- **Executive Functions** — "Can the model plan, inhibit impulses, adapt flexibly?"

Note: Since AskUserQuestion supports max 4 options, Social Cognition is available via the "Other" escape hatch that AskUserQuestion automatically provides. If a track was auto-detected from the repo, pre-select it as the default.

Wait for the user's selections before proceeding. Then execute only the relevant steps for the chosen research type and track(s).

### Direct Brief Mode

When `$ARGUMENTS` contains a detailed research brief, skip the menu and run the full workflow (Steps 1-11):
- A topic: `"Reinforcement learning from human feedback"`
- A comparison: `"Compare transformer architectures for long-context"`
- A project with sub-areas: `"AGI benchmarks across 5 cognitive tracks"`

## Output Location

**Repo-aware:** Before creating any output, check if the current working directory is a git repo with a `geno-tools/` directory. If so:
- All output goes into `geno-tools/docs/research/` instead of `research/`
- Read `CLAUDE.md` and `README.md` from the repo root to auto-detect the project context (track, benchmark name, what it measures)
- Use that context to scope the research — e.g., in an attention benchmark repo, default to researching the Attention track and related benchmarks/papers

**Standalone mode:** If there is no `geno-tools/` directory, fall back to creating a `research/` directory in the current working directory (original behavior).

The rest of the folder structure (`literature/`, `benchmarks/`, `tracks/`, canvas, etc.) is created inside whichever root directory is selected.

## Layer System

Every note lives at exactly ONE layer:

| Layer | Tag | Content | Max Length |
|-------|-----|---------|-----------|
| L0 | `#L0` | Intuition — why it matters, no details | 150 words |
| L1 | `#L1` | Concepts — definitions, structure, key papers | 200-300 words |
| L2 | `#L2` | Specifics — algorithms, benchmarks, approaches | 200-300 words |
| L3 | `#L3` | Implementation — code patterns, math, scoring | 200-300 words |

## Note Format

Every note MUST follow this structure:

```markdown
# Title

#topic-tag #layer-tag #optional-tags

1-2 sentence summary.

## Body content
(varies by layer)

## Links
- Up: [[Parent Note]]
- Down: [[Child 1]], [[Child 2]]
- Related: [[Cross-link 1]], [[Cross-link 2]]
```

Rules:
- Max 200-300 words per note (split if longer)
- Use `[[wikilinks]]` aggressively — every concept that has its own note gets linked
- Up/Down creates the tree hierarchy; Related creates the graph cross-links
- Tags enable filtering: topic tags + layer tags + quality tags like `#high-discrimination`

## Workflow

### Step 1: Analyze the research brief

Parse `$ARGUMENTS` to identify:
- **Sub-areas** — the 3-7 major branches to investigate (these become track-level folders)
- **Key questions** — what each sub-area needs to answer
- **Cross-cutting themes** — themes that span multiple sub-areas (noted in track notes via Related links)

### Step 2: Create folder structure

Determine the output root:
- If `geno-tools/` exists in the repo → `RESEARCH_ROOT = geno-tools/docs/research/`
- Otherwise → `RESEARCH_ROOT = research/`

```
{RESEARCH_ROOT}/
├── Research Overview.md          # L0 root entry point
├── Track Map.canvas              # Top-down visual navigation (created last)
├── literature/                   # Papers, math refreshers, concept primers
│   ├── papers/                   # Individual paper summaries, organized by track
│   │   ├── {sub-area-1}/         # Papers for each track
│   │   ├── {sub-area-2}/
│   │   └── general/              # Cross-cutting / foundational papers
│   ├── primers/                  # Math/concept refresher notes
│   └── Literature Index.md       # Entry point for lit review
├── benchmarks/                   # Public benchmarks discovered during research
│   └── {org}/                    # Organized by organization (e.g., google, openai, open-benchmarks)
│       └── {suite-or-benchmark}/ # Suite or standalone benchmark
│           ├── README.md         # Overview, links, description
│           ├── *.pdf             # Downloaded paper(s)
│           ├── {sub-benchmark}/  # If suite has sub-benchmarks
│           │   ├── README.md
│           │   └── *.ipynb       # Starter/reference notebooks
│           └── ...
├── tracks/                       # All sub-area folders live here
│   ├── {sub-area-1}/
│   │   ├── analysis.md           # Full-length analysis doc (no word limit, updated on each research run)
│   │   └── ...                   # L0-L3 notes
│   ├── {sub-area-2}/
│   └── ...
```

### Step 3: Create the L0 root note

`Research Overview.md` — the entry point. Contains:
- 1-2 sentence framing of the research question
- Linked list of all sub-area L0 notes
- Selection criteria or evaluation framework if applicable

### Step 4: Research all sub-areas in parallel

Launch one Agent per sub-area (up to 5-7 in parallel). Each agent:
1. **Web searches** for the sub-area topic — existing work, benchmarks, papers, known limitations
2. Returns a structured summary with:
   - Existing approaches/benchmarks (with sources)
   - Gaps and limitations
   - Novel ideas or opportunities (3-5 per sub-area)
   - Key papers with citations

### Step 5: Discover and catalog public benchmarks

Search for existing public benchmarks relevant to the research topic. This runs in parallel with Step 4.

**Where to search:**
- **Kaggle Benchmarks** (`kaggle.com/benchmarks`) — search for authoritative suites (e.g., Google FACTS, OpenAI SimpleQA, MMLU-Pro) and community benchmarks
- **arXiv** — papers introducing benchmarks referenced in the research
- **HuggingFace** — datasets and leaderboards

**For each relevant benchmark or suite found:**

1. Create `benchmarks/{org}/{benchmark-or-suite}/` directory
2. Create a `README.md` with: name, description, what it measures, example counts, links (leaderboard, paper, code)
3. **Download the paper PDF** (from arXiv or direct link) into the same folder
4. **Download starter/reference notebooks** using `kaggle kernels pull` if available on Kaggle
5. If it's a suite with sub-benchmarks, create a subfolder per sub-benchmark with its own `README.md` and notebooks

**Prioritize:**
- Authoritative benchmarks from major orgs (Google, OpenAI, DeepMind, Meta)
- Benchmarks directly relevant to the research sub-areas
- Benchmarks with public leaderboards showing model comparisons
- Novel or recent benchmarks (2024-2026) that test capabilities not covered by older ones

**Skip:** Benchmarks that are purely academic with no public evaluation infrastructure, or that are superseded by newer versions.

### Step 6: Create L0 track notes (one per sub-area)

Place in `tracks/{sub-area}/` folder. Short, intuitive, heavily linked. Contains:
- Intuition paragraph
- Key Concepts section (links to L1 notes)
- Existing Work section (links to L2 notes)
- Top Ideas section (links to L2 benchmark/approach notes)
- Links section with Up/Down/Related

### Step 7: Create L1-L3 notes per sub-area

Launch one Agent per sub-area to create all granular notes. Each agent creates:

**L1 Concept Notes (3-5 per sub-area):**
- Definition + structure + key papers
- Links down to L2 notes, cross-links to other sub-areas

**L2 Existing Work Notes (3-5 per sub-area):**
- What it does, key results, limitations
- Source citations

**L2 Novel Idea Notes (2-5 per sub-area):**
- What it tests/does, why it's novel, design sketch
- Expected impact/discrimination/value

**L3 Implementation Notes (1-2 per sub-area, for top ideas only):**
- Concrete design: data, metrics, scoring, difficulty tiers
- Code patterns, SDK integration notes

### Step 8: Create or update analysis.md per track

Each track gets a `tracks/{sub-area}/analysis.md` — a full-length analysis document (NO word limit):
- Contains complete benchmark tables, gap analyses, detailed idea descriptions, all sources
- The L0 track note links here via "Full detail: [[analysis]]"
- **Incremental updates:** If `analysis.md` already exists, READ IT FIRST. Merge new findings into the existing document rather than overwriting. Add new sections, update existing sections with new data, and append a dated changelog entry at the bottom:
  ```
  ## Changelog
  - YYYY-MM-DD: Added [description of what was added/updated]
  ```

### Step 9: Build the literature review

Place in `research/literature/`. This step runs in parallel with steps 5-8.

#### 9a. Identify papers

From the research agents' results (Step 4), collect all cited papers. Also search for:
- Foundational/seminal papers in each sub-area
- Recent survey papers that cover the landscape
- Papers that introduce key methods or benchmarks referenced in the research

#### 9b. Create paper summary notes

Place in `literature/papers/{track}/` (use `general/` for foundational/cross-cutting papers). One note per paper.

**PDF download:** For each paper, attempt to download the original PDF alongside the summary note. Use the arXiv PDF URL (e.g., `https://arxiv.org/pdf/XXXX.XXXXX`) or the direct PDF link from the source. Save as `{Paper Title} ({Year}).pdf` in the same folder as the summary note. If the PDF is not freely available, note this in the summary.

```markdown
# {Paper Title} ({Year})

#paper #literature #{sub-area-tag}

**Authors:** ...
**Source:** arXiv:XXXX.XXXXX / Conference / URL

## Key Contribution
1-2 sentences: what this paper introduced or proved.

## Problem Addressed
What gap or question motivated this work?

## Method
How they approached it (high-level, 3-5 bullet points).

## Key Results
The headline numbers or findings.

## Limitations
What it doesn't cover or where it falls short.

## Relevance to Our Research
Why this paper matters for our specific project.

## Links
- Related: [[concept notes]], [[other papers]]
```

#### 9c. Create math/concept primer notes

Place in `literature/primers/`. These are refresher notes for foundational concepts that appear across papers. Each primer:

- Covers ONE concept (not a textbook chapter)
- Starts with intuition, then builds to the math
- Includes worked examples where applicable
- Links to papers that use this concept

Common primers to create (as needed by the research topic):

**Probability & Statistics:**
- `Bayes Theorem.md` — prior, likelihood, posterior, worked example
- `KL Divergence.md` — intuition (measuring distribution mismatch), formula, asymmetry, connection to cross-entropy
- `Expected Value and Variance.md` — definitions, linearity, common distributions
- `Confidence Intervals and Statistical Significance.md` — p-values, sample size, effect size

**Linear Algebra:**
- `Vectors and Dot Products.md` — geometric intuition, similarity, projections
- `Matrix Multiplication.md` — as linear transformation, attention as matrix ops
- `Eigenvalues and Eigenvectors.md` — intuition (stretching directions), PCA connection
- `Norms and Distances.md` — L1, L2, cosine similarity, when to use which

**Information Theory:**
- `Entropy.md` — measuring uncertainty/surprise, bits, connection to compression
- `Cross-Entropy Loss.md` — why we use it for classification, connection to KL divergence
- `Mutual Information.md` — shared information between variables

**ML Foundations:**
- `Gradient Descent.md` — intuition, learning rate, SGD vs batch
- `Softmax and Temperature.md` — converting logits to probabilities, temperature scaling
- `Attention Mechanism.md` — Q/K/V, scaled dot-product, multi-head
- `Calibration in ML.md` — reliability diagrams, ECE, Brier score

**Only create primers that are actually referenced** by the research. Don't generate a textbook — generate targeted refreshers for concepts that appear in the papers and notes.

Each primer follows this format:

```markdown
# {Concept Name}

#primer #literature #math

## Intuition
Plain-English explanation. What is this? Why do we care?

## The Math
Core formula(s) with each symbol defined.

$$
D_{KL}(P \| Q) = \sum_{x} P(x) \log \frac{P(x)}{Q(x)}
$$

Where:
- $P$ = true distribution
- $Q$ = approximate distribution

## Worked Example
A concrete, small-scale example walking through the computation.

## Where It Shows Up
- [[Paper 1]] uses this for...
- [[Paper 2]] extends this by...
- [[Concept Note]] relies on this because...

## Common Gotchas
- KL divergence is NOT symmetric
- ...

## Links
- Related: [[other primers]], [[concept notes]]
```

#### 9d. Create the Literature Index

`literature/Literature Index.md` — entry point for the lit review:

```markdown
# Literature Index

#literature #L0

## Papers by Sub-Area
### {Sub-area 1}
- [[Paper Title (Year)]] — one-line summary

### {Sub-area 2}
- ...

## Math & Concept Primers
- [[KL Divergence]] — measuring distribution mismatch
- [[Calibration in ML]] — reliability diagrams, ECE, Brier score
- ...

## Key Surveys
- [[Survey Paper (Year)]] — covers...

## Links
- Up: [[Research Overview]]
```

### Step 10: Create the top-down canvas

Include the Literature Index in the canvas as a card in the top-right area, connected to the root.

`Track Map.canvas` — a visual spatial layout with cards arranged top-to-bottom:

```
Row 1: Research Overview (root)
Row 2: Sub-area L0 notes (color-coded)
Row 3: Key L1 concept notes per sub-area
Row 4: Top L2 idea notes (starred)
Row 5: L3 implementation notes
```

All cards are file embeds linked by edges flowing downward. Use Obsidian canvas color coding:
- Different color per sub-area
- Dark for implementation notes

### Step 11: Verify and report

- Count total notes created
- List the folder structure
- Confirm the canvas was created
- Suggest next steps (e.g., "pick a sub-area to focus on")

## Important Guidelines

- **Split aggressively** — if a section exceeds 300 words, it needs its own note
- **Link everything** — every concept reference should be a `[[wikilink]]`
- **Tags for filtering** — every note gets layer tag + topic tag at minimum
- **Contamination awareness** — when researching AI/ML topics, flag contamination risks in existing benchmarks
- **Sources matter** — L2 existing work notes must cite sources (arXiv IDs, URLs, paper names)
- **Parallel is key** — always launch research agents and note-creation agents in parallel (up to 5-7 at a time)
- **Canvas is last** — create the canvas only after all notes exist, so file paths are correct
- **Obsidian compatibility** — note filenames should be human-readable (spaces OK, avoid special chars except —)
