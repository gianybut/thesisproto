# Manuscript TODO

What the Google Doc **"OCULUBAK_Manuscript"** still lacks, as of 2026-11-15, after the Part B revision
(acceptance level removed, Chapters I–III in past tense, 5.7 / 6.1 / 6.2 condensed):
https://docs.google.com/document/d/1nn5vxNuuDDfNycLGlEwNVaJkqvsrUo4MOAzarpffXuw/edit

- Every change is logged in [manuscript_change_log.md](manuscript_change_log.md).
- Number sources: [results/system_level_evaluation.md](../results/system_level_evaluation.md) (SL) and
  [results/test_evaluation.md](../results/test_evaluation.md).
- This file replaces the 2026-11-12 TODO. That file described an older draft and is now obsolete:
  - the validator has signed;
  - the UAT is done;
  - the old `[FILL]` and `[PENDING]` tokens are gone.

## Before and after this revision

| Check | Before (start of 15 Nov session) | After |
|---|---|---|
| Acceptance level (0.80 as a pass mark, "acceptance criterion/level", "meets … 0.80") | 10 places: 3.8.1, NFR1, 4.4.4, 5.1.1 ×4, 5.1.7, 5.7, 6.1 ×2 (6.1 also said "the level set for the system"), and the plain-language sub-tab ("Did the system reach the 0.80 goal?") | 0 |
| "0.80" anywhere | 12 lines | 2, both the **high-confidence operating point**: 3.8.1 and 5.1.1. This is a precision target fixed in advance, not an acceptance level (see Consistency risks, item 1). |
| "will" in Chapters I–III | 85 sentences | 1, kept on purpose (3.7: "Upon completion of the study, all remaining footage … will be deleted", which is still in the future) |
| mAP / AP@50 | 12 lines, all in Chapter II (literature) | 12, unchanged; awaiting your decision |
| Bracket placeholders (excluding reference-type brackets) | 6: two `[FILL]` and four `[PENDING]` | 2: the two `[FILL]` (all `[PENDING]` filled on 15 Nov after the R07 review) |
| 5.7 / 6.1 / 6.2 | 5.7: an intro plus a 5-item numbered list. 6.1: 6 paragraphs. 6.2: an intro plus 6 run-in paragraphs | 5.7: 1 paragraph. 6.1: 3 paragraphs (your team's text). 6.2: **3 paragraphs** (your team's text; see Consistency risks, item 2) |

## Your edits that I did not touch

The current Google Doc was compared with my last saved version of the main tab (end of Stage 2).
These paragraphs differed, so they are your team's and final. Part B did not change them:

- Title page: "May 2026" → "November 2026".
- **2.2** "The researchers searched four public repositories…" (date removed).
- **2.3** "The literature also showed web-based platforms…" (date removed).
- **3.3.1** "Second-stage classifier…" (dates removed).
- **3.7** "Responsible Use of AI" paragraph.
- **3.8.1** "Model selection and the test…" and "Second-stage classifier…" (dates removed).
- **4.2.4** "Five changes were made…".
- **4.2.5** "Model testing…".
- Hardware: "iPhone 14 Pro Max", and "476 GB system drive, about 96 GB free".
- **5.1.7** "The classifier was trained after the single box-level test run…".
- **5.1.8** five limitation items deleted.
- **Four "[image]" items in 4.1.8** removed.
- **During this session**, while I was editing, your team rewrote three more places:
  - the Chapter VI intro;
  - **6.1** ("The study achieved its general objective…", 3 paragraphs);
  - **6.2** ("To improve detection…", 3 paragraphs).
  
  Your team also added the **Appendices A–G** list. Your 6.1 and 6.2 replaced the versions I had written a few minutes earlier, and I left them as they are.

Sentences in these team-edited paragraphs that Part B would otherwise have changed (your decision):

| Section | Sentence | Why it would have changed |
|---|---|---|
| 2.3 | "Therefore, the present study aims to address this research gap by developing a web-based road damage detection and mapping system…" | Present tense ("aims") for the study's purpose |
| 3.8.1 | "Second-stage classifier. The classifier described in Section 3.3.1 is also scored alone by its top-1 accuracy, …" | Present tense for an evaluation procedure ("is also scored") |
| 3.8.1 | "Model selection and the test. … the threshold is the value from 0.01 to 0.50 that gives the highest overall F1-score there." | Present tense for a procedure (could stay as a definition) |
| 6.2 | The whole section: it has **three** paragraphs ("To improve detection…", "To improve positioning and the system…", "Future studies may explore…") | Part B asked for exactly two |
| 6.2 | "The mobile application should be built for Android, …" | Part B asked to keep "Android validation". The text now says "built for", not "validated on". |
| 6.2 | (missing) | Part B asked to keep "handling shadows, glare and wet roads". It is not in your 6.2, but it is in 5.6.8. |
| 6.2 | "…and larger test sets labeled by more than one reviewer, together with repeated training runs…" | Part B asked for "larger val/test sets". Only test sets are named. |

---

## 1. Bracket placeholders

| Section | Full sentence | What is needed |
|---|---|---|
| 5.1.4 Confusion Matrices | `[FILL: insert runs/eval/final_v2b_foreign_test_all_six_countries/confusion_matrix_normalized.png, the same file of final_v3_foreign_test_all_six_countries, and of final_S5_v8m_1920_foreign_test_all_six_countries]` (under the Figure 5.1.2 caption) | **A file to insert**: the three normalized confusion matrices (they are in `runs/eval/…`, which is gitignored). |
| 5.1.5 Training Behavior | `[FILL: insert runs/local/v2b/results.png, runs/local/v3/results.png, and runs/v3/S5_v8m_1920/results.png]` (under the Figure 5.1.3 caption) | **A file to insert.** These Ultralytics plots contain **mAP50 and mAP50-95 panels**. To keep mAP out of the manuscript, crop those panels or re-plot only the losses. |
| ~~5.1.6, 5.3, 5.7, 6.1 and the sub-tab `[PENDING]`~~ | Filled on 15 Nov from the scored R07 review (change log, "Record-level fills"). The yellow is removed. | Done. |
| References | "[Model weights, AGPL-3.0]", "[Computer software]", "[Model weights, CC BY 4.0]" | Nothing to fill. These are APA source-type labels, not placeholders. |


## 2. Highlights

I cannot read highlight colours through the API. This list comes from what I applied, and what you have since removed may differ.

- **Yellow:** none left from me; every `[PENDING]` was filled on 15 Nov. 6.1 held your own marker; check that no yellow remains there.
- **Green, this revision:**
  - Chapter I: 1.1, 1.2, 1.3, 1.4, 1.6, 1.7.
  - 2.1: "worked".
  - Chapter III: intro, 3.1–3.1.5, 3.2.1, 3.3.1, 3.3.2, 3.3.3, 3.4, 3.4.2, 3.4.3, 3.5, 3.6, 3.7, 3.8, 3.8.1–3.8.7.
  - 5.1.1 (four places), 5.1.7, and all of 5.7.
  - Not highlighted, because they are table cells (the API gives no cell positions): **NFR1** in Table 4.2.2.1, and the detection row of the **4.4.4** table.
- **Green, earlier passes (Stage 2, 15 Nov), probably still present:**
  - 1.2, 1.3 RQ1, 1.5.2 SO1;
  - 3.3.1, 3.3.3, 3.8.1;
  - Tables 3.8.7, 4.1.1, 4.3.1.1 and the 4.4.4 table;
  - 4.1.5, 4.4.5;
  - Chapter V captions and text.
  
  The green in 6.1 and 6.2 went with your rewrite.
- Remove the highlights before submission (Format › Text › Highlight colour › None).

## 3. Figures and images

| Figure | Status |
|---|---|
| 5.1.2 Normalized Confusion Matrices (5.1.4) | **No image**: a `[FILL]` note sits under the caption |
| 5.1.3 Training Curves (5.1.5) | **No image**: `[FILL]` note. Mind the mAP panels (section 1). |
| 3.5.1 Use Case Diagram | The paragraph under the caption holds two tab characters and possibly an image. Check visually that the diagram is there. |
| 4.1.8.8–4.1.8.11 (records, repair stage, administrator, mobile recording screens) | The "[image]" lines above these captions disappeared during your edits today. Check that the screenshots are still in place. |
| 3.1, 3.2.1, 3.3.1, 3.4, 3.4.1, 4.1.8.1–4.1.8.7, 4.1.8.12, 5.1.1 | An image paragraph follows or precedes the caption. The 15 Nov list of corrections for the Chapter III diagrams (old TODO, section 4) still applies if those images were not replaced. |

## 4. Manual steps in Google Docs (the API cannot do these)

1. **Table of contents:** click it, then **Update table of contents**. Do this last, after the images. Heading 5.1.3 was renamed on 15 Nov, and Appendices A–G are new.
2. **Table 2.3.1:**
   - The row **Sarmiento & Reyes (2022)** is still in the table, although its paragraph and reference were removed. Delete the row.
   - Optionally add rows for **Radford et al. (2021)** and **Arya et al. (2020)** (wording in the 12 Nov TODO, git history).
3. **Equation (20)** (accuracy, typed in Cambria Math) and the typed equations (12), (21), (22), (26): for the same look as the others, retype them with Insert › Equation. Set a centre tab at 3 in and a right tab at 6 in so the numbers align.
4. **5.7:** the numbered list was removed, but check that no list indent remains on the single paragraph (Format › Bullets & numbering › none).
5. **Highlights:** remove them all before submission (section 2).

## 5. Consistency risks

1. **"0.80" in the high-confidence operating point** (3.8.1, "High-confidence operating point…"; 5.1.1, "A high-confidence operating point was also fixed in advance: … reaches 0.80"). It is a precision target fixed in advance, not an acceptance level. Removing it would change a pre-registered measure, so I left it. **Your decision.**
2. **6.2 has three paragraphs, not two** (your text; section "Your edits").
3. **mAP in Chapter II** (literature, 12 lines). Your decision is still open (L1–L13 in the change log):
   - 2.1: Khare et al., Zeng & Zhong, Zhang et al., RDD2022 model cards;
   - 2.2: Sarmiento, Manalo et al. ("average precision 95.43%"), Fortin et al.;
   - Table 2.3.1: six cells.
   
   The model-card paragraph (2.1) is no longer referred to by Chapter V.
4. **Record-level method text: updated on 15 Nov.** Updated: 3.8.3, 4.1.1, 4.1.4, 4.1.5, 4.2.5, 4.4.2, 4.4.4, the Chapter V intro, 1.7, 5.3, and Table 5.3.1 (rebuilt). What was outdated, kept for reference:
   - **3.8.3** says duplicate candidates are "records of the same class … within 15 meters and a few seconds". The review page lists records of **any** class within 15 m and **5 s** of all 112 records, and adds a "real damage" question.
   - **4.4.2** "Damage log checklist" and **4.4.4** ("the correctness of the damage type [was] not [measured]") also need updating.
   - **5.3 / Table 5.3.1** still say "10 candidates in 5 pairs". That count compared same-class records inside the sample only. The new automatic check suggests that 22 of the 50 records have an earlier record of the survey within 15 m and 5 s. Your answers decide the final rate.
   - **1.7** says the AI check's "accuracy is not part of the evaluation of this study". Once the flagged records are scored, 5.1.6 reports it, so this sentence needs one line.
5. **Survey 3 was analysed again on 12 Nov (fusion + classifier) after the checklist was drawn on 11 Nov.**
   - The 50 sampled detections are the same: same snapshots, boxes and confidences.
   - They now have new record ids, and 3 of them have the classifier's type:
     - item 13: D40 → D10;
     - item 31: D10 → D40;
     - item 32: D20 → D00.
   - The review judges the current, deployed records. The old ids and types are kept in the CSV.
   - 5.3 should say this in one sentence when it is filled.
6. **Stored times are 1/30 s late.** `frame_number` counts from 1 (`backend/services/video_processor.py:526-535`), so a record's time is 0.033 s after its frame. 3.8.3's "within 0.05 seconds" still holds. Not changed in the code.
7. **Past-tense statements that assert facts I could not check** (they were plans before). Please confirm:
   - **3.7:** "the default administrator password was replaced before the system was used with respondents".
   - **3.7:** "Raw uploaded videos are deleted from the server 30 days after upload". This conflicts with **NFR (4.2.2)**: "…by a task that will be scheduled on the server". `backend/purge_uploads.py` runs only by hand (dry-run unless `--apply`).
   - **3.7:** "Recordings kept on the researchers' phones were deleted once their upload had been confirmed".
   - **3.5:** "all of whom used the system under the Road Maintenance Personnel role during the evaluation". 4.4.2 says the respondents tested the deployed online copy with sample files; check the role they signed in with.
   - **3.6:** "All personnel … who met the inclusion criteria were invited to participate".
   - **3.1.5:** I added "that could be completed within the study period" and "planned activities". Its list still names field validation and a comparison of inspection time, which were not done.
8. **"will" in Chapter IV** (outside the Part B scope, now out of step with Chapter III):
   - NFR on raw-video deletion;
   - 4.2.5 "will be used to list fixes";
   - 4.4.2 field validation form ("the researcher will record");
   - 4.4.3 data gathering steps (4 sentences, although the UAT is done);
   - 4.4.5 "will be computed with Equation 25".
9. **Numbers.** Every three-decimal value in 5.1 matches SL or `test_evaluation.md`, after rounding.
   - **`results/uat_tables.md` does not exist** in the repository, so the UAT figures could not be checked against a file:
     - 4.62, SD 0.22, t(51) = 39.83;
     - section means 4.50, 4.71, 4.63, 4.60, 4.64;
     - n = 52.
   - Add the UAT output file if you have one.
10. **1.6 Significance:** "…detection and classification results reported separately for foreign and local test subsets…". SO1 no longer requires the foreign subset. The sentence is still true, but optional.
11. **Abstract:** the document still has none.
12. **Table 5.3.1 was rebuilt** (7 rows; the API cannot add rows), so its borders and widths are Google Docs defaults: match them to the other tables by hand. The Table 5.1.6 cell "22 of 36 (61.1%)", the two 4.4.4 table cells and the 5.1.8 additions are not all highlighted (cells have no positions in the API).
13. **AI-check figure.** Your instruction quoted "63% vs 61% real". After the three records were settled (809 is flagged and in the sample), it is **57.9% (11 of 19) vs 61.3% (19 of 31)**; the manuscript uses these.

---

## Update 2026-11-15 (evening): Chapter V restructured, Figure 5.1.2 slots

- **Removed at your request:** 5.1.5 Training Behavior (Figure 5.1.3 and its `[FILL]`) and 5.1.6 Effect of the Detection
  Pipeline (Table 5.1.6, mostly "Not measured"). The one real result of 5.1.6 (R07's 112 records by class and the review of
  the 36 flagged records) moved to **5.3** as its last paragraph.
- **Renumbered:**
  - 5.1.7 Second-Stage Classifier → **5.1.5**;
  - Tables 5.1.7 / 5.1.8 → **5.1.6 / 5.1.7**;
  - every "Section 5.1.7" → "Section 5.1.5" (including your 3.7 Responsible Use paragraph: a number change only);
  - 1.7's "(Section 5.1.6)" → "(Section 5.3)".
- **5.1.8 Limitations of the Detection Results** → new **5.7 LIMITATIONS OF THE STUDY** (Heading 2, numbered list, before the
  summary, which is now **5.8 SUMMARY OF FINDINGS**). It keeps the 8 earlier items and adds study-wide ones: positional error not
  measured, recording conditions, perceived (not measured) efficiency, prototype deployment.
- **Figure 5.1.2 (still to do by hand, 1 minute):** the `[FILL]` note is replaced by three empty lines, each followed by a label
  "(a) v2b (YOLOv8s)", "(b) v3 (YOLOv8m)" and "(c) S5_v8m_1920 (YOLOv8m)". The cropped images are in your Google Drive (My Drive):
  - `OcuLubak_Fig5.1.2a_v2b_confusion_matrix_normalized.png`;
  - `OcuLubak_Fig5.1.2b_v3_confusion_matrix_normalized.png`;
  - `OcuLubak_Fig5.1.2c_S5_v8m_1920_confusion_matrix_normalized.png`.
  
  To place them: click each empty line above a label, then Insert › Image › Drive, and set a width of about 5.5 in.
  The API could not insert them: Google Docs only fetches images that are publicly shared, and making them public was not permitted.
- **Table of contents:** refresh it. The headings changed: 5.1.5, 5.1.6, 5.1.7 and 5.1.8 are gone or renamed, and 5.7 and 5.8 are new.
- **Bracket placeholders left: none.**
