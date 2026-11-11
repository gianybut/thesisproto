# Manuscript change log

Revision of the OCULUBAK manuscript (Chapters I-VI) so that it matches the final system and the measured results.

- **Edited document:** "OCULUBAK Manuscript — revision draft"
  (https://docs.google.com/document/d/1SaaJn2eGL9cCUOT7B0pXqCJUZk2z4U2iLjvXZUgn6S0/edit), a Drive copy of
  "OCULUBAK CHAPTER 1-6" (https://docs.google.com/document/d/1Fr2K6TC3QqaWLNfHcDJA4bILUfp_v_5xdQrQ-W12vos/edit).
  The original is not edited.
- **Single source for numbers:** `results/FINAL_METRICS_FOR_PAPER.md` (FM below). Every number added to the
  manuscript cites FM or the file it cites.
- **Highlights in the document:** yellow = changed approved wording (for the adviser), or a `[PENDING: ...]` /
  `[FILL: ...]` placeholder. No number was invented; nothing was run on the test set.
- **"41.1%"** does not appear anywhere in the manuscript (checked 2026-11-12 on the full text, also "0.411").

---

## Chapter I (applied 2026-11-12)

| # | Section | Old → new (summary) | Sources for every number / fact |
|---|---|---|---|
| 1 | 1.1 Project Context, ¶3 | "The detection model will be fine-tuned on … approximately 1,500 annotated frames extracted from road survey footage" → "The detection models were fine-tuned on … 7,465 human-labelled frames extracted from 18 vehicle-mounted road survey recordings (2.71 hours, 78.26 km)" | 7,465: FM:196 (`results/local_datasets_nz.md:7-9`); 18: FM:188; 2.71 h: FM:189; 78.26 km: FM:190 (both computed in FM from `data/local/recordings.csv`) |
| 2 | 1.1, ¶5 (conceptual framework) | "YOLOv8m-based road damage detection on the road area of each frame" → "road damage detection and classification by three fine-tuned YOLOv8 models whose detections are combined by weighted box fusion, applied to the near zone of the road area of each frame" | FM:16-18; `ml/models/model_config.json` |
| 3 | 1.2 Purpose and Description, ¶1 | New sentences: detection includes classification (locates with a bounding box and classifies as D00/D10/D20/D40); detection evaluated by mAP, classification by the classification accuracy of detected damage, defined as the share of detections matched to a reviewed box at IoU ≥ 0.50 (any class) whose class is correct | `results/metric_definitions.md:20,39-44`; FM:131 |
| 4 | 1.2, ¶2 | "a fine-tuned YOLOv8m object detection model" → "three fine-tuned YOLOv8 object detection models, whose detections are combined by weighted box fusion"; "within road surfaces" → "within the near zone of the road surface". "About five frames per second" kept. | FM:16-18; 5 fps: FM:213 |
| 5 | 1.3 RQ1 (**highlighted**) | Added "and the classification accuracy of detected damage" to the listed measures | `results/metric_definitions.md:39-44` |
| 6 | 1.4 Hypothesis (**highlighted**) | "a fine-tuned YOLOv8m detection model" → "fine-tuned YOLOv8 detection models"; nothing else in the hypothesis changed. Stray leading space removed from the heading " 1.4 Hypothesis". | Team decision 2026-11-12; FM:16 |
| 7 | 1.5.1 General Objective (**highlighted**) | "a YOLOv8m model fine-tuned on the RDD2022 dataset and locally collected Philippine road imagery" → "three YOLOv8 models fine-tuned on locally collected Philippine road imagery from starting weights trained on the RDD2022 dataset, with their detections combined by weighted box fusion" | FM:26-32 (starting weights of v2b, v3, S5_v8m_1920 and their ancestors) |
| 8 | 1.5.2 Specific Objective 1 (**highlighted**) | "a YOLOv8m object detection model" → "YOLOv8 object detection models"; added "and the classification accuracy of detected damage" to the performance measures | FM:16; `results/metric_definitions.md:39-44` |
| 9 | 1.6, DPWH District Engineering Offices | "such as the DPWH Cavite 2nd District Engineering Office" → "in particular the DPWH Cavite 2nd District Engineering Office, the partner office of this study" | Team decision 2026-11-12 (partner office) |
| 10 | 1.6, Future Researchers | "the four-class detection results" → "the four-class detection and classification results"; "the measured positional error" → "the positional error … [PENDING: localization accuracy, Section 5.4]" (**highlighted**) | Localization in metres NOT MEASURED: FM:160 |
| 11 | 1.7 Scope and Limitations, ¶1 | Removed the duplicated opening sentence; fixed "videoframes", "cracks,and", "GPStrack", "asReact-Leaflet"; "processed using the YOLOv8m object detection model to identify road damage" → "processed by three fine-tuned YOLOv8 object detection models, combined by weighted box fusion, to identify and classify road damage" | FM:16-17 |
| 12 | 1.7, ¶2 | "trained on the India subset of the RDD2022 dataset … supplemented with locally collected road images" → fine-tuned on local images labelled by **[FILL: the three researchers / the three researchers and N volunteer annotators]** (highlighted), from RDD2022 starting weights; one model also trained with 600 RDD2022 images; new sentences defining the near zone (from one-tenth of the frame height below the horizon line to the bonnet line; a 1920 × 432-pixel strip in the evaluation data) and stating that damage farther ahead is outside the scope | 600: FM:30; 1920 × 432: FM:18; one-tenth (`NEAR_ZONE_DELTA = 0.10`): `backend/services/video_processor.py:29-33,67-71`; out of scope: FM:228-231 |
| 13 | 1.7, ¶4 | "limited to ten minutes and 500 MB" → "limited to ten minutes, so the mobile capture application saves a long recording as consecutive parts of 590 seconds, each uploaded as its own survey"; "must be uploaded again" → "must be analyzed again from the files already on the server"; fixed "server.Detection"; new sentence on the advisory CLIP AI check (Radford et al., 2021, already in the reference list): flags likely false detections, not trained on road damage, never hides or deletes, its accuracy not part of the evaluation | ten minutes: `backend/app.py:27`; 590 s: `mobile/src/config.js:9`; no size cap: `mobile/src/config.js:14-17`; reprocess: `backend/routes/videos.py` (`/reprocess`); AI check: FM:151-153 |

Unchanged in Chapter I (checked against the sources): the thread-based processing, single-file SQLite, ffmpeg and
iPhone-only sentences in 1.7; RQ2-RQ4; SO2-SO4.

Open for later chapters: who labelled on the annotation site (`[FILL]` in 1.7 ¶2, to be worded the same way in
Chapter III).
