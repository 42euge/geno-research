# geno-research

Research skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Build and maintain a wiki of linked markdown notes using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

The LLM maintains an evolving, cross-referenced knowledge base rather than producing one-off summaries. Knowledge accumulates and becomes increasingly interconnected.

## Commands

| Command | Description |
|---------|-------------|
| `/gt-research <topic>` | Research a topic — web search, create/update wiki pages with `[[wikilinks]]` |
| `/gt-research ingest <url-or-file>` | Ingest a source into the wiki (URL, PDF, file) |
| `/gt-research lint` | Check wiki health — broken links, orphans, contradictions |
| `/gt-lab-notes <subcommand>` | Project lab notes: `create`, `add-task`, `do-task`, `done-task`, `note` |
| `/gt-gen-paper [focus]` | Generate academic paper from findings |
| `/gt-repo-docs [focus]` | Generate purpose-driven repo documentation |

## Wiki structure

```
research/
├── index.md          # Entry point — links to all wiki pages
├── raw/              # Original sources (PDFs, URLs, notes)
└── wiki/             # LLM-maintained pages with [[wikilinks]]
```

## Install

```bash
./install.sh
```

Or install via geno-tools ecosystem installer:
```bash
cd ../geno-tools && ./install.sh
```

## Part of the geno ecosystem

- [geno-tools](https://github.com/42euge/geno-tools) — orchestrator + general tools
- [geno-kaggle](https://github.com/42euge/geno-kaggle) — Kaggle benchmarking
- [geno-media](https://github.com/42euge/geno-media) — media creation (audiobooks, video)

## License

MIT
