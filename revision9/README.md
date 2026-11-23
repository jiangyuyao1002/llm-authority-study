# Reference-answerability review and sensitivity

The author reviewed the 24 references with AI assistance; this was not independent blinded adjudication.
Original labels, scores and all-24-task results are unchanged. Category A means supported under ordinary table-question conventions, B requires interpretation, and C contains priority disputes.
Both the 21-task exclusion and the further 15-task analysis are post hoc relative to the original study.

Recompute the complete 24/21/15-task sensitivity and clean-correction transition records from the repository root:

```bash
python revision9/reference_sensitivity.py --scores validation/results/trial_scores.csv --review revision9/reference_review.json --plan revision9/sensitivity_plan.json --output /tmp/reference_sensitivity
```

Choose a new writable output directory appropriate to your operating system.
