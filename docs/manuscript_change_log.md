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
