# llm-authority-study

Parser replay on fixed responses: separating format compliance, recipient
authorization and answer correctness in structured LLM evaluation.

This repository contains the frozen data, scoring code, analysis scripts and
figures for the study reported in:

> Yuyao Jiang. *Format compliance and content correctness in structured LLM
> evaluation: Parser replay on fixed responses.* (preprint, 2026)

The paper audits the scoring stage of structured LLM evaluation. A single
success rate conflates three outcomes: whether the response parsed, whether it
was routed to an authorized recipient, and whether the answer was correct. We
replay **2,232 recorded responses** from two reporting experiments under two
parsers — strict whole-response JSON parsing and a rule that also accepts one
enclosing Markdown fence — and account for where each policy contrast
originates.

## Headline results

- Exploratory replay (Experiment 1): the Qwen3.5-Plus evidence-binding
  advantage over the boundary policy was **27.1 points under strict parsing**
  and **−2.1 points** after removing one enclosing fence.
- Prespecified follow-up (Experiment 2, BIPIA/WikiTableQuestions tables,
  DeepSeek-V3 added): strict-minus-normalized interaction **−41.7 points**,
  largely explained by unequal recovery of correct fenced reports near a
  rejection floor.

## Repository layout

| Path | Contents |
|---|---|
| `experiment.py` | Task construction, request collection and transport for Experiment 1 (stdlib only; reads `BAILIAN_API_KEY` from the environment) |
| `analyze.py` | Offline scoring and paired analysis of frozen responses |
| `write_results.py` | Builds result tables/figures from scored output |
| `collect_references.py`, `figure1_revision/` | Reference collection helper; reproducible source for Figure 1 |
| `data/` | Frozen Experiment 1 artifacts: `protocol.json`, `cases.json`, `responses.jsonl` (1,152 responses), `http_attempts.jsonl`, transport amendment |
| `results/` | Per-response scores (`trial_scores.csv`), condition counts, paired contrasts, summary, audit |
| `validation/` | Independent offline validation study: replayed scoring over all 2,232 responses (Experiment 1 + Experiment 2), 56,016 Boolean score comparisons |
| `qa/` | Parser run audit for the public-table labels |
| `figures/` | Paper figures (PDF/PNG/SVG) |

Experiment 2 responses and configuration are included inside `validation/`
(they were collected under the prespecified follow-up protocol).

## Reproduction

Offline replay of all scoring (no model calls, ~1 minute):

```bash
python -m pip install -r requirements.txt
python analyze.py
```

Re-collecting Experiment 1 requires access to the endpoints described in the
paper:

```bash
export BAILIAN_API_KEY=...   # Alibaba Cloud Model Studio key
python experiment.py
```

The paper's endpoints were `qwen-plus-2025-01-25` and
`qwen3.5-plus-2026-02-15` plus DeepSeek-V3 (Experiment 2), served through the
Alibaba Cloud Model Studio OpenAI-compatible Beijing endpoint. Requested and
returned model identifiers were retained and matched for every response;
provider labels identify the requested service, not underlying weight hashes.

## Data and code availability

All recorded responses, prompts, cases, per-response scores and analysis
scripts are in this repository. Files were frozen before analysis; request
SHA-256 hashes are reconstructable from the frozen cases and policies.

- Code: [MIT License](LICENSE)
- Data (`data/`, `results/`, `validation/`, `qa/`, `figures/`):
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Citation

```bibtex
@misc{jiang2026parserreplay,
  author = {Jiang, Yuyao},
  title  = {Format compliance and content correctness in structured
            {LLM} evaluation: Parser replay on fixed responses},
  year   = {2026},
  note   = {Preprint}
}
```

The public-table experiment uses BIPIA contexts
(commit `a004b69ec0dd446e0afd461d98cb5e96e120a5d0`) and
WikiTableQuestions; see `validation/ATTRIBUTION.md`.
