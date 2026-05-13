# geno-research

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://42euge.github.io/geno-research/)

Research skills for AI coding agents. Build and maintain a wiki of linked markdown notes using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

The LLM maintains an evolving, cross-referenced knowledge base rather than producing one-off summaries. Knowledge accumulates and becomes increasingly interconnected.

Part of the [geno-tools](https://github.com/42euge/geno-tools) ecosystem.

## Install

```bash
geno-tools install geno-research
```

Or from within an agent session:

```
/geno-tools install geno-research
```

## Skills

| Skill | Description |
|---|---|
| `/geno-research <topic>` | Research a topic — web search, create/update wiki pages with `[[wikilinks]]` |
| `/geno-research ingest <url-or-file>` | Ingest a source into the wiki (URL, PDF, file) |
| `/geno-research lint` | Check wiki health — broken links, orphans, contradictions |
| `/geno-research-papers-generate [focus]` | Generate academic paper from findings |
| `/geno-research-repos-document [focus]` | Generate purpose-driven repo documentation |

## Wiki structure

```
research/
├── index.md          # Entry point — links to all wiki pages
├── raw/              # Original sources (PDFs, URLs, notes)
└── wiki/             # LLM-maintained pages with [[wikilinks]]
```

## Runtime

No venv, no scripts — all skills are pure markdown workflows.

## License

MIT
