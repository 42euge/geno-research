---
name: geno-research-repo-docs
description: >-
  Generate purpose-driven repository documentation that captures what we're
  trying to achieve, the reasoning behind design decisions, and how the repo
  fits into the broader research context.
  Use when user says /geno-research-repo-docs.
license: MIT
metadata:
  author: 42euge
  version: "0.4.0"
observability:
  success_signal: "docs directory populated with README.md, STRUCTURE.md, and CONTRIBUTING.md"
  failure_signals:
    - "repo has no source code or meaningful content to document"
    - "write to geno-tools/docs/ directory failed"
    - "generated docs contain only generic boilerplate without repo-specific content"
  knowledge_reads:
    - "CLAUDE.md, README.md for project context"
    - "src/, notebooks/, data/, tests/ for codebase understanding"
    - "requirements.txt / pyproject.toml / package.json for dependencies"
    - "geno-notes (tasks, journal, plans) for development history"
    - "research/ folders (up to 3 parent dirs) for research context"
    - "git log for development trajectory"
  knowledge_writes:
    - "geno-tools/docs/README.md (the story — main entry point)"
    - "geno-tools/docs/STRUCTURE.md (codebase map)"
    - "geno-tools/docs/CONTRIBUTING.md (how to work here)"
---

# Repo Docs — Purpose-Driven Documentation

Generate documentation about the current repository in `geno-tools/docs/`. This is NOT just a "how to run it" guide — it captures **what we're trying to achieve**, the reasoning behind design decisions, and how this repo fits into the broader research context.

## Input

`$ARGUMENTS` — Optional focus area or instructions (e.g., "focus on the benchmark design", "update the architecture section"). If empty, generate/refresh the full documentation.

## Output Location

All output goes into `geno-tools/docs/` in the current working directory.

## Workflow

### Step 1: Gather context

Read these sources in parallel to build a complete picture:

**Repo-level:**
- `CLAUDE.md` — project instructions and context
- `README.md` — existing readme if any
- `requirements.txt` / `pyproject.toml` / `package.json` — dependencies
- Browse `src/`, `notebooks/`, `data/`, `tests/` and other key directories
- Project tasks and journal via `geno-notes` (defaults to project scope; falls back to global if none):
  - `geno-notes list --json` — all tasks with status, dates, tags
  - `geno-notes search <topic>` — find relevant journal entries + plans
  - `$(geno-notes path)/journal/` — timestamped development log (one .md + .jsonl per month)
  - `$(geno-notes path)/plans/` — per-task design plans
  - Use `--all` on `list` or `search` to include global-scope entries when synthesizing across projects
- Recent git log (last 20-30 commits) for development trajectory

**Research context (blend in from /gt-research outputs):**
- Check for a `research/` folder in the repo OR in parent directories (walk up to 3 levels)
- If found, read:
  - The root `Research Overview.md` for overall framing
  - Any sub-area L0 notes relevant to this repo's domain
  - Cross-cutting concept notes in `concepts/`
  - Key L2 idea notes that this repo might implement
  - Reference docs that provide deeper analysis
- Also check `CLAUDE.md` for pointers to research directories (look for paths mentioning `research/`)

**Parent project context:**
- Walk up directories looking for parent `CLAUDE.md` files (up to 3 levels) to understand how this repo fits into a larger project

### Step 2: Synthesize the story

Before writing any files, form a mental model of:

1. **The Why** — What problem or question does this repo address? What would we learn from it?
2. **The What** — What does it actually do? What are its components?
3. **The How** — Key design decisions, algorithms, data pipelines
4. **The Where** — How does it fit into the larger project/research?
5. **The Status** — What's done, what's in progress, what's planned?

### Step 3: Create the documentation

Create the following files in `geno-tools/docs/`:

#### `README.md` — The Story (main entry point)

This is the most important file. It tells the narrative:

```markdown
# {Repo Name}

## Why This Exists

{2-3 paragraphs explaining the motivation, research question, and what we hope to learn.
Pull from research notes to ground this in the broader intellectual context.
Reference specific papers or concepts from the research knowledge graph if available.}

## What It Does

{Clear explanation of what the repo produces/measures/builds.
Not a feature list — a conceptual explanation that someone unfamiliar could follow.}

## Key Concepts

{Explain the domain-specific concepts that are central to this repo.
Link to research notes where deeper exploration exists.
Use analogies and intuitions, not just definitions.}

## Architecture

{How the pieces fit together. Describe the flow from input to output.
Include a simple ASCII diagram if helpful:}

```
input -> [component A] -> [component B] -> output
```

## Design Decisions

{Key choices made and WHY. These are the things that aren't obvious from reading the code.
Format as decision records:}

### Decision: {title}
- **Context:** {what situation led to this choice}
- **Choice:** {what we chose}
- **Reasoning:** {why}
- **Trade-offs:** {what we gave up}

## How It Fits In

{Where this repo sits in the larger project. What depends on it, what it depends on.
Reference parent project context.}

## Current Status

{What's working, what's in progress, what's planned. Pull from `geno-notes list --json` (by status) and recent journal entries.}
```

#### `STRUCTURE.md` — Codebase Map

```markdown
# Codebase Structure

## Directory Layout

{Annotated tree showing what each directory/key file does.
Not just file names — explain the PURPOSE of each.}

## Key Files

{For each important file, 1-2 sentences on what it does and why it exists.
Group by functional area, not alphabetically.}

## Data Flow

{How data moves through the system. What generates what.
Trace the path from raw inputs to final outputs.}

## Dependencies

{Key external dependencies and WHY they're used (not just a list).}
```

#### `CONTRIBUTING.md` — How to Work Here

```markdown
# Working in This Repo

## Setup

{How to get a working development environment. Step by step, tested.}

## Running

{How to run the main workflows. Include actual commands.}

## Common Tasks

{Patterns for common development tasks:
- Adding a new [task/benchmark/feature]
- Running tests
- Updating data
- Debugging common issues}

## Conventions

{Code style, naming conventions, file organization patterns used in this repo.
Only include conventions that aren't obvious from the code.}
```

### Step 4: Weave in research context

Go back through the generated docs and enrich them:

- Where a concept is explained, add references to research notes: `(see research: [[Note Name]])`
- Where a design decision was informed by a paper, cite it
- Where the repo implements an idea from the research graph, connect them explicitly
- Add a "Research Background" section to README.md if there's substantial research context, with a brief reading path through the most relevant notes

### Step 5: Verify and report

- List all files created/updated in `geno-tools/docs/`
- Highlight any gaps (things you couldn't determine from the available context)
- Suggest what documentation would benefit from the user's input (design rationale you couldn't infer, etc.)

## Important Guidelines

- **Tell the story first** — always lead with WHY before WHAT or HOW
- **Don't repeat the code** — documentation should add understanding that reading the code alone doesn't provide
- **Be honest about gaps** — if you don't know why something was designed a certain way, say so and flag it for the user
- **Research enrichment is key** — the research context is what makes this more than a generic README generator. Find the connections.
- **Keep it maintainable** — write docs that can be updated incrementally, not a monolith that goes stale
- **No fluff** — every sentence should add information. No "This is a very important project that..."
- **Use concrete examples** — when explaining how something works, show a real example from the repo

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-research-repo-docs \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = docs directory populated with repo-specific README.md, STRUCTURE.md, and CONTRIBUTING.md
- `failure` = repo had no meaningful content, writes failed, or docs are generic boilerplate
- `abandoned` = user stopped early
