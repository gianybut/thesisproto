# Second-stage classifier: what was built, what it changes, how to report it

Written 2026-11-12 from the code, the git history and the metadata stored in the checkpoint. Nothing here
was taken from the manuscript. Sources are given per statement.

## 1. What was built

Both a second-stage classifier and a view of it in the web app, in one commit:
`5d796a1` "feat: implement optional second-stage YOLO classifier for damage detection", 2026-11-12 10:40 +08:00
(13 files, +382 / -17). The classifier was trained 23 minutes before that commit, on the Windows training PC.

**Model** (read from `ml/models/classifier.pt` itself: `train_args`, `train_results`, `train_metrics`, `git`, `date`):

| Item | Value | Source |
|---|---|---|
| Architecture | YOLOv8n-cls, from `yolov8n-cls.pt` (ImageNet-pretrained), 4 classes D00 D10 D20 D40 | checkpoint `train_args.model`, `model.names` |
| Trained | 2026-11-12 10:17:49, Ultralytics 8.4.48, on `C:\Users\GIAN\Downloads\thesisproto`, branch develop at `4d46a1f` | checkpoint `date`, `version`, `git` |
| Run | `runs/classify/road_damage_retry` (a second attempt; the first, `road_damage`, is the script default) | checkpoint `train_args.name` |
| Data | `data\local\classification`, built by `ml/build_classifier_dataset.py` from `data/local/yolo_nz`: train = crops of the reviewed boxes of `local_train.txt`, val = `val_reviewed.txt`, **test = `test.txt`** (as committed in `5d796a1`) | checkpoint `train_args.data`; `git show 5d796a1:ml/build_classifier_dataset.py` |
| Crops | one per reviewed box, box plus 25% of its width/height on each side, from the 1920 x 432 near-zone frames | `build_classifier_dataset.py --padding 0.25` default |
| Crop counts | val 122 (= the 122 boxes of the 270 reviewed val frames: 100 / 122 = 0.81967, the stored top-1). Train most likely 388 (D00 165, D10 103, D20 23, D40 97: the boxes of the 526 `local_train.txt` frames in `results/local_datasets_nz_export.md`), **to confirm** from `data/local/classification/dataset_metadata.json` on the PC | checkpoint `train_metrics`; `results/local_datasets_nz_export.md` |
| Settings | 224 px, batch 32, up to 50 epochs, patience 20, optimizer auto, lr0 0.01, seed 0, deterministic, workers 0; default classification augmentation (RandAugment, erasing 0.4, fliplr 0.5, HSV) | checkpoint `train_args` |
| Training | stopped after 30 of 50 epochs (no gain for 20 epochs); kept epoch 10 | checkpoint `train_results` |
| Validation result | top-1 **0.820** (100 of 122) at the kept epoch; top-5 1.000 (meaningless with 4 classes); epoch-to-epoch top-1 0.73 to 0.82 | checkpoint `train_metrics`, `train_results` |

The kept epoch was chosen on the same 122 validation crops, so 0.820 is a selection figure (optimistic), and it is
measured on the reviewed boxes, not on the detector's boxes the app classifies.

**Runtime** (`backend/services/damage_classifier.py`, `backend/services/video_processor.py`): when
`model_config.json` has `"classifier": {"enabled": true}` (it does, since `5d796a1`), every fused detection in every
analysed frame is cut from the frame **without padding** and classified at 224 px; `conf_threshold` is 0.0, so every
detection is relabelled. The track's record takes the classifier label of its best (most confident) sighting.

**Interface** (`frontend/src/components/StatusLabel.jsx` `AiClassification`): the survey page close-up and the
Damage records review pane show "AI classification: <class> <code> · <confidence>%" (or "Detector classification"
when the record has no classifier label); the About page lists the classifier weights; the annotated video and
snapshots label each box with the classifier class and "<classifier confidence>% cls" instead of the detector
confidence. New `detections` columns: `classification_type`, `classification_label`, `classification_confidence`,
`classification_model` (`backend/models.py`, `backend/migrate.py`).

## 2. Does it change the deployed system's output?

**Yes.** It relabels. It does not add, drop, move or filter records: the tracker ignores the class
(`backend/services/damage_tracker.py`), so the number of records, their times, boxes, positions, detector
confidences and AI-check scores are the same as without it. But `Detection.damage_type` / `damage_label` are
overwritten with the classifier's class (`video_processor.py`, `save_track`), so the class on the map, in the records
list, filters, counts per class and the CSV/JSON export all come from the classifier.

**The deployed system now differs from the one evaluated in `results/test_evaluation.md`.** That evaluation (run
2026-11-11 17:09-17:27, metrics fixed at 17:05 in `7fbc094`) scored the fusion's own classes. Every per-class figure
in Chapter V (Table 5.1.2 per-class precision, recall, F1 and AP; the 96.0% classification accuracy on 25 matched
detections; Figure 5.1.1) describes the system **without** the classifier. Detection figures that ignore class
(how many damages are found at all) are unaffected only in so far as matching ignores class; the per-class and
class-accuracy figures are not.

Also differing from the evaluated system and not measured: the per-box classifier calls add processing time (the
R07 figure, 729 s for 590 s of video, was without the classifier); and the app cuts crops without padding while the
classifier was trained on padded crops.

Already affected:
- On this Mac, survey 1 (a dev video, not a study recording) was re-analysed at 2026-11-12 12:53 +08:00 with the
  classifier on: 16 of 16 records carry classifier labels (`backend/pothole_detection.db`).
- Survey 3 on the PC (R07, the damage-log sample) was analysed on 2026-11-11 before the classifier existed, and the
  checklist was drawn on 2026-11-11 17:09 (`6117fb5`). **Do not use "Analyse again" on survey 3**: it would replace
  its records and break the checklist (the review tools refuse when that happens).

## 3. Was the test set used for the classifier?

The code as committed builds crops of the 270 test frames (`'test': root / 'test.txt'` in
`build_classifier_dataset.py`) and, after training, evaluates them automatically whenever a `test/` folder exists
(`model.val(..., split='test')` in `train_classifier.py`, printing "Test top-1 accuracy"). The checkpoint shows that
the run used `data\local\classification` built by that script. So **a test top-1 accuracy was almost certainly
computed and printed at about 10:17-10:20 on 2026-11-12**, on the 99 test boxes.

- That was after the one test evaluation (2026-11-11 17:09) and with **no metric definitions for the classifier**:
  the first ones are `results/classifier_metric_definitions.md`, written 2026-11-12 after the fact.
- The number is in no file of the repository. On the PC, look in the console history and in Ultralytics' default
  runs folder (`model.val` was called without `project=`, so its output went to the global `runs_dir`, which points
  outside this repo; see CLAUDE.md) for a `classify/val*` folder dated 2026-11-12.
- It must not be reported as a result. If it is mentioned at all, it must be disclosed as an unplanned second use of
  the test set, made after the test results were known.

Fixed in this commit so it cannot happen again: `build_classifier_dataset.py` no longer makes test crops and
`train_classifier.py` no longer evaluates test. Delete `data/local/classification/test/` on the PC.

## 4. Evaluation so far (validation only)

| Measure | Value | Status |
|---|---|---|
| Top-1 on the 122 reviewed val boxes (training-style 25% crops), kept epoch | 0.820 (100 / 122) | from the checkpoint; selection figure |
| Fusion's own class on its matched val detections (reference) | 92.5% (37 / 40; 95% CI 80.1% to 97.4%) | `results/test_evaluation.md` val column (manuscript 5.1.2) |
| Classifier on the same matched val detections, as the app applies it | not yet run | `ml/local/classifier_val_compare.py` (PC; metrics in `results/classifier_metric_definitions.md`) |

The two numbers in the first rows are not directly comparable (reviewed boxes vs detected boxes; 122 vs 40), but
nothing so far suggests the classifier labels detections better than the fusion does.

## 5. Options for reporting it honestly

A. **Disable it** (`"classifier": {"enabled": false}` in `ml/models/model_config.json`, restart the backend). The
   deployed system is then exactly the test-evaluated one (with the classifier off, the code takes the
   pre-classifier path). Report the classifier as a validation-only experiment (Chapter V, after 5.1.2 or as a
   limitation) with `classifier_val_compare.py`'s result, and keep it in the Chapter VI recommendations.
   *Recommended*, and required for the repeat-drive analysis (`tools/repeat_drive.py process` refuses otherwise).
B. **Keep it on, and say so everywhere.** Chapters III-IV describe a two-stage system; Chapter V states plainly
   that the test figures were measured before the classifier was added and describe the fusion's classes, that the
   deployed system's per-class behaviour has no test figure, and gives the validation comparison only. The demo and
   UAT then show a system whose class decisions were never tested.
C. **Evaluate it on test.** Not acceptable under the rule that the test set is used once: it would be a second,
   post-hoc use of the test set (and a test figure was probably already seen). Only with an explicit decision by the
   team and the adviser, fully disclosed.

## 6. Paste-ready text (option A; fill in the validation numbers after `classifier_val_compare.py`)

**Chapter III (end of 3.3.1):**
> A second-stage classifier was also trained after the detection models had been evaluated: a YOLOv8n
> classification model (224 pixels) that re-labels each detected box as D00, D10, D20 or D40. It was trained on
> crops of the reviewed boxes of the local training frames and its best epoch was chosen on the 122 boxes of the
> 270 reviewed validation frames. It is not part of the deployed system: it was compared with the fusion's own
> class decision on the validation frames only, and the test set was not used for it.

**Chapter IV (4.2.4, after the paragraph on the pipeline changes):**
> After the test evaluation, the researchers trained an optional second-stage classifier that re-labels each
> detected damage from a crop of its box. The system can run it and show its label on the survey page and the
> damage records page, but it is switched off in the deployed system, because it was evaluated on validation
> data only and would change the damage type of every record from the one evaluated on the test set.

**Chapter V (new 5.1.x, or in 5.1.7 as a limitation):**
> On the 122 reviewed validation boxes, the second-stage classifier gave the correct type for 82.0% (100 of 122),
> a figure chosen on these same boxes. Applied as the system would apply it, to the [n] detections of the deployed
> fusion matched to a reviewed box on the 270 validation frames, it gave the correct type for [x]% ([k] of [n];
> 95% CI [a]% to [b]%), against [y]% for the fusion's own class (exact McNemar p = [p]). [It therefore did not /
> did] improve the class decision, and it was [not enabled / ...]. It was not evaluated on the test set.
