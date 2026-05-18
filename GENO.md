# geno-research — research toolkit skillset

Research skills for AI coding agents. Build and maintain a wiki of linked markdown notes using the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Research topics via web search, ingest sources, and lint the wiki for consistency. Includes paper generation and repo documentation.

## Skills

| Skill | Slash command | Description |
|-------|---------------|-------------|
| geno-research | /geno-research | Research a topic, ingest sources, or lint the wiki |
| geno-research-paper-generate | /geno-research-paper-generate | Generate an academic paper from benchmark findings |
| geno-research-repo-docs | /geno-research-repo-docs | Generate purpose-driven repo documentation |

## Repo structure

```
geno-research/
├── GENO.md              # agent instructions (this file)
├── SKILL.md             # umbrella skill manifest
├── CLAUDE.md            # agent shim → GENO.md
├── GEMINI.md            # agent shim → GENO.md
├── AGENTS.md            # agent shim → GENO.md
├── genotools.yaml       # geno-tools install manifest
├── skills/
│   ├── geno-research/                    # umbrella skill
│   │   └── SKILL.md
│   ├── geno-research-paper-generate/     # sub-skill: generate academic paper
│   │   └── SKILL.md
│   └── geno-research-repo-docs/          # sub-skill: generate repo docs
│       └── SKILL.md
├── docs/
│   └── index.html
├── LICENSE
└── README.md
```

## Conventions

- **Canonical prefix**: slash commands use the `geno-` prefix in source (e.g., `/geno-research`).
- **Prefix aliasing**: short `/gt-` aliases (e.g., `/gt-research`) are configured per-installation by `geno-tools` and are not defined in this repo.
- **Adding a new skill**: create a directory under `skills/` named after the skill, write a `SKILL.md` with YAML frontmatter (name, description, allowed-tools, etc.), and add the skill to the Skills table above.
- **Versioning**: version is tracked in `genotools.yaml` and in each skill's SKILL.md frontmatter. Bump all together.

## Architecture

Pure markdown workflows — no venv, no scripts, no runtime dependencies. Each skill is a markdown file that tells the agent what to do. The agent uses web search, file reading, and bash tools to execute the workflow.

| Layer | Content | Role |
|-------|---------|------|
| **Skills** | `skills/*/SKILL.md` | Agent instructions for each workflow |
| **Schema** | `SKILL.md`, `GENO.md`, `genotools.yaml` | Tells geno-tools how to install and discover skills |
| **Output** | `research/` (in user's project) | Wiki pages, raw sources, index |
