# Research

Research a topic and build a wiki of linked markdown notes. Based on the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the LLM maintains an evolving, cross-referenced knowledge base rather than producing one-off summaries.

## Input

`$ARGUMENTS` — A topic, URL, file path, or research question. Examples:
- `"transformer architectures for long context"`
- `"https://arxiv.org/abs/2401.12345"`
- `lint`
- `ingest paper.pdf`

## Wiki Location

All output goes into `research/` in the current working directory.

```
research/
├── index.md          # Entry point — links to all wiki pages
├── raw/              # Original sources (saved URLs, PDFs, notes)
└── wiki/             # LLM-maintained pages with [[wikilinks]]
```

If `research/` doesn't exist, create it along with `raw/`, `wiki/`, and a starter `index.md`.

## Operations

### Research (default)

When given a topic or question:

1. Create the wiki structure if it doesn't exist
2. Web search the topic — find papers, articles, code, benchmarks, discussions
3. For each significant finding, create or update wiki pages in `wiki/`
4. Each page covers ONE concept, approach, paper, or idea
5. Use `[[wikilinks]]` to cross-reference between pages
6. Update `index.md` with links to all pages, loosely grouped by theme
7. If wiki pages already exist on related topics, UPDATE them with new findings — don't just add new pages in isolation

Launch multiple research agents in parallel when the topic has distinct sub-areas.

### Ingest

When `$ARGUMENTS` starts with `ingest` followed by a URL or file path:

1. Fetch the URL or read the file
2. Save a reference in `raw/` (URL bookmark file, or copy the file)
3. Extract knowledge and create/update wiki pages
4. A single source often touches multiple pages — update all of them
5. Update cross-references across affected pages
6. Update `index.md`

### Lint

When `$ARGUMENTS` is `lint`:

1. Scan all wiki pages in `wiki/`
2. Find broken `[[wikilinks]]` (link to pages that don't exist)
3. Find orphaned pages (no incoming links from other pages)
4. Find pages that should be split (covering multiple distinct concepts)
5. Find stale or contradictory information across pages
6. Report findings, then fix what's straightforward (create missing pages, add links, split oversized pages)

## Wiki Page Guidelines

- **One concept per page** — if a page covers multiple distinct ideas, split it
- **Link aggressively** — every concept that has or could have its own page gets a `[[wikilink]]`
- **Concise but complete** — no artificial word limits, but don't ramble
- **Sources matter** — cite papers (arXiv IDs), URLs, or other references
- **No rigid format** — let the content dictate structure. A paper summary looks different from a concept explanation or a comparison table
- **Human-readable filenames** — spaces OK, avoid special chars except dashes
- **Obsidian-compatible** — standard markdown with `[[wikilinks]]` and optional `#tags`
