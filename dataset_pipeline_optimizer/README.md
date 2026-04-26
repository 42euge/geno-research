# dataset_pipeline_optimizer

A fast, composable, debuggable dataset preparation framework.

Build pipelines as YAML DAGs of reusable transforms. Run them with parallel
execution, content-addressed caching, and incremental recomputation — only
the steps whose inputs or configs changed are re-executed.

## Highlights

- **DAG-based pipelines** — declare steps and dependencies in YAML.
- **Reusable transforms** — filtering, deduplication, formatting, augmentation,
  plus loaders for JSON / JSONL / CSV / text and writers for the same.
- **Parallel execution** — independent nodes run concurrently with a thread pool.
- **Incremental recomputation** — content-addressed cache keys mean unchanged
  steps are reused across runs.
- **Schema + quality validation** — declared as ordinary nodes in the DAG.
- **Debug mode** — dump every stage's input/output and timing info.
- **DAG visualization** — render the pipeline as Graphviz DOT or ASCII.

## Quickstart

```bash
# From the project root (the dataset_pipeline_optimizer/ directory):
python run_pipeline.py examples/configs/training_ready.yaml

# Or from the parent directory, as a module:
python -m dataset_pipeline_optimizer examples/configs/training_ready.yaml
```

Outputs land in `./out/` and intermediate cache in `./.pipeline_cache/`.
Re-run the same command and only changed steps execute.

## Project Layout

```
dataset_pipeline_optimizer/
├── pipeline/            # DAG model + YAML loader
├── transforms/          # filter / dedup / format / augment / IO
├── execution/           # scheduler, cache, runner
├── validation/          # schema + quality checks
├── cli/                 # run_pipeline entry point
├── examples/
│   ├── configs/         # YAML pipelines
│   └── data/            # tiny raw datasets
└── tests/               # unit + integration tests
```

## Pipeline YAML

```yaml
name: training_ready
nodes:
  - id: load
    transform: load_jsonl
    params: {path: examples/data/raw.jsonl}

  - id: clean
    transform: filter_records
    deps: [load]
    params:
      where: "len(record.get('text', '')) > 20"

  - id: dedup
    transform: deduplicate
    deps: [clean]
    params: {key: text}

  - id: format
    transform: format_chat
    deps: [dedup]
    params: {prompt_field: text, role: user}

  - id: validate
    transform: validate_schema
    deps: [format]
    params:
      required: [messages]

  - id: write
    transform: write_jsonl
    deps: [validate]
    params: {path: out/training.jsonl}
```

## CLI

```
python run_pipeline.py CONFIG [options]

  --debug              dump stage I/O to .pipeline_cache/debug
  --no-cache           ignore cache, recompute everything
  --workers N          parallel workers (default: cpu count)
  --visualize FORMAT   print DAG as 'ascii' or 'dot' and exit
  --only NODE [...]    run only the listed nodes (and their deps)
```

## Caching

Each node's cache key hashes:
- the transform name + version
- its parameters
- its upstream cache keys

So edits ripple downstream automatically; unrelated branches stay cached.
