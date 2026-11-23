# llm-authority-study

Data, scoring code and analysis for Yuyao Jiang, *Format compliance and content correctness in structured LLM evaluation: Parser replay on fixed responses* (preprint, 2026).

## Original experiments

The original two experiments contain 2,232 frozen responses: 1,152 synthetic-report responses in Experiment 1 and 1,080 public-table responses in Experiment 2. Parser replay holds these responses fixed and separates format compliance, recipient authorization and answer correctness.

- E1 Qwen3.5-Plus: evidence-binding minus boundary was +27.1 percentage points under strict parsing and -2.1 after accepting one enclosing fence.
- E2 correction interaction: Qwen-Plus 0.0, Qwen3.5-Plus -29.2, DeepSeek-V3 -41.7 points. DeepSeek-V3 strict scores are near a rejection floor; the interaction adds limited information beyond the normalized contrast there.
- The reference review and 24/21/15-task sensitivity preserve original references and main results. The review is author checking with AI assistance, not independent adjudication.

## Layout

| Path | Contents |
|---|---|
| `data/`, `results/` | Frozen E1 inputs, responses, scores and original analyses |
| `validation/` | E2 public-table inputs, protocol, 1,080 responses, collection and scoring scripts |
| `revision4/` | Supplementary parser implementation audit |
| `revision6/` | First-object comparator, frozen replay records and two retained edge responses |
| `revision9/` | Author reference review, fixed exclusions, 24/21/15-task sensitivity and recomputation script |
| `revision10/` | Fixed-commit benchmark audit manifest, licence notices, updated figure source and clean-correction transitions |
| `supplementary/` | Manuscript Files S1-S4 and their index |
| `manuscript/` | Current JSS PDF and complete English arXiv source archive |
| `qa/audit_replay.py` | Portable offline verification of all 56,016 original Boolean score fields and first-object agreement |
| `figures/` | Manuscript figures; three updated figures retain the original numeric source |

## Offline verification

The core score replay uses only Python's standard library and makes no model calls:

```bash
python qa/audit_replay.py
```

For the reference sensitivity, install NumPy and follow `revision9/README.md`.
Original collection scripts read `BAILIAN_API_KEY` from the environment. Re-running them is a new collection and must not overwrite the frozen responses.

## Models and scope

The original endpoints were `qwen-plus-2025-01-25`, `qwen3.5-plus-2026-02-15` and `deepseek-v3`, all through Alibaba Cloud Model Studio's Beijing OpenAI-compatible endpoint. Identifiers describe the returned service, not verified weight hashes. E2 has one generation per original task-condition-policy cell; task bootstrap intervals do not separately estimate generation variance. The truncated word-count prompt remains part of the historical protocol and is explicitly documented.

## Licences and provenance

Software is MIT-licensed. Author-created data and figures are offered under CC BY 4.0, subject to third-party exceptions. BIPIA/WikiTableQuestions tables, questions, reference answers and the adapted table-input dataset retain CC BY-SA 4.0. Those exceptions apply to `validation/cases.json` and copied source tables/questions; they are not overridden by the general output terms. See `LICENSE`, `validation/ATTRIBUTION.md`, `revision10/LICENSES.md` and retained upstream notices.

The table inputs derive from BIPIA commit `a004b69ec0dd446e0afd461d98cb5e96e120a5d0` and WikiTableQuestions. This adapted diagnostic evaluation is not official BIPIA scoring.

## Citation

```bibtex
@misc{jiang2026parserreplay,
  author = {Jiang, Yuyao},
  title = {Format compliance and content correctness in structured {LLM} evaluation: Parser replay on fixed responses},
  year = {2026},
  note = {Preprint}
}
```

## Additional control and repeated-generation batch

`additional_experiments/20261123/` contains a separately frozen 576-response
batch using `deepseek-v4-flash` through the recorded third-party API service.
It crosses the same 24 tasks, clean/correction conditions, boundary, binding A,
complete control and the original truncated control, with three generations
per cell. Both controls and binding A have 43 whitespace-separated words.

This is a new model and service channel with a different token cap and an
explicit tool declaration; it is not same-endpoint replication of original
DeepSeek-V3 or Qwen results. Original 2,232 responses and results remain separate.
All 576 new responses, including failures of the task contract, are retained.
The analysis averages repetitions within task, resamples 24 paired task means,
and reports repetition-specific estimates and the prior 21/15-task sensitivities.

Run `python -I analyze_isolated.py` inside the additional batch directory to
reproduce it without API access. Credentials are supplied through environment
variables only; no API credential is included in this repository.

The current manuscript source archive is `manuscript/arxiv_source_v9_20261123.zip`;
earlier named source archives are historical. Supplementary File S4 contains
the complete additive batch as a self-contained archive. See `revision11/`
for the corresponding manuscript sections.
