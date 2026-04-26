---
name: geno-research
description: >-
  Research toolkit — build and maintain a wiki of linked markdown notes using the
  LLM Wiki pattern. Research topics via web search, ingest sources (URLs, PDFs, files),
  and lint the wiki for consistency. Includes paper generation and repo documentation.
  Use when user says /geno-research, /geno-research-papers-generate, or /geno-research-repos-document.
allowed-tools: "Bash(*) Read(*) Edit(*) Write(*) WebSearch(*) WebFetch(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.4.0"
---

# geno-research

Research skills for AI coding agents. Maintains an evolving, cross-referenced knowledge base using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Installed via [geno-tools](https://github.com/42euge/geno-tools):
```bash
geno-tools install geno-research
```

## Skills

| Skill | Sub-skillset | Slash command |
|-------|-------------|---------------|
| geno-research | — | /geno-research (umbrella) |
| geno-research-papers-generate | papers | /geno-research-papers-generate |
| geno-research-repos-document | repos | /geno-research-repos-document |

### Umbrella commands

| Command | Description |
|---|---|
| `/geno-research <topic>` | Research a topic and build/update a wiki of linked markdown notes |
| `/geno-research ingest <url-or-file>` | Ingest a source into the wiki |
| `/geno-research lint` | Check wiki health — broken links, orphans, contradictions |

## Runtime

No venv or scripts — all skills are pure markdown workflows.
