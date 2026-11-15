# Decisions

Decisions that change what the manuscript reports or how results are judged. Newest first.

## 2026-11-15: report system-level performance instead of mAP@50 (per adviser consultation)

**Decision.** The manuscript reports system-level performance of the deployed pipeline, not box-level
mAP@50. The acceptance criterion of ≥ 0.80 refers to system performance (accuracy, precision, recall
or F1), not specifically to mAP@50.

**Made by.** The thesis adviser, at consultation; recorded by the team on 2026-11-15.

**What stays.** The box-level evaluation was carried out and its results are kept unchanged in the
repository as evidence: `results/test_evaluation.md` / `.json` (local test mAP@50 **0.173**, i.e.
0.17312; mAP@50-95 0.057), its pre-registered definitions `results/metric_definitions.md`, and
`results/test_eval_done.json`. They are removed from the manuscript, not from `results/`.

**What it does not change.** The deployed model, its fusion, threshold (0.25) and road band are not
retrained or changed. No model is selected on the test set. Every metric is reported as it comes out,
including low ones.

**Where the new results are.** `results/system_level_evaluation.md` (definitions and sources),
computed by `ml/local/system_level_eval.py`. The report carries the note: "These system-level
metrics were adopted after the initial box-level evaluation, at the adviser's recommendation, to
reflect how the system is used."
