---
name: geno-research
description: >-
  Research toolkit — build and maintain a wiki of linked markdown notes using the
  LLM Wiki pattern. Research topics via web search, ingest sources (URLs, PDFs, files),
  and lint the wiki for consistency. Includes lab notes, paper generation,
  repo documentation, and long-running autonomous research loops.
  Use when user says /gt-research, /gt-research-notes, /gt-research-paper-generate,
  /gt-research-repo-docs, or /gt-research-supercharge.
license: MIT
metadata:
  author: 42euge
  version: "0.3.0"
---

# geno-research

Research skills for Claude Code. Maintains an evolving, cross-referenced knowledge base using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Installed via [geno-tools](https://github.com/42euge/geno-tools):
```bash
geno-tools install research
```

## Commands

| Command | Description |
|---|---|
| `/gt-research <topic>` | Research a topic and build/update a wiki of linked markdown notes |
| `/gt-research ingest <url-or-file>` | Ingest a source into the wiki |
| `/gt-research lint` | Check wiki health — broken links, orphans, contradictions |
| `/gt-research-notes <subcommand>` | Project lab notes: tasks, timestamped notes, plans |
| `/gt-research-paper-generate [focus]` | Generate an academic paper from findings |
| `/gt-research-repo-docs [focus]` | Generate purpose-driven repo documentation |
| `/gt-research-supercharge [duration]` | Long-running autonomous agent loop for benchmarks |

## Runtime

No venv or scripts — all commands are pure markdown workflows. The only persistent runtime state is:
- `~/.geno-tools/geno-research/configs/supercharge/state.json` — cross-session memory for the supercharge loop (preserved across `geno-tools update`).
