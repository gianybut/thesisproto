# Manuscript TODO

What is still open in the Google Doc **"OCULUBAK Manuscript — revision draft"**
(https://docs.google.com/document/d/1SaaJn2eGL9cCUOT7B0pXqCJUZk2z4U2iLjvXZUgn6S0/edit).

- The original document ("OCULUBAK CHAPTER 1-6") was not edited.
- Every open item below is highlighted in yellow in the draft.
- The record of what changed and why is in [manuscript_change_log.md](manuscript_change_log.md).
- The only source for numbers is [results/FINAL_METRICS_FOR_PAPER.md](../results/FINAL_METRICS_FOR_PAPER.md).

---

## 1. Fill-ins (team decisions or facts the repository does not hold)

Each fill-in appears in the sections listed. Once decided, replace every copy with the same wording, then remove the highlight.

| Placeholder | Sections | What is needed |
|---|---|---|
| `[FILL: the three researchers / the three researchers and N volunteer annotators]` | 1.7, 3.4.3, 3.7, 4.1.3 | Who labelled the 6,399 frames on the annotation website. In 3.7 the same choice also says who the frames were shared with. |
| `[FILL: dimensions of the evaluation questionnaire]` | 3.6, 3.8.5, 4.1.3, 4.4.2 | The UAT instrument. Choose either the six dimensions (usability, perceived detection accuracy, interface design, inspection efficiency, decision-making support, overall usefulness) or the existing Google Form's dimensions. |
| `[FILL: confirm the instrument — …]` | 4.4.4 | The same decision. Keep or replace the six-item list below it. |
| `[FILL: align Sections 5.6.2 to 5.6.6 and Tables 5.6.3 to 5.6.8 …]` | 5.6 | The same decision. The 5.6 headings and tables still follow the old ISO/IEC 25010 characteristics. Retitle them, and re-group their items, to match the chosen instrument. |
| `[FILL: exact name of the DPWH Batangas office]` | 3.6, 4.1.2, 4.1.4, 4.4.1 (text and Table 4.4.1.1 header), 5.6.1 | The office's official name. |
| `[FILL: Yes, recording ___ was uploaded from the phone app … / No: … upload script …]` | 4.2.5 | Whether any recording was sent end to end from the mobile app. Keep one option. The R07 test used `tools/upload_recording.py`. |
| `[FILL: hosting service or server]`, `[FILL: address]` | 4.2.6 | Where the online copy for the remote evaluation will run, and its HTTPS address. |
| `[FILL: ASUS ROG Strix G17 — keep only if it was used, and for what]` | Table 4.3.2.1 | Keep the laptop only if it was used, and say for what. Otherwise delete the clause. |
| `[FILL: iOS version]` | Table 4.3.2.1 | The iOS version of each phone (two iPhone 13 Pro Max, one iPhone 16). |
| `[FILL: storage available for uploads, processed videos, and snapshots]` | Table 4.3.2.1 | Free disk space on the processing PC. |
| `[FILL: weeks]` ×5 | Table 4.3.4.1 | The duration of each sprint. |
| `[CITATION NEEDED: volume]` | References (Solovyev et al., 2021) | The volume of *Image and Vision Computing* for article 104117. The publisher page did not load; the DOI is 10.1016/j.imavis.2021.104117. |
| `[CITATION NEEDED: full author list …]` | References: Busireddy (2026), Dabous (2025), Fortin (2024), Irsal (2025), Yin (2024), Zhang (2025) | APA 7 lists every author (up to 20), never "et al.". See the notes below. |

Reference notes:
- **Fortin (2024):** the entry's title and journal differ from the ResearchGate record it links to.
- **Irsal (2025):** "IEEE Xplore" is not a venue; give the conference or journal.
- **Yin (2024):** the entry names a journal but links an arXiv record.
- **Not checked in this pass:** Roy & Bhaduri (2023), Alwahhab et al. (2025), Busireddy et al. (2026), Bustria et al. (2025) and iWatchRoad Project (2026). They resolve to links but were not verified against the publisher. Verify them before submission.

---

## 2. Pending evaluations (results to measure, then write into the draft)

Nothing here may be estimated. Each `[PENDING]` stays until a result file exists.

| Placeholder | Sections | How to get it |
|---|---|---|
| `[PENDING: damage log correctness]` | 4.1.4, 4.1.5, 4.4.2, 5.3 (Table 5.3.1), 5.7, 6.1 | 1. Fill in `results/damage_log_check/survey3_checklist.csv` (50 records of survey 3, seed 42; the columns are explained in `tools/damage_log_check.py`). 2. Run `python tools/damage_log_check.py score results/damage_log_check/survey3_checklist.csv`. |
| `[PENDING: localization accuracy]` (and `…, Section 5.4`) | 1.6, 3.8.4, 4.1.3, 4.1.5, 4.2.5, 5.4 (Tables 5.4.1-5.4.2), 5.7, 6.1 | Field validation of 20-30 damages: stand beside each damage and average one minute of phone fixes. Compute the Haversine error (Equation 27). **No script exists yet**: write one that reads the reference positions, the records and the GPX files, and reports mean, SD and maximum error and the survey conditions. |
| `[PENDING: expert validation]` | 3.4.3, 4.1.3, 4.1.5, 4.1.6, 4.4.2, 5.2 (Table 5.2.1), 6.1 | The DPWH Batangas engineer marks and signs `data/local/validation_sheet/OcuLubak_dataset_validation.docx`: 40 boxes, 10 per class, with a certification letter. `ml/local/annotation_agreement.py` computes percent agreement and kappa, but it reads Google Form responses. Enter the sheet's answers in that CSV format (`--responses`), or adapt the script. |
| `[PENDING: UAT]`, `[PENDING: UAT results]` | 4.1.3, 4.1.5, 4.2.5, 4.4.3, 5.6 (all tables), 5.7, 6.1 | Run the questionnaire with the participating offices, then compute weighted means, SDs and one-tailed t-tests against 3.41, overall and per dimension, with and without the validating engineer. **`tools/uat_analysis.py` does not exist yet**: write it from the Google Forms CSV. |
| `[PENDING: n]` | 4.1.4, 4.4.1 (and Table 4.4.1.1) | The number of respondents, after the UAT. |
| `[PENDING: device tests]` | 4.2.5, 5.5 | The stopwatch start-time gap, full-length sessions in a moving vehicle, and the midday heat test of the mobile app. |
| `[PENDING: deployment]` | 4.2.6 | Set up the online copy for the evaluation (see the fill-ins). |
| `[PENDING: review of flagged records]` | 5.1.6 (text and Table 5.1.6) | Review the 36 R07 records flagged by the AI check, and count how many are truly false. |
| `[PENDING: improvements suggested by the respondents, Section 5.6.8]` | 6.2 | From the UAT comments. |
| `[PENDING]` (bare) | 4.1.1, 4.1.2, 4.2.4, 4.3.4 | These mark sentences that list the evaluations above as still to be done. Remove each one when its evaluation is done. |

Before these are written up, also update the sentences that call these evaluations pending: Chapter V intro, 4.4.4 ("so far only detection performance has been measured"), and 5.7 / 6.1.

---

## 3. Manual edits in Google Docs (the API cannot do these)

1. **Equations.** Replace each highlighted placeholder with Insert › Equation, keeping its number:
   - (12) weighted box fusion, 3.3.3. The old de-duplication equation object was deleted.
   - (22) classification accuracy, 3.8.1.
   - (23) Wilson interval, 3.8.1.
   - (27) Haversine, 3.8.4.

   The placeholder lines are centred body text. Give the new lines the same layout as the other equation lines: centre tab 4320, right tab 8640.
2. **Table 2.3.1 (synthesis table).**
   - Delete the **Sarmiento & Reyes (2022)** row. Its paragraph and reference are already removed.
   - Insert a row below **Asian Development Bank (2026)** for **Radford et al. (2021)**:
     - Focus: "Learning visual models from natural language supervision (CLIP)"
     - Method: "Trained an image encoder and a text encoder to match images with their captions on a large collection of image–text pairs"
     - Findings: "The model classifies images into categories described in text without task-specific training (zero-shot classification)"
     - Implication: "Supports the use of CLIP as an advisory check that flags detections that are likely not road damage"
3. **Table of contents.** Click the TOC, then **Update table of contents**. It is a TOC element, so the API cannot refresh it. It still lists old headings, for example "3.3.1 YOLOv8m …" and "3.8.2 User Acceptance Testing", and no 5.x entries.
4. **Figure images**, replacing the highlighted `[FILL: insert …]` notes:
   - **Figure 5.1.1** (5.1.4): a 4 × 4 chart or table of matched test pairs, reviewed by detected class: D00 17/0/0/0; D10 0/3/0/1; D20 0/0/3/0; D40 0/0/0/1 (`results/test_evaluation.md`, lines 44-51). This is the deployed fusion on the local test subset at 0.25.
   - **Figure 5.1.2** (5.1.4): `runs/eval/final_v2b_foreign_test_all_six_countries/confusion_matrix_normalized.png` and the same file for `final_v3_…` and `final_S5_v8m_1920_…`. Each model alone, on the foreign test subset.
   - **Figure 5.1.3** (5.1.5): `runs/local/v2b/results.png`, `runs/local/v3/results.png`, `runs/v3/S5_v8m_1920/results.png`. Training curves of each model on its own validation list during training, not the test set.

---

## 4. Figures to redraw (images in Chapter 3; the repository `figures/` folder does not hold them)

| Figure | What it must show now |
|---|---|
| **3.1** Agile phases | Phase 2: a starting model trained on six RDD2022 countries; the local dataset; fine-tuned YOLOv8 models and their weighted box fusion; threshold calibrated on the reviewed validation frames; cross-frame tracking and the fixed-spot filter. Remove "India subset", "YOLOv8m", "de-duplication" and "hyperparameter adjustment". |
| **3.2.1** Conceptual framework (IPO) | Process: frames sampled at about 5 per second → near-zone crop of the road band → three YOLOv8 models + weighted box fusion (fused score ≥ 0.25) → cross-frame tracking and fixed-spot filter → advisory CLIP AI check → GPS synchronization, or control points → storage and annotated video. Output record includes the AI check score. |
| **3.3.1** YOLOv8 architecture | Titled "YOLOv8" (the s and m sizes share it), not "YOLOv8m". Input: the 1920 × 432 near-zone crop plus 24 px of grey above and below, scaled to 1,024 or 1,280 px, not 640 × 640. Head with four classes (D00, D10, D20, D40). Optionally a side panel: three models → weighted box fusion → 0.25. |
| **3.4** End-to-end pipeline | Upper lane: RDD2022 (six countries) teacher; 18 recordings → 9,590 frames → near zone; labelling (review tool, 1,066 frames; annotation website, 6,399); split by route group with the 50 m rule; v2b, v3, S5_v8m_1920; selection on the 270 reviewed validation frames; fusion + threshold 0.25 → deploy; one local test; members alone on the foreign test. Lower lane: phone records 590-s parts, server limit ten minutes (no "500 MB") → background thread → near zone → three models + fusion → tracking → fixed-spot filter → AI check → GPS or control points → ffmpeg → map, records, export. |
| **3.4.1** Three-tier architecture | Application tier worker: frame sampler → near-zone crop → three YOLOv8 models + weighted box fusion → threshold, tracking, fixed-spot filter → CLIP AI check → positioning and annotation → ffmpeg. Data tier: SQLite, file storage, the three model weights with their settings file, and the CLIP model. No "YOLOv8m inference engine" or "de-duplication". |
| **3.5.1** Use case diagram | The System Administrator connects to three use cases: managing user accounts, viewing the activity log, and correcting or deleting detection records. The administrator still inherits every Road Maintenance Personnel use case. |

---

## 5. Adviser items

1. **Approved wording changed** (highlighted in the draft, for the adviser's approval):
   - **RQ1** (1.3): adds "and the classification accuracy of detected damage" to the measures.
   - **Specific Objective 1** (1.5.2): "YOLOv8 object detection models", plus the same added measure.
   - **Hypothesis** (1.4): "a fine-tuned YOLOv8m detection model" → "fine-tuned YOLOv8 detection models". Nothing else changed.
   - **General Objective** (1.5.1): three YOLOv8 models fine-tuned on local imagery from RDD2022 starting weights, combined by weighted box fusion.
2. **The acceptance criterion was not met.** The panel's requirement was mAP@50 ≥ 0.80 overall and per class on the local test subset (3.8.1, NFR1). The deployed fusion reached 0.173 on its single test run, with per-class AP@50 from 0.035 to 0.381. Chapter V and 6.1 state this plainly.
3. **The hypothesis is undecided** until the UAT is done (5.6.7, 5.7, 6.1 are `[PENDING: UAT]`).
4. **Disclosure of AI assistance.** Check the school's policy on disclosing AI-tool use in the manuscript, for example the use of an AI assistant to revise text and check consistency. If disclosure is required, add the required statement in the required place.
5. **Partner office.** The draft now names the DPWH Cavite 2nd District Engineering Office as the partner office, replacing the Mendez-Nuñez Municipal Engineering Office. It also says the DPWH Batangas engineer who validates the labels may also be a respondent, with results reported with and without that engineer. Check that this matches the signed ethics and request letters.
