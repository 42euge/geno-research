# geno-research — research wiki, paper generation, repo docs

Research toolkit for AI coding agents. Build and maintain a wiki of linked markdown notes using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Knowledge accumulates and becomes increasingly interconnected across sessions.

## Skills

| Skill | Sub-skillset | Slash command |
|-------|-------------|---------------|
| geno-research | — | — (umbrella) |
| geno-research-papers-generate | papers | /geno-research-papers-generate |
| geno-research-repos-document | repos | /geno-research-repos-document |

### Umbrella commands

The umbrella skill (`/geno-research`) supports three modes:

| Command | Description |
|---|---|
| `/geno-research <topic>` | Research a topic — web search, create/update wiki pages with `[[wikilinks]]` |
| `/geno-research ingest <url-or-file>` | Ingest a source into the wiki (URL, PDF, file) |
| `/geno-research lint` | Check wiki health — broken links, orphans, contradictions |

## Repo structure

```
geno-research/
├── GENO.md              # agent instructions (this file)
├── SKILL.md             # umbrella skill manifest
├── genotools.yaml       # geno-tools manifest
├── skills/              # skill definitions
│   ├── geno-research/               # umbrella skill
│   ├── geno-research-papers-generate/  # paper generation
│   └── geno-research-repos-document/   # repo documentation
├── docs/                # MkDocs Material site
│   ├── index.md
│   └── getting-started.md
├── README.md
└── LICENSE
```

## Conventions

- **Wiki output** goes to `research/` in the user's working directory (not in this repo)
- **One concept per wiki page** — split pages that cover multiple distinct ideas
- **Link aggressively** — every concept that has or could have its own page gets a `[[wikilink]]`
- **Obsidian-compatible** — standard markdown with `[[wikilinks]]` and optional `#tags`
- **Sources matter** — cite papers (arXiv IDs), URLs, or other references
- **Prefix aliasing** — slash commands use the canonical `geno-` prefix in source (e.g., `/geno-research`). Short `/gt-` aliases are configured per-install via `~/.geno/config.yaml` and should never appear in source files or documentation.
- **Adding new sub-skills** — create a new directory under `skills/` named after the skill (e.g., `skills/geno-research-<name>/`), write a `SKILL.md` with the required frontmatter (`name`, `description`, `slash_command`), and add the skill to the Skills table in this file.

## Runtime

No venv, no scripts — all skills are pure markdown workflows. The wiki structure is created in the user's working directory on first use.
