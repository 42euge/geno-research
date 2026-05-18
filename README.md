# geno-research

Research skills for AI coding agents. Build and maintain a wiki of linked markdown notes using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

The LLM maintains an evolving, cross-referenced knowledge base rather than producing one-off summaries. Knowledge accumulates and becomes increasingly interconnected.

Part of the [geno-tools](https://github.com/42euge/geno-tools) ecosystem.

## Install

```bash
geno-tools install research                       # from registry
geno-tools dev research /path/to/local/checkout   # for local dev
```

## Commands

| Command | Description |
|---|---|
| `/geno-research <topic>` | Research a topic — web search, create/update wiki pages with `[[wikilinks]]` |
| `/geno-research ingest <url-or-file>` | Ingest a source into the wiki (URL, PDF, file) |
| `/geno-research lint` | Check wiki health — broken links, orphans, contradictions |
| `/geno-research-paper-generate [focus]` | Generate academic paper from findings |
| `/geno-research-repo-docs [focus]` | Generate purpose-driven repo documentation |

Project tasks and journal have moved to the [`geno-notes`](https://github.com/42euge/geno-notes) repo — use `/geno-notes`.

## Wiki structure

```
research/
├── index.md          # Entry point — links to all wiki pages
├── raw/              # Original sources (PDFs, URLs, notes)
└── wiki/             # LLM-maintained pages with [[wikilinks]]
```

## Repository structure

```
geno-research/
├── GENO.md              # agent instructions (single source of truth)
├── SKILL.md             # umbrella skill manifest
├── genotools.yaml       # install manifest (no venv, pure markdown)
└── skills/              # skill .md files
    ├── geno-research/
    │   └── SKILL.md
    ├── geno-research-paper-generate/
    │   └── SKILL.md
    └── geno-research-repo-docs/
        └── SKILL.md
```

## Runtime

No venv, no scripts — all commands are pure markdown workflows.

## License

MIT
