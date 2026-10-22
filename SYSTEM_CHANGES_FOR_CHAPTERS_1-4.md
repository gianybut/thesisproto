# OCULUBAK: what changed in the system, and what Chapters 1–4 must revise

Prepared on 21 October 2026 from the system's source code. It compares the system as it now
runs with the thesis drafts *THESIS CHAPTERS 1-3* (May 2026) and *CHAPTER 4* (draft). It also
records the change of partner office that the adviser approved.

## How to use this document (read first)

This file is input for revising Chapters 1–4. It describes what the software actually does. It
does not contain thesis prose.

Rules for anyone, person or AI, revising the chapters with it:

1. **Never invent a number.** Where a value has not been measured, keep a bracketed placeholder
   such as `[n]` or `[measured value]`. Section 9 lists what is still unmeasured.
2. **The model now running is a placeholder.** The server currently loads an external,
   MIT-licensed YOLOv8n model trained on seven RDD2022-style classes. It is not the team's
   model. None of its numbers may appear as results in Chapter 4 or 5. Every reported metric
   must come from the team's own fine-tuned four-class YOLOv8m model, which has not been
   trained yet (Section 9).
3. **Numbers in this file are development observations**, not evaluation results. They show why a
   design was chosen. Where one is quoted, it says which model and data produced it.
4. Chapters 1–3 are written as a proposal ("will"). Chapter 4 is written in the past tense
   ("was"). Keep each chapter's tense. Describe features in Chapter 4 only if they exist in the
   system, and do not report results that have not been measured.
5. Section references below use the numbering printed in the drafts (for example "Ch3 §3.4.2,
   p. 49"). Page numbers are the footer page numbers of the PDF.

---

## 1. Scope change: the partner office

**What happened.** The team visited the LGU of Mendez-Nuñez. The LGU does not handle road
damage. Roads in Mendez-Nuñez are handled by the **DPWH Cavite 2nd District Engineering Office
(DEO)**. The team proposed, and the adviser approved:

- **New partner:** DPWH Cavite 2nd District Engineering Office.
- **Also partnered:** DPWH Batangas, the office of the engineer the team interviewed during the
  proposal.
- **Evaluation is remote:** the team sends each office a demo video and a link to a deployed
  (internet-reachable) website that already holds processed surveys. The partners see the web
  app and the mobile app working without an in-person session.

**What does not change.** The study area stays Mendez-Nuñez, Cavite: survey footage and the local
dataset are still recorded on its roads. The system's two roles (road maintenance personnel,
system administrator) stay the same.

**Where the drafts must change because of this**

| Where | Current text (summary) | Revise to reflect |
|---|---|---|
| Ch1 §1.3 RQ4, p. 7 | "…decision-making for local government units…" | The partner is now a DPWH district office. Decide whether RQ4 names "DPWH district engineering offices" or "road agencies such as DPWH district offices and LGUs" (Decision D1). |
| Ch1 §1.6 Significance, p. 9 | Lists "Local Government Units (LGUs)" as a beneficiary | Add, or put first, DPWH district engineering offices, which maintain national roads. LGUs can stay as secondary beneficiaries. |
| Ch1 §1.1, p. 3 | Data from "national, city, and barangay roads in Mendez-Nunez" | Mendez-Nuñez is a municipality, so "city" should be "municipal". DPWH maintains national roads; municipal and barangay roads belong to the LGU and barangays. Decide which road classes the surveys cover now that the partner is DPWH (D2). |
| Ch3 §3.6 Respondents, p. 54 | Respondents are personnel of the "Municipal Engineering Office of Mendez-Nuñez"; DPWH Cavite 2nd DEO is only a fallback | Swap: DPWH Cavite 2nd DEO is the primary respondent office, and DPWH Batangas is the second. Inclusion criteria become "currently employed by DPWH Cavite 2nd DEO or DPWH Batangas…". Drop or rewrite the fallback paragraph. |
| Ch3 §3.6, p. 55 | "The DPWH engineer from Batangas who validates the annotations … is not a respondent" | Now that DPWH Batangas is also a partner, state clearly whether that engineer is excluded from the respondents (recommended, because they validate the labels) and that other Batangas personnel may respond (D3). The cross-reference "Section 3.4.4" should be "Section 3.4.3". |
| Ch3 §3.7, ethics | Access limited to the research team and the partner office; systems are password-protected | The website is now reachable over the internet for the remote demo. Add how access is controlled: accounts for evaluators only, the default admin password changed, HTTPS. Say what the online copy contains, for example only the team's own demo surveys. See Section 7. |
| Ch4 §4.1.2, p. 2 | "Primary data were gathered by the researchers in Mendez-Nuñez" | Still true for footage. Add that the evaluation was done with DPWH Cavite 2nd DEO and DPWH Batangas. |
| Ch4 §4.1.3 item 4, p. 3 | "After using OCULUBAK, each respondent answered…" | Describe the remote format: demo video, deployed website, accounts given by the administrator (D4). |
| Ch4 §4.1.4 Sampling, p. 3 | "personnel of the Municipal Engineering Office of Mendez-Nuñez… If the partner LGU could not provide enough respondents, … DPWH Cavite 2nd DEO…" | Primary: DPWH Cavite 2nd DEO. Second: DPWH Batangas. Remove the LGU fallback, or turn it around. |
| Ch4 §4.1.7, p. 5 | "authorized accounts of the partner LGU" | "authorized accounts of the partner offices (DPWH Cavite 2nd DEO, DPWH Batangas)". |
| Ch4 §4.2.6 Deployment, p. 12 | "[deployment machine or server]", "[address or local network setup]" | Now an internet-hosted deployment for the remote demo. See Section 8 for what the system still needs. |
| Ch4 §4.4.1, pp. 16–17 | Respondents from the Municipal Engineering Office; Table 4.4.1.1 Office column | DPWH Cavite 2nd DEO and DPWH Batangas. The three groups map onto DEO sections (for example Planning and Design, Maintenance, Construction). Fill the Office column with the two offices. |
| Ch4 §4.4.3 Procedure, p. 17 | Steps 1–6 assume an in-person session: the respondent uploads a survey and watches it process | Remote steps: briefing and consent (online form or scanned), demo video, sign-in to the deployed site, guided tasks on surveys already processed there, questionnaire, debrief. Decide whether respondents upload a survey themselves (D4). |
| Ch4 §4.4.2 Instruments, p. 17 | Questionnaire "[printed / Google Forms]" | Remote evaluation points to Google Forms. Add the demo video and the deployed site as instruments or materials. |

**Note on the software.** The system does not show the partner office's name anywhere in its
interface. The only place the old partner appears is the default administrator account created
on first start, whose organisation field reads "Local Government Unit of Mendez-Nuñez". That is
internal. It should be changed to the DPWH office before the remote demo (Section 10).

---

## 2. Summary of system changes since the drafts

Ordered by how much they affect the chapters.

| # | Change | Chapters affected |
|---|---|---|
| C1 | **Cross-frame de-duplication rewritten as damage tracking.** The 100-pixel-grid-cell + 2-second-window key in Algorithm 3.1, Equation 12 and Rule 4 is gone. Sightings are now joined into tracks, and one record is stored per track from its best (most confident) sighting. | Ch3 §3.2.1, §3.3.2 (Algorithm 3.1, Rule 4), §3.3.3 Eq. 12, Fig. 3.4; Ch4 FR8, §4.2.4 |
| C2 | **Road band.** The model looks only at the strip of each frame between the horizon and the vehicle's bonnet. The surveyor sets both lines on the phone; each survey stores them. | Ch3 §3.2.1, §3.3.2, §3.4, §3.4.2; Ch4 §4.1.3, §4.1.8.3, FR3/FR7 |
| C3 | **Model input size 1280** instead of 640. | Ch3 §3.3.1, Eq. 2, Eq. 5–7; Ch4 §4.2.4 |
| C4 | **Fixed-spot filter.** Detections that keep coming back at the same spot in the picture (the dashboard reflected in the windshield) are discarded. | Ch3 §3.3.2; Ch4 FR8 |
| C5 | **AI check: a second, advisory model (CLIP).** Each record gets a score saying how much its close-up looks like road damage. Low scores are flagged "Likely not road damage" for the administrator. Nothing is deleted automatically. | Ch1 §1.7 (optional), Ch2 (one new citation), Ch3 §3.2.1, §3.3, §3.4.1, §3.7, §3.8; Ch4 §4.1.8, FRs, §4.2.3, §4.3.1 |
| C6 | **Phone recordings have no time limit.** A recording is saved as parts of 590 seconds each; the next part starts by itself. Each part uploads as its own survey. | Ch1 §1.7; Ch3 §3.4.2; Ch4 §4.1.8.3, FR4, Table 4.3.2.1 |
| C7 | **No 500 MB upload limit.** The ten-minute limit per uploaded video remains. | Ch1 §1.7; Ch3 §3.4; Ch4 §4.1.8.3, FR6 |
| C8 | **Damage close-up preview** on the survey page, the damage map (hover and click) and the damage records page, with a review pane for checking and deleting false detections. | Ch4 §4.1.8.1, FR14 |
| C9 | **"Analyse again"** reruns a failed or finished survey from the files already on the server. A failed survey shows the reason. | Ch1 §1.7; Ch3 §3.4.1; Ch4 §4.1.8.4, FR13 |
| C10 | **Administrator features** go beyond account management: an activity log, correcting a record's damage type, deleting false records, and seeing every survey. | Ch3 §3.5, Fig. 3.5.1; Ch4 §4.1.8.2, FR2 |
| C11 | **Mobile app updates.** Record without signing in, Horizon and Bonnet lines, a tilt-based horizon guess, a landscape layout with controls beside the preview, and a review screen for all parts. | Ch3 §3.4.2; Ch4 §4.1.8.3 |
| C12 | **Rotated phone videos are read upright.** Earlier, a phone video held upside down was analysed upside down. | Ch3 Rule 7 (minor) |

Sections 3–6 give the detail and the exact places to revise.

---

## 3. How a survey is processed now (detection pipeline)

Use this section to rewrite Ch3 §3.2.1 (Process), §3.3.2 (Algorithm 3.1 and its rules), §3.3.3
(equations) and Fig. 3.4, and Ch4 FR7/FR8, §4.2.3 and §4.2.4.

### 3.1 Steps, in order

1. **Read the frame upright.** Phone videos carry a rotation flag; the system applies it, so a
   video recorded with the phone upside down or sideways is analysed the right way up.
2. **Sample.** Every frame is decoded and written to the annotated video, but the model runs
   only on every *n*-th frame, *n* = max(1, ⌊FPS / 5⌋). This is unchanged: five analysed frames
   per second of footage (Eq. 11 is still right).
3. **Crop to the road band.** Only the strip between `road_top` and `road_bottom` is passed to
   the model. Both are fractions of the frame height measured from the top (for example
   0.50 to 0.90). Phone surveys bring their own band (Section 5.2). Surveys uploaded on the web
   have no band, and use the defaults: top 0.50 (the middle of the frame) and bottom 1.00
   (nothing cut off below). The annotated video draws both lines, so viewers can see what was
   analysed.
4. **Detect.** YOLO runs on the band at **input size 1280** (longest side), confidence threshold
   `c_min` and NMS IoU 0.45. Boxes are moved back into full-frame coordinates by adding the
   band's top offset.
5. **Keep damage classes only.** Class names are mapped to D00/D10/D20/D40. Classes that are not
   one of the four (for example a generic "crack" class in the placeholder model) are dropped.
6. **Track across frames** (replaces the grid-cell key; Section 3.3).
7. **Drop fixed spots** after the video ends (Section 3.4).
8. **Store one record per track.** Each record is taken from the track's best sighting: that
   frame's box, class, confidence, timestamp t = frame / FPS, position and snapshot. The
   snapshot is the whole frame with the box drawn on it.
9. **AI check** (Section 3.5): a second model scores the clean frame (before anything is drawn on
   it) and stores `ai_check_score` on the record.
10. **Position.** Unchanged: linear interpolation of the GPS track at t + Δt, clamped at the track
    ends (Eq. 13–15); or control points afterwards, never clamped.
11. **Re-encode** the annotated video to H.264 MP4 (unchanged).

### 3.2 Settings (all in one place in the code, so the thesis and the code cannot drift)

| Setting | Value now | What the drafts say |
|---|---|---|
| Analysed frames per second | 5 | 5 (correct) |
| Confidence threshold `c_min` | 0.15 in the code for now | "calibrated on the validation set" (correct as a plan: set it when the team's model is trained) |
| NMS IoU | 0.45 | 0.45 (correct) |
| Model input size at inference | **1280**, on the road band only | 640 (Ch3 §3.3.1, Eq. 2, Eq. 5) |
| Road band default (web uploads) | top 0.50, bottom 1.00 | not described |
| Track overlap to join | IoU ≥ 0.15 | not described |
| Track closes after | 1.0 s unseen | not described (the old key used a fixed 2-s window) |
| Nested box in one frame | ≥ 50% of its area inside a more confident box = the same damage | not described |
| Fixed spot | ≥ 3 tracks with their best boxes overlapping (IoU ≥ 0.5), at least one of which stood still for ≥ 1 s | not described |
| AI check threshold | score < 0.60 = flagged | not described |

### 3.3 Damage tracking (replaces the de-duplication key)

**Why it changed.** The old key (top-left corner in a 100-pixel grid cell + a fixed 2-second
window) stored the same pothole again and again. A pothole seen from a moving car slides down
the picture and grows as the car approaches. Its box crosses into a new 100-pixel cell on almost
every analysed frame, so each sighting looked new. On a real survey one pothole was stored at
20% confidence far away and again at 50% close up.

**How it works now.** For each analysed frame:

1. **Same damage boxed twice in one frame.** If a box lies at least half inside a more confident
   box, only the more confident one is kept. This happens with a whole patch and part of it, or
   with two classes on one spot.
2. **Match each box to an open track**, each box and track used at most once:
   - first by overlap: IoU with the track's last box ≥ 0.15, highest overlap first;
   - otherwise by expected movement: the box's centre lies in the area the damage can reach
     before the next analysed frame. With *s* = the larger side of the track's last box, that
     area is the last box widened by *s* on each side, raised by *s*/2 and lowered by 3*s*. Road
     damage moves down the picture as the vehicle drives towards it. Damage further up the road
     sits above the box, outside this area, so it is not merged in.
3. **Unmatched boxes** start new tracks.
4. **A track not seen for 1 second** is finished and becomes one record.

The damage class comes from the best sighting, so a pothole called an alligator crack in one
frame is still one record. The record's timestamp, and therefore its GPS position, is the
moment of the best sighting, usually when the damage is closest to the camera.

**What this changes in the drafts.**

- Algorithm 3.1 lines 1, 3, 16–18 (K, w, key k) and Rule 4 must be replaced by the tracking
  steps. Keep Eq. 9 (IoU), which the tracker reuses.
- Eq. 12 (the de-duplication key) is removed. If you want an equation, define the reachable area
  R(b) = [x₁ − s, y₁ − s/2, x₂ + s, y₂ + 3s] with s = max(x₂ − x₁, y₂ − y₁).
- Fig. 3.4 box "Cross-frame de-duplication (100-px grid cell, 2-s window)" becomes "Cross-frame
  tracking (one record per damage, best sighting)".
- Ch3 Rule 4 says the old rule "may produce more than one record" for one damage, to be measured
  in the damage-log check. Keep measuring the duplicate rate (Ch3 §3.8.3). The tracker can still
  split one damage into two records (unseen for more than 1 s, for example behind a passing car)
  or, rarely, merge two damages that sit close together.
- Ch3 §3.3.2 Rule 4 and Ch3 §3.8.3 should refer to the same section number; see Section 11.

### 3.4 Fixed-spot filter (new)

**Why.** Behind a windshield, the dashboard is reflected in the glass. The model reads the
reflection as a pothole, at the same place in the picture whenever the light allows. On the
team's 3.5-minute windshield survey this reached 65% confidence and came back repeatedly over
nearly three minutes (observed with the placeholder model).

**Rule.** After the video, take a spot where at least 3 separate tracks have their best boxes
overlapping (IoU ≥ 0.5). If at least one of those tracks stood still in the picture for 1 second
or longer, every track at that spot is discarded as fixed to the camera. Real damage moves down
the picture while the vehicle drives. A real pothole seen while stopped at a junction stands
still too, but does not come back at the same spot two more times.

### 3.5 AI check (new, advisory)

**Purpose.** The detector is trained only on road damage, so things that look like damage to it
get reported as damage. On the team's survey these included worn lane markings, pedestrian
crossings, car and bus bodies, the vehicle's own bonnet, manhole covers and roadside wall
brackets. The AI check gives each record a second, independent opinion.

**Method.**

- **Model:** CLIP ViT-B/16 (Radford et al., 2021), a general image–text model used zero-shot: it
  needs no training on project data.
- **Crop:** a square around the damage, three times the box's larger side and at least 112
  pixels, cut from the clean frame before any box or label is drawn. CLIP can read text, so a
  drawn "Pothole" label would bias it.
- **Comparison:** the crop is compared with 5 descriptions of road damage (pothole, crack,
  broken surface, alligator cracking, patched pothole) and 11 of the look-alikes found on real
  surveys (lane markings, pedestrian crossing, car, bus, wall, manhole cover, the bonnet,
  smooth asphalt, concrete barrier, tyre, shadow).
- **Score:** the share of CLIP's softmax over all 16 descriptions that falls on the five damage
  descriptions, from 0 to 1. It is stored as `ai_check_score`.
- **Threshold:** a score below 0.60 marks the record "Likely not road damage".

**It only advises.** Nothing is hidden or deleted. The administrator sees the flag in the damage
records list, the review pane, the survey page and the map, and decides whether to delete. Human
validation stays where Chapter 3 puts it.

**Development observation, not a thesis result.** One survey, the placeholder detector, 38
hand-labelled records (15 real damages, 23 false detections; 11 unclear records left out):
- real damage scored above false detections in 94% of pairs (AUC 0.94);
- at 0.60, 14 of 15 real damages passed and 18 of 23 false detections were flagged;
- the larger CLIP model (ViT-L/14) did worse (AUC 0.83), as did tighter crops (AUC 0.84–0.85).

The crop size and threshold were chosen on this same survey, so these figures are optimistic. If
the AI check is reported in the thesis, measure it on a different survey (Section 9).

**Runs offline.** The CLIP model (about 570 MB) is downloaded once by the installer and then works
without internet. Without it, surveys are still analysed and records show "AI check not run".

**Equation, if Chapter 3 wants one.** With image embedding v, the text embeddings t_k of the 16
descriptions (all normalised) and D the set of damage descriptions:
`S = Σ_{k∈D} exp(100·v·t_k) / Σ_k exp(100·v·t_k)`; the record is flagged when S < 0.60.

**Literature.** Ch2 does not cover zero-shot vision–language models. Add Radford et al. (2021),
*Learning transferable visual models from natural language supervision*, ICML. Optionally,
connect it to the false-positive concern in Zeng & Zhong (2024) and the "decision-support"
framing in Ch3 §3.7 "Responsible Use of AI".

### 3.6 Input size 1280 and the road band (C2, C3)

**Why.** At Ultralytics' default input of 640, a 1920-pixel phone frame is shrunk to a third of
its width, and a pothole 20–40 m ahead becomes a few pixels across. On the team's 3.5-minute
windshield survey, the placeholder model returned 13 boxes at 640 and 157 at 1280. Damage
records went from 8 to 62 when the road band was also used. Passing only the road band keeps the
cost at about twice that of 640 (58 s of model time instead of 32 s for that survey on a Mac
CPU), because sky and buildings are never processed. The extra records include both real damage
the 640 run missed and more false detections (vehicles, lane paint). The AI check (Section 3.5)
targets the second group.

**Where this goes in the thesis.** Ch3 §3.3.1 already says: "if validation results indicate that
a change, such as a larger input size for small cracks, improves performance, the change and its
reason will be reported in Chapter IV." Ch4 §4.2.4 has a placeholder for exactly this ("[Add here
any changes made during development, for example a different input size…]"). Report it there,
naming the placeholder model as the source of the observation. Zhang et al. (2025, OBC-YOLOv8),
already in Ch2, supports the point that small, distant potholes are hard to detect.

**Consistency to keep.** The team's model should be trained and evaluated at the input size used
at inference (Decision D5). The drafts plan training at 640. If inference stays at 1280, either
train at 1024–1280 or justify the mismatch. Training images are full frames while inference uses
the road band; because the band keeps the full width, objects appear at about the same scale.

**Equations to update.**

- **Eq. 2:** p is no longer 640 × 640. With the band, the model input is 1280 pixels wide and as
  tall as the band, scaled. Write p as a symbol, or give it for a typical band.
- **Eq. 5–7:** T = 1280. I_w and I_h are the band's width and height. After Eq. 7, add the band
  offset: y_frame = y + y_top, where y_top = road_top × frame height.
- **Rule 7** stays true: coordinates are mapped back to the original frame, now including the
  band offset.

---

## 4. Web application changes

Use this section for Ch4 §4.1.8.1–4.1.8.2, FR1/FR2/FR6/FR13–FR15, and Ch3 §3.4.1 and §3.5.

| Page (draft name) | What the draft says | What the system does now |
|---|---|---|
| **Login** (Ch4 §4.1.8.1; FR1) | Sign in with **email address** and password | Sign in with **username** and password (D6). Token lifetime of twelve hours: correct. No self-registration: correct. |
| **Dashboard** (Ch4 §4.1.8.1; FR14) | Totals plus "how the detections are split across the four damage classes" | Called **Overview** in the app. Four counts: surveys uploaded, surveys being analysed now, damage found, damage with a location. Recent surveys with their status, shortcuts, and a "Connect a phone" panel that shows the server address for the mobile app. **No per-class split** on this page; the per-class counts are on the damage map legend (D7). Personnel see their own surveys in the counts; the administrator sees all. |
| **Upload** (Ch4 §4.1.8.3; FR6) | MP4/MOV/AVI/MKV/WebM, ≤ 10 minutes, **≤ 500 MB** | Formats and 10-minute limit: correct. **No size limit** (removed because iPhone recordings passed 500 MB). The GPS track (GPX/CSV) and time offset stay optional. |
| **Survey list** (Ch4 §4.1.8.4; FR13) | A survey interrupted by a restart "is marked as failed so the user knows to upload it again" | It is still marked failed, with the reason shown. The user can press **Analyse again**, which reruns from the files already on the server, so no re-upload is needed. This works unless the raw video was already deleted by the 30-day retention. Analyse again also works on a finished survey, to test a changed model or setting; it replaces that survey's records after confirmation. The administrator's list shows "By <name>". |
| **Detection viewer** (Ch4 §4.1.8.5; FR14) | Each detection listed "with its snapshot, damage class, confidence value, video timestamp, coordinates, and position source" | Called the **survey page** ("Damage found" tab). The annotated video plays beside a list of damages: video time, class with its code, and confidence. Clicking a damage jumps the video there and shows a **close-up**: the saved frame zoomed to the damage, with a switch to the whole frame, and the AI check verdict. Records the AI check flags are marked in the list. Coordinates and position source are not shown per row; the survey shows its position source (GPS track, placed by hand, or none). A filter by damage class is available. |
| **Georeference** (Ch4 §4.1.8.6) | As described | Correct. It is the second tab of the survey page ("Place on the map"), shown only for surveys without GPS that did not fail. |
| **Damage map** (Ch4 §4.1.8.7) | "Clicking a marker opens the detection's class, confidence, time, and snapshot" | **Hovering** over a marker shows a preview pane with the zoomed close-up. **Clicking** keeps it open until it is closed. The pane shows class, confidence, time in the video, repair stage, road name, coordinates, the AI check, and "Open in the video". Filters: survey, kind of damage, repair stage. One colour per damage class, a route per survey with Start and End markers, and hand-placed points drawn differently. No heatmap and no clustering, so do not cite Albouchi et al. (2025) as if the system had a heatmap. |
| **Database page** (Ch4 §4.1.8.8; FR15) | "filter by damage class, survey, or date and sort by any column. The filtered records can be exported" | Called **Damage records**. Filters: road name search, kind of damage, inspection status, AI check (likely not damage / looks like damage / not run). **No survey or date filter.** Sorting: damage kind, inspection status, confidence, AI check, date recorded. Each row has a **close-up thumbnail**. Clicking it opens a **review pane** with the large close-up, the record's details, the inspection status, and (administrator) kind correction and delete, plus Previous/Next; after a delete it moves to the next record. **Export (CSV/JSON) always contains all records, not only the filtered ones** (D8). The export includes the AI check score. |
| **Account management** (Ch4 §4.1.8.2; FR2) | The admin "sees every page… plus an account management page" | **Administration** has two tabs. **Accounts:** create, change name and role, turn off or on, reset password. The last active administrator cannot be demoted or turned off, and an administrator cannot change their own role or status. **Activity log:** sign-ins and refusals, uploads, renames, deletes, placements, status changes, record corrections and deletions, exports, report reviews, account changes. The administrator also **manages detections** on Damage records (correct the damage type, delete a record) and **sees every survey**. |
| **Inspection status** (not in Ch4 §4.1.8) | — | Every record has a repair stage: Not yet checked → Checked on site → Repair scheduled → Repair under way → Repaired. Both roles can change it. |
| **Resident reports** (not in the drafts) | — | The server can accept and promote citizen reports, and promoted ones show as "Resident report" on the map and in the records. There is no public page for submitting them. Leave this out of the chapters unless the team decides otherwise (D9). |

**Ch3 §3.5 and Fig. 3.5.1 (use cases).** The current diagram gives the administrator only
"Manage user accounts". The system also has, for the administrator: **View activity log**,
**Manage detections** (correct a record's damage type, delete a record, review resident reports)
and **View every survey**. For both roles, use cases the diagram leaves out: **Update inspection
status**, **Rename / delete own survey**, **Analyse a survey again**, and **Review a detection's
close-up** (part of viewing results). The generalisation arrow (the administrator inherits every
personnel use case) is correct.

---

## 5. Mobile capture app changes

Use this section for Ch3 §3.4.2, Ch4 §4.1.8.3, FR3–FR5, and Table 4.3.2.1.

### 5.1 Recording length: parts instead of a 590-second stop (C6)

| Draft says | Now |
|---|---|
| "limits each recording to 590 seconds" (Ch3 §3.4.2); "stops automatically at 590 seconds" (Ch4 §4.1.8.3, FR4) | **No time limit.** A recording continues until the surveyor stops it. Every 590 seconds (9:50) the current part is saved and the next part starts by itself, with a gap of well under a second (estimated; to be measured, Section 9). |
| One recording = one upload | **Each part is its own survey** and its own upload, so every upload stays under the server's ten-minute limit. Parts share a recording ID and are titled "part 2 of 3". |
| GPS track per recording | GPS is logged **once for the whole recording**, without gaps between parts. Each part's GPX takes its stretch of the log plus 10 seconds on either side, so damage in a part's first and last seconds can still be placed. Neighbouring parts' routes on the map overlap by a few seconds. |
| "enough free storage" (Ch3); "At least 544 MB free before each recording" (Ch4 Table 4.3.2.1) | **At least 2 GB free before each part**, checked again before every part. If the phone runs out, the recording ends cleanly at a part boundary. (544 MB applied only while a 500 MB file cap was on.) |
| After stopping, one review | One review screen for **all parts**: total length, size and GPS points, one road name given to every part, and "Upload all N parts". |

### 5.2 Horizon and Bonnet lines (C2), replacing the "level guide"

**Why.** The first version of the camera screen assumed a level phone, with the horizon at the
middle of the picture. A phone mounted on a windshield is tipped up or down and sits high or low
on the glass, with more or less bonnet in view. The horizon is rarely in the middle.

**What it does now.**

- Two lines are drawn over the camera preview: **Horizon** (drag it to where the road ends) and
  **Bonnet** (drag it to the top edge of the bonnet). The parts outside them are dimmed. Only the
  road between the lines is analysed.
- Until the Horizon line is dragged, it follows an estimate from the phone's motion sensors:
  y = 0.5 + tan θ / (2 tan(φ/2)), with θ the camera's pitch and φ the vertical field of view
  (about 41° in landscape and 67° in portrait for a phone's main camera).
- The sensor estimate is only a starting point, because braking and acceleration tilt the sensed
  gravity (0.2 g reads as about 11°).
- The lines are remembered for the next drive, since a mounted phone keeps its view, and they are
  stored separately for landscape and portrait.
- The lines are fixed for the length of a recording. Each part sends them with the upload
  (`road_top`, `road_bottom`) and they are written into the GPX metadata.
- A warning appears if the phone is turned more than 5° sideways, or if little road is between
  the lines.

This fits the "shared mounting checklist" in Ch3 §3.4.3 and Ch4 §4.1.3: the checklist fixes the
mount, and the lines record where the road is in that mount's picture.

### 5.3 Other mobile changes

- **Record without signing in.** A phone that has never signed in can record straight away.
  Sign-in, which is where the server address is entered, is needed only to upload. Recordings
  wait on the phone until then.
- **Camera layout.** The preview has its own box in the exact shape of the recording. In
  landscape, the controls sit in a panel beside it; in portrait, above and below it. Nothing
  covers the video except the two lines, so a line on screen is the same line in the recorded
  frame.
- **Following the server.** After upload, the phone shows the server's analysis status and the
  number of damages found. For testing, it offers "Analyse again on the server" and "Upload again
  as a new survey".
- **Unchanged and correct in the drafts:** 1080p H.264 in a MOV container without audio,
  5 Mbit/s requested; the GPS gate (fix under 5 s old and within ±20 m); stale fixes dropped;
  gaps over 3 s flagged; time offset with clock-skew correction (Eq. 16); persistent queue,
  Wi-Fi only by default, automatic retries; screen kept awake; a recording interrupted by locking
  the phone is labelled as such.
- **Observed but not measured:** iPhone recordings came out larger than 5 Mbit/s would give
  (about 37 MB per minute), so the requested bitrate may not be applied. Measure it (Section 9).

---

## 6. Requirements table (Ch4 Table 4.2.2.1), item by item

| ID | Status | Revise to |
|---|---|---|
| FR1 Authentication | Change | Username (not email address) and password; JWT expires after twelve hours. |
| FR2 Account management | Extend | Also: change a name or role, reset a password, reactivate an account; the last active administrator is protected. Consider a new FR for the activity log (see below). |
| FR3 Survey capture | Extend | Add: records the road band (Horizon and Bonnet lines) with each survey; a recording longer than 590 s is saved as consecutive parts with one continuous GPS log. |
| FR4 Recording safeguards | Change | GPS gate unchanged; at least 2 GB free before each part; **does not stop at 590 s**: saves a part every 590 s and continues. |
| FR5 Upload queue | Correct | Add: recordings can be made signed out and wait for sign-in to upload. |
| FR6 Survey upload | Change | Remove "or larger than 500 MB". Keep the ten-minute limit. |
| FR7 Damage detection | Extend | Add: analyses only the road band of each frame, at input size 1280. |
| FR8 Detection filtering | Change | Replace "store a repeated sighting… only once within its de-duplication window" with: joins sightings of the same damage across analysed frames into one record (tracking), and discards detections fixed to the camera (the windshield reflection). |
| FR9 GPS synchronization | Correct | — |
| FR10 Georeferencing | Correct | — |
| FR11 Damage log | Extend | Add: AI check score; the road band of each survey; inspection status. |
| FR12 Annotated video | Correct | Add: the annotated video shows the road-band lines. |
| FR13 Processing status | Extend | Add: a failed survey shows the reason, and any failed or finished survey can be analysed again from the files on the server. |
| FR14 Results viewing | Extend | Add: a zoomed close-up of each detection on the survey page, the map and the records page. |
| FR15 Records and export | Change | Filters: kind, inspection status, AI check, road name. Sorting by kind, status, confidence, AI check, date. Export always covers all records (or change the system, D8). |
| **New FR16 AI check** | Add | The system shall score each detection with a second, general image model and flag likely false detections for the administrator, without deleting or hiding any record. |
| **New FR17 Record review** | Add | The administrator shall review each record's close-up and correct its damage type or delete it; both roles shall update its inspection status. |
| **New FR18 Activity log** | Add | The system shall log sign-ins, uploads, changes, deletions, exports and account changes, viewable by the administrator. |
| NFR1 Detection accuracy | Correct | mAP@50 ≥ 0.80 overall and per class on the local test subset. Applies to the team's own model only. |
| NFR3 Privacy and access control | Mostly correct | Personnel see only their own surveys and video files; the administrator sees all. Detection records, their snapshots and the map are shared among all accounts. The AI check does not identify people or plates (Section 7). |
| NFR4 Data retention | Needs action | A purge script exists. It deletes raw uploads older than 30 days, but only when run with `--apply`; it is not scheduled automatically. Schedule it on the deployed server (Task Scheduler / cron), or reword NFR4 (D10). |
| NFR8 Compatibility | Correct | iPhone only for the study. The Android build exists but is not evaluated. |
| NFR10 Maintainability | Correct | The model is replaced by changing one setting (the weights file path). |
| **New NFR (offline)** | Add (optional) | Detection and the AI check run on the server without internet once their models are installed. |

---

## 7. Ethics and data protection (Ch3 §3.7, Ch4 §4.1.7)

1. **"The YOLOv8m model … does not detect, identify, or classify people or vehicles."** Still true
   for the detector. The **AI check** compares each damage close-up with descriptions that include
   "a car" and "a bus", so that it can recognise a false detection on a vehicle. It does not
   identify or record people, faces or plates, and stores only one number: how much the close-up
   looks like road damage. Reword so this is accurate, for example: "…no stage of the system
   identifies people, faces or license plates; the AI check compares a damage close-up with
   descriptions of road damage and of common look-alikes such as vehicles and lane markings, and
   stores only a road-damage score."
2. **Phone copies.** Ch3 says recordings on the researchers' phones "will not be copied to personal
   photo libraries or cloud services". The app keeps recordings after upload until they are
   deleted, and offers **"Save video to Photos"** and **"Share video"** on each survey. Either
   state a procedure (the team does not use these and deletes surveys after upload is confirmed),
   or have these buttons removed for the study build (D11).
3. **Retention.** "Raw uploaded videos will be deleted from the server 30 days after upload" needs
   the purge script scheduled on the server (NFR4). It removes only the original upload; the
   annotated video and snapshots stay, and they also show bystanders and plates unblurred.
4. **Online deployment** (new, from the scope change). Survey footage and snapshots will be
   reachable over the internet for the remote demo. Before going online:
   - change the default administrator password (`admin` / `admin123` is created on first start);
   - serve over HTTPS;
   - create accounts only for evaluators;
   - consider putting only the team's demo surveys on the online copy.
   The drafts' note that tokens travel in media URLs and may appear in server logs matters more
   on a public host.
5. **Stored account data.** Ch3 lists "name, office, email address, and role". The user table also
   stores a username and an organisation/agency, plus legacy fields that are no longer filled
   (sector level, ID photo, rejection reason). Mention the username; the legacy fields are empty.
6. **Duplicated text.** In the Chapters 1–3 PDF, the paragraphs "Privacy, Anonymity, and
   Confidentiality" through "Responsible Use of AI" appear **three times** (pp. 56–62). Keep one
   copy.

---

## 8. Deployment for the remote demo (what the system still needs)

The system was built to run on one computer on the office's local network: phones connect to it
over Wi-Fi. The remote demo needs it on the internet. **This work is not done yet.** It affects
Ch4 §4.2.6, NFR11 and Ch3 §3.7.

| Item | Today | Needed for an online deployment |
|---|---|---|
| Web app → server address | Fixed to `http://localhost:5000/api` in the web client | Make the API address configurable for the hosted build, or serve the web app and the API from one address. |
| HTTPS | None (plain HTTP on the local network) | Required for a public site and for the iPhone app: iOS only allows plain HTTP to local-network addresses. |
| Mobile app → server | Server address typed on the sign-in screen; allowed only on the local network | Works with an HTTPS address once the server is online; needs a rebuild if the network setting changes. |
| Processing power | Analysis runs on the server's CPU or GPU, one thread per upload | A hosted server must be able to run YOLO at 1280 and CLIP. Alternatively, host already-processed demo surveys and show uploading in the demo video (D4). |
| Uploads over the internet | No size cap; a 590-s iPhone part can be several hundred MB | The host and any proxy must accept large uploads, or the demo relies on pre-processed surveys. |
| Data | SQLite file, local folders | Fine for one demo server (NFR11 holds). Back up before the demo. |
| Mobile install | Built and installed from a Mac with Xcode; a free Apple ID's install expires after 7 days | Ch4 §4.2.6 "[TestFlight / direct install / Expo, confirm]": the current method is **direct install from Xcode (Release build)**. TestFlight would need a paid Apple Developer account. |

---

## 9. Still unmeasured (keep placeholders; do not estimate)

| Item | Needed for | How to get it |
|---|---|---|
| The team's four-class YOLOv8m model | Everything in RQ1 and NFR1 | Train it. The team's current weights are still one class (pothole). The server runs the placeholder model until the team's model is swapped in. |
| Training input size that matches inference (1280) | Ch3 §3.3.1, Eq. 2 | Decide (D5), then train. |
| Confidence threshold `c_min` | Rule 2 | Choose it on the validation set by maximum F1, once the model exists. |
| Dataset counts (RDD2022 India per class; local frames per class) | Ch3 Table 3.4.3, Ch4 | Run the preparation scripts; collect and annotate the local data. |
| Dataset split | Ch3 §3.4.3 says 70/15/15 for both | **The preparation scripts still use 80/15/5 for RDD2022.** Change the scripts to 70/15/15, or the text (D12). No script yet builds the local split by survey route. |
| AI check on a second survey | If C5 is reported | Hand-label records from a survey not used to tune it; report AUC and flagged/passed counts at 0.60. |
| Gap between recording parts | Ch3 §3.4.2, device tests | Film a running clock across a part change; compare the last frame of part *k* with the first frame of part *k*+1. |
| Video start-time gap, GPS rate, clock skew | RQ3 factors | Already planned (stopwatch test; GPX metadata). |
| Actual bitrate and frame rate on the team's iPhones | Ch3 §3.4.2 | From uploaded files (size ÷ duration; frame rate per video). |
| Processing throughput | Ch4 | Per-survey frames, sampled frames and processing seconds come from the system's export endpoint; state the hardware. Note that throughput changed with input size 1280 and the AI check. |
| Positional error, damage-log correctness, inspection time, UAT | RQ2–RQ4, hypothesis | Field validation and evaluation as planned, now with the DPWH offices. |

Also: Ch4 §4.2.5 "Unit testing. Each module was tested on its own…" is stronger than what exists.
The repository has self-checks for the tracker and two mobile scripts (GPX building and the
upload body), and manual smoke tests; there is no automated test suite for every module. Either
add the tests or describe what was actually tested.

---

## 10. Decisions the team needs to make

| # | Decision | Recommendation |
|---|---|---|
| D1 | RQ4 and significance: name DPWH district offices, LGUs, or both? | "DPWH district engineering offices and LGUs", with DPWH first. |
| D2 | Which road classes are surveyed now that the partner is DPWH? | National roads in Mendez-Nuñez (DPWH jurisdiction), plus municipal/barangay roads only if the dataset needs them. Fix "city roads" → "municipal roads". |
| D3 | Is the DPWH Batangas annotation validator a respondent? | No: keep the validator out of the respondents; other Batangas personnel may respond. |
| D4 | Do remote respondents upload a survey themselves, or review surveys already processed on the site? | Pre-processed surveys on the site, with upload shown in the demo video. This avoids slow uploads and processing on a hosted server. Change Ch4 §4.4.3 step 3 to match. |
| D5 | Train the team's model at 640 (plan) or at 1024–1280 to match inference? | Train at 1024 or 1280; report the change in Ch4 §4.2.4. |
| D6 | Login by email (drafts) or username (system)? | Change the drafts to username; it matches the system. |
| D7 | Overview shows no per-class split. Add it to the system, or change Ch4 §4.1.8.2? | Change the text: the per-class counts are on the map legend. |
| D8 | Export covers all records, not the filtered ones. Change the system or the text? | A small system change: export with the current filters. Otherwise reword FR15 and §4.1.8.8. |
| D9 | Mention resident reports? | Leave them out; there is no public submission page. |
| D10 | 30-day retention: schedule the purge script or reword? | Schedule it on the deployed server and say so. |
| D11 | "Save to Photos" / "Share" on the phone vs. the ethics text | Remove them from the study build, or state the procedure. |
| D12 | Dataset split 70/15/15 (text) vs 80/15/5 (scripts) | Update the scripts to 70/15/15. |
| D13 | Report the AI check as part of the system, as an extra evaluated component, or not at all? | Describe it as an advisory feature in Ch3 and Ch4. Report its accuracy only if measured on a held-out survey. |

**Small system follow-ups that come with the scope change** (not done yet):

- Rename the default administrator's organisation from "Local Government Unit of Mendez-Nuñez" to
  the DPWH office.
- Update the project notes that name the partner office.
- Do the online-deployment work in Section 8.

---

## 11. Text errors found in the drafts (not caused by system changes)

- **Ch1 §1.1 vs Ch3 §3.4.3:** the local dataset is "approximately 2,000 annotated frames" in
  Ch1 but "approximately 1,500 … with 500 frames as the minimum" in Ch3. Use one target.
- **Ch1 §1.7, p. 10:** the first sentence is repeated ("This study focuses on the development of
  a web-based…" twice).
- **Ch3 §3.8 introduction:** maps RQ2 → §3.8.4, RQ3 → §3.8.3, RQ4 → §3.8.5, hypothesis → §3.8.6.
  The actual subsections are 3.8.1 model performance, 3.8.2 annotation agreement, 3.8.3 damage log
  correctness, 3.8.4 user acceptance testing, 3.8.5 frequency and percentage, 3.8.6 software
  tools.
  - There is **no positional-error subsection** and no inspection-efficiency subsection.
  - Ch4 §4.1.5 cites Equation 24 (Haversine) and Equation 26 (time reduction), neither of which is
    in Ch3.
  - Equation numbering jumps 23 → 25 → 27.
  - Add the Haversine equation (24) and the time-per-kilometre / percentage-reduction equations
    (26), and renumber.
- **Ch3 §3.3.2 Rule 4:** refers to "Section 3.8.4" for the duplicate rate; the damage-log check is
  §3.8.3.
- **Ch3 §3.6:** refers to "Section 3.4.4" for the annotation validation; it is §3.4.3.
- **Ch3 §3.4.2:** "wwhere" typo under Eq. 16.
- **Ch3 §3.7:** three copies of the same subsections (Section 7, item 6).
- **Ch3 Table 3.8.8** is the software tools table in §3.8.6; its number does not follow the
  section.
- **Ch1 §1.5.1:** "aYOLOv8m" and "application,to" are missing spaces.
- **Names:** the system is called **OcuLubak** in the app interface and OCULUBAK in the thesis.
  Pick one style for the chapters. Spell the place "Mendez-Nuñez" consistently; some passages use
  "Mendez-Nunez".
