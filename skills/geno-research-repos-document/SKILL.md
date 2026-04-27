---
name: geno-research-repos-document
description: >-
  Generate purpose-driven documentation for a repository. Captures what the repo
  is trying to achieve, design reasoning, and how it fits into broader context.
  Use when user says /geno-research-repos-document.
allowed-tools: "Bash(*) Read(*) Edit(*) Write(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.4.0"
---

# Repo Docs — Purpose-Driven Documentation

Generate documentation about the current repository. This is NOT just a "how to run it" guide — it captures **what we're trying to achieve**, the reasoning behind design decisions, and how this repo fits into the broader research context.

## Input

`$ARGUMENTS` — Optional focus area or instructions (e.g., "focus on the benchmark design", "update the architecture section"). If empty, generate/refresh the full documentation.

## Output Location

All output goes into a `docs/` directory in the current working directory.

## Workflow

### Step 1: Gather context

Read these sources in parallel to build a complete picture:

**Repo-level:**
- Agent instruction files — project instructions and context
- `README.md` — existing readme if any
- `requirements.txt` / `pyproject.toml` / `package.json` — dependencies
- Browse `src/`, `notebooks/`, `data/`, `tests/` and other key directories
- Project tasks and journal via `geno-notes` (defaults to project scope; falls back to global if none):
  - `geno-notes list --json` — all tasks with status, dates, tags
  - `geno-notes search <topic>` — find relevant journal entries + plans
  - `$(geno-notes path)/journal/` — timestamped development log
  - `$(geno-notes path)/plans/` — per-task design plans
  - Use `--all` on `list` or `search` to include global-scope entries when synthesizing across projects
- Recent git log (last 20-30 commits) for development trajectory

**Research context (blend in from /geno-research outputs):**
- Check for a `research/` folder in the repo OR in parent directories (walk up to 3 levels)
- If found, read relevant research notes for theoretical grounding

**Parent project context:**
- Walk up directories looking for parent instruction files (up to 3 levels) to understand how this repo fits into a larger project

### Step 2: Synthesize the story

Before writing any files, form a mental model of:

1. **The Why** — What problem or question does this repo address?
2. **The What** — What does it actually do? What are its components?
3. **The How** — Key design decisions, algorithms, data pipelines
4. **The Where** — How does it fit into the larger project/research?
5. **The Status** — What's done, what's in progress, what's planned?

### Step 3: Create the documentation

Create the following files:

#### `README.md` — The Story (main entry point)
Tells the narrative: Why This Exists, What It Does, Key Concepts, Architecture, Design Decisions, How It Fits In, Current Status.

#### `STRUCTURE.md` — Codebase Map
Directory Layout, Key Files, Data Flow, Dependencies.

#### `CONTRIBUTING.md` — How to Work Here
Setup, Running, Common Tasks, Conventions.

### Step 4: Weave in research context

Enrich the generated docs with references to research notes and connections to the broader research graph.

### Step 5: Verify and report

- List all files created/updated
- Highlight any gaps
- Suggest what documentation would benefit from user input

## Important Guidelines

- **Tell the story first** — always lead with WHY before WHAT or HOW
- **Don't repeat the code** — documentation should add understanding that reading the code alone doesn't provide
- **Be honest about gaps** — if you don't know why something was designed a certain way, say so
- **Research enrichment is key** — the research context makes this more than a generic README generator
- **Keep it maintainable** — write docs that can be updated incrementally
- **No fluff** — every sentence should add information
- **Use concrete examples** — when explaining how something works, show a real example from the repo
