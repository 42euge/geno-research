---
name: geno-research
description: >-
  Research toolkit — build and maintain a wiki of linked markdown notes using the
  LLM Wiki pattern. Research topics via web search, ingest sources (URLs, PDFs, files),
  and lint the wiki for consistency. Includes paper generation and repo documentation.
  Use when user says /geno-research, /geno-research-wiki, /geno-research-paper-generate,
  or /geno-research-repo-docs.
allowed-tools: "Bash(*) Read(*) Edit(*) Write(*) WebSearch(*) WebFetch(*)"
license: MIT
metadata:
  author: 42euge
  version: "0.4.0"
observability:
  success_signal: "sub-skill dispatched and completed successfully"
  failure_signals:
    - "no sub-skill matched the user's request"
    - "sub-skill failed (see individual skill traces)"
  knowledge_reads:
    - "user arguments to determine which sub-skill to dispatch"
  knowledge_writes: []
---

# geno-research

Research toolkit with wiki, paper generation, and repo documentation.

## Sub-skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| geno-research-wiki | /geno-research-wiki | Research a topic and build a wiki |
| geno-research-paper-generate | /geno-research-paper-generate | Generate a paper from wiki pages |
| geno-research-repo-docs | /geno-research-repo-docs | Generate documentation for a repo |
