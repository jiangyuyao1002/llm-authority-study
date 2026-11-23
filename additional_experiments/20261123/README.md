# Additive control repair and repeated-generation batch

This batch uses 24 original public-table tasks with unchanged tables, questions,
reference labels and clean/correction annotations. It collects three generations
for boundary, binding A, the original truncated neutral prompt and a completed
neutral prompt. Each extension has 43 whitespace-separated words. Completion
changes only the final word `subsequent` to `review.`.

The endpoint is `deepseek-v4-flash` at the recorded third-party API base.
The original study used Bailian `deepseek-v3`; these are different models and
service channels. This addendum is not a repeat of the original endpoint and
must not be pooled with the original 1,080 Experiment 2 observations.
The 1,024-token output cap, explicit tool definition and `tool_choice=none`
are also batch differences. No real tool or recipient action is executed.
The interface change was frozen before the first completed task response.

## Files

- `protocol.json`, `protocol.sha256`: local prospective addendum and checksum.
- `jobs.jsonl`: the 576 requests, including complete prompts and payload hashes.
- `cases.json`: unchanged original 72 task-condition cases; only clean/correction
  are used by this batch.
- `reference_review.json`: the existing author-reviewed 24-item classification.
- `responses.jsonl`, `http_attempts.jsonl`: append-only collected responses and
  transport records. Incorrect, schema-invalid and truncated responses are kept.
- `precollection_interface_v1/`: original freeze and rejected-interface record;
  no completed task responses under that version.
- `scoring.py`: the original Experiment 2 scorer functions, unchanged.
- `analyze.py`: the analysis fixed before collection.
- `analyze_isolated.py`: local import wrapper for running that analysis under
  Python's isolated mode; it does not change the frozen analysis.
- `results/`: counts, task-level paired contrasts, replicate-specific contrasts,
  per-task correct-out-of-three counts and collection audit.

## Reproduce scoring and analysis

Requires Python and NumPy. Run from a copy of this complete directory:

```bash
python -I analyze_isolated.py
```

This performs no API calls. All 576 responses are required for final contrasts.
Original 24-task results remain primary for the original experiments.
The addendum reports full-24, exclude-C-21 and A-only-15 estimates separately.
The subsets use the prior author review; they are not independent adjudications.

## New collection

Use an empty copy for new data collection and retain this frozen batch. The key
is read only from an environment variable; no credential belongs in this folder.

```bash
python -I run.py --run --key-env STUDY_API_KEY
```

The API base and model must agree with the frozen protocol. The runner preserves
completed responses on resumption and retries transport failures, not wrong answers.
Protocol scripts and inputs are hashed. Do not edit the frozen experiment scripts
and then resume it as though the requests were unchanged.

Tables, questions, reference answers and adapted inputs retain CC BY-SA 4.0.
See the parent artifact's upstream attribution and licence notices. Study-written
software is MIT; author-created outputs use CC BY 4.0 subject to third-party terms.
