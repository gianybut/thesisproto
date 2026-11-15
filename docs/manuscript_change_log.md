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

---

## Chapter II and reference list (applied 2026-11-12)

Citations were verified on 2026-11-12 against the publisher, arXiv, Hugging Face and PyPI pages (URLs in the
reference entries below). Literature figures quoted in Chapter II come from those sources, not from our results.

| # | Section | Old → new (summary) | Sources |
|---|---|---|---|
| 1 | 1.1, ¶3 (Chapter I) | "and Pham et al. (2024)" → "and Jin et al. (2025)" | see reference fix 13 |
| 2 | 2.1, ¶3 | "Pham, Pham, and Dang (2022) implemented a real-time road damage detection system using deep learning-based image analysis … YOLO-based models could accurately identify road defects" → "Pham et al. (2022) applied YOLOv7 to the multinational road images of CRDDC 2022, adding a coordinate attention mechanism, label smoothing, and an ensemble of models, and showed that YOLO-based models could detect and classify longitudinal, transverse, and alligator cracks and potholes" | arXiv:2211.00091 |
| 3 | 2.1, ¶4 | "Pham et al. (2024), who analyzed successive improvements in YOLO models … robustness under varying environmental conditions …" → "Jin et al. (2025), who proposed AVD-YOLO … multi-scale feature extraction and a position-modulated attention mechanism … built a dataset of nine road anomaly types" (last sentence of the paragraph kept) | doi:10.3390/info16121064 |
| 4 | 2.1, new ¶ after the PaveSync (Asamoah) paragraph | RDD2022 benchmark context: model cards report mAP@50 of about 0.60-0.63 (YOLOv8s 0.5995, 3-seed mean; YOLOv12s 0.6192; YOLOv12m 0.6325; SreekarAditya, 2026; YOLOv8m 0.6203, dronefreak, 2026); splits differ, not comparable with each other or with Philippine roads. Placed after the PaveSync paragraph rather than directly after the RDD2022 paragraph, because the PaveSync paragraph opens with "Similarly" and refers back to RDD2022. | `results/pretrained_sources.md:9-11`; `results/train_runs.md:81`; both model cards (checked 2026-11-12) |
| 5 | 2.1, new ¶ after the transfer-learning (Alwahhab) paragraph | CLIP (Radford et al., 2021): image-text model, zero-shot classification; used in this study as an advisory check that flags likely false detections without hiding or deleting them. No numbers. | FM:151-153; `backend/services/damage_verifier.py` |
| 6 | 2.2, new ¶ after the Bustria et al. paragraph | Dated limited search: November 2026, GitHub, Hugging Face, Roboflow Universe and Kaggle; no publicly available Philippine-trained road damage model or dataset found; stated as a limited search, not a claim that none exists | Team statement 2026-11-12 |
| 7 | 2.2 | **Removed** the whole paragraph "The importance of localized deep learning systems was further explored by Sarmiento and Reyes (2022), who developed a deep learning-based road damage classification system for Philippine highways. Their research utilized convolutional neural networks to classify potholes and road cracks using locally trained datasets. The researchers concluded that models trained on Philippine road data achieved improved detection performance and classification accuracy compared to systems relying on foreign datasets, reinforcing the significance of localized model development." 2.2 now runs Sarmiento (2021) → "Another significant local study was conducted by Manalo et al. (2022) …", which reads without a change. | Reference could not be verified (no record of the title, authors or journal found) |
| 8 | 2.3 Synthesis | Added after "… Philippine LGUs and infrastructure agencies.": "A limited search of public repositories in November 2026 also found no publicly available road damage model or dataset trained on Philippine roads (Section 2.2)." | as 6 |
| 9 | 2.3.1 Synthesis Table | Pham et al. (2022) row: focus, method and finding cells reworded for the YOLOv7 paper. Pham et al. (2024) row → Jin et al. (2025): author, focus, method and finding cells reworded (implication cell kept). Terven row: "YOLOv8m as the detection model … the specific variant used" → "YOLOv8 as the detection architecture … the variants used (YOLOv8s and YOLOv8m)". Arya row: "Its India subset serves as the secondary dataset for training and evaluating the proposed system," → "Its images supply the starting weights of the proposed system's models, replay images for one model, and the foreign test subset,". Sapkota row: "(YOLOv8m) for real-time road survey video processing" → "(YOLOv8) for processing road survey video" (the system is not real time: 590 s analysed in 729 s). Alwahhab row: "YOLOv8m" → "YOLOv8 models". | FM:16, FM:26-32 (starting weights, replay), FM:105-116 (foreign test), FM:213 (729 s) |
| 10 | 2.3.1 Synthesis Table | **Pending, needs a manual step:** delete the Sarmiento & Reyes (2022) row; insert a row below the Asian Development Bank (2026) row for Radford et al. (2021). The connector cannot insert or delete table rows; the Radford row text is filled in after the row exists. | — |
| 11 | All chapters | "Arya et al., 2022" / "Arya et al. (2022)" → 2024 (six citations: Chapters I-IV and the synthesis table) | reference fix 12 |

Reference list:

| # | Entry | Old → new |
|---|---|---|
| 12 | Arya et al. | (2022) … *Geoscience Data Journal*. https://rmets.onlinelibrary.wiley.com/doi/10.1002/gdj3.260 → (2024) … *Geoscience Data Journal, 11*(4), 846–862. https://doi.org/10.1002/gdj3.260 (verified journal version) |
| 13 | Pham et al. (2022) | "Pham, V., Pham, C., & Dang, T. (2022). Real-time road damage detection system on deep learning based image analysis. IJACSA, 13(9). [URL of a different paper: Kulambayev et al., 2024, IJACSA 15(9), Mask R-CNN]" → "Pham, V., Nguyen, D., & Donan, C. (2022). *Road damages detection and classification with YOLOv7* (arXiv:2211.00091). arXiv. https://arxiv.org/abs/2211.00091" |
| 14 | Pham et al. (2024) | Removed ("Successive improvements in YOLO architectures for detecting road anomalies", IEEE T-ITS: no such paper found; its URL was Jin et al., 2025). Added in alphabetical place: "Jin, M., Zhu, Z., Tu, R., Lv, A., & Yu, Z. (2025). AVD-YOLO: Active vision-driven multi-scale feature extraction for enhanced road anomaly detection. *Information, 16*(12), Article 1064. https://doi.org/10.3390/info16121064" |
| 15 | Sarmiento (2021) | "Sarmiento, J. A. (2021). Pavement distress detection using YOLOv4 and DeepLabv3 on pavements in the Philippines. *IET Intelligent Transport Systems*." (venue not verifiable) → "Sarmiento, J.-A. (2021). *Pavement distress detection and segmentation using YOLOv4 and DeepLabv3 on pavements in the Philippines* (arXiv:2103.06467). arXiv. https://arxiv.org/abs/2103.06467" |
| 16 | Sarmiento & Reyes (2022) | Removed (not verifiable; see 7) |
| 17 | New | "dronefreak. (2026). *YOLOv8m finetuned on RDD2022 road damage* [Model weights, AGPL-3.0]. Hugging Face. https://huggingface.co/dronefreak/rdd2022-yolov8m" (no real name or date on the card; year = revision used, 2026-10-01, `results/pretrained_sources.md:11`) |
| 18 | New | "SreekarAditya. (2026). *YOLO × RDD2022 benchmark* [Model weights, CC BY 4.0]. Hugging Face. https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark" (CC BY 4.0 attribution for v2b's starting checkpoint; year = revision used, 2026-04-24, `results/pretrained_sources.md:9`) |

New and changed entries use the list's existing format: 0.5 in indent, journal name and volume (or a stand-alone
title) in italics, plain URLs (as 25 of the 27 existing entries).

---

## Chapter III (applied 2026-11-12)

Placeholders left by the team's answers (highlighted): annotation-site labellers `[FILL: the three researchers / the
three researchers and N volunteer annotators]` (3.4.3 and 3.7, same wording as 1.7); UAT dimensions
`[FILL: dimensions of the evaluation questionnaire]` (3.6 and 3.8.5); `[FILL: exact name of the DPWH Batangas office]`
(3.6). Equations the API cannot create are highlighted `[EQUATION n: …]` lines for the team to convert with
Insert › Equation.

| # | Section | Old → new (summary) | Sources |
|---|---|---|---|
| 1 | 3.1.1-3.1.2 (phase bullets) | "initial YOLOv8m inference service" → "YOLOv8"; "India subset of RDD2022" → "six countries of RDD2022"; "Fine-tuning YOLOv8m on the combined dataset and adjusting its hyperparameters" → fine-tuning YOLOv8 models from RDD2022 weights and choosing models/fusions on reviewed val (no tuning); threshold "on the reviewed validation frames"; "cross-frame de-duplication" → "cross-frame tracking … and the fixed-spot filter"; "the model" → "the deployed models" | FM:26-32; `results/train_runs.md:27` (no `model.tune`) |
| 2 | 3.2.1 | Stage 2: near zone analysed by three fine-tuned YOLOv8 models combined by weighted box fusion; stage 5: snapshot plus advisory AI check score | FM:16-18, FM:153 |
| 3 | 3.3.1 heading, caption, ¶1 | "3.3.1 YOLOv8m Deep Learning Algorithm" → "3.3.1 YOLOv8 Deep Learning Algorithm and Weighted Box Fusion"; caption "YOLOv8m Architecture…" → "YOLOv8 Architecture…"; "YOLOv8m has three parts" → "a YOLOv8 model has three parts"; added that YOLOv8s and YOLOv8m share the structure | FM:26-30 |
| 4 | 3.3.1 ¶3 (planned 640 px, batch 16, 100 epochs, patience 20, AdamW 0.001, shear/vertical flip/mixup) | Replaced with what was done: three models, Ultralytics 8.4.48 (Jocher et al., 2026), RTX 4060 8 GB, seed 42; augmentation HSV, rotation ±5°, translation, scaling, horizontal flip, mosaic (closed for the last epochs); no shear, vertical flip or mixup; no tuning; best.pt on mAP@50-95, models compared on mAP@50. New ¶ on each member's lineage (v2b YOLOv8s from the CC BY 4.0 checkpoint trained by its author at 640 px for 100 epochs; S5_v8m_1920 from the teacher trained on 5,750 RDD2022 images, 600 replay images; v3 from S5 on local frames only; S5 stopped at epoch 10 of 40) | `runs/local/v2b/args.yaml`, `runs/local/v3/args.yaml`, `runs/v3/S5_v8m_1920/args.yaml` (seed 42; hsv 0.015/0.7/0.4, degrees 5, translate 0.1, scale 0.5, shear 0, flipud 0, fliplr 0.5, mosaic 1, mixup 0); FM:24, FM:26-34; FM:227; `results/train_runs.md:27, 81`; RTX 4060: CLAUDE.md |
| 5 | 3.3.1, new Table 3.3.1 "Training of the Three Fused Models" (+ Note) | v2b (YOLOv8s): external RDD2022 checkpoint; 4,783 local per epoch; no replay; 1,024/1,024; 12, SGD, 0.001; 40/40/13. v3 (YOLOv8m): S5_v8m_1920; 4,783 local; none in this stage; 1,280/1,280; 4, SGD, 0.001; 20/20/16. S5_v8m_1920 (YOLOv8m): B v2; 814 local + 600 RDD2022; 600 images; 1,920/1,280; 2, AdamW, 0.0005; 40/10/8. Note: 4,783 = every damage frame, D10/D20/D40 frames ×3, 1,500 no-damage frames. Cells Times New Roman 11, bold header, as Table 3.4.3. | FM:28-31; `results/train_runs.md:19` |
| 6 | 3.3.1, new ¶ (fusion) and ¶ (input) | Members at conf 0.05, NMS IoU 0.45; weighted box fusion (Solovyev et al., 2021), cluster IoU 0.55, fused box = confidence-weighted mean, fused score = sum ÷ number of models (Equation 12); kept at ≥ 0.25, chosen as max overall F1 over 0.01-0.50 on the 270 reviewed val frames. Near zone (one-tenth of frame height below the horizon to the bonnet; 1920×432 in the evaluation data), 24 px grey border; v2b 1,024, v3 and S5 1,280; S5 at 1,280/1,600/1,920 gives mAP@50 0.200/0.205/0.201; no TTA | `backend/services/box_fusion.py:1-12` (FUSE_IOU 0.55); `backend/services/video_processor.py:29-33, 51`; `ml/models/model_config.json`; FM:17-20; FM:232 |
| 7 | 3.3.2 Algorithm 3.1 | Label "3.3.2 Algorithm:" → Heading 3 "3.3.2 Algorithm"; title "…De-duplication, and Positioning" → "…Fusion, Tracking, and Positioning". Pseudocode from the M/c_min/t_nms inputs to the end rewritten (inputs top/bot, M1..M3, c_min 0.25; near-zone crop with 24 px border; three models at conf 0.05; fusion and threshold; UpdateTracks; DropFixedSpots; per track: best sighting, GPS interpolation, snapshot, AI check; 32 lines). Bordered Courier New 9.5 pt box kept. | `backend/services/video_processor.py:260-289, 420-600`; `backend/services/damage_tracker.py:37-42` |
| 8 | 3.3.2 rules | Rule 2 "Confidence filtering" → "Near zone"; rule 3 "Non-maximum suppression" → "Detection and fusion" (0.05, 0.45, fusion, 0.25); rule 4 "Cross-frame de-duplication" (100-px grid, 2-s window) → "Cross-frame tracking" (nested ≥ half, IoU ≥ 0.15 or centre in the area below, closed after 1 s, stored once from its best sighting; duplicates measured in Section 3.8.3); new rule 5 "Fixed-spot filter" (≥ 3 tracks at one spot, one still ≥ 1 s); new rule 6 "AI check" (CLIP ViT-B/16, flagged below 0.6, advisory); rule 9 "resized model input" → "cropped and resized model input". Rules 1, 7, 8 unchanged; new rules are items of the same numbered list. | `damage_tracker.py:37-42`; `damage_verifier.py:30-33`; `video_processor.py:520-560` |
| 9 | Equations 1-3 "where" lines | E "at most 100" → "at most 40"; "B = 16" → "B (12, 4, and 2 for the three models, Table 3.3.1)"; p "640 × 640, p = 409,600" → pixels of a model's input, summed over the three models; m "the detector's limit" → "each model's limit" | FM:28-30 |
| 10 | 3.3.3 | Throughput "in Chapter IV" → "Chapter V"; letterbox "a frame into the square model input" → "the near-zone crop into the model input"; "T … (640)" → "(1,024 for v2b; 1,280 for v3 and S5_v8m_1920)"; IoU also used in weighted box fusion (≥ 0.55) and tracking; "De-duplication key." + Equation 12 (equation object deleted) → "Weighted box fusion." + highlighted `[EQUATION 12: …]` | `model_config.json`; `box_fusion.py:1-12` |
| 11 | 3.4 (Figure 3.4 text) | Upper lane rewritten (RDD2022 six countries → starting model; local frames split by route group, labelled, three models fine-tuned; selection and threshold on reviewed val; fusion deployed; one local test; members on foreign test). Lower lane: "ten minutes and 500 MB" → "ten minutes"; processing crops the near zone, runs three models and fuses, joins sightings, removes fixed spots; each record stored with snapshot and AI check score | FM:16-40, 103-116; `mobile/src/config.js:14-17` |
| 12 | 3.4.1 | Application tier: inference engine runs the three models on the near zone and fuses boxes; post-processor applies the fused threshold, tracking and fixed-spot filter; CLIP AI check; "must be uploaded again" → "must be analyzed again from the files already on the server". Data tier: "fine-tuned YOLOv8m weights" → the three models' weights, the settings file, the CLIP model | CLAUDE.md (reprocess); `model_config.json` |
| 13 | 3.4.2 | "limits each recording to 590 seconds … enough free storage" → saves consecutive 590-s parts, each its own survey; at least 2 GB free | `mobile/src/config.js:9, 28` |
| 14 | 3.4.3 Secondary dataset | India subset, 9,665 images, Philippine-similarity rationale → RDD2022 (Arya et al., 2024), six countries (Czech Republic, India, Japan, Norway, United States, China motorbike); 15% per country held out (seed 42) = 3,277-image foreign test; 5,750 images trained the teacher; 600 replayed into S5_v8m_1920 | FM:32, FM:105; FM:30; countries: `runs/eval/final_*_foreign_test_*` |
| 15 | 3.4.3 Primary dataset | Mendez-Nuñez only, two lighting conditions, damage frames selected, target 1,500 → 21 recordings in Tagaytay City, Mendez-Nuñez and Alfonso; R01-R03 hand-held excluded; 18 mounted (R04-R21), 2.71 h, 78.26 km; team-approved road bands for R04-R14; 1 frame/s → 9,778 frames, 9,590 after near-duplicate removal; near zone only | FM:187-192; `ml/local/road_band_overrides.csv` |
| 16 | 3.4.3 "Annotation." → "Labeling." | Model-assisted drafts reviewed by "the researchers"; 12%/≥ 20 per class engineer sample → as done: 1,066 frames (270 val, 270 test, 526 train) by one researcher in the review tool from draft boxes (stand-in model and teacher for val/test; teacher and earlier local models for train); no-damage test frames self-checked; val/test chosen in two batches (draft-box frames + random; then half teacher-detected D10/D20/D40 frames, half random, ≥ 3 s apart). 5,045 train + 1,354 val frames on the annotation website by `[FILL]`, from S5_v8m_1280 pre-drawn boxes corrected by hand; 22% of site val boxes kept unchanged; site frames not used for selection; no unreviewed model box used for training | FM:196-198, FM:205; `ml/local/select_review.py:1-12`; `ml/local/select_review_more.py:1-20`; `results/step2_review_batch2.md:1-8`; `results/step2_review_train_batch.md`, `step2_review_AL_batch.md`, `step2_review_AL2_batch.md`; `results/train_runs.md:8-9` (22%); CLAUDE.md (self-check; human-reviewed labels only) |
| 17 | 3.4.3, new ¶ | 7,465 labelled near-zone frames (5,571 / 1,624 / 270), 3,695 boxes (D00 1,700, D10 714, D20 237, D40 1,044); DPWH Batangas engineer will check 40 boxes (10 per class) on a two-page sheet and sign a certification letter `[PENDING: expert validation]` | FM:196, FM:203 (computed in FM); FM:161 |
| 18 | 3.4.3 Splitting | 70/15/15 by survey route → by route group: 15 groups (14 used); train 8 groups/6,103 frames, val G04, G06, G10/1,717, test G05, G13, G15/1,661; 50 m rule dropped 109 (val 19, test 90); only 270 test-group frames labelled (207 no damage, 99 boxes); 270 reviewed val frames (122 boxes) = selection set, all 1,624 reported beside it | FM:193-195, FM:199, FM:202, FM:204; `results/step1_split.md:9-13` |
| 19 | Table 3.4.3 | Caption "Planned Composition" → "Composition"; secondary row: RDD2022 (Arya et al., 2024), six countries / 15% per country held out (seed 42) / foreign test 3,277, teacher 5,750, replay 600; primary row: 18 vehicle-mounted iPhone recordings, Tagaytay City, Mendez-Nuñez, Alfonso / by route group (8/3/3) with the 50 m rule / 7,465 frames (5,571/1,624/270), 3,695 boxes | as 14-18 |
| 20 | 3.5.1 | "3.5.1. Use Case Diagram" (plain text) → Heading 3 "3.5.1 Use Case Diagram" | — |
| 21 | 3.6 | Partner: Municipal Engineering Office of Mendez-Nuñez → DPWH Cavite 2nd District Engineering Office; "municipal engineers" → "engineers"; fallback recruitment → `[FILL: exact name of the DPWH Batangas office]`; Batangas engineer "is not a respondent" → may also be a respondent, disclosed, results with and without; "Section 3.4.4" → "Section 3.4.3"; assessed dimensions → `[FILL: dimensions of the evaluation questionnaire]` | Team decisions 2026-11-12 |
| 22 | 3.7 | **Removed the duplicated block** (the second copy of the six subsections "Privacy, Anonymity, and Confidentiality" to "Responsible Use of AI"; the first copy was kept because its head indents match the other heads). In the kept copy: "The YOLOv8m model is trained…" → "The detection models are trained…" + the AI check stores only a score; "how the YOLOv8m model processes" → "how the detection models process"; frames shared with `[FILL]` on the annotation website and the DPWH engineer; "evaluation reported in Chapter IV will use only … YOLOv8m model" → Chapter V, the fusion of the researchers' three models, external CC BY 4.0 checkpoint credited (SreekarAditya, 2026) | FM:233 (caveat 6) |
| 23 | 3.8 intro | Cross-references fixed: RQ2 → 3.8.3, RQ3 → 3.8.4, RQ4 → related UAT dimensions in 3.8.5, agreement → 3.8.2, hypothesis → 3.8.5 | — |
| 24 | 3.8.1 | Heading H2 → H3. ¶1 rewritten: local test (270 frames, 99 boxes) primary, deployed fusion; foreign test (3,277 images) secondary, members alone; one-to-one matching, highest IoU first. New ¶: P/R/F1 at 0.25 with app settings, Wilson 95% intervals (Equation 23). AP: 101-point interpolation over all confidences; mAP@50-95 beside mAP@50. New: classification accuracy of detected damage (IoU ≥ 0.50, any class; `[EQUATION 22]`), reported with recall and the matched count, 4×4 matched-pairs table; Wilson interval (`[EQUATION 23]`, z = 1.96); high-confidence operating point (lowest threshold with reviewed-val precision ≥ 0.80). Confusion-matrix sentence: Ultralytics matrices for the foreign test, the 4×4 table for the local test. Old threshold sentence → new ¶ "Model selection and the test" (reviewed val only; best.pt on mAP@50-95; metrics committed 11 Nov 2026 17:05; single test run started 17:09). Acceptance criterion paragraph unchanged. | `results/metric_definitions.md:1-71`; FM:7-8, 38, 103-116, 118-147, 226-227; `results/test_evaluation.md:44`; `runs/eval/final_*_foreign_test_*/confusion_matrix.png`; commit `7fbc094`; `results/test_eval_done.json` |
| 25 | 3.8.2 | "stratified sample described in Section 3.4.4 … per class" → "sample of 40 boxes described in Section 3.4.3, 10 per damage class, … per class and overall"; labels (22), (23) → (24), (25) | FM:161 |
| 26 | 3.8.3 | "from the evaluation surveys" → 50 records drawn at random (seed 42) from survey 3 (R07, a validation route in Alfonso); "de-duplication rule described in Section 3.3.1" → "cross-frame tracking (Section 3.3.2) can still split one damage into two records"; label (25) → (26) | FM:159; `results/train_runs.md:72-75` |
| 27 | New 3.8.4 Localization Accuracy (Heading 3) | Field validation of 20-30 damages (procedure from the manuscript's own 4.1.3/4.1.4), Haversine formula `[EQUATION 27]` (R = 6,371 km), mean/SD/max, related to GPS rate, time offset, clock skew, frame rate; `[PENDING: localization accuracy]` | FM:160 (not measured) |
| 28 | 3.8.4-3.8.6 → 3.8.5-3.8.7 | Headings renumbered; "Table 3.8.4" → "Table 3.8.5"; "Table 3.8.8" → "Table 3.8.7"; UAT "five dimensions: …" → `[FILL: dimensions of the evaluation questionnaire]`; labels (27)-(30) → (28)-(31) | — |
| 29 | Table 3.8.7 | "Ultralytics YOLOv8" → "… (version 8.4.48)", purpose adds mAP@50-95; Python row adds weighted box fusion, classification accuracy, Wilson intervals; "Roboflow / Model-assisted annotation of the local dataset" → "Review tool and annotation website built by the researchers / Labeling of the local dataset by correcting pre-drawn draft boxes" | FM:227 (Ultralytics 8.4.48) |
| 30 | References | Jocher et al.: (2023) "Version 8.0.0" → (2026) "Version 8.4.48" (released 2026-05-08, PyPI). Added "Solovyev, R., Wang, W., & Gabruseva, T. (2021). Weighted boxes fusion: Ensembling boxes from different object detection models. *Image and Vision Computing*, [CITATION NEEDED: volume], Article 104117. https://doi.org/10.1016/j.imavis.2021.104117" (authors, title, journal, year, article number and DOI verified via arXiv:1910.13302; the volume could not be confirmed) | — |

Equation numbering after Chapter III: 1-11 unchanged; 12 weighted box fusion (placeholder); 13-21 unchanged;
22 classification accuracy (placeholder); 23 Wilson interval (placeholder); 24-25 kappa; 26 damage log correctness;
27 Haversine (placeholder); 28-30 UAT; 31 percentage. Each label (1)-(31) appears once (checked).

Figures that are images and need redrawing by the team: 3.1, 3.2.1, 3.3.1, 3.4, 3.4.1 (what each must show is in the
Chapter III report to the team).

---

## Chapter IV, and an addition to 3.5 / 3.5.1 (applied 2026-11-12)

Tense rule applied: work with a result file stays in the past tense; UAT, field validation, the engineer's check,
device tests, the damage log check and the online deployment are written as planned, each with a highlighted
`[PENDING: …]`. "partner offices" → "participating offices" in Chapter IV (team decision). New highlighted placeholders:
`[FILL: exact name of the DPWH Batangas office]`, `[FILL: dimensions of the evaluation questionnaire]`, the
annotation-site `[FILL]`, `[FILL: confirm the instrument …]` (4.4.4), `[FILL: Yes, recording ___ was uploaded from the
phone app … / No: … upload script …]` (4.2.5), `[FILL: hosting service or server]`, `[FILL: address]`,
`[FILL: ASUS ROG Strix G17 …]`, `[FILL: iOS version]`, `[FILL: storage …]`, `[FILL: weeks]` ×5, `[PENDING: n]`.

| # | Section | Old → new (summary) | Sources |
|---|---|---|---|
| 1 | 3.5, 3.5.1 | Administrator also "view the activity log, and correct or delete detection records"; the administrator actor is connected to managing accounts, viewing the activity log, and correcting or deleting records (Figure 3.5.1 image must be redrawn to match) | CLAUDE.md (Roles table) |
| 2 | 4.1.1, Table 4.1.1 | Quantitative side: detection and classification metrics of the deployed fusion (measured); positional error, damage-log correctness and ratings still to be gathered `[PENDING]`; qualitative side future. RQ1 measure adds classification accuracy; local test (primary), foreign (secondary) | FM §2, §8 |
| 3 | 4.1.2 | Primary data: footage, GPS tracks and labelled frames (done); field reference positions and questionnaire responses of DPWH Cavite 2nd DEO and `[FILL Batangas]` pending. Secondary: "India subset … foreign training and testing data" → six countries of RDD2022 (starting weights, replay images, foreign test); "the model behaves" → "the models behave" | FM:30-32, 105 |
| 4 | 4.1.3 item 1 | "[n] separate drives" and "at least two lighting conditions" (removed) → 21 recordings, 3 hand-held excluded, 18 mounted used (2.71 h, 78.26 km); recorded in daylight on 31 October 2026, 9:41-11:08 a.m., and 3 November 2026, 9:11 a.m.-12:00 noon (Philippine time), from the first and last GPX points; team-approved road bands for R04-R14 | FM:187-190; GPX files of R04-R21 in `VID+GPX/` (first/last `<trkpt>` times, UTC+8; read 2026-11-12); `ml/local/road_band_overrides.csv` |
| 5 | 4.1.3 item 2 | Roboflow, damage frames only, engineer reviewed → 1 frame/s (9,778), near-duplicates removed (9,590), near zone; review tool 1,066 frames (one reviewer) and annotation website 6,399 frames by `[FILL]`; engineer check of 40 boxes `[PENDING]`; six RDD2022 countries | FM:191-198 |
| 6 | 4.1.3 items 3-4 | Field validation and respondents' evaluation → future tense with `[PENDING]`; dimensions → `[FILL]` | FM:160, 162 |
| 7 | 4.1.4 | Respondents → future, DPWH Cavite 2nd DEO (partner) and `[FILL Batangas]`, `[PENDING: n]`; annotation check 12%/≥ 20 → 40 boxes, 10 per class; damage-log check `[n]` → 50 records (seed 42) of survey 3, checklist prepared, not filled `[PENDING]` | FM:159, 161 |
| 8 | 4.1.5 | Detection: local test (fusion, once) and foreign test (members alone), P/R/F1 at threshold, classification accuracy, Wilson intervals, "Equations 19 to 23" → "17 to 23"; confusion matrices (Ultralytics for foreign, matched-pairs table for local). Agreement, positional error, damage log, questionnaire → future + `[PENDING]`; with/without the engineer "if that engineer takes part" | `results/metric_definitions.md`; FM §2, §5 |
| 9 | 4.1.6 | Validity ¶ rewritten: test never used for training/selection/threshold; selection on the 270 reviewed val frames; metrics fixed before the single test; route-group split + 50 m rule; engineer check and kappa pending. Reliability: hardware "(Section 4.3.2)"; respondents future | FM §6, FM:193-195 |
| 10 | 4.1.7 | Consent → future; "the model was trained" → "the detection models were trained"; access "partner offices" → "participating offices"; online copy future; deletion "will be … by a task that will be scheduled on the server" | `backend/purge_uploads.py` (not scheduled) |
| 11 | 4.1.8 | "partner offices" → "participating offices" (login, records) | — |
| 12 | 4.2.1 | "background processing with YOLOv8m on the road area" → "with three fused YOLOv8 models on the near zone of the road band" | FM:16-18 |
| 13 | 4.2.2 | FR7: near zone, three models at 1,024 and 1,280 px, weighted box fusion. FR8: NMS within each model, fuse, discard fused detections below the calibrated threshold. NFR4: "by a task that will be scheduled on the server". NFR10: weights files and the settings file. NFR11: "participating offices". NFR1 unchanged | `model_config.json`; FM:16-20 |
| 14 | 4.2.3 | Worker runs the three models and fuses their boxes on the near zone; data tier holds the three weights, the settings file and the CLIP model | — |
| 15 | 4.2.4 | Sprint 1 "initial YOLOv8m model" → "YOLOv8"; sprint 2 rewritten (six-country starting model, local dataset, several models compared on reviewed val, three fused, threshold on the same frames); sprint 5 done vs pending `[PENDING]`; **removed** "; on one 3.5-minute survey, the stand-in model returned 13 boxes at 640 and 157 at 1280" (no result file); added three later changes (near zone, 24 px border, fusion); "[1280 or 1024] … [B] … [value] … [n] … [n]" → v2b 1,024/12, v3 1,280/4, S5 1,920→1,280/2, threshold 0.25 on the 270 reviewed val frames, 7,465 frames from 18 recordings | FM:16-20, 28-30, 196; `backend/services/video_processor.py:29-46`; `results/train_runs.md:44-47` (border) |
| 16 | 4.2.5 | Intro notes pending tests; component checks add the weighted box fusion self-checks; "Integration testing." → "End-to-end test.": R07 (590 s) analysed in 729 s, 3,539 frames, 112 records all GPS-placed, 36 flagged, H.264 video + `[FILL: phone app or upload script]`; model testing: compared on reviewed val, one test on 11 Nov 2026, members on foreign test; device tests, field validation, UAT → future + `[PENDING]` | FM:213-215; FM §2, §5, §6; `backend/services/box_fusion.py:10-11`; `tools/upload_recording.py:1-10` |
| 17 | 4.2.6 | Deployment → future with `[FILL: hosting service or server]`, `[FILL: address]`, `[PENDING: deployment]`; "participating offices"; Xcode "on a MacBook Air M1"; comments "will be used" | Team statement |
| 18 | Table 4.3.1.1 | "Ultralytics YOLOv8 (PyTorch)" → "…, version 8.4.48"; purpose: three YOLOv8 models (YOLOv8s and YOLOv8m), weighted box fusion (Solovyev et al., 2021); "Roboflow / Model-assisted annotation" → "Review tool and annotation website built by the researchers / Labeling of the local dataset by correcting pre-drawn draft boxes"; Python row adds classification accuracy and Wilson intervals | FM:227 |
| 19 | Table 4.3.2.1 | Device: "Macbook M1 and ASUS Rog Strix G17 2019 Model" → desktop PC with an MSI B550M Pro SE motherboard (training and processing); MacBook Air M1 (iPhone app build); `[FILL: ASUS ROG …]`. Phones: "Iphone 14 Pro Max and Iphone 16" → two iPhone 13 Pro Max and one iPhone 16. OS: Windows 11 Pro 64-bit (build 26200); macOS on the MacBook; `[FILL: iOS version]`. CPU: AMD Ryzen 5 5600 (6 cores, 12 threads, about 3.5 GHz). Phone chips: Apple A15 Bionic (iPhone 13 Pro Max), A18 (iPhone 16) (team-approved, from Apple's specifications). RAM 16 GB. GPU: NVIDIA GeForce RTX 4060, 8 GB. Storage `[FILL]` | Team statement 2026-11-12; Windows build: session environment (10.0.26200) |
| 20 | 4.3.3, Table 4.3.4.1 | "the YOLOv8m model" → "the three YOLOv8 models"; sprint 1 "first YOLOv8 inference"; sprint 2 output rewritten; sprint 5 output done vs `[PENDING]`; "[Weeks]" ×5 → `[FILL: weeks]` | — |
| 21 | 4.4.1, Table 4.4.1.1 | Respondents → future, `[PENDING: n]`; jurisdiction kept with "as confirmed with the municipalities"; Batangas office → `[FILL]`; inclusion criteria future; engineer "may also take part … if so … disclosed … with and without"; header "DPWH Cavite 2nd District Engineering Office Alfonso" → "DPWH Cavite 2nd District Engineering Office"; header "DPWH Batangas 2nd District Engineering Office" → `[FILL]`; total "[n]" → `[PENDING: n]`; note "if that engineer takes part" | Team decisions 2026-11-12 |
| 22 | 4.4.2 | Test sets: local (270 frames, 99 boxes, 3 route groups) and foreign (15% of six countries, 3,277 images), never used for training/selection/threshold; fusion once on local, members on foreign. "Annotation check sheet" → "Annotation validation sheet" (40 boxes, 10 per class, certification letter) `[PENDING]`. Field form future. Damage-log checklist: 50 records, seed 42, survey 3, prepared, not filled `[PENDING]`. Questionnaire "six dimensions" → `[FILL]`. Demonstration future | FM:40, 105, 159, 161 |
| 23 | 4.4.3 | All steps → future tense; "each partner office" → "each participating office"; results "will be presented in Chapter V" `[PENDING: UAT]` | — |
| 24 | 4.4.4, 4.4.5 | Criteria present tense, "so far only detection performance has been measured"; detection row: "deployed models find and classify", local (primary) and foreign (secondary), classification accuracy; added a sentence on classification accuracy read with recall; the six dimensions kept under `[FILL: confirm the instrument …]`; 4.4.5 future tense (Equation 28 = weighted mean, correct after Chapter III) | `results/metric_definitions.md:39-44` |

Remaining "partner offices" (3) are in Chapters V and VI and are handled with those chapters.

---

## Chapter V (applied 2026-11-12)

TE = `results/test_evaluation.md`. Structure: new 5.1.2 "Validation Results and Model Selection" and 5.1.7 "Limitations
of the Detection Results" (Heading 3); 5.1.2-5.1.5 renumbered to 5.1.3-5.1.6; new Tables 5.1.3 and 5.1.4; Tables 5.1.3 and
5.1.4 renumbered to 5.1.5 and 5.1.6. **Figure 5.1.4 removed** (caption and image slot): the single test run saved only
summary metrics (`results/test_evaluation.json`: counts, P/R/F1, classification accuracy, mAP), no raw predictions, so no
precision-recall curve of the fused model on the test set can be drawn without a new run. No template placeholder remains
in the measured sections (5.1, 5.5, 5.7; checked); the template placeholders of the pending sections (5.2-5.4, 5.6) are
kept and highlighted (87 highlights in Chapter V).

| # | Section | Old → new (summary) | Sources |
|---|---|---|---|
| 1 | Chapter intro | "the detection performance of the fine-tuned YOLOv8m model" → "the detection and classification performance of the deployed fusion of three fine-tuned YOLOv8 models"; added: only detection and processing time measured so far, others pending | FM §8 |
| 2 | 5.1 intro | India subset, [n] frames, [n] epochs, [1280 or 1024], [B], [value] → the deployed fusion (v2b, v3, S5_v8m_1920; Section 3.3.1), 7,465 labelled near-zone frames from 18 recordings, RDD2022 start, one model with 600 RDD2022 images, threshold 0.25 on the 270 reviewed val frames | FM:16-20, 28-32, 196 |
| 3 | Table 5.1.1 | Header "Foreign (Train / Val / Test)" → "Foreign (images: train / val / test)", "Total" → "Local total"; foreign class cells "Not reported per class", total 5,750 / 900 / 3,277; local D00 1,450/214/36 (1,700), D10 556/150/8 (714), D20 152/51/34 (237), D40 779/244/21 (1,044), total 2,937/659/99 (3,695). Class-balance placeholder → D20 fewest (152 train boxes), test only 8 D10 and 21 D40, no-damage frames val 1,314 / test 207 | FM:32, 105, 199-203 |
| 4 | 5.1.1 + Table 5.1.2 | "drives the model never saw" → "route groups the models never saw"; table: D00 0.44/0.47/0.45/0.381, D10 0.14/0.38/0.21/0.124, D20 0.33/0.09/0.14/0.152, D40 0.11/0.05/0.07/0.035, all 0.31/0.24/0.27/0.173 (mAP@50). Template ¶s → mAP@50 0.173 (mAP@50-95 0.057), **acceptance level 0.80 not met**, best D00 0.381, worst D40 0.035; P 0.31 (95% CI 21.6-41.7%), R 0.24 (16.9-33.5%), F1 0.27, 24 correct / 54 false alarms / 75 missed of 99, 78 detections (computed here: 24 + 54); new ¶ classification accuracy 96.0% (24/25; 95% CI 80.5-99.3%), stated with recall 0.24 and the 25 matched detections, the one error D10 → D40; per-class ¶ (8-36 boxes; D40 0.376 val → 0.035 test, 1 of 21 found; D20 0.027 → 0.152) | TE:13-18, 25, 31-35, 42, 48-51; FM:131-138, 234-236 |
| 5 | 5.1.1, new Table 5.1.3 + ¶ | Fused 0.173/0.057/0.381/0.124/0.152/0.035; v2b alone 0.146/0.056/0.334/0.077/0.130/0.041; v3 alone 0.160/0.055/0.337/0.171/0.100/0.032; S5_v8m_1920 alone 0.141/0.051/0.350/0.130/0.070/0.016; fusion above every member, within what the small set can separate | TE:80-83 |
| 6 | 5.1.1, new ¶ | High-confidence point: threshold 0.62, test P 1.00 / R 0.04 (4 of 99); rests on one validation detection; precision ≥ 0.80 only at near-zero recall | TE:57-60; FM:140-147 |
| 7 | New 5.1.2 + Table 5.1.4 | Reviewed val (270 frames, 122 boxes, selection set) 0.275 / 0.095, P 0.37 R 0.30 F1 0.33; all val (1,624 frames, 659 boxes) 0.161 / 0.062, P 0.32 R 0.19 F1 0.24; explanation of the selection figure and the site-labelled frames; val classification accuracy 92.5% (37/40; 80.1-97.4%) | FM:74-91; TE:41 |
| 8 | 5.1.3 (was 5.1.2) + Table 5.1.5 (was 5.1.3) | "test split of the RDD2022 India subset" → 3,277 images, six countries, each model alone. Table reused with members as columns: header "Damage Class / v2b (not held out) / v3 / S5_v8m_1920 / Images"; D00 0.290/0.330/0.406, D10 0.179/0.242/0.284, D20 0.190/0.230/0.328, D40 0.143/0.154/0.254, row "mAP@50" 0.200/0.239/0.318, images 3,277. ¶: v2b not held out (external checkpoint), v3 and S5 held out; model cards about 0.60-0.63 (Section 2.1), not comparable. New ¶: teacher 0.472 foreign val vs 0.090 local reviewed val at 1,280 px; external stand-in 0.155 (external baseline only, not ours); fusion 0.275 | TE:66-68; FM:109-116, 168-181; `results/zero_shot_nz_val.md:10`; `results/teacher_foreign_val.md:7`; `results/val_sets_comparison.md:34` |
| 9 | 5.1.4 (was 5.1.3) figures | Fig. 5.1.1 caption → "Matched Pairs by Reviewed and Detected Class: Deployed Fusion (v2b + v3 + S5_v8m_1920), Local Test Subset, Threshold 0.25", image slot → `[FILL: insert a 4 × 4 chart or table …]` with the counts. Fig. 5.1.2 → "Normalized Confusion Matrices of v2b, v3, and S5_v8m_1920, Each Model Alone, on the Foreign Test Subset (RDD2022, Six Countries)", slot → `[FILL: insert runs/eval/final_*_foreign_test_all_six_countries/confusion_matrix_normalized.png]`. ¶ rewritten from the matched pairs; states Fig. 5.1.2 does not show the fused model | TE:44-51; `runs/eval/final_*_foreign_test_all_six_countries/` |
| 10 | 5.1.5 (was 5.1.4) | Fig. 5.1.3 → "Training Curves of v2b, v3, and S5_v8m_1920: Training Losses and Each Run's Own Validation Metrics During Training", slot → `[FILL: insert runs/local/v2b/results.png, runs/local/v3/results.png, runs/v3/S5_v8m_1920/results.png]`. **Fig. 5.1.4 (PR curves on the local test subset) removed.** ¶: validation lists during training (all 1,624 val frames for v2b; 270 reviewed for v3 and S5), epochs 40/13, 20/16, 10 of 40/8 (S5 unfinished), best.pt on mAP@50-95; "not the fused model on the test set" | FM:28-30, 227 |
| 11 | 5.1.6 (was 5.1.5) + Table 5.1.6 (was 5.1.4) | **Removed** "raising the input size from 640 to 1280 pixels increased the number of boxes returned on one 3.5-minute survey from 13 to 157" (no result file). Table → "Records at Each Pipeline Stage, Recording R07": before tracking "Not measured", after tracking "Not measured", stored 112, flagged 36, confirmed false `[PENDING: review of flagged records]`. ¶: R07 112 records (D00 23, D10 15, D20 10, D40 64), all GPS-placed, 36 flagged, flags not reviewed `[PENDING]` | FM:215; `results/train_runs.md:74-75` |
| 12 | New 5.1.7 | Numbered list of the eight caveats of FM §12 (small sets and noise; not held out; best.pt on mAP@50-95; near zone, full band not measured; S5 trained 1,920 / run 1,280, unfinished; not local labels only; validation does not predict per-class test; one reviewer, expert validation pending) | FM:217-237 |
| 13 | 5.2 | Engineer "independently labeled a stratified random sample" → "will check a random sample of 40 labeled boxes, 10 per class" `[PENDING: expert validation]`; template kept, placeholders highlighted | FM:161 |
| 14 | 5.3 | "[n] stored records from the evaluation surveys was checked" → "50 stored records (seed 42) from survey 3, recording R07, will be checked; the checklist has been prepared" `[PENDING]`; template kept, highlighted | FM:159 |
| 15 | 5.4 | "[n] detected damages … was validated" → "20 to 30 … will be validated" `[PENDING]`; template kept, highlighted | FM:160 |
| 16 | 5.5 + Table 5.5.1 | Intro → the one end-to-end survey; caption "…of the Evaluation Surveys" → "…of the End-to-End Survey"; row "Average" → "R07 (survey 3)": 590 s / 3,539 / 729 s / 112. ¶: 729 s for 590 s (about 1.2×), 0.206 s per analysed frame (computed in FM), a little slower than real time, background processing, one survey only; S5 alone 10.7 ms per crop. Device-test ¶ → still to be done `[PENDING: device tests]` | FM:211, 213-215 |
| 17 | 5.6 | **Removed the ISO/IEC 25010:2023 framing** ("The questionnaire was based on the product quality model of ISO/IEC 25010:2023 and used…" → "The questionnaire used…") + `[FILL: align Sections 5.6.2 to 5.6.6 and Tables 5.6.3 to 5.6.8 to the dimensions of the evaluation questionnaire]` `[PENDING: UAT results]`; 5.6.1 Batangas office → `[FILL]`; 5.6.7 "Because the DPWH engineer who validated the annotations also took part … were computed" → "If … takes part … will be computed"; templates kept, highlighted | Team decision 2026-11-12 |
| 18 | 5.7 | RQ1 rewritten from measured results (0.173; per class 0.035-0.381; 0.80 not met; P 0.31, R 0.24, F1 0.27; classification 96.0% (80.5-99.3%) of the damage found, about one in four; foreign 0.200 (v2b, not held out), 0.239, 0.318). RQ2: records carry time, GPS, type, snapshot; all 112 R07 records GPS-placed; correctness `[PENDING]`. RQ3 `[PENDING: localization accuracy]`. RQ4 `[PENDING: UAT results]`. Hypothesis `[PENDING: UAT]`, decided by the UAT not yet carried out | FM §2, §5, §6, §8, §11 |


---

## Chapter VI (applied 2026-11-12)

| # | Section | Old → new (summary) | Sources |
|---|---|---|---|
| 1 | 6.1 ¶1 | "a YOLOv8m model fine-tuned on the RDD2022 India subset and on locally collected … imagery" → "a weighted box fusion of three YOLOv8 models fine-tuned on locally collected Philippine road imagery from weights trained on RDD2022"; "Based on the results, …" → "Based on the results measured so far, …; conclusions that depend on evaluations not yet carried out are marked as pending." | FM:16-32 |
| 2 | 6.1 Objective 1 | Template ([n], [strength], κ, [value]) → 7,465 human-labelled near-zone frames, 3,695 boxes, 18 recordings; expert agreement `[PENDING]`; local test mAP@50 0.173, P 0.31, R 0.24, F1 0.27, 96.0% of 25 matched detections correct type; foreign 0.200-0.318 (v2b not held out); acceptance level 0.80 not met, finds about one in four damages; potholes weakest on test (0.035); teacher 0.472 foreign val vs 0.090 local val; 99 test boxes, uncertain | FM:196, 203, 44, 55, 135, 109-113, 170-173 |
| 3 | 6.1 Objective 2 | Template → stores each record with class, confidence, time, coordinates, snapshot, AI check score, status; R07: 112 records, all GPS-placed, 590 s analysed in 729 s; correctness and duplicates `[PENDING: damage log correctness]` | FM:213-215, 159 |
| 4 | 6.1 Objective 3 | Template → method and app implemented and used for all 18 recordings; positional error not measured `[PENDING: localization accuracy]` | FM:160 |
| 5 | 6.1 Objective 4 | Template → UAT with the personnel of the participating offices not yet carried out `[PENDING: UAT results]`; hypothesis undecided `[PENDING: UAT]` | FM:162 |
| 6 | 6.1 Overall | "[can / cannot yet] support … its detections reduce the footage that personnel need to review by hand" → the parts work together in one web application, detection results well below the level set, support for DPWH offices still to be judged by users `[PENDING: UAT]`; a decision-support tool that points to likely damage; at its current recall its records are not a complete list | FM:55 |
| 7 | 6.2 Detection model | "[the class with the lowest AP@50]" sentence → more drives and labelled frames, especially D40 and D10 (21 and 8 test boxes) and D20 (152 training boxes); conditions not covered (all drives in daylight on two mornings); larger validation and test sets labelled by more than one reviewer; repeated seeded runs with confidence intervals; "the model confused" → "the models confused". Severity sentence kept | FM:200-202; GPX times (Chapter IV log, #4) |
| 8 | 6.2 new "Model comparison." ¶ | Per-country RDD2022 comparison under the same protocol; YOLO11 and YOLO12 under the same protocol (route-group split, selection on reviewed val only, metrics fixed in advance, one test run); a second-stage classifier that re-checks the damage type; a full-band test set | FM:149-151, 228-231 |
| 9 | 6.2 System | "A server with a GPU would shorten processing time." → "A faster graphics card would shorten the processing time, which is now about 1.2 times the length of the footage."; "partner offices" → "participating offices". Database and task-queue recommendation kept | FM:213 |
| 10 | 6.2 Future research | "[Add the improvements suggested by the respondents in Section 5.6.8.]" → `[PENDING: improvements suggested by the respondents, Section 5.6.8]`. Android recommendation kept (Mobile capture application ¶) | — |

---

## Final document-wide check (2026-11-12)

Run on a .docx export of the whole draft (table of contents excluded).

- **Not found anywhere:** "41.1%", "0.411", "India subset", "500 MB", "partner offices", "Equations 19", "Pham et al. (2024)", "ISO/IEC", "13 boxes", "two lighting conditions", "Municipal Engineering Office", "Arya et al. (2022)".
- **Kept on purpose:**
  - "Roboflow" occurs once, as "Roboflow Universe" in the dated repository search (2.2).
  - "Sarmiento & Reyes (2022)" occurs once, in its synthesis-table row, which waits for the manual row deletion.
  - Every "YOLOv8m" left refers to the YOLOv8m members, the teacher, or the dronefreak model card.
  - Singular "partner office" always means DPWH Cavite 2nd DEO.
- **Placeholders:** 80 tokens (33 distinct) of `[FILL]`, `[PENDING]`, `[EQUATION]` and `[CITATION NEEDED]`; all highlighted.
- **References inside the text:**
  - Every "Section x.y" reference points to an existing heading, and every table reference to an existing caption.
  - **Fixed:** Figure 3.3.1 was referenced but its caption had no number. The caption is now "Figure 3.3.1 YOLOv8 Architecture as Configured for the Four Road Damage Classes".
  - Equation references 1-3, 12, 16, 17-23, 24-25, 26, 27, 28-30 match the labels.
- **Numbers not found in the result and source files** (scanned: FM, test_evaluation, train_runs, pretrained_sources, metric_definitions, local_datasets_nz, step1_split, zero_shot_nz_val, model_config, code constants, args.yaml):
  - Section numbers.
  - The original interpretation scales (1.00-5.00, kappa bands) and the criterion 3.41.
  - Literature figures kept from the original text (47,000; 95.43%; R² 0.58).
  - The speed example in 5.4 (8.3 m and 16.7 m per second; original text).
  - Three values added in this revision, each from a stated derivation:
    - **6,399** = 5,045 + 1,354 annotation-site frames (computed here; FM:198).
    - **1.96**, the z value of the 95% Wilson interval.
    - **6,371 km**, the mean Earth radius in the Haversine formula.
  - The hardware values (Ryzen 5 5600, 16 GB, build 26200, A15/A18) come from the team's statement of 2026-11-12. The drive dates and times come from the GPX files.
- **References list:**
  - Every in-text citation has an entry and every entry is cited. The only mismatch, Sarmiento (2022), is the table row waiting for deletion.
  - The list is in alphabetical order.
  - **Marked `[CITATION NEEDED]`:** the six entries that list authors as "et al." (Busireddy 2026, Dabous 2025, Fortin 2024, Irsal 2025, Yin 2024, Zhang 2025), with notes where the venue or title does not match the linked record, plus the Solovyev volume.
- **Table of contents:** a TOC element that the API cannot refresh. It must be updated by hand in Google Docs.

Open items for the team are in [MANUSCRIPT_TODO.md](MANUSCRIPT_TODO.md).


---

## Placeholder pass (2026-11-12): placeholders filled from verified sources

Each item lists the placeholder, the value now in the document, and the source.

- **Highlight handling.** Filled text was replaced starting from the plain word before each placeholder, so it carries no highlight. The two table cells (iOS, storage) had no plain text before the placeholder, so their background was set to white (no visible highlight).
- **Remaining placeholders:** 76 tokens, 32 distinct, all still highlighted.

| # | Placeholder (sections) | Value now in the draft | Source |
|---|---|---|---|
| 1 | `[FILL: the three researchers / the three researchers and N volunteer annotators]` (1.7, 3.4.3, 3.7, 4.1.3) | "the three researchers" | The annotation site allows exactly three accounts, `USERS = ['Gian', 'Janmikael', 'Kyle']` (`tools/review_labels/annotate.py:39`), the first names of the three researchers on the title page; `backups/labels_FINAL_20261111_013131.db` shows all 6,399 labelled frames under those three accounts (2,849 / 2,608 / 943, including 1 skipped) |
| 2 | `[FILL: iOS version]` (Table 4.3.2.1) | "iOS 27.0.1 and iOS 26.7 at the time of recording (GPX metadata of the 21 recordings; the version on each individual phone was not recorded)" | `platform` in `data/local/recordings.csv` and in each GPX `<bk:capture>` element: iOS 27.0.1 in 19 recordings, iOS 26.7 in 2; the GPX files do not record the phone model |
| 3 | `[FILL: storage available for uploads, processed videos, and snapshots]` (Table 4.3.2.1) | "476 GB system drive, about 96 GB free on 12 November 2026" | Measured on the processing PC (`Get-PSDrive C`: 380 GB used + 96 GB free); same machine as the table (NVIDIA GeForce RTX 4060 8 GB via `nvidia-smi`, MSI B550M Pro SE, 16 GB RAM via CIM) |
| 4 | `[CITATION NEEDED: volume]` (Solovyev et al., 2021) | *Image and Vision Computing, 107*, Article 104117 | Crossref, DOI 10.1016/j.imavis.2021.104117 (volume 107, article 104117) |
| 5 | `[CITATION NEEDED: full author list]` (Zhang et al., 2025) | "Zhang, S., Liu, Z., Wang, K., Huang, W., & Li, P. (2025)." | Crossref, DOI 10.7717/peerj-cs.2593 |
| 6 | `[CITATION NEEDED: full author list; title and journal differ from the linked record]` (Fortin et al., 2024) | "Fortin, L. V., Delos Santos, A. R. V., Cagud, P. J. B., Castor, P. R., & Llantos, O. E. (2024). Eyeway: An artificial intelligence of things pothole detection system with map visualization. *Procedia Computer Science, 251*, 216–223. https://doi.org/10.1016/j.procs.2024.11.103". In-text "Fortin et al. (2024)" unchanged. | Crossref, DOI 10.1016/j.procs.2024.11.103 (the record the old ResearchGate link pointed to) |
| 7 | `[CITATION NEEDED: full author list]` (Dabous et al., 2025) | Entry replaced: "Abu Dabous, S., Ait Gacem, M., Zeiada, W., Hamad, K., & Al-Ruzouq, R. (2025). Artificial intelligence applications in pavement infrastructure damage detection with automated three-dimensional imaging – A systematic review. *Alexandria Engineering Journal, 117*, 510–533. https://doi.org/10.1016/j.aej.2024.11.081", moved to its alphabetical place (first). In-text "Dabous et al." → "Abu Dabous et al." (4: 1.3, 2.1 ×2, Table 2.3.1). | Crossref, DOI 10.1016/j.aej.2024.11.081 (family name "Abu Dabous"; the full title was shortened in the old entry) |

Not filled; the questions go to the team:
- **Irsal et al. (2025):** the title and IEEE link are Nurcahyo et al. (2024), DOI 10.1109/FORTEI-ICEE64706.2024.10824488.
- **Yin et al. (2024):** the title and arXiv link are Khare et al. (2023), arXiv:2311.00073.
- **Busireddy et al. (2026):** Crossref lists Esther Priya R. as first author, DOI 10.36106/ijsr/4816016.
- **Abu Dabous et al.:** confirm the claims attributed to it in 1.3 and 2.1. Its full title shows it reviews AI with automated 3D imaging.

(All four were resolved in the next section.)

## Reference audit and answers pass (2026-11-12)

### Method

- **Metadata.** Each of the 29 entries was checked against Crossref (authors, title, venue, year, volume, pages, DOI). Entries without a DOI were checked on the source page: arXiv API, ADB, ATIFTAP / Journal of Global Business, IJSR, Hugging Face, GitHub `CITATION.cff`, PyPI.
- **Claims.** Each cited claim was checked against the paper, as far as the text was reachable:
  - **Full text read:** Khare et al. (arXiv), Sahoo et al. / iWatchRoad (arXiv), Kyem et al. / PaveSync (arXiv), Sarmiento (arXiv), Pham et al. (arXiv), Arya et al. 2020 (arXiv), Bustria et al. (ATIFTAP PDF), Esther Priya. R et al. (IJSR PDF).
  - **Abstract only** (publisher full text closed or blocked to automated access): Nurcahyo et al., Albouchi et al., Alwahhab et al., Abu Dabous et al., Fortin et al., Manalo et al., Sapkota et al., Zeng & Zhong, Zhang et al., Jin et al., ADB (publication page).
  - **Not reachable:** Dacanay et al. and Ramos et al. (Springer login); Roy & Bhaduri (record not found).
- **Scope.** Fixed only what a source confirms. Unsupported claims were reworded to what the paper says, or removed. The original document was not touched.

### The four items the user named

| Item | Finding | Change |
|---|---|---|
| Irsal et al. (2025) | The title and IEEE link belong to Nurcahyo et al. (2024), *2024 FORTEI-ICEE*, pp. 47–51, DOI 10.1109/FORTEI-ICEE64706.2024.10824488. Its abstract says YOLOv8 was trained on a pothole dataset (various road conditions and sizes) and presented for real-time monitoring. It says nothing about an anchor-free mechanism improving localization or about "high detection precision". | 2.1: claim reworded to the abstract; anchor-free claim removed (Terven et al. still supports it in Chapter I). Table 2.3.1 row and reference entry replaced. |
| Yin et al. (2024) | The title and arXiv link belong to Khare, Gandhi, Rahalkar & Mane (2023), arXiv:2311.00073 (also published in IEEE PuneCon 2023, DOI 10.1109/PuneCon58714.2023.10449999; the preprint was read). It contains no "multi-scale feature learning". Measured: on 3,770 images, YOLOv8 nano reached mAP@0.5 0.911 at 8.8 ms, ahead of YOLOv5n/s and YOLOv7 in mAP, time and size. The paper also states that manual inspections are "time-consuming, subjective, and impractical for covering extensive road networks". | 2.1 reworded to the measured comparison; Table 2.3.1 row and reference entry replaced (preprint cited, as read). |
| Busireddy et al. (2026) | The paper prints the first author as "Mrs. Esther Priya. R" (Assistant Professor), followed by Busireddy Lakshmi Bhavani, Chinni Mahalakshmi, Sasi Dharan R and Shyaamal S; *IJSR* 15(4), 45–47, DOI 10.36106/ijsr/4816016. It is a Flask web app for uploaded images (YOLO detector, CNN severity classifier, Grad-CAM) with "GPS-based location tagging and structured data logging". There is no timestamp synchronization and no claim about time to locate damage. | Cited as "Esther Priya. R et al. (2026)", the name exactly as printed (honorific dropped). Entry lists the names as printed, placed under E. 2.1 claim reworded, 2.3 and 5.4 citations renamed, Table 2.3.1 row rewritten. |
| Abu Dabous et al. (2025) | A systematic review of 85 studies (2011 to mid-2024) on AI with 3D imaging (laser scanners, stereo cameras, infrared). The full text could not be read: the publisher blocks automated access. The abstract and scope do not cover web platforms, GPU processing or mobile overheating. The only verified source found for overheating is Fortin et al. (2024), whose on-edge AIoT prototype reported "system overheating" and "GPS data inaccuracies". No verified source was found for centralized GPU processing or battery drain. | GPU, battery and inconsistent-performance claims removed (2.1, 2.1 iWatchRoad ¶, 2.3, Table 2.3.1). 2.1 ¶ rewritten to what the abstract says (85 studies, 3D sensors, cost of 3D collection, lack of open 3D datasets), contrasted with the study's smartphone video. Overheating now cited to Fortin et al. (2.2, 2.3). 1.3 citation replaced by (Khare et al., 2023; Pham et al., 2022; Sarmiento, 2021), which state that manual inspection is time-consuming, laborious and impractical for large networks, and still manual in the Philippines. |

### Other problems found and fixed

| Reference | Problem | Fix |
|---|---|---|
| Asamoah et al. (2025) | First author is Kyem, B. A. (6 authors); published in *2025 IEEE FMLDS*, pp. 495–500, DOI 10.1109/FMLDS67896.2025.00095 (declared on arXiv). "Strengthens model robustness across geographic conditions" is not stated. | Cited as Kyem et al. (2025); 2.1 reworded (52,747 images, 7 countries, 13 standardized distress types; standardization enables fair comparison and zero-shot transfer); table row and entry replaced. |
| iWatchRoad Project (2026) | Authors are Sahoo, Mohanty & Mishra (2025), *Proc. 13th ACM IKDD CODS*, pp. 262–270, DOI 10.1145/3799830.3799873. The paper does not compare its architecture with on-device alternatives. | Cited as Sahoo et al. (2025); 2.1 reworded to the paper: dashcam video and GPS upload, YOLOv8 on 7,000+ frames, OCR timestamps matched to the GPS log, OSM map, runs on standard computers without cloud. |
| Albouchi et al. (2025) | Wrong venue: *2025 IEEE 22nd International Conference on Sciences and Techniques of Automatic Control and Computer Engineering (STA)*, pp. 639–644, DOI 10.1109/STA66620.2025.11364925. Second author is "Hajjaji, M. A.". No heat map in the abstract. | Entry corrected; 2.1 and table row reworded to the abstract (fine-tuned YOLOv10s, higher detection rates with low false positive and false negative rates, integration into monitoring systems). |
| Alwahhab et al. (2025) | The claims about fewer false detections from shadows or wet pavement and higher accuracy in developing countries are not stated. It is VGG16 with multi-head attention, a local dataset of cracks, potholes and ruts, three public datasets, and a real-time test on local roads. | 2.1, Ch I and table reworded. URL → DOI 10.32985/ijeces.16.2.7. |
| Sarmiento (2021) | Does not test foreign-trained models on Philippine roads and does not name textures, shadows, debris or lighting. It reports YOLOv4 mAP 0.272 on 305 DPWH images, attributed to the small dataset, non-uniform collection and distress types unsuited to boxes. It notes surveys are still manual in the Philippines. | 2.2 ¶ and table row reworded. Removed from the "foreign models lose accuracy" sentences (Ch I ×2, 2.3). |
| (new) Arya et al. (2020) | Verified replacement for the "foreign imagery loses accuracy" claim: "Mostly the performance of a model significantly degrades when applied to road images from another country" (arXiv:2008.13101, read in full). | Added to the Ch I sentence and to 2.1 (transfer-learning ¶). New reference entry before Arya et al. (2024). |
| Bustria et al. (2025) | Wrong title and authors. Actual: Bustria, J. L. Y. A., Briones, N. A. Q., Riboroso, R. M. A., Dela Cruz, J., Ferrer, B. E., & Ferrer, V., Jr., "YOLOv11-based mobile application for damage classification and severity level identification of roads in the Philippines", *Journal of Global Business, 14*(3) (ATIFTAP). Battery consumption, thermal throttling and inconsistent performance are not in the paper. It is an on-device YOLOv11 classifier for uploaded photos, trained mainly on DPWH Baguio City images, 86% accuracy, and states that models trained on international datasets fail to generalize to Philippine conditions. | Entry replaced; 2.2 ¶ and table row reworded. Now also cited for the generalization sentences (Ch I ×2, 2.3). |
| Fortin et al. (2024) | "Geospatial technologies significantly improved the accuracy of pothole location tracking" is not stated; the abstract reports GPS data inaccuracies and overheating as challenges. Its AIoT prototype detects on edge hardware (YOLOv5m, mAP 91.8%). | 2.2 ¶ and table row reworded. |
| Zeng & Zhong (2024) | "Reduce false detections" is not stated. It is a lightweight YOLOv8n with BOT, LSKA, C2fGhost and LSCD-Head: +1.4 points mAP on RDD2022 at about 74% of the baseline's parameters and FLOPs. | 2.1 and table row reworded. |
| Zhang et al. (2025) | "Small and distant potholes in dashcam footage" is not stated. It adds ODConv, BoTNet and coordinate attention: +1.8% mAP@0.5 and +1.6% F1 on RDD2022-China. | 2.1 and table row reworded. |
| Asian Development Bank (2026) | Published March 2025, DOI 10.22617/TCS250091-2. The guidebook does not say ML is "essential"; it explains how smartphones, free satellite imagery and AI can supplement traditional surveys and make data collection cheaper and faster (developed with the governments of the Philippines and Thailand). | Year 2026 → 2025 (text, table, entry); claim reworded; URL → DOI. |
| Jocher et al. (2026) | `CITATION.cff` lists the authors as Jocher, Qiu, Chaurasia and the title as "Ultralytics YOLO". | Entry corrected (version 8.4.48 kept). |
| Dacanay et al. / Ramos et al. (2024) | Pages missing (Crossref: pp. 355–364 and 81–94; editor E. Strauss and year 2024 confirmed). | Pages added. Claims not checked (Springer login). |
| Pham et al. (2022), Jin et al. (2025) | Ch I said they detect anomalies "from images and continuous video feeds"; both work on images. | "from road images". |
| Ch I / 2.3 generic claims | "irregular pavement textures, lighting, flooding, weather… especially for models trained on foreign datasets (Sarmiento, 2021)" and the 2.3 list of factors were not supported by the cited paper. | Replaced by the verified Bustria et al. (2025) statement, plus Manalo et al. (2022) for pothole shape and size variability (abstract: 33%–69% accuracies "given the numerous various forms and sizes of potholes"). |

### Problems listed, not fixed (not verifiable)

- **Roy & Bhaduri (2023), *International Journal of Computer Applications*.** No record found in Crossref or by title search. A paper with the same title is Aina, Haghi, Famewo, Lambert, Owolabi & Efe (2025), *International Conference on Transportation and Development 2025*, pp. 411–418, DOI 10.1061/9780784486191.036; its abstract does not compare YOLOv8 with earlier versions. A highlighted [CITATION NEEDED] was added to the entry; the text citing it (Ch I ×2, 2.1, Table 2.3.1) is unchanged.
- **Dacanay et al. (2024):** claims about Project PAVE (DOST, UP Diliman), DPWH practice and the applicability of foreign systems are unchecked. **Ramos et al. (2024):** R² 0.58, DPWH district photographs and VCI critique are unchecked. Both are behind the Springer login.
- **Manalo et al. (2022):** the abstract confirms YOLOv3, AP 95.43% and 33%–69% accuracies. "Philippine roads", "locally compiled dataset" and the three universities are not in the abstract; full text is closed.
- **Arya et al. (2024)** sentence "significantly improving generalized detection performance" and **Sapkota et al. (2025)** "practical for real-time monitoring in transportation and surveillance" were checked against abstracts only. Sapkota's abstract names autonomous vehicles and traffic safety and surveillance among five application areas.
- **Abu Dabous et al. (2025):** full text not read (publisher access); the text now cites only what the abstract states.

### User answers applied

| # | Where | Change |
|---|---|---|
| 1 | 4.2.5 end-to-end test | [FILL] → "The recording was not uploaded from the phone: like the other recordings, it was made with the mobile capture application and uploaded with the researchers' upload script (tools/upload_recording.py), which sends the same video, GPX track, and time offset as the application, together with the team-approved road band for R04 to R14." (`tools/upload_recording.py` sends video, GPX, `time_offset`, and the road band, with overrides for R04–R14) |
| 2 | 4.2.6 deployment | The hosting [FILL]s, the access steps and [PENDING: deployment] → "An online copy of the system was not deployed for the remote evaluation because of limitations in uploading." |
| 3 | 4.5 ethics | Removed the clause "the online copy used for the remote evaluation will be served over HTTPS with accounts only for evaluators". |
| 4 | 4.1.3 (evaluation data), NFR12, 4.4.2 (materials and procedure), 5.6 intro | Each still describes respondents using an online copy, so each got a highlighted "[FILL: no online copy was deployed (Section 4.2.6); state how respondents will use the system instead]" (5 places). |
| 5 | Table 4.3.2.1 hardware | ROG [FILL] → "ASUS ROG Strix G17 (UI/UX development)". |
| 6 | iOS version | Kept as is. |

Not applied:
- **"DPWH Batangas office: DPWH Cavite 2nd District Engineering Office".** This gives the Cavite partner's name for the Batangas office, so it cannot be right as written. The [FILL] stays until the Batangas office's exact name is given.
- **Sprint durations.** Left as [FILL: weeks]. Inventing them would break the rule against invented numbers and dates; git history can give dated, labelled spans instead (see the TODO).
- **UAT instrument (dimensions).** Still [FILL].

### Repo

- `tools/uat_analysis.py` (new). Reads the Google Forms CSV and a JSON map of dimensions to item columns, and computes Equations 28–30:
  - item weighted mean and SD; dimension and overall weighted mean and SD over respondents;
  - one-tailed one-sample t-test against 3.41 (t, df, p), the Table 4.4.5.2 interpretation and the hypothesis decision rule;
  - everything with all respondents and without the engineer (`--engineer COLUMN=VALUE`).

  Standard library only. The t-distribution tail was checked against known values (for example t = 2.0, df = 10 → p = 0.036694) and on synthetic responses in the scratchpad. It was not run on real data, since none exist yet.
- **After the reference audit:** 74 placeholder tokens remained (26 distinct), all highlighted. The reference list has 30 entries in alphabetical order, and every in-text citation matches an entry by author and year. The only exception is "Sarmiento & Reyes (2022)" in Table 2.3.1, the row awaiting manual deletion.


## Manual-edit pass and diagram check (2026-11-12)

### Revision draft

| # | Where | Change | Source |
|---|---|---|---|
| 1 | 3.3.3 Eq. (12), 3.8.1 Eqs. (22) and (23), 3.8.4 Eq. (27) | `[EQUATION n: …]` placeholders replaced with typed equations in Cambria Math (Unicode sub- and superscripts, linear fractions); highlight removed. (12) keeps its centre and right tab stops; (22), (23) and (27) stay centred lines, because the Docs API cannot create equation objects or set tab stops. | Same formulas as the placeholders; (12) checked against `backend/services/box_fusion.py:9` (score = sum of confidences divided by the number of models) |
| 2 | 3.3.2 | Title line of the algorithm block: "Algorithm 3.1 " added (bold), since the text cites "Algorithm 3.1" and the block had no label. Steps unchanged: they match `video_processor.py:12, 33, 71, 424, 527` (stride floor(FPS/5), near zone top + 0.10, 24 px border), `damage_tracker.py:38` (1 s gap) and `box_fusion.py` | Code |
| 3 | Table 4.3.4.1 | `[FILL: weeks]` ×5 → spans from the git history: 1) 23 Apr – 22 May 2026 (4 weeks), 2) 16 Sep – 11 Nov 2026 (8 weeks), 3) 22 May – 21 Oct 2026 (22 weeks), 4) 12 Oct – 4 Nov 2026 (3 weeks), 5) from 11 Nov 2026 (in progress). The 4.3.4 intro now says where they come from and why a span is not weeks of active work (work before the first commit is not recorded; sprints overlapped; no commits 22 May – 16 Sep). | `git log` (67 commits). Sprint 1 = commits `391240d`–`bcd6b76`; 2 = `918e4e9` (four-class RDD2022), tracker 19–22 Oct, AI check 21 Oct, labelling, training and test 10–11 Nov (`a3b6d00`); 3 = `1267702` (gps_service, map page) to `c676feb` (mobile app), georeferencing `3869b33`; 4 = `17b6964` (signed tokens, survey page) to `96656f9`, admin and activity log `2a8fda8`; 5 = `a17b6f5` (end-to-end check), `6117fb5` (damage log checklist) |

Not done:
- **Table 2.3.1 rows:** delete Sarmiento & Reyes, add Radford. The connector has no row operations, the Docs API refuses deleting a row as a text range, the section rows are merged cells, and the Apps Script API is disabled in the connector's Google Cloud project.
- **Table of contents:** no API can refresh it.

### Diagram check (`figures/*.drawio`)

Checked against the code, `results/FINAL_METRICS_FOR_PAPER.md`, `results/train_runs.md`, `ml/models/model_config.json`, Ultralytics 8.4.48's `cfg/models/v8/yolov8.yaml`, and Chapter III of the draft. Wrong or missing items were corrected in the XML. Afterwards a layout check (box overlaps, edges through boxes, crossing edges) reported no problems in any of the six files.

| Figure | Change |
|---|---|
| 3.1 | Rebuilt. Phase names and contents now follow 3.1.1–3.1.5 (System Foundation and Core Development; Detection Refinement and Feature Expansion; Geospatial Integration and Data Synchronization; System Integration and Interface Enhancement; Optimization and Validation) instead of "Planning and Requirements / Model Development / System Development / Integration and Testing / Evaluation and Deployment". The sprint cycle Planning → Design → Development → Testing → Review (3.1) was added. "Partner offices" and "Deployment" removed. |
| 3.2.1 | "classification by type" (no such view) → records filterable by kind of damage; model sizes added; the process box now orders positioning before storage with the AI check, as in the 3.2.1 text. |
| 3.3.1 | Backbone and neck now match `yolov8.yaml`: 5 Conv (stride 2), 4 C2f and SPPF; neck with two upsample + concat + C2f steps and two Conv (stride 2) + concat + C2f steps. Head boxes give the strides 8, 16 and 32, and the box (DFL) and class branches. Input box: 24 px above and below, 1,024 px for v2b and 1,280 px for v3 and S5. |
| 3.4 | Upper lane rebuilt with the real lineage: RDD2022 → teacher (COCO start, 5,750 images) → B v2 (local + 600 replay) → S5_v8m_1920 (local + 600 replay, 1,920 px) → v3 (local only, 1,280 px); external YOLOv8s checkpoint (SreekarAditya) → v2b (1,024 px). Before, the teacher was drawn as the starting weights of all three. Label counts (1,066 and 6,399) added; selection on the 270 reviewed val frames; one test. Lower lane: the missing edge from the no-GPS branch into the AI check was added (those records are still checked and stored); "by-type view" removed; the "Analyse again" arrow re-routed so it no longer crosses the storage arrow; member sizes added. |
| 3.4.1 | "Damage by type" page (does not exist) → "Place on the map (control points)" (`SurveyPlaceTab.jsx`, route `/videos/:id/georeference`). API routes list completed (detections, resident reports). Database adds resident reports (`PublicReport`); file storage adds `reports/` (`backend/app.py:23`). Web client link label "HTTPS" → "REST API calls + JWT" (no online copy is deployed). |
| 3.5.1 | "damage by type" removed from "View detections…". Association lines now attach to the near side of each use case, so they no longer run through other use cases. |


## Validator change (2026-11-12)

Team decisions:
- **Validator.** Engr. Carlo Almanzor of the DPWH Cavite 2nd District Engineering Office is now the expert validator, replacing the DPWH Batangas engineer.
- **Batangas.** DPWH Batangas stays as a backup respondent office; its name is still `[FILL]`.
- **Sample.** The hand-picked sheet is kept. The check is described as an expert check of the labeling criteria, not an agreement measure.
- **Status.** `[PENDING: expert validation]` stays until the signed letter is back.

### Revision draft

| # | Where | Change |
|---|---|---|
| 1 | 3.4.3 | "A road engineer from the DPWH in Cavite will check a random sample of 40 boxes … agreement … Section 3.8.2" → Engr. Carlo Almanzor (DPWH Cavite 2nd DEO) checks 40 boxes selected by the researchers; chosen by hand, not drawn at random, so an expert check of the labeling criteria, not a measure of agreement. Source: `data/local/validation_sheet/counts.json` (`"picked": "by_hand"`), `selection.json`. |
| 2 | 3.6 | The Batangas-engineer disclosure → Engr. Almanzor works at the main respondent office and may also answer the questionnaire; if so, disclosed and reported with and without his responses. The Batangas backup-recruitment sentence is unchanged. |
| 3 | 3.7 | Frames shared "with the DPWH engineer who validates the annotations" → "with Engr. Carlo Almanzor of the DPWH Cavite 2nd District Engineering Office, who checks the annotations". |
| 4 | 3.8 intro | "The agreement of the local labels with an expert's is examined in Section 3.8.2" → "The expert check of the local labels is described in Section 3.8.2". |
| 5 | 3.8.2 | Heading "Annotation Agreement" → "Expert Check of the Annotations". Body rewritten to match the sheet and letter (`tools/make_validation_letter.js`): he marks whether each box shows the class named on the sheet, lists incorrect boxes and signs; reported as boxes confirmed and corrected per class with remarks; no agreement statistic. Equations (24) percent agreement and (25) Cohen's kappa and their where-lines deleted. |
| 6 | 3.8.3–3.8.6 | Equations renumbered (26)→(24), (27)→(25), (28)→(26), (29)→(27), (30)→(28), (31)→(29); references updated: "Equation 26/27" (4.1.5) → 24/25, "Equation 28" (4.4.5) → 26, "Equations 28 to 30" (4.1.5) → 26 to 28. Equations now run 1–29 without gaps. |
| 7 | Tables of tools (3.x, 4.3.x) | "annotation agreement" removed from the computations listed. |
| 8 | Ch IV intro; 4.1.1 (training data); 4.1.3 (annotation check); 4.1.5; 4.1.6 | Validator named; "random sample"/"drawn at random" → "selected by the researchers"; 4.1.5 agreement and kappa sentence → expert check reported as boxes confirmed and corrected, no agreement statistic; 4.1.5 UAT disclosure → Engr. Almanzor; 4.1.6 "check by an outside engineer and the agreement measured with Cohen's kappa" → review by Engr. Almanzor, an expert check on 40 boxes selected by the researchers. |
| 9 | 4.4.1 and Table 4.4.1.1 | Batangas-engineer disclosure and table note → Engr. Almanzor (DPWH Cavite 2nd DEO). |
| 10 | 4.4.2 | Annotation validation sheet: "drawn at random … The DPWH Batangas engineer will mark each box … compared with the researchers' labels" → selected by the researchers; Engr. Almanzor marks whether each box shows the named class, lists incorrect boxes, signs. |
| 11 | 4.4.4 evaluation table | Row "Annotation agreement / Whether the local labels are trustworthy / Percent agreement and Cohen's kappa per class" → "Expert check of the annotations / Whether the labels follow the labeling criteria, in the view of a DPWH engineer / Boxes confirmed and corrected per class, out of 40 selected by the researchers, with remarks". |
| 12 | 4.4.5 | The Cohen's-kappa sentence (Landis & Koch) and Table 4.4.5.3 deleted. |
| 13 | Ch V intro; 5.1 limitations | "the agreement of the local annotations" → "the expert check of the local annotations"; "expert validation of the labels" → "expert check of the labels". |
| 14 | 5.2 | Heading → "5.2 EXPERT CHECK OF THE ANNOTATIONS"; intro rewritten (validator, hand-picked, does not estimate agreement of all labels); Table 5.2.1 retitled "Expert Check of the Annotations per Damage Class", columns "Boxes Checked / Confirmed / Corrected / Main Remark" (were Instances Checked / Percent Agreement / Cohen's Kappa / Strength of Agreement); result template rewritten without kappa and Landis & Koch, and no longer claims that the check supports the test labels (the 40 boxes come from training and validation frames); its `[n]` and instruction brackets highlighted as before. |
| 15 | 5.6.7 | Disclosure before Table 5.6.9 → Engr. Almanzor. |
| 16 | 6.1 | "the agreement of its labels with those of a DPWH engineer is still to be measured" → "an expert check of its labeling criteria by Engr. Carlo Almanzor … is still pending". |
| 17 | References | Landis & Koch (1977) deleted (no longer cited). |

Checked after the edit: no "Batangas engineer", "kappa", "Landis", "random sample of 40" or "annotation agreement" remain; "Batangas" remains only for the backup office (7 highlighted `[FILL]`s) and Batangas State University (Ch II). 1.6 never mentioned the validator. Every table and figure reference resolves.

Not filled (the user also asked to fix all highlighted `[ ]` text): the 64 remaining highlighted tokens are pending measurements, the Chapter V result templates, the Table 4.4.1.1 counts, the Batangas office name, the UAT dimensions, the online-copy procedure, the figure inserts and the Roy & Bhaduri source. No result file for any of them exists in the repository (`results/damage_log_check/survey3_checklist.csv` has no check column filled), so none can be filled without inventing values.

### Repo

- `tools/make_validation_letter.js`:
  - the letter names Engr. Carlo Almanzor and the DPWH Cavite 2nd District Engineering Office (opening sentence, printed name, Office / Agency);
  - fills the three former `[ ]` fields from the title page (thesis title, researchers, program) and the school as De La Salle University – Dasmariñas (the manuscript writes "DLSU-D");
  - adds, for a hand-picked sample, a sentence that the samples were chosen by the researchers and that the certification is not a measure of the accuracy of every label.

  `data/local/validation_sheet/OcuLubak_dataset_validation.docx` was regenerated (gitignored; the sample sheet and class strips are unchanged, still the hand pick).
- `tools/uat_analysis.py`:
  - new `--validator-id` (with `--id-column`, default "Respondent ID" or "ID") excludes Engr. Almanzor by respondent ID and reports whether he answered;
  - `--exclude` (old name `--engineer`) is kept;
  - equation numbers updated to 26–28.

  Tested on synthetic responses: exclusion by ID, an unknown ID, the old option name, and a CSV without an ID column.

---

## System-level revision (2026-11-15, per adviser consultation)

Decision: `docs/decisions.md` (2026-11-15). The manuscript now reports system-level (frame-level) performance;
box-level mAP@50 (test 0.173) stays in `results/test_evaluation.md` as evidence and is removed from the manuscript.

- **Edited document:** "OCULUBAK_Manuscript" (Drive title now "OCULUBAK_Manuscript_CLAUDED", last edited by the team on
  2026-11-14): https://docs.google.com/document/d/1nn5vxNuuDDfNycLGlEwNVaJkqvsrUo4MOAzarpffXuw/edit
- **Backup made before any edit:** "OCULUBAK_Manuscript — backup before system-level revision (2026-11-15)":
  https://docs.google.com/document/d/1z_fNYcfeOQyLCzKNbW0gic7rVlo4P3Qbe3pL2UzhXwQ/edit
- **Source for every number:** `results/system_level_evaluation.md` / `.json` (SL), computed by
  `ml/local/system_level_eval.py`; box-level figures that remain come from `results/test_evaluation.md` (TE).
- **Highlights in the document:** light green (#D9EAD3) = changed wording (approved wording in Chapters I, III and IV,
  results text in V and VI); yellow = `[PENDING: ...]` record-level items, left until the R07 review is scored.
  Earlier passes used yellow for both; green is new so that the two can be told apart. Changed table cells in Chapter V
  are not highlighted (their captions are); the changed cells in Tables 3.8.7, 4.1.1, 4.2.2.1 (NFR1), 4.3.1.1 and the
  4.4.4 table are.
- **Decisions applied (user, 2026-11-15):** "the system" = the deployed pipeline, the fusion followed by the second-stage
  classifier (configuration unchanged); type correctness reported with the classifier (23/25 = 92.0%); the classifier
  alone on the 99 held-out test crops (85.9%, 85/99, per class); the 0.80 statement as instructed; the comparison
  wording as instructed; limitations: potholes 1 of 17, 63 damage frames, padding mismatch, adoption after the initial
  evaluation.
- **Method:** every text change was one find/replace whose find text was checked to occur exactly once, in order, on
  the full text before sending; after applying, the document text was compared with the simulated result (0 differing
  lines). Tables were edited by cell position; positions were re-read after every write.

### Text changes (in document order)

| # | Section | Old → new (abridged; full text in the document) | Highlight |
|---|---|---|---|
| 1 | 1.2 Purpose and Description | "Both parts are evaluated: detection by mean Average Precision, and classification by the classification accuracy of detected damage" → "Both parts are evaluated at the level at which the system is used: detection by frame-level accuracy, precision, recall, and F1-score (whether the system reports damage i …" | green |
| 2 | 1.2 Purpose and Description | "A second-stage classification model that re-checks the damage class of each detected box was added after the test evaluation; it is optional and was evaluated on validati …" → "A second-stage classification model that re-checks the damage class of each detected box was added after the first test evaluation; it is part of the deployed system and …" | green |
| 3 | 1.3 RQ1 | "from uploaded road survey videos, as measured by precision, recall, F1-score, mean Average Precision, and the classification accuracy of detected damage?" → "from uploaded road survey videos, as measured by frame-level accuracy, precision, recall, and F1-score for damage detection, the classification accuracy of detected damag …" | green |
| 4 | 1.5.2 SO1 | "using precision, recall, F1-score, mean Average Precision at IoU 0.50, and the classification accuracy of detected damage as performance measures, with results reported s …" → "using frame-level accuracy, precision, recall, and F1-score for damage detection, the classification accuracy of detected damage, the correctness of the stored damage rec …" | green |
| 5 | 3.3.1 training paragraph | "Each run kept the weights of the epoch with the highest mAP@50-95 on its own validation list, which is Ultralytics’ default choice, although the models were compared with …" → "Each run kept the weights of the epoch with the best box-level score on its own validation list, which is Ultralytics’ default choice, and the models were compared with o …" | green |
| 6 | 3.3.1 input size of S5_v8m_1920 | "but on the reviewed validation frames it scored about the same at 1,280, 1,600, and 1,920 pixels (mAP@50 of 0.200, 0.205, and 0.201)." → "but on the reviewed validation frames it scored about the same at 1,280, 1,600, and 1,920 pixels on that box-level score." | green |
| 7 | 3.3.1 second-stage classifier | "Because it was added after the single test run, it has no test result, and all test figures in Chapter V describe the class labels of the fusion alone (Section 5.1.7)." → "It is part of the deployed system, so the system-level test results in Chapter V include it; because it was added after the first test evaluation, its own test figure was …" | green |
| 8 | 3.3.3 intro | "including precision, recall, F1-score, mean Average Precision, and positional error," → "including accuracy, precision, recall, F1-score, classification accuracy, and positional error," | green |
| 9 | 3.7 Ethical Considerations | "The test evaluation reported in Chapter V uses only the fusion of the researchers’ three fine-tuned four-class models, as deployed on 11 November 2026." → "The test results reported in Chapter V as results of this study are those of the researchers’ deployed system: the fusion of their three fine-tuned four-class models, as …" | green |
| 10 | 3.7 Ethical Considerations | "and no model of another party is reported as a result of this study. The second-stage classifier added after the test is reported with a validation figure only." → "and no model of another party is reported as a result of this study; pretrained models of other parties appear only as comparisons and are credited to their authors. The …" | green |
| 11 | 3.8.1 first paragraph | "Detection performance was computed at an IoU threshold of 0.50 on two test subsets. The local test subset, 270 near-zone frames from the three test route groups with 99 b …" → "Detection performance is measured at the level at which the system is used: whether it reports damage in a frame that shows damage, and whether it gives that damage the c …" | green |
| 12 | 3.8.1 precision definition | "measures the proportion of detections that are correct:" → "measures the proportion of frames reported as damaged that show damage:" | green |
| 13 | 3.8.1 recall definition | "measures the proportion of actual damage that the model detects:" → "measures the proportion of frames with damage that the system reports:" | green |
| 14 | 3.8.1 reporting paragraph | "Precision, recall, and F1-score are reported at the deployed threshold of 0.25, with the system’s own settings, overall and for each class. Because the counts are small, …" → "All four measures are reported at the deployed threshold of 0.25, with the system’s own settings, overall and for each class. Because the counts are small, 95 percent Wil …" | green |
| 15 | 3.8.1 AP paragraph -> accuracy | "(AP) for one class is the area under its precision-recall curve over all confidence levels, computed by Ultralytics with 101-point interpolation, and the mean Average Pre …" → "is the proportion of all frames that the system judges correctly, with or without damage:" | green |
| 16 | 3.8.1 AP paragraph -> accuracy (term) | "Average Precision is the proportion of all frames" → "Accuracy is the proportion of all frames" | green |
| 17 | 3.8.1 where-list | "pc(r) = precision of class c as a function of recall r" → "TP, FP, FN, TN = numbers of frames counted as defined above; N = TP + FP + FN + TN = 270" | green |
| 18 | 3.8.1 where-list (baseline note) | "C = number of damage classes (4)" → "Because 207 of the 270 test frames show no damage, a system that never reported damage would reach an accuracy of 0.767, so accuracy is always read together with precisio …" | green |
| 19 | 3.8.1 classification accuracy | "It measures the class decision only for damage that was found, so it is always reported together with recall and the number of matched detections." → "It is computed for the deployed system, whose damage types are set by the second-stage classifier, and for the fusion without it. It measures the class decision only for …" | green |
| 20 | 3.8.1 Wilson z | "z = 1.96, used for overall precision, overall recall, and classification accuracy" → "z = 1.96, used for accuracy, precision, recall, and classification accuracy" | green |
| 21 | 3.8.1 model selection | "Within each training run, Ultralytics kept the weights of the epoch with the highest mAP@50-95, while the runs and fusions were compared on mAP@50. The metrics in this se …" → "Within each training run, Ultralytics kept the weights of the epoch with the best box-level score, its default. The box-level metrics first planned for this study were wr …" | green |
| 22 | 3.8.1 model selection (system-level added later) | "and the deployed fusion was then evaluated on the local test subset once, starting at 17:09 the same day. The test subset was not used for training, model selection, or t …" → "and the deployed fusion was then evaluated on the local test subset once, starting at 17:09 the same day. The system-level measures in this section were adopted afterward …" | green |
| 23 | 3.8.1 second-stage classifier | " The classifier described in Section 3.3.1 is scored by its top-1 accuracy, the share of validation crops whose predicted class is the same as the labeled class, on the c …" → " The classifier described in Section 3.3.1 is also scored alone by its top-1 accuracy, the share of crops whose predicted class is the same as the labeled class, with a W …" | green |
| 24 | 3.8.1 acceptance criterion | "As required by the panel, the model must reach an mAP@50 of at least 0.80 overall and an AP@50 of at least 0.80 for each of the four damage classes on the local test subs …" → "As required by the panel, the system must reach a performance of at least 0.80 in accuracy, precision, recall, or F1-score on the local test subset, which represents the …" | green |
| 25 | 3.8.7 software tools table | "Model training, and computation of precision, recall, AP, mAP@50, and mAP@50-95 per class and per test subset" → "Model training and inference, and computation of box-level precision and recall per test subset" | green |
| 26 | 4.1.1 Table 4.1.1 (RQ1 measure) | "Precision, recall, F1-score, and mAP@50 per class, and the classification accuracy of detected damage, on the local test subset (primary) and the foreign test subset (sec …" → "Frame-level accuracy, precision, recall, and F1-score for damage detection, overall and per class; the classification accuracy of detected damage; the correctness of the …" | green |
| 27 | 4.1.5 detection bullet | "Detection performance was computed at an IoU threshold of 0.50 with Ultralytics and the system’s own fusion code, per class, on the local test subset (the deployed fusion …" → "Detection performance was computed at the frame level on the 270 local test frames with the deployed system (the fusion with the second-stage classifier) at its threshold …" | green |
| 28 | 4.1.5 classifier bullet | "The second-stage classifier was scored by its top-1 accuracy on the crops of the 122 reviewed validation boxes, with a Wilson interval; it has no test result." → "The second-stage classifier was scored alone by its top-1 accuracy, with a Wilson interval and per-class precision and recall, on the crops of the 122 reviewed validation …" | green |
| 29 | 4.1.6 validity | "The metrics were written down before the test was run, and the local test subset was evaluated once. The second-stage classifier was added after this test and is reported …" → "The box-level metrics were written down before the test was run, and the local test subset was evaluated once with them; the system-level measures reported in Chapter V w …" | green |
| 30 | 4.2.2 NFR1 | "The fine-tuned model shall reach an mAP@50 of at least 0.80 overall and an AP@50 of at least 0.80 for each of the four damage classes on the local test subset (Section 3. …" → "The system shall reach a performance of at least 0.80 in accuracy, precision, recall, or F1-score on the local test subset, for the detection and the classification of th …" | green |
| 31 | 4.2.5 model testing | "The deployed fusion was then evaluated once on the local test subset on 11 November 2026, with metrics fixed beforehand, and each model alone on the foreign test subset ( …" → "The deployed fusion was then evaluated once on the local test subset on 11 November 2026, with box-level metrics fixed beforehand, and each model alone on the foreign tes …" | green |
| 32 | 4.3.1 software specifications table | "including precision, recall, AP, and mAP@50 per class, and training of the second-stage YOLOv8n classification model;" → "including box-level precision and recall, and training of the second-stage YOLOv8n classification model;" | green |
| 33 | 4.4.4 Detection performance row (what it shows) | "How well the deployed models find and classify each of the four damage classes" → "How well the deployed system finds and classifies each of the four damage classes" | green |
| 34 | 4.4.4 Detection performance row (basis) | "Precision, recall, F1-score, and mAP@50 at IoU 0.50 on the local test subset (primary) and the foreign test subset (secondary), and the classification accuracy of detecte …" → "Frame-level accuracy, precision, recall, and F1-score for damage detection, overall and per class, and the classification accuracy of detected damage, on the local test s …" | green |
| 35 | 4.4.4 paragraph | "The F1-score combines the two, and mAP@50 summarizes performance across all confidence levels and all four classes." → "The F1-score combines the two, and accuracy counts every frame judged correctly, with or without damage; because most road frames show no damage, accuracy is read togethe …" | green |
| 36 | Chapter V intro | "the detection and classification performance of the deployed fusion of three fine-tuned YOLOv8 models," → "the detection and classification performance of the deployed system, a fusion of three fine-tuned YOLOv8 models with a second-stage classifier," | green |
| 37 | 5.1 intro | "A second-stage classifier added after the test evaluation is reported separately in Section 5.1.7; the test results below describe the class labels of the fusion alone." → "The deployed system then passes each detected box to a second-stage classifier that sets its damage type (Section 3.3.1). The test results below are those of the deployed …" | green |
| 38 | 5.1.1 first paragraph | "Table 5.1.2 presents the per-class results at an IoU threshold of 0.50: AP@50 over all confidence levels, and precision, recall, and F1-score at the deployed threshold of …" → "Table 5.1.2 presents the frame-level results of the deployed system at its threshold of 0.25 on the 270 test frames, 63 of which show damage: whether it reported damage i …" | green |
| 39 | Table 5.1.2 caption | "Table 5.1.2 Per-Class Detection Results on the Local Test Subset" → "Table 5.1.2 Frame-Level Detection Results on the Local Test Subset (270 Frames, Threshold 0.25)" | green |
| 40 | 5.1.1 mAP paragraph | "The deployed fusion reached an overall mAP@50 of 0.173 on the local test subset (mAP@50-95 of 0.057), far below the acceptance level of 0.80 set in NFR1 (Section 3.8.1); …" → "The deployed system reported damage in 58 of the 270 test frames: 34 of the 63 frames with damage and 24 of the 207 frames without, for a frame-level accuracy of 0.804 (9 …" | green |
| 41 | 5.1.1 precision/recall paragraph | "At the deployed threshold of 0.25, precision was 0.31 (95% CI 21.6% to 41.7%) and recall 0.24 (95% CI 16.9% to 33.5%), for an F1-score of 0.27: of the 78 detections, 24 m …" → "When the damage type must also be correct, the deployed system found 23 of the 63 frames with damage, for an accuracy of 0.763, precision of 0.489, recall of 0.365, and a …" | green |
| 42 | 5.1.1 classification paragraph | "Among the 25 detections that matched a reviewed damage at an IoU of at least 0.50, regardless of class, 24 were given the correct damage type, a classification accuracy o …" → "Among the 25 detections of the deployed system that matched a reviewed damage at an IoU of at least 0.50, regardless of class, 23 were given the correct damage type, a cl …" | green |
| 43 | 5.1.1 per-class paragraph (before Table 5.1.3) | "The per-class results rest on few boxes, from 8 transverse cracks to 36 longitudinal cracks, so differences between classes are uncertain. Longitudinal cracks, the most c …" → "Table 5.1.3 presents the frame-level results for each damage class, with a frame counted as positive for a class when it holds a reviewed box of that class, and as correc …" | green |
| 44 | Table 5.1.3 caption | "Table 5.1.3 mAP of the Deployed Fusion and of Each Model Alone on the Local Test Subset" → "Table 5.1.3 Frame-Level Results per Damage Class on the Local Test Subset, Deployed System, Threshold 0.25" | green |
| 45 | 5.1.1 paragraph after Table 5.1.3 | "On the same test frames, each model alone reached a lower mAP@50 than the fusion (0.146 for v2b, 0.160 for v3, and 0.141 for S5_v8m_1920), so combining the three models i …" → "The per-class accuracies of 0.896 to 0.944 meet the acceptance level, but they come almost entirely from the many frames without that class: each class appears in only 5 …" | green |
| 46 | 5.1.2 first paragraph | "Table 5.1.4 shows the deployed fusion on these frames and on all 1,624 validation frames." → "Table 5.1.4 shows the deployed system on these frames and on all 1,624 validation frames, at the frame level and, for the fusion, at the box level." | green |
| 47 | Table 5.1.4 caption | "Table 5.1.4 Validation Results of the Deployed Fusion" → "Table 5.1.4 Validation Results of the Deployed System" | green |
| 48 | 5.1.2 paragraph after Table 5.1.4 | "The reviewed validation figure of 0.275 is the selection figure: the models, the fusion, and the threshold were all picked by looking at these frames, so it is optimistic …" → "The reviewed validation figures are selection figures: the models, the fusion, and the threshold were all picked by looking at these frames, so they are optimistic, and t …" | green |
| 49 | 5.1.3 heading | "5.1.3 Detection Performance on the Foreign Test Subset" → "5.1.3 Comparison with Pretrained Models and Foreign Test Results" | green |
| 50 | 5.1.3 first paragraph | "Table 5.1.5 presents the results on the foreign test subset, 3,277 images from six RDD2022 countries. Each model was evaluated alone at its deployed input size; the fusio …" → "Table 5.1.5 compares the deployed system with four models that were not fine-tuned on local roads, on the same 270 test frames and with the same frame-level measures (Sec …" | green |
| 51 | Table 5.1.5 caption | "Table 5.1.5 Per-Class AP@50 of Each Model on the Foreign Test Subset" → "Table 5.1.5 Frame-Level Comparison with Pretrained Models on the Local Test Subset (270 Frames)" | green |
| 52 | 5.1.3 paragraph after table (foreign mAP -> comparison) | "On the foreign test subset, the models reached an mAP@50 of 0.200 (v2b), 0.239 (v3), and 0.318 (S5_v8m_1920). The v2b figure is not a held-out result: v2b starts from an …" → "The deployed system is comparable to the best public RDD2022 checkpoints (overlapping confidence intervals) and better than the RDD2022-only model and the stand-in model …" | green |
| 53 | 5.1.3 paragraph (teacher / stand-in mAP -> foreign box-level) | "The opposite gap, between foreign and local roads, motivated the local labels. The RDD2022-only teacher model, a YOLOv8m trained on 5,750 RDD2022 images and never deploye …" → "On the foreign test subset, 3,277 images from six RDD2022 countries, each of the three fused models was evaluated alone at its deployed input size with Ultralytics; the f …" | green |
| 54 | 5.1.4 text | "The local errors are therefore mostly missed damage and false alarms, not wrong types." → "With the second-stage classifier, as deployed, 2 of the 4 transverse cracks were labeled potholes and every other type was unchanged (Section 5.1.1). The local errors are …" | green |
| 55 | 5.1.5 text | "In each run, the kept weights are those of the epoch with the highest mAP@50-95." → "In each run, the kept weights are those of the epoch with the best box-level validation score, Ultralytics’ default." | green |
| 56 | 5.1.7 first paragraph | "After the test evaluation, a second-stage classifier was added" → "After the first test evaluation, a second-stage classifier was added" | green |
| 57 | 5.1.7 first paragraph (table intro) | "Table 5.1.7 presents its training settings and its result on the validation crops." → "Table 5.1.7 presents its training settings and its results on the validation and test crops." | green |
| 58 | Table 5.1.7 caption | "Table 5.1.7 Training Settings and Validation Result of the Second-Stage Classifier" → "Table 5.1.7 Training Settings and Results of the Second-Stage Classifier" | green |
| 59 | 5.1.7 second paragraph | "A comparison of the two on the same matched validation detections was not run, so it is not known whether the classifier labels the detections of the fusion better than t …" → "On the 99 crops of the local test subset, which the classifier never saw in training or selection, it gave the correct class to 85, a top-1 accuracy of 85.9% (95% CI 77.7 …" | green |
| 60 | 5.1.7 third paragraph | "The classifier has no test result. It was trained after the single test run of 11 November 2026, and no metrics were fixed for it beforehand, so evaluating it on the test …" → "The classifier was trained after the single box-level test run of 11 November 2026, and no metrics were fixed for it beforehand. Its test figure was computed on 15 Novemb …" | green |
| 61 | 5.1.7 fourth paragraph | "The classifier is enabled in the current settings of the system. When it is enabled, it replaces the damage type of every record with its own prediction, while the number …" → "The classifier is part of the deployed system. It replaces the damage type of every record with its own prediction, while the number of records and their boxes, times, po …" | green |
| 62 | 5.1.8 item 1 | "Small evaluation sets. The reviewed validation frames hold 122 boxes and the test frames 99, with only 8 transverse cracks and 21 potholes in the test set. Differences of …" → "Small evaluation sets. Only 63 of the 270 test frames show damage, and only 5 of them hold a transverse crack and 17 a pothole. The frame-level intervals are about ±12 pe …" | green |
| 63 | 5.1.8 item 2 | "The reviewed validation figure of 0.275 is a selection figure," → "The reviewed validation figures are selection figures," | green |
| 64 | 5.1.8 item 3 | "Selection of the kept weights. Each training run kept the epoch with the highest mAP@50-95, Ultralytics’ default, while the models were compared on mAP@50." → "Selection of the kept weights. Each training run kept its epoch by Ultralytics’ default box-level score, while the system is judged at the frame level." | green |
| 65 | 5.1.8 item 7 | "Validation does not predict per-class test results: potholes fell from 0.376 AP@50 on validation to 0.035 on test, and alligator cracks rose from 0.027 to 0.152." → "Validation does not predict per-class test results: the frame-level F1-score of potholes fell from 0.517 on the reviewed validation frames to 0.071 on test, and that of a …" | green |
| 66 | 5.1.8 item 9 (+ new items 10-11) | "The second-stage classifier has no test result. It was added after the single test run, its 82.0% accuracy is a selection figure on validation crops, and the test figures …" → "The second-stage classifier was evaluated on the test crops only after the change to system-level measures, and that figure was not fixed in advance. It is trained on cro …" | green |
| 67 | 5.1.6 (pending review of flagged records) | "whether those flags are correct was not reviewed within the study period." → "whether those flags are correct was not reviewed within the study period. [PENDING: review of the 36 flagged records]" | yellow (pending) |
| 68 | 5.3 (pending record-level review) | "Table 5.3.1 presents the results." → "Table 5.3.1 presents the results. [PENDING: manual review of the 50 sampled R07 records: record precision (real damage), type correctness, location correctness, and dupli …" | yellow (pending) |
| 69 | 5.7 item 1 (RQ1) | "On the local test subset, the deployed fusion of three YOLOv8 models reached an mAP@50 of 0.173, with per-class AP@50 from 0.035 for potholes (D40) to 0.381 for longitudi …" → "On the 270 frames of the local test subset, 63 of which show damage, the deployed system, the fusion of three YOLOv8 models with the second-stage classifier, reached a fr …" | green |
| 70 | 5.7 item 2 (pending) | "The correctness of the damage type was not measured, because the manual review was not completed within the study period." → "The correctness of the damage type was not measured, because the manual review was not completed within the study period. [PENDING: R07 record review]" | yellow (pending) |
| 71 | 6.1 objective 1 | "On the held-out local test subset, the deployed fusion reached an mAP@50 of 0.173, with precision of 0.31, recall of 0.24, and an F1-score of 0.27 at its threshold, and 9 …" → "On the held-out local test subset of 270 frames, 63 of them with damage, the deployed system reported damage with a frame-level accuracy of 0.804, precision of 0.586, rec …" | green |
| 72 | 6.1 objective 2 (pending) | "Whether the damage type of each record is correct was not measured, because the manual review was not completed, so no conclusion on the damage type or on the duplicate r …" → "Whether the damage type of each record is correct was not measured, because the manual review was not completed, so no conclusion on the damage type or on the duplicate r …" | yellow (pending) |
| 73 | 6.1 overall paragraph | "but the measured detection results are well below the level set for the system, while its intended users" → "but its detection precision, recall, and F1-score are below the level set for the system, although the damage it finds is classified above that level, while its intended …" | green |
| 74 | 6.2 model comparison recommendation | "and compared with the class labels of the fusion on the same detections, since its present result is a validation figure only." → "since its test figure was computed after the fact, and it should be trained on crops cut in the same way as the boxes it receives in the system, since on the present test …" | green |
| 75 | 4.1.5 Haversine reference | "the Haversine formula (Equation 25)" → "the Haversine formula (Equation 24)" | green |
| 76 | 4.1.5 damage log reference | "for time and location (Equation 24)" → "for time and location (Equation 23)" | green |
| 77 | 4.1.5 t-test reference | "at the 0.05 level (Equations 26 to 28)" → "at the 0.05 level (Equations 25 to 27)" | green |
| 78 | 4.4.5 weighted mean reference | "will be computed with Equation 26." → "will be computed with Equation 25." | green |

### Tables, equations and formatting

| Place | Change | Source |
|---|---|---|
| Table 5.1.2 | Was per-class P / R / F1 / AP@50 of the fusion. Now frame-level results, 6 × 5: damage present (deployed system); correct type (deployed system); correct type (fusion without the classifier); reference "reports no damage" (accuracy 0.767); damage present on the reviewed validation frames (selection set). Accuracy, precision, recall and F1 with 95% CIs (Wilson; F1 bootstrap). Last row un-bolded (it had kept the bold of the old "All classes" row). | SL §2; JSON `fusion_cls.test`, `fusion.test`, `fusion_cls.val` |
| Table 5.1.3 | Was mAP / mAP@50-95 / AP@50 per class for the fusion and each model alone. Now frame-level results per class for the deployed system: frames with the class, TP / FP / FN / TN, accuracy, precision, recall, F1 with CIs. | SL §3 Table S4; JSON `fusion_cls.test.per_class_typed` |
| Table 5.1.4 | The two mAP columns replaced by frame-level F1 (damage present; correct type) of the deployed system; the box-level P / R / F1 columns of the fusion kept and relabelled "Box-level … (fusion)". The all-validation frame-level figures (0.531, 0.440) were newly computed on the 1,624 val frames (`system_level_eval.py --val-all`); validation only, nothing selected. | SL JSON `fusion_cls.val`, `val_all_1624`; TE Table 5.B |
| Table 5.1.5 | Old foreign per-class AP@50 table deleted. New 7 × 7 frame-level comparison: deployed system, fusion without the classifier, teacher, SA YOLOv8s, SA YOLOv12s, stand-in; threshold, accuracy / precision / recall / F1 (CI) for damage present, and F1 for the correct type. | SL §5 |
| Table 5.1.7 | Last row "Result on the local test subset: None; not evaluated on test" → "Top-1 accuracy on the 99 held-out test crops: 85.9% (85 of 99; 95% CI 77.7% to 91.4%)". | SL §4 |
| Table 5.1.8 (new) | Caption and 6 × 6 table after Table 5.1.7: reviewed class × predicted class of the classifier on the 99 test crops, per-class recall and precision with CIs, top-1 accuracy. | SL §4 |
| 3.8.1 equations | The AP equation (20) replaced by the typed equation `Accuracy = (TP + TN) / (TP + FP + FN + TN)` (20) in Cambria Math; the mAP equation (21) deleted; its "where" lines replaced (TP / FP / FN / TN definition; the 0.767 baseline note). | — |
| Equation numbers | (22)→(21) classification accuracy, (23)→(22) Wilson, (24)→(23) correctness rate, (25)→(24) Haversine, (26)→(25), (27)→(26), (28)→(27) UAT, (29)→(28) frequency and percentage. References updated: 3.8.1 "(Equation 22)"; 4.1.5 "Equations 17 to 22", "(Equation 24)" Haversine, "(Equation 23)" damage log, "(Equations 25 to 27)"; 4.4.5 "Equation 25". Equations 1-19 unchanged. | — |
| 3.8.1 bold | "Comparison with pretrained models." set bold as a run-in heading; only "Accuracy " bold in the paragraph that replaced the "Average Precision" run-in. | — |

### Every place mAP@50, mAP@50-95 or AP@50 was removed

- **Chapter I:** 1.2 (detection evaluated by mean Average Precision); 1.3 RQ1; 1.5.2 SO1.
- **Chapter III:** 3.3.1 (kept epoch on mAP@50-95, compared on mAP@50; S5_v8m_1920 at 0.200 / 0.205 / 0.201); 3.3.3
  intro; 3.8.1 (AP and mAP definitions, equations 20-21 and their "where" lines, model-selection sentence, acceptance
  criterion); Table 3.8.7 (Ultralytics row).
- **Chapter IV:** Table 4.1.1 (RQ1 measure); NFR1 in Table 4.2.2.1; Table 4.3.1.1 (Ultralytics row); the 4.4.4 table
  (detection basis and acceptance) and the paragraph under it.
- **Chapter V:** 5.1.1 (text and Tables 5.1.2, 5.1.3, including the "0.173 (mAP@50)" cell); 5.1.2 (Table 5.1.4 columns
  and the 0.275 / 0.161 / 0.173 paragraph); 5.1.3 (Table 5.1.5, the foreign mAP paragraph, the model-card sentence,
  teacher 0.472 / 0.090, stand-in 0.155, fusion 0.275); 5.1.5 (kept epoch on mAP@50-95); 5.1.8 items 1, 2, 3 and 7;
  5.7 item 1.
- **Chapter VI:** 6.1 objective 1.
- **Table of contents:** no entry mentions mAP, but the heading "5.1.3 Detection Performance on the Foreign Test Subset"
  was renamed "5.1.3 Comparison with Pretrained Models and Foreign Test Results", so the TOC must be refreshed by hand
  (the API cannot do it).
- **Abstract:** the document has **no abstract** (nothing between the title page and Chapter I), so none was edited or
  written. If one should be added, it would be written only from SL.
- **Figure captions:** none mentioned mAP. **Figure 5.1.3** (training curves, `results.png`, image still to be inserted)
  plots Ultralytics' mAP50 and mAP50-95 panels; replace the image or crop those panels if mAP must not appear in figures.

### Chapter II literature that cites mAP (not changed; for the team's decision)

| # | Place | Text |
|---|---|---|
| L1 | 2.1, Khare et al. (2023) | "their YOLOv8 nano model reached an mAP@0.5 of 0.91 at 8.8 ms per image" |
| L2 | 2.1, Zeng & Zhong (2024) | "which raised mAP by 1.4 percentage points on RDD2022" |
| L3 | 2.1, Zhang et al. (2025) | "reported increases of 1.8% in mAP@0.5 and 1.6% in F1-score on the China subset of RDD2022" |
| L4 | 2.1, RDD2022 model cards | "these models report an mAP@50 of about 0.60 to 0.63: 0.5995 for a YOLOv8s model …" |
| L5 | 2.2, Sarmiento (2021) | "YOLOv4 reached an mAP of only 0.272" |
| L6 | 2.2, local study (three universities) | "achieved an average precision of 95.43%" |
| L7 | 2.2, Fortin et al. (2024) | "Its YOLOv5m model reached an mAP of 91.8%" |
| L8 | Table 2.3.1, Khare et al. | "YOLOv8 nano reached an mAP@0.5 of 0.91 …" |
| L9 | Table 2.3.1, Zeng & Zhong | "Raised mAP by 1.4 percentage points on RDD2022 …" |
| L10 | Table 2.3.1, Zhang et al. | "Increased mAP@0.5 by 1.8% and F1-score by 1.6% on RDD2022-China" |
| L11 | Table 2.3.1, Sarmiento | "YOLOv4 reached an mAP of 0.272 on 305 DPWH images …" |
| L12 | Table 2.3.1, Fortin et al. | "YOLOv5m reached an mAP of 91.8% …" |
| L13 | Table 2.3.1, local study (three universities) | "Achieved 95.43% average precision …" |

The Chapter V sentence that compared with the model cards (5.1.3, "Published RDD2022 model cards report about 0.60 to
0.63 mAP@50 … (Section 2.1)") was removed with the foreign-mAP paragraph; if L4 is removed from 2.1, nothing else
refers to it.

### Points to check

1. **"Better than the RDD2022-only model."** True for damage present (F1 0.562 vs 0.462; CIs overlap). For the correct
   type the teacher is slightly higher (0.448 vs 0.418). The text uses the instructed sentence, scoped "in detecting
   damage", and states the teacher's type F1 next to it (5.1.3).
2. **An earlier statement in 5.1.7 was removed as inaccurate.** It said a test-crop figure "was not saved" and that "the
   test crops have since been removed from the scripts". In the repository a test-crop validation was saved on
   2026-11-12 (`runs/classify/road_damage_test/`, confusion matrices), and `ml/build_classifier_dataset.py` still builds
   the test crops. The new text says that a test-crop result was produced once on 12 November and that the classifier
   was not chosen or changed on it.
3. **Foreign test subset.** Its only per-class results were AP@50; 5.1.3 now gives each model's box-level precision and
   recall at Ultralytics' validation settings (TE Table 5.F). SO1 no longer says "reported separately for the foreign
   and local test subsets", following the instructed SO1 wording.
4. **Figure 5.1.1** (matched pairs, image) shows the fusion without the classifier; 5.1.4 now adds that, with the
   classifier, 2 of the 4 transverse cracks are labelled potholes.
5. **Record-level subsections** (5.1.6 flagged records, 5.3, 5.7 item 2, 6.1 objective 2) carry yellow `[PENDING]`
   markers; the existing automatic time and location results in 5.3 are unchanged. To be scored after the R07 review.
6. **Not changed:** the high-confidence operating point (box-level precision ≥ 0.80, 3.8.1 and 5.1.1), the UAT results
   (4.62, hypothesis supported), and everything not listed above.

---

## Part B revision (2026-11-15): acceptance level removed, Chapters I–III in past tense, 5.7 / 6.1 / 6.2 condensed

- **Document:** https://docs.google.com/document/d/1nn5vxNuuDDfNycLGlEwNVaJkqvsrUo4MOAzarpffXuw/edit (main tab `t.0` and the
  sub-tab "System Performance (Plain Language)", `t.dulxisearlym`).
- **Team edits respected.** Before any change, the main tab was compared with the last text written in Stage 2. Paragraphs that
  differed are the team's and were not touched:
  - the title-page date;
  - 2.2 and 2.3;
  - 3.3.1, 3.7, and the 3.8.1 classifier and model-selection paragraphs;
  - 4.2.4 and 4.2.5;
  - the hardware rows;
  - 5.1.7 and the 5.1.8 list;
  - four "[image]" items in 4.1.8.

  No edit's find text fell inside them (checked).
- **Concurrent team edits.** While this revision ran, the team rewrote the Chapter VI intro, **6.1** and **6.2**, and added
  Appendices A–G. Their text replaced the 6.1 / 6.2 versions written here a few minutes earlier, and it was left as it is.
  `docs/MANUSCRIPT_TODO.md` lists where it differs from the Part B instructions:
  - 6.2 has three paragraphs;
  - "Android validation" and "shadows, glare and wet roads" are not in it.
- **Method.**
  - 107 find/replace edits, each found exactly once in its tab before sending, applied with `match_case` and limited to their tab.
  - The 5.7 / 6.1 / 6.2 rewrites were made by position: the first paragraph's text was replaced and the rest deleted.
  - Afterwards the text was compared with the simulation. It matched, apart from the team's concurrent edits.
  - Changed words are highlighted green, by position, read back after the edits. The read was checked to be unchanged before the
    highlights were applied.
  - Two table cells (NFR1, 4.4.4) are not highlighted.
- **Numbers.** None changed. "0.80" was removed only where it was an acceptance level. It remains in the high-confidence operating
  point (3.8.1, 5.1.1), a precision target fixed in advance; that one is for the team to decide. The "a system reporting nothing
  would score 0.767" sentence is kept everywhere.

### Rewritten sections

| Section | Before | After |
|---|---|---|
| 5.7 Summary of Findings | An intro plus a five-item numbered list by research question; said "Only detection accuracy reached the acceptance level of 0.80" and "Classification meets the acceptance level" | One paragraph: frame-level detection results, classification, pretrained comparison, expert check, damage log (automatic checks; `[PENDING: R07 record review…]` in yellow), positional error not measured, UAT (4.62, hypothesis supported). Same numbers. |
| 6.1 Conclusion | An intro, four objective paragraphs and an "Overall" paragraph; said "only detection accuracy reached 0.80", "Classification meets the acceptance level" and "below the level set for the system" | Written here as three paragraphs without a threshold, **then replaced by the team's own three paragraphs** ("The study achieved its general objective…"), which stand. |
| 6.2 Recommendations | An intro plus six run-in paragraphs | Written here as two paragraphs covering every listed recommendation, **then replaced by the team's own three paragraphs** ("To improve detection…"), which stand. |

### Text changes (in the order of the edit list)

| # | Section | Kind | Old → new (abridged) |
|---|---|---|---|
| B1 | 3.8.1 run-in label | Acceptance level removed | “Acceptance criterion. As required by the panel” → “Adoption of the system-level measures. As required by the panel” |
| B2 | 3.8.1 acceptance paragraph | Acceptance level removed | “As required by the panel, the system must reach a performance of at least 0.80 in accuracy, precision, recall, or F1-score on the local test subset, w … the system and is separate from the hypothesis of the study.” → “These system-level measures were adopted after the initial box-level evaluation, at the adviser’s recommendation, to reflect how the system is used. E … separately, by the user acceptance testing in Section 3.8.5.” |
| B3 | 4.2.2 NFR1 (Table 4.2.2.1) | Acceptance level removed | “The system shall reach a performance of at least 0.80 in accuracy, precision, recall, or F1-score on the local test subset, for the detection and the classification of the four damage classes (Section 3.8.1).” → “The system shall detect and classify the four damage classes on the local test subset, with its frame-level accuracy, precision, recall, and F1-score and its classification accuracy reported as measured (Section 3.8.1).” |
| B4 | 4.4.4 table, detection basis | Acceptance level removed | “with a comparison with pretrained models on the same frames; acceptance requires a performance of at least 0.80 in accuracy, precision, recall, or F1-score” → “with a comparison with pretrained models on the same frames” |
| B5 | 5.1.1 detection paragraph | Acceptance level removed | “Detection accuracy is the only one of these measures that reached the acceptance level of 0.80 set in NFR1 (Section 3.8.1), and only just: because 207 … recision, recall, and F1-score for detection are below 0.80.” → “Accuracy is the highest of these measures, but it has to be read with care: because 207 of the 270 test frames have no damage, a system that reported  … r in ten of the frames in which it reported damage had none.” |
| B6 | 5.1.1 correct type | Acceptance level removed | “and an F1-score of 0.418, all below 0.80.” → “and an F1-score of 0.418.” |
| B7 | 5.1.1 classification accuracy | Acceptance level removed | “(95% CI 75.0% to 97.8%), which meets the acceptance level of 0.80.” → “(95% CI 75.0% to 97.8%).” |
| B8 | 5.1.1 per class | Acceptance level removed | “The per-class accuracies of 0.896 to 0.944 meet the acceptance level, but” → “The per-class accuracies of 0.896 to 0.944 are high, but” |
| B9 | 5.1.1 per class | Acceptance level removed | “Precision, recall, and F1-score are below 0.80 for every class, except the precision of alligator cracks (D20), 0.857” → “Precision, recall, and F1-score are lower for every class, most of them far lower; the highest is the precision of alligator cracks (D20), 0.857” |
| B10 | 5.1.7 classifier test figure | Acceptance level removed | “a top-1 accuracy of 85.9% (95% CI 77.7% to 91.4%), which meets the acceptance level of 0.80.” → “a top-1 accuracy of 85.9% (95% CI 77.7% to 91.4%).” |
| B11 | Ch I intro | Past tense | “This study aims to develop a web-based road damage detection” → “This study aimed to develop a web-based road damage detection” |
| B12 | Ch I intro | Past tense | “The proposed system seeks to support more efficient” → “The proposed system was designed to support more efficient” |
| B13 | Ch I intro | Past tense | “The study is intended to benefit” → “The study was intended to benefit” |
| B14 | 1.1 | Past tense | “so that the detector is adapted to the road conditions in which it will be used.” → “so that the detector is adapted to the road conditions in which it is used.” |
| B15 | 1.1 | Past tense | “the proposed study integrates YOLOv8-based road damage detection” → “the present study integrated YOLOv8-based road damage detection” |
| B16 | 1.1 | Past tense | “The study specifically addresses the four road damage categories” → “The study specifically addressed the four road damage categories” |
| B17 | 1.1 | Past tense | “the proposed system aims to automate the detection, localization, and mapping of road damage records” → “the proposed system was designed to automate the detection, localization, and mapping of road damage records” |
| B18 | 1.2 | Past tense | “This study aims to develop OCULUBAK” → “This study aimed to develop OCULUBAK” |
| B19 | 1.2 | Past tense | “Both parts are evaluated at the level at which the system is used” → “Both parts were evaluated at the level at which the system is used” |
| B20 | 1.2 | Past tense | “the proposed system aims to improve the efficiency” → “the proposed system was designed to improve the efficiency” |
| B21 | 1.2 | Past tense | “The study also seeks to provide” → “The study also sought to provide” |
| B22 | 1.3 | Past tense | “This study addresses the following research questions:” → “This study addressed the following research questions:” |
| B23 | 1.4 | Past tense | “It is hypothesized that the Web-Based” → “It was hypothesized that the Web-Based” |
| B24 | 1.4 | Past tense | “timestamp synchronization, will be effective in improving” → “timestamp synchronization, would be effective in improving” |
| B25 | 1.6 | Past tense | “The study focuses on the development of a web-based road damage detection and mapping system that integrates” → “The study focused on the development of a web-based road damage detection and mapping system that integrates” |
| B26 | 1.6 | Past tense | “the system aims to provide a more organized” → “the system was designed to provide a more organized” |
| B27 | 1.7 | Past tense | “This study focuses on the development of OCULUBAK” → “This study focused on the development of OCULUBAK” |
| B28 | 1.7 | Past tense | “The study specifically covers the four road damage categories” → “The study specifically covered the four road damage categories” |
| B29 | 1.7 | Past tense | “Survey data will be recorded with a companion mobile capture application on iPhones.” → “Survey data were recorded with a companion mobile capture application on iPhones.” |
| B30 | 1.7 | Past tense | “no detection or analysis, and its behavior on Android devices is not evaluated in this study.” → “no detection or analysis, and its behavior on Android devices was not evaluated in this study.” |
| B31 | 1.7 classifier (consistency) | Consistency | “was added after the test evaluation. It changes only the class label of a record, and it was evaluated on validation data only, so the test results of this study describe the fusion of the three detection models without it.” → “was added after the first test evaluation. It changes only the class label of a record; it is part of the deployed system, so the system-level test results of this study include it (Section 5.1.7).” |
| B32 | 2.1 | Past tense | “The present study works instead from ordinary two-dimensional video” → “The present study worked instead from ordinary two-dimensional video” |
| B33 | Ch III intro | Past tense | “the methods that the researchers will use to develop and evaluate” → “the methods that the researchers used to develop and evaluate” |
| B34 | 3.1 | Past tense | “The researchers will follow the Agile methodology” → “The researchers followed the Agile methodology” |
| B35 | 3.1 | Past tense | “The development of OCULUBAK is organized into five sprints” → “The development of OCULUBAK was organized into five sprints” |
| B36 | 3.1 | Past tense | “Every sprint passes through the same five activities” → “Every sprint passed through the same five activities” |
| B37 | 3.1 | Past tense | “Phase 1 will establish the system foundation and produce the first working prototype. Phase 2 will refine detection performance using the four-class d … view at the end of each sprint will determine the objectives” → “Phase 1 established the system foundation and produced the first working prototype. Phase 2 refined detection performance using the four-class dataset … e review at the end of each sprint determined the objectives” |
| B38 | 3.1.1 | Past tense | “The first phase will establish the architecture and the core functions of the system and will produce a working prototype that can accept a road surve … n results. This phase will involve the following activities:” → “The first phase established the architecture and the core functions of the system and produced a working prototype that could accept a road survey video and return detection results. This phase involved the following activities:” |
| B39 | 3.1.1 | Past tense | “The review of this phase will identify the detection and positioning limitations that the next phases must address.” → “The review of this phase identified the detection and positioning limitations that the next phases had to address.” |
| B40 | 3.1.2 | Past tense | “The second phase will focus on the detection model. Its activities will be the following:” → “The second phase focused on the detection model. Its activities were the following:” |
| B41 | 3.1.2 | Past tense | “which will begin only after ethics clearance has been obtained.” → “which began only after ethics clearance had been obtained.” |
| B42 | 3.1.3 | Past tense | “The third phase will connect detection results with geographic locations. Its activities will be the following:” → “The third phase connected detection results with geographic locations. Its activities were the following:” |
| B43 | 3.1.4 | Past tense | “The fourth phase will combine the separate modules into one application. Its activities will be the following:” → “The fourth phase combined the separate modules into one application. Its activities were the following:” |
| B44 | 3.1.5 | Past tense | “The fifth phase will stabilize the system and carry out the evaluations described in Section 3.8. Its activities will be the following:” → “The fifth phase stabilized the system and carried out the evaluations described in Section 3.8 that could be completed within the study period. Its planned activities were the following:” |
| B45 | 3.2.1 | Past tense | “In this study the two will be recorded concurrently by the mobile capture application” → “In this study the two were recorded concurrently by the mobile capture application” |
| B46 | 3.3.1 | Past tense | “Algorithm 3.1 presents the procedure that OCULUBAK will apply to an uploaded survey video” → “Algorithm 3.1 presents the procedure that OCULUBAK applies to an uploaded survey video” |
| B47 | 3.3.2 | Past tense | “The rate of duplicate records that remain will be measured in the damage log correctness check (Section 3.8.3).” → “The rate of duplicate records that remain is reported in the damage log correctness check (Section 3.8.3).” |
| B48 | 3.3.3 | Past tense | “the formulas for processing throughput will be reported with the measured results in Chapter V.” → “the formulas for processing throughput are reported with the measured results in Chapter V.” |
| B49 | 3.4 | Past tense | “how the concepts in Section 3.2 will be realized in the implemented system” → “how the concepts in Section 3.2 were realized in the implemented system” |
| B50 | 3.4.2 | Past tense | “The application will be used on the researchers' iPhones for all survey data collected in this study.” → “The application was used on the researchers' iPhones for all survey data collected in this study.” |
| B51 | 3.4.2 | Past tense | “and will not start a recording unless the phone has at least 2 GB” → “and does not start a recording unless the phone has at least 2 GB” |
| B52 | 3.4.2 | Past tense | “the application will not start recording until it has a GPS fix” → “the application does not start recording until it has a GPS fix” |
| B53 | 3.4.2 | Past tense | “recorded in each session's GPS file and will be reported as a measured value.” → “recorded in each session's GPS file and is reported as a measured value (Section 5.4).” |
| B54 | 3.4.3 (consistency) | Consistency | “The foreign and local test subsets are kept separate so that performance can be reported for each, as required by the first specific objective.” → “The foreign and local test subsets were kept separate so that performance could be reported for each.” |
| B55 | 3.5 | Past tense | “all of whom will use the system under the Road Maintenance Personnel role during evaluation.” → “all of whom used the system under the Road Maintenance Personnel role during the evaluation.” |
| B56 | 3.6 | Past tense | “The respondents of this study will consist of personnel” → “The respondents of this study consisted of personnel” |
| B57 | 3.6 | Past tense | “The respondents will be drawn from three groups:” → “The respondents were drawn from three groups:” |
| B58 | 3.6 | Past tense | “All personnel of the partner office who meet the inclusion criteria will be invited to participate, so the number of respondents will equal the number … s do not involve road condition assessment will be excluded.” → “All personnel of the partner office who met the inclusion criteria were invited to participate, so the number of respondents was to equal the number o … ies did not involve road condition assessment were excluded.” |
| B59 | 3.6 | Past tense | “The respondents will be chosen because they are the intended end-users” → “The respondents were chosen because they are the intended end-users” |
| B60 | 3.6 | Past tense | “The study will use purposive sampling in selecting respondents, as only individuals directly involved in infrastructure management and road monitoring … uation of the system. The respondents will assess the system” → “The study used purposive sampling in selecting respondents, as only individuals directly involved in infrastructure management and road monitoring participated in the evaluation of the system. The respondents assessed the system” |
| B61 | 3.6 | Past tense | “Information gathered from the respondents through the evaluation questionnaire will be used to analyze” → “Information gathered from the respondents through the evaluation questionnaire was used to analyze” |
| B62 | 3.7 | Past tense | “The development and evaluation of OCULUBAK will be guided by ethical principles” → “The development and evaluation of OCULUBAK were guided by ethical principles” |
| B63 | 3.7 | Past tense | “Institutional ethics review applies to the evaluation questionnaire” → “Institutional ethics review applied to the evaluation questionnaire” |
| B64 | 3.7 | Past tense | “access to them will be restricted as described below, and they will not be published or shared” → “access to them was restricted as described below, and they were not published or shared” |
| B65 | 3.7 | Past tense | “all surveys will be recorded by the researchers themselves, who consent to the collection of their own routes.” → “all surveys were recorded by the researchers themselves, who consented to the collection of their own routes.” |
| B66 | 3.7 | Past tense | “Access to the system will require login with a signed JSON Web Token that expires after twelve hours. Accounts will be created only by a system admini … le detection records and the damage map will be shared among” → “Access to the system requires login with a signed JSON Web Token that expires after twelve hours. Accounts are created only by a system administrator, …  while detection records and the damage map are shared among” |
| B67 | 3.7 | Past tense | “All respondents will be required to give written informed consent before taking part in the evaluation. Before signing, each respondent will receive a … e of road damage classification. The consent form will state” → “All respondents were required to give written informed consent before taking part in the evaluation. Before signing, each respondent received an expla … rpose of road damage classification. The consent form stated” |
| B68 | 3.7 | Past tense | “Participation in the study is voluntary, with no coercion or obligation to give reasons for declining. Respondents may withdraw at any time without pe … spondents will face no professional or personal consequences” → “Participation in the study was voluntary, with no coercion or obligation to give reasons for declining. Respondents could withdraw at any time without … d respondents faced no professional or personal consequences” |
| B69 | 3.7 | Past tense | “The study will involve no deception. Before the evaluation, respondents will be informed of the types” → “The study involved no deception. Before the evaluation, respondents were informed of the types” |
| B70 | 3.7 | Past tense | “the purpose of the evaluation questionnaire; and how their feedback will be used.” → “the purpose of the evaluation questionnaire; and how their feedback would be used.” |
| B71 | 3.7 | Past tense | “Survey videos, GPS tracks, detection records, and questionnaire responses will be stored on password-protected systems accessible only to the research … naire responses will be analyzed without respondents' names.” → “Survey videos, GPS tracks, detection records, and questionnaire responses were stored on password-protected systems accessible only to the research te … ionnaire responses were analyzed without respondents' names.” |
| B72 | 3.8 | Past tense | “the statistical methods that will be used to analyze the data gathered” → “the statistical methods that were used to analyze the data gathered” |
| B73 | 3.8 | Past tense | “because it states that the effectiveness of the system will be determined through evaluation” → “because it stated that the effectiveness of the system would be determined through evaluation” |
| B74 | 3.8.1 | Past tense | “Detection performance is measured at the level at which the system is used” → “Detection performance was measured at the level at which the system is used” |
| B75 | 3.8.1 | Past tense | “It is computed on the local test subset, 270 near-zone frames” → “It was computed on the local test subset, 270 near-zone frames” |
| B76 | 3.8.1 | Past tense | “The same measures are computed for each of the four damage classes” → “The same measures were computed for each of the four damage classes” |
| B77 | 3.8.1 | Past tense | “are reported beside them, and for each model alone on the foreign test subset” → “were reported beside them, and for each model alone on the foreign test subset” |
| B78 | 3.8.1 | Past tense | “All four measures are reported at the deployed threshold of 0.25” → “All four measures were reported at the deployed threshold of 0.25” |
| B79 | 3.8.1 | Past tense | “95 percent Wilson score intervals are given for accuracy, precision, and recall” → “95 percent Wilson score intervals were given for accuracy, precision, and recall” |
| B80 | 3.8.1 | Past tense | “the class decision is also measured on its own. At the deployed threshold, each detection is paired” → “the class decision was also measured on its own. At the deployed threshold, each detection was paired” |
| B81 | 3.8.1 | Past tense | “It is computed for the deployed system, whose damage types” → “It was computed for the deployed system, whose damage types” |
| B82 | 3.8.1 | Past tense | “so it is always reported together with recall and the number of matched detections” → “so it was always reported together with recall and the number of matched detections” |
| B83 | 3.8.1 | Past tense | “reaches at least 0.80 is also reported, with its precision and recall” → “reaches at least 0.80 was also reported, with its precision and recall” |
| B84 | 3.8.1 | Past tense | “the confusion matrix of each model is produced by Ultralytics; for the local test subset, the 4 × 4 table of matched pairs described above serves this purpose.” → “the confusion matrix of each model was produced by Ultralytics; for the local test subset, the 4 × 4 table of matched pairs described above served this purpose.” |
| B85 | 3.8.1 | Past tense | “The same frame-level measures are computed on the same 270 test frames” → “The same frame-level measures were computed on the same 270 test frames” |
| B86 | 3.8.1 | Past tense | “Each runs with the system’s settings” → “Each was run with the system’s settings” |
| B87 | 3.8.1 | Past tense | “The deployed system keeps its threshold of 0.25” → “The deployed system kept its threshold of 0.25” |
| B88 | 3.8.2 | Past tense | “of the DPWH Cavite 2nd District Engineering Office will review the 40 boxes” → “of the DPWH Cavite 2nd District Engineering Office reviewed the 40 boxes” |
| B89 | 3.8.2 | Past tense | “The sheet names the damage class of each group of boxes, and for each box he will mark whether it shows that class, list any boxes he finds incorrect, and sign the certification letter. The result is reported” → “The sheet named the damage class of each group of boxes, and for each box he marked whether it showed that class, listed any boxes he found incorrect, and signed the certification letter. The result was reported” |
| B90 | 3.8.3 | Past tense | “the researchers will check 50 stored records drawn at random” → “the researchers checked 50 stored records drawn at random” |
| B91 | 3.8.3 | Past tense | “For each record, the damage type will be checked against the snapshot, the timestamp will be checked by opening the video at that time, and the locati …  The correctness rate of each attribute will be computed as:” → “For each record, the damage type was checked against the snapshot, the timestamp was checked by opening the video at that time, and the location was c … ime. The correctness rate of each attribute was computed as:” |
| B92 | 3.8.3 | Past tense | “will also be reported, since cross-frame tracking” → “was also reported, since cross-frame tracking” |
| B93 | 3.8.3 | Past tense | “The time and the location are checked automatically.” → “The time and the location were checked automatically.” |
| B94 | 3.8.3 | Past tense | “are listed as duplicate candidates. The damage type and the duplicate candidates are then judged by a researcher” → “were listed as duplicate candidates. The damage type and the duplicate candidates were then judged by a researcher” |
| B95 | 3.8.4 | Past tense | “a sample of 20 to 30 detected damages from surveys recorded with a GPS track will be validated in the field. A researcher will stand beside each sampl … eld still for one minute, and the readings will be averaged.” → “a sample of 20 to 30 detected damages from surveys recorded with a GPS track was to be validated in the field. A researcher was to stand beside each s …  still for one minute, and the readings were to be averaged.” |
| B96 | 3.8.4 | Past tense | “The error will be summarized with the mean, standard deviation, and maximum” → “The error was to be summarized with the mean, standard deviation, and maximum” |
| B97 | 3.8.5 | Past tense | “The usability and effectiveness of the system will be evaluated through user acceptance testing” → “The usability and effectiveness of the system were evaluated through user acceptance testing” |
| B98 | 3.8.5 | Past tense | “The evaluation questionnaire will use a five-point Likert scale” → “The evaluation questionnaire used a five-point Likert scale” |
| B99 | 3.8.5 | Past tense | “The responses will be analyzed with the following statistics.” → “The responses were analyzed with the following statistics.” |
| B100 | 3.8.5 | Past tense | “a one-tailed one-sample t-test will be applied at the 0.05 level of significance:” → “a one-tailed one-sample t-test was applied at the 0.05 level of significance:” |
| B101 | 3.8.5 | Past tense | “The hypothesis will be supported if the overall weighted mean is at least 3.41 and the t-test shows it to be significantly greater than 3.41 at the 0.05 level. The results for each dimension will be reported” → “The hypothesis was to be considered supported if the overall weighted mean was at least 3.41 and the t-test showed it to be significantly greater than 3.41 at the 0.05 level. The results for each dimension were reported” |
| B102 | 3.8.6 | Past tense | “Frequency and percentage distributions will be used to summarize” → “Frequency and percentage distributions were used to summarize” |
| B103 | 3.8.7 | Past tense | “The following software tools will be used for training, evaluation, and statistical analysis.” → “The following software tools were used for training, evaluation, and statistical analysis.” |
| B104 | Sub-tab heading (sub-tab) | Acceptance level removed | “Did the system reach the 0.80 goal?” → “Which scores are high, and which are low?” |
| B105 | Sub-tab (sub-tab) | Acceptance level removed | “Reached: detection accuracy (0.804), but only just, and mostly because most frames have no damage.” → “Highest: detection accuracy (0.804), mostly because most frames have no damage.” |
| B106 | Sub-tab (sub-tab) | Acceptance level removed | “Reached: naming the damage type (92% in the system, and 86% for the type checker on its own).” → “Also high: naming the damage type (92% in the system, and 86% for the type checker on its own).” |
| B107 | Sub-tab (sub-tab) | Acceptance level removed | “Not reached: precision (0.586), recall (0.540), and F1-score (0.562) for finding damage.” → “Lower: precision (0.586), recall (0.540), and F1-score (0.562) for finding damage.” |

### Not changed (listed in `docs/MANUSCRIPT_TODO.md`)

- The one remaining future tense in Chapters I–III (3.7, "Upon completion of the study, … will be deleted"), which is still in the future.
- "will" in Chapter IV (4.2.2 NFR on video deletion, 4.2.5, 4.4.2, 4.4.3, 4.4.5): outside the Chapters I–III scope.
- The research questions (1.3) and the objectives (1.5): questions and infinitives have no tense to change.
- System descriptions kept in the present tense as instructed ("the system stores…", 3.3, 3.4.1, the CLIP check in 2.1).

---

## Record-level fills (2026-11-15, R07 review scored)

- **Review:** 50 sampled + 36 flagged R07 records, reviewer Gian Paolo Ybut, on `tools/review_damage_log/`. Three records got
  different answers in the two batches (794, 809, 838); the user settled all three as "not real damage" in both batches
  (`review_events.csv`, note in the checklists). Scored with `tools/damage_log_check.py score`; results in
  `results/damage_log_check/survey3_checklist_score.md` and `results/system_level_evaluation.md` §6.
- **Numbers:** record precision 30/50 = 60.0% (46.2–72.4%); type correct 30/30 = 100% (88.6–100%); time and location 50/50 (92.9–100%);
  duplicates 0/50 (0.0–7.1%); fully correct 30/50. Flagged: 22/36 not damage (61.1%, 44.9–75.2%), 14 real; in the sample 11/19 flagged and
  19/31 unflagged real (57.9% vs 61.3%). The user's instruction quoted 63% vs 61%, the figure before the three records were settled; the
  settled figure is used.
- **Positional edits:** Table 5.3.1 deleted and rebuilt as 7 × 4 (real damage, type among real, timestamp, location, not a duplicate,
  fully correct); one surplus empty paragraph after it removed. Two items added to the 5.1.8 limitations ("Damage log review." with the
  user's sentence, "AI check." advisory only), bold run-ins, green.
- **Highlights:** every `[PENDING]` replaced; the replacements carry no yellow and are green.

| # | Section | Old → new (abridged) |
|---|---|---|
| R1 | 1.7 AI check | “it was not trained on road damage images, it never hides or deletes a record, and its accuracy is not part of the evaluation of this study.” → “it was not trained on road damage images and it never hides or deletes a record. In the manual review of the R07 records it did not separate real from false damage (Section 5.1.6), so it is treated as advisory only.” |
| R2 | 3.8.3 procedure | “The time and the location were checked automatically. The time of a record is counted as correct when it is within 0.05 seconds of its frame number di … her from the snapshots on a review page built for the check.” → “The time and the location were first checked automatically: the time of a record is counted as correct when it is within 0.05 seconds of its frame num … te is given with a 95 percent Wilson interval (Equation 22).” |
| R3 | 4.1.1 research design | “The manual review of the damage types of those records and the positional error of GPS-to-video synchronization against field reference positions were planned but could not be completed within the study period.” → “Those records, and the records flagged by the AI check, were then reviewed by hand. The positional error of GPS-to-video synchronization against field … s planned but could not be measured within the study period.” |
| R4 | 4.1.4 sampling | “were checked automatically for time and location; the manual review of their damage types was not completed within the study period.” → “were checked automatically for time and location and reviewed by hand for real damage, damage type, and duplicates, together with the 36 records of the survey flagged by the AI check.” |
| R5 | 4.1.5 data analysis | “Damage log correctness was computed for time and location (Equation 23) with an automatic check of the 50 sampled records, together with the number of … the manual review was not completed within the study period.” → “Damage log correctness was computed for each attribute of the 50 sampled records (Equation 23): record precision, type correctness among the records t … e share that shows real damage was computed in the same way.” |
| R6 | 4.2.5 testing | “(Section 5.3); the manual review of their damage types was not completed.” → “(Section 5.3), and they and the 36 records flagged by the AI check were then reviewed by hand.” |
| R7 | 4.4.2 instruments | “on which the researcher marks whether the type, timestamp, and location are correct and whether the record duplicates another. The time and location w … d for duplicates were not completed within the study period.” → “on which the researcher marked whether the box shows real road damage, whether the type, timestamp, and location are correct, and whether the record d … age built for the check, which saved them to the checklists.” |
| R8 | 4.4.4 intro | “Detection performance, the expert check, and the time and location of the damage log were measured; the positional error against field reference positions and the correctness of the damage type were not.” → “Detection performance, the expert check, and the correctness of the damage log were measured; the positional error against field reference positions was not.” |
| R9 | 4.4.4 table | “Whether each stored record has the right type, time, and location” → “Whether each stored record shows real damage and has the right type, time, and location” |
| R10 | 4.4.4 table | “Correctness rate per attribute and duplicate rate” → “Record precision, correctness rate per attribute, and duplicate rate” |
| R11 | 5 intro | “the time and location of the damage log, the recording conditions” → “the correctness of the damage log, the recording conditions” |
| R12 | 5 intro | “The manual review of the damage types and the positional error against field reference positions could not be completed within the study period, and this is stated where it applies.” → “The positional error against field reference positions could not be measured within the study period, and this is stated where it applies.” |
| R13 | 5.1.6 Table 5.1.6 | “Not reviewed” → “22 of 36 (61.1%)” |
| R14 | 5.1.6 text | “The AI check flagged 36 of them (32.1%) as likely not road damage; whether those flags are correct was not reviewed within the study period. [PENDING: review of the 36 flagged records]” → “The AI check flagged 36 of them (32.1%) as likely not road damage. On review, 22 of the 36 flagged records showed no road damage, so the flag was righ …  this way and never hides or deletes a record because of it.” |
| R15 | 5.3 text | “The time and the location of each sampled record were checked automatically against the frame numbers of the video and the GPS track of the recording, …  type correctness, location correctness, and duplicate rate]” → “The sample was drawn before the survey was analyzed again with the second-stage classifier; the same 50 detections, with the same boxes, times, and po … nd settled before scoring. Table 5.3.1 presents the results.” |
| R16 | 5.3 duplicates paragraph | “Ten of the 50 sampled records formed five duplicate candidate pairs, that is, two records of the same class within 15 meters and a few seconds of each …  not counted, and the number of candidates is a lower bound.” → “No sampled record was judged a duplicate: 0 of 50 (95% CI 0.0% to 7.1%). The automatic check had listed 22 of the 50 records as possible duplicates, b …  damages seen a moment apart share nearly the same position.” |
| R17 | 5.3 type paragraph | “Whether each record has the correct damage type was not measured, because the manual review of the snapshots was not completed within the study period … fusion on the labeled test frames is given in Section 5.1.1.” → “Of the 50 sampled records, 30 showed real road damage, a record precision of 60.0% (95% CI 46.2% to 72.4%); the other 20 boxes showed no road damage.  … uracy on the held-out test frames is given in Section 5.1.1.” |
| R18 | 5.7 | “from the track point of its video time. [PENDING: R07 record review: record precision, type correctness, duplicate rate, and the review of the 36 flagged records]” → “from the track point of its video time. On review, 30 of the 50 sampled records showed real road damage (record precision 60.0%; 95% CI 46.2% to 72.4% … .3% of unflagged records were real), so it is advisory only.” |
| R19 | 6.1 (team paragraph, PENDING only) | “on the GPS track at its video time. [PENDING: results of the R07 record review]” → “on the GPS track at its video time. On review, 60% of the sampled records showed real road damage, every real record had the correct damage type, and  … he AI check did not reliably mark them and remains advisory.” |
| R20 | Sub-tab (sub-tab) | “Whether each record shows real damage of the right type, and how many records are duplicates: [PENDING: manual review of the 50 R07 records]” → “Whether each record shows real damage: in a review of 50 records from R07, 30 (60%) showed real road damage and the other 20 were false alarms. All 30 real ones had the right type, and none was a duplicate.” |
| R21 | Sub-tab (sub-tab) | “Damage flagged by the AI check: 36 of the 112 R07 records were marked "likely not road damage". [PENDING: review of the 36 flagged records]” → “Damage flagged by the AI check: 36 of the 112 R07 records were marked "likely not road damage". On review, 22 of them were indeed not damage, but 14 w … equally often (58% and 61%), so the AI check is only a hint.” |
| R22 | 5.3 Table 5.3.1 | 5 × 4 (Damage type: not reviewed; Duplicate: 10 candidates in 5 pairs) → 7 × 4 with the scored rates |
| R23 | 5.1.8 Limitations | Added "Damage log review. Nineteen records appeared in both review batches; the reviewer’s first two judgments disagreed on 3 of them (16 of 19 consistent), which were re-examined and settled before scoring. …" and "AI check. … 57.9% of the flagged and 61.3% of the unflagged records showed real damage. It should be treated as advisory only." |


---

## Chapter V restructure (2026-11-15, at the user's request)

| # | Place | Change |
|---|---|---|
| S1 | 5.1.4, Figure 5.1.2 | `[FILL: insert runs/eval/final_…/confusion_matrix_normalized.png …]` → three empty centred image lines with labels "(a) v2b (YOLOv8s)", "(b) v3 (YOLOv8m)", "(c) S5_v8m_1920 (YOLOv8m)". The images (title and white margins cropped, values unchanged) were uploaded to the user's Drive. They could not be inserted through the API, because Docs fetches only public images; the user places them by hand. |
| S2 | 5.1.5 Training Behavior | Section deleted (heading, Figure 5.1.3 caption, `[FILL]`, paragraph). |
| S3 | 5.1.6 Effect of the Detection Pipeline | Section deleted (heading, intro, Table 5.1.6, paragraph). Its result paragraph moved to the end of 5.3 ("Over the whole recording, R07 produced 112 damage records … advisory only …"), without the sentence on unrecorded stage counts. |
| S4 | 5.1.7 → 5.1.5 | Heading renumbered; Table 5.1.7 → 5.1.6, Table 5.1.8 → 5.1.7; "Section 5.1.7" → "Section 5.1.5" in 1.2, 1.7, 3.3.1, 3.7 (team paragraph, number only), 4.1.6, the 5.1 intro and 5.1.1; "(Section 5.1.6)" → "(Section 5.3)" in 1.7. |
| S5 | 5.1.8 → 5.7 | "5.1.8 Limitations of the Detection Results" deleted; new "5.7 LIMITATIONS OF THE STUDY" (Heading 2, ordered list) before the summary. It holds the 8 earlier items (the review item now adds "and only on recording R07, a validation route") plus four new ones: positional error not measured; recording conditions; perceived efficiency; prototype deployment. |
| S6 | 5.7 → 5.8 | "5.7 SUMMARY OF FINDINGS" → "5.8 SUMMARY OF FINDINGS". |
