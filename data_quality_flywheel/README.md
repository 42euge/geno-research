# Data Quality Flywheel

A self-contained, zero-dependency toolkit for the closed loop:

```
detect issues -> surface -> fix -> reinsert -> track improvements
```

It helps researchers spot problematic training transcripts (low-signal
responses, ambiguity, contradictions, duplicates), curate fixes, reinsert
the cleaned samples, and track quality improvements across iterations.

## Layout

```
data_quality_flywheel/
  ingestion/    dataset loaders + normalization (JSON, JSONL, CSV)
  analysis/     heuristic + pluggable model-based quality scoring
  issues/       detectors (low-signal, ambiguity, inconsistency, redundancy, duplicates)
  curation/     suggest / flag / edit / remove tooling
  feedback/     reinsertion pipeline + per-iteration reports
  versioning/   content-addressed dataset version store
  cli/          `analyze_dataset`, `export_issues`, `apply_fixes`
  data/         sample transcripts
  tests/        unittest suite
```

## Install / requirements

Pure Python 3.10+, no third-party dependencies. Drop the package into your
PYTHONPATH (or run from the repo root, as the examples below do).

## Input format

Any of:

- JSON array, JSONL, or CSV
- Records: `{id, prompt, response, [reward], [grade], [metadata]}`
  (`prompt`/`response` aliases like `input`/`output`, `instruction`/`completion` are accepted)

If `id` is missing it is generated from a SHA-1 of the content.

## Quickstart

```bash
# 1. Score + detect issues, write report
python -m data_quality_flywheel analyze_dataset \
    data_quality_flywheel/data/sample_transcripts.jsonl \
    --out reports/iter1

# 2. Export issues + suggested fixes for human review
python -m data_quality_flywheel export_issues \
    data_quality_flywheel/data/sample_transcripts.jsonl \
    --out reports/iter1

# 3. (human edits reports/iter1/fixes.jsonl)

# 4. Apply fixes, write cleaned dataset, snapshot a version
python -m data_quality_flywheel apply_fixes \
    data_quality_flywheel/data/sample_transcripts.jsonl \
    reports/iter1/fixes.jsonl \
    --out reports/iter1 \
    --version-store reports/versions \
    --message "first cleanup pass"
```

Outputs:

- `summary.json` — dataset size, average quality, issue-type histogram
- `scores.json` — per-transcript quality score with sub-components
- `issues.json` — flat list of `Issue` records
- `fixes.jsonl` — one suggested `Fix` per transcript (editable by humans)
- `cleaned.jsonl` — dataset after fixes applied
- `iteration_report.json` — before/after sizes, scores, issue counts
- `reports/versions/` — content-addressed version store with a `log.jsonl`

## Quality scoring

`analysis.score_transcript` produces a 0..1 composite of:

| component        | what it measures                                        |
| ---------------- | ------------------------------------------------------- |
| `length`         | response inside a sane length window                    |
| `diversity`      | type-token ratio                                        |
| `repetition`     | dominance of top-3 tokens                               |
| `refusal`        | "I cannot...", "as an AI..." patterns                   |
| `low_signal`     | "I don't know", "n/a", trivially short responses        |
| `prompt_overlap` | parroting the prompt back as the response               |
| `reward`         | optional signal coming from the dataset                 |
| `model`          | optional callable judge (`model_scorer=fn(p, r)->float`) |

Plug in your own LLM judge or reward model:

```python
from data_quality_flywheel.analysis import score_dataset, ModelScorer

def my_judge(prompt: str, response: str) -> float:
    # call Anthropic, a local reward model, a rubric LLM judge, ...
    return 0.85

scores = score_dataset(transcripts, model_scorer=ModelScorer(my_judge))
```

## Issue types

| tag             | detector                                                              |
| --------------- | --------------------------------------------------------------------- |
| `low_signal`    | composite score below threshold                                       |
| `ambiguity`     | very short open questions, multi-question prompts, hedged responses   |
| `inconsistency` | similar prompts with response divergence + negation flip              |
| `redundancy`    | exact-prompt duplicates                                               |
| `duplicate`     | 5-gram Jaccard `>=` threshold across (prompt + response)              |

## Curation workflow

1. `export_issues` writes `fixes.jsonl` with one record per transcript:
   `{transcript_id, action, new_prompt, new_response, reason}`.
2. A reviewer changes `action` (`keep`, `remove`, `edit`, `rewrite_response`)
   and fills in `new_response` where appropriate.
3. `apply_fixes` consumes the edited file, produces a `cleaned` dataset and
   a curation log, and (optionally) snapshots the new version.

## Versioning

`VersionStore` is a tiny, dependency-free, content-addressed dataset log:

```python
from data_quality_flywheel.versioning import VersionStore

store = VersionStore("reports/versions")
v_id = store.commit(cleaned_transcripts, "removed contradictions",
                    meta={"iteration_report": report.to_dict()})
store.history()       # list of commits
store.load(v_id)      # rehydrate that version
```

## Testing

```bash
python -m unittest discover -s data_quality_flywheel/tests
```

21 tests covering ingestion, scoring, every detector, curation actions,
the feedback report, the version store, and the CLI subcommands.

## Programmatic API (one-shot example)

```python
from data_quality_flywheel.ingestion import load_dataset, normalize
from data_quality_flywheel.analysis import score_dataset
from data_quality_flywheel.issues import detect_all
from data_quality_flywheel.curation import suggest_fixes, apply_fixes
from data_quality_flywheel.feedback import build_iteration_report

ts = normalize(load_dataset("transcripts.jsonl"))
scores = score_dataset(ts)
issues = detect_all(ts, scores)
fixes = suggest_fixes(ts, issues)            # heuristic; override before applying
cleaned, log = apply_fixes(ts, fixes)
report = build_iteration_report(1, ts, cleaned, log)
print(report.avg_score_before, "->", report.avg_score_after)
```
