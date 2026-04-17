---
name: geno-research
description: >-
  Research toolkit — build and maintain a wiki of linked markdown notes using the
  LLM Wiki pattern. Research topics via web search, ingest sources (URLs, PDFs, files),
  and lint the wiki for consistency. Also includes lab notes, paper generation,
  and repo documentation.
  Use when user says /gt-research, /gt-lab-notes, /gt-gen-paper, or /gt-repo-docs.
license: MIT
metadata:
  author: 42euge
  version: "0.3.0"
---

# geno-research

Research skills for Claude Code. Maintains an evolving, cross-referenced knowledge base
using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Commands

| Command | Description |
|---------|-------------|
| `/gt-research <topic>` | Research a topic and build/update a wiki of linked markdown notes |
| `/gt-research ingest <url-or-file>` | Ingest a source into the wiki |
| `/gt-research lint` | Check wiki health — broken links, orphans, contradictions |
| `/gt-lab-notes <subcommand>` | Project lab notes: tasks, timestamped notes, plans |
| `/gt-gen-paper [focus]` | Generate academic paper from findings |
| `/gt-repo-docs [focus]` | Generate purpose-driven repo documentation |
