# geno-research

Research skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Build and maintain a wiki of linked markdown notes using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

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
| `/gt-research <topic>` | Research a topic — web search, create/update wiki pages with `[[wikilinks]]` |
| `/gt-research ingest <url-or-file>` | Ingest a source into the wiki (URL, PDF, file) |
| `/gt-research lint` | Check wiki health — broken links, orphans, contradictions |
| `/gt-research-notes <subcommand>` | Project lab notes: `create`, `add-task`, `do-task`, `done-task`, `note` |
| `/gt-research-paper-generate [focus]` | Generate academic paper from findings |
| `/gt-research-repo-docs [focus]` | Generate purpose-driven repo documentation |
| `/gt-research-supercharge [duration]` | Long-running autonomous agent loop with structured cycles |

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
├── SKILL.md              # umbrella (discovered by geno-tools)
├── genotools.yaml        # install manifest (no venv, pure markdown)
└── commands/             # slash-command .md files
    └── gt-research*.md
```

## Runtime

No venv, no scripts. The only persistent state written at runtime:
- `~/.geno-tools/geno-research/configs/supercharge/state.json` — supercharge cross-session memory (created lazily).

## License

MIT
