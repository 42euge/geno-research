# Getting Started

## Prerequisites

- [geno-tools](https://github.com/42euge/geno-tools) installed (`pipx install geno-tools`)
- A supported coding CLI (Claude Code, Gemini CLI, Codex, or OpenCode)

## Install

```bash
geno-tools install geno-research
```

Or from within an agent session:

```
/geno-tools install geno-research
```

## First use

Start a research session by invoking the umbrella skill with a topic:

```
/geno-research transformer architectures for long context
```

This creates a `research/` directory in your working directory with a wiki of linked markdown notes.

### Ingest a source

Add a paper, URL, or file to the wiki:

```
/geno-research ingest https://arxiv.org/abs/2401.12345
```

### Check wiki health

Lint the wiki for broken links, orphans, and contradictions:

```
/geno-research lint
```

### Generate a paper

Synthesize research findings into an academic paper:

```
/geno-research-papers-generate
```

### Generate repo docs

Create purpose-driven documentation for the current repository:

```
/geno-research-repos-document
```

## Wiki structure

All research output lives in `research/` in your working directory:

```
research/
├── index.md          # Entry point — links to all wiki pages
├── raw/              # Original sources (PDFs, URLs, notes)
└── wiki/             # LLM-maintained pages with [[wikilinks]]
```

Pages use standard Markdown with `[[wikilinks]]` for cross-references, compatible with Obsidian and other wiki tools.
