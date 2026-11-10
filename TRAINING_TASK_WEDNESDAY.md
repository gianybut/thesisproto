# Task: A Working Trained OCULUBAK Model by Wednesday, Nov 11

**Today is Monday, Nov 9. The deployed, working model is due Wednesday,
Nov 11.** The manuscript is due by Nov 14, so the result tables must exist by
Wednesday too. Every step below has a time box. If a step runs over, take
the listed fallback instead of extending it.

**Rules for every step:**
- **Do not change the detection algorithm** (road band, tracking, fixed-spot
  filter, AI check). Only the model weights and the calibrated confidence
  threshold change.
- **Keep YOLOv8m** (Chapter III commits to it).
- **Model choices are made on the local validation set only.** The local test
  set is evaluated at the end, for the chosen model only. If the test *labels*
  are later corrected (for example after the expert check), re-running the
  evaluation is allowed; re-choosing the model based on test results is not.
- **Validation and test labels must be human-reviewed.** Training labels may be
  automatic (pseudo-labels). Scripts must enforce this.
- Fixed seed everywhere. Log every setting and the wall-clock time of every
  run. Every training run must resume from its last checkpoint if it is
  interrupted (Ultralytics `resume=True`).
- **Verify, don't assume:** read the code before relying on it, and report
  "confirmed / not true / partly true" with file and line.

**Compute:** everything, including training, runs **on this Windows PC from
VS Code**. No Colab.

| Part | Spec |
|---|---|
| GPU | NVIDIA GeForce RTX 4060, **8 GB VRAM**, driver 32.0.16.1088 |
| CPU | AMD Ryzen 5 5600 (6 cores / 12 threads) |
| RAM | **16 GB** (the page file was nearly full when checked) |
| OS | Windows 11 Pro 64-bit |

**Settings that follow from this hardware (apply to every training run):**
- `device=0` (CUDA). Install the CUDA build of PyTorch and confirm
  `torch.cuda.is_available()` is True before anything else.
- `batch=-1` (Ultralytics AutoBatch picks the largest batch that fits in
  8 GB). Log the batch it chose. Expect about 16 at 640, 8 at 960, and 4–6 at
  1024–1280.
- `amp=True` (mixed precision; saves memory and time).
- `cache=False` (16 GB of RAM cannot hold the datasets in memory) and
  `workers=4`.
- **One GPU, so one training job at a time.** Never start two runs together,
  and do not run the OCULUBAK server's video processing while training.
- Windows: put every script's entry point under `if __name__ == "__main__":`
  (needed for data-loader worker processes). Handle folder names with spaces,
  `+`, and characters that Windows changed during download (for example `?`
  in Drive names); never rely on a folder name being a valid identifier.
- Before long runs, set Windows to **never sleep** while plugged in
  (`powercfg /change standby-timeout-ac 0`, restored afterwards) and tell the
  user to close browsers and other heavy apps.

---

## Setup: read this before starting

**Data location:** the team's recordings are in **`VID+GPX/`** at the root of
this project (`thesisproto/VID+GPX/`), one subfolder per recording, each with
a video and a GPX file. Read them from there; do not move or rename them.
**Add `VID+GPX/` and every generated dataset folder (frames, labels, zips) to
`.gitignore` before anything else.** The footage can show people and plates
and must never be pushed to GitHub. Confirm by running `git status`.

**Before Step 1, check these and stop and ask if any is missing:**
- 21 recording subfolders in `VID+GPX/`, each with a video and a GPX file.
  Report any folder that is missing one.
- The stand-in RDD2022 checkpoint the system currently uses. Find its path in
  the backend config and report it.
- The backend's AI-check (CLIP) code and model files, which `autolabel.py`
  must import rather than copy.
- Free disk space: at least about 60 GB (RDD2022 country archives, frames,
  and training runs). Report the actual free space.

## Step 0 · Environment check and benchmark (time box: 30 min)

1. Install or confirm the CUDA build of PyTorch and Ultralytics in the project's
   Python environment; print the PyTorch, CUDA, and Ultralytics versions and
   the GPU name.
2. Train YOLOv8m for **1 epoch** on a 300-image RDD2022 sample at `imgsz` 640,
   960, and 1024 with `batch=-1`, and record the batch size chosen, the time
   per epoch, and peak GPU memory.
3. From those timings, estimate the wall-clock time of every planned run in
   Steps 4–6 (real image counts, epochs, imgsz). Print a table, and propose
   cuts if the total does not fit before **Wednesday 6 AM**: for example
   fewer comparison pairs, 960 instead of 1024 for the final model, or fewer
   epochs. Wait for "continue".

## Monitoring every training run (applies to Steps 0, 4, 5, and 6)

You cannot watch a run on your own between messages, so build the monitoring
into the run itself and report it whenever the user asks.

1. **Start every training run in the background**, writing its console output
   to a log file (`runs/<run>/train.log`), so it keeps going while you are
   doing other work and the user can close the chat.
2. **`tools/watch_training.py`** runs alongside training and every 5 minutes
   (parameter) updates `results/training_status.md` with, for each active or
   recent run:
   - run name, epoch / total, time elapsed, estimated time left
   - latest train losses (box, cls, dfl) and local val precision, recall,
     mAP@50, per-class AP@50 when available, and the best epoch so far
   - GPU utilization, memory used / 8 GB, and temperature (`nvidia-smi`),
     system RAM used, and free disk space
   - whether the training process is still alive
3. **Alerts.** Mark the status line **⚠ ALERT** and show a Windows
   notification when any of these happen:
   - the process has died, or the log shows an error or out-of-memory crash
   - a loss becomes NaN or infinite
   - local val mAP@50 has not improved for 5 epochs (early stopping is
     approaching; normal, but worth knowing)
   - GPU temperature above 85 °C, system RAM above 90%, or free disk space
     below 10 GB
   - no new epoch logged for more than twice the usual epoch time (the run is
     stuck)
4. **What to do on each alert** (write these into the status file too, so the
   user can act without you):
   - **Crash or out-of-memory:** resume from `last.pt` with a smaller batch.
   - **NaN loss:** resume with `amp=False` and half the learning rate.
   - **Overheating:** pause, check the PC's airflow, and resume.
   - **Low RAM:** close other apps, lower `workers` to 2, and resume.
   - **Stuck:** stop it and resume from `last.pt`.

   Never restart a run from scratch if `last.pt` exists.
5. **First-epoch sanity check (every run).** After epoch 1, open the images
   Ultralytics saves (`labels.jpg`, `train_batch0.jpg`, `val_batch0_labels.jpg`)
   and confirm that the boxes sit on road damage and the class names are right
   (D00, D10, D20, D40, in that id order). Report what you saw. A wrong class
   mapping or misplaced boxes caught here saves a whole night of training.
6. **When the user says "check"** (or starts a new session), read
   `results/training_status.md` and the latest `results.csv`, and give a short
   report: progress, current best local val mAP@50 and per-class AP, any
   alerts, and whether the run will finish on schedule. If something is wrong,
   say what to do.

**Check schedule for the team** (also write it at the top of the status file):
- Right after each run starts: confirm the first-epoch sanity check passed.
- Every 1–2 hours while awake: open `results/training_status.md`, or ask
  Claude Code to "check".
- Before going to bed on Tuesday: confirm the final run is alive, with no
  alerts, and has an ETA before Wednesday 6 AM.
- First thing Wednesday morning: check it finished, then continue to Step 6.3.

**Work step by step.** Finish one step, report, and wait for "continue"
before starting the next. Pause points that need the team are marked; do not
skip them.

## Step 1 · Monday: intake, frames, split (time box: 3 h)

The team recorded 21 videos (each one app part, about 9 min 50 s) with GPX
files, in `VID+GPX/` at the project root (one subfolder per recording).

1. `ingest_local.py`: per recording, read the duration, frame rate, resolution,
   and rotation, and from the GPX the road band (`road_top`, `road_bottom`),
   time offset, clock skew, and video start time **if present** (if the road
   band is missing, use the default band 0.50–1.00 and list the recording).
   Write `recordings.csv` with IDs R01–R21.
2. `route_groups.py`: two recordings share a route group if at least 20%
   (a parameter) of one track lies within 30 m of the other, in either
   direction. "Part 2" recordings join their first part. Write
   `route_groups.csv` and `route_groups.html` (Leaflet map, one color per
   group). **Print the groups and pause for the team to confirm or edit**
   (time box: 20 min). Several folders cover the same roads in opposite
   directions (e.g. "Indang Mendez Road" / "Mendez Indang Road"), so expect
   merges.
3. `extract_frames.py`: 1 frame per second, rotation applied, **cropped to the
   road band**, near-duplicates removed (perceptual hash, threshold as a
   parameter). Write `manifest.csv` (frame, recording, route group, second,
   lat/lon from the GPX).
4. `split_local.py --by-route-group`: assign whole route groups to train / val /
   test at about 70/15/15 of frames. Use the draft detections from Step 2.1 only
   to balance classes across splits. **Fail** if a route group appears in two
   splits. Write `splits.csv`.

## Step 2 · Monday night: automatic labels + review tool (time box: 3 h)

1. `autolabel.py`, run on **all** extracted frames:
   - Run the openly licensed RDD2022 checkpoint already used as the system's
     stand-in. Keep boxes with detector confidence ≥ 0.25 (a parameter).
   - Score each box with the **system's own AI check** (CLIP, importing the
     backend's code and prompts, not a copy). Drop boxes with S < 0.60.
   - Write YOLO label files (D00, D10, D20, D40 → 0–3) and `autolabel_log.csv`
     (frame, box, class, detector confidence, CLIP score, kept or dropped).
2. **Training split (pseudo-labels):** select up to 600 frames (a parameter)
   with at least one kept box, spread across the train route groups, favoring
   frames with D20 or D40. **No detector-empty frames** go into train, since
   they may hide missed damage.
3. **Val and test splits:** select up to 120 frames each (a parameter), spread
   across their route groups. Include frames with no auto-labels as well, so
   missed damage can be caught and background frames confirmed.
4. `tools/review_labels/`, a fast local review tool (single page, served
   locally) for val/test frames only. It shows the frame with its auto-labels.
   Keys:
   - **Enter**: accept the frame and go to the next one
   - **Click a box, then Delete**: remove that box
   - **Click a box, then 1/2/3/4**: set it to D00/D10/D20/D40
   - **Drag**: draw a new box, then press 1–4 for its class
   - **B**: mark the frame as background (removes all its boxes)
   - **←/→**: previous / next frame

   Save on every change. Write `review_log.csv` (frame, reviewer, time,
   reviewed = yes), and show progress. Let the three reviewers split the frames
   by route group. **Build this first**, so the team can start reviewing while
   the rest runs.

**Team task, Monday night to Tuesday noon:** review all val and test frames
(about 240 in total; 80 each).

## Step 3 · Monday night (parallel): RDD2022 country data (time box: 2 h)

`prepare_rdd2022.py`: download the **per-country** RDD2022 archives (not the
full release) for Japan, India, Czech, Norway, United States, and
China_MotorBike. **Exclude China_Drone** (aerial viewpoint; say so in the
report). Use only the annotated portion of each country's release. Keep D00,
D10, D20, D40; drop images with none of them. Convert to YOLO format; split
70/15/15 by image with the fixed seed. Print counts per class per split per
country.

## Step 4 · Tuesday morning: safety model (start as soon as val is reviewed)

So that a working model exists no matter what happens to the experiments,
kept small so the GPU is free for Step 5 by Tuesday afternoon (target: about
3 h):
- Data: local pseudo-labeled train + a random **3,000** images from the
  **India** train split (Chapter III's original choice). Validation: local val
  (reviewed).
- YOLOv8m from COCO weights, `imgsz` 960, 40 epochs, patience 10.
- Save as `ml/models/safety.pt` and **deploy it to the local server
  immediately** when done. This is the fallback for Wednesday.

## Step 5 · Tuesday afternoon to evening: country comparison (time box: 6 h; runs after Step 4 finishes)

**Fair-comparison rules:** the same local train set and the same local val set
in every run. The **same total number of foreign training images,
`N_foreign`**, in every run: the smallest filtered training pool among the six
countries, capped at 2,000. A single-country run samples `N_foreign` from one
country; a pair samples `N_foreign / 2` from each. Same model, seed,
augmentation, and settings.

**Screening settings:** YOLOv8m from COCO weights, `imgsz` 640, 20 epochs,
patience 5. The report must say that screening used a smaller input size and
fewer epochs than the final model.

**Runs, in this order:**
1. Local only (the reference point)
2. The six single-country runs
3. The pairs among the **top 3** single countries (3 runs)

`run_country_comparison.py` skips completed runs and resumes interrupted ones.
`summarize.py` writes `results/country_comparison.md`: run, countries, foreign
images, **local val** mAP@50, AP@50 per class, time. Mark the best single
country and the best pair.

**Fallback:** if time runs out after the single-country runs, skip the pairs
and say so.

## Step 6 · Tuesday night to Wednesday: final model (time box: 14 h)

1. **Train the best mix** from Step 5 (single or pair, whichever has the higher
   local val mAP@50) with the **full** training pools of those countries plus
   local train, with local train images **repeated ×3** (via the training image
   list; never repeat val or test). YOLOv8m from COCO weights, `imgsz` 1024
   (1280 only if Step 0's estimate shows it fits overnight; 960 if even 1024
   does not), 50 epochs, patience 10. Start it before going to bed on Tuesday.
2. **Local fine-tune:** continue from step 1 on local train plus a 20% random
   sample of the foreign train data, with `lr0` 0.0002, the first 10 layers
   frozen, 30 epochs, patience 8.
3. **Choose** between the step 1 model, the step 2 model, and `safety.pt` by
   local val mAP@50 (ties: the higher lowest class AP). Report whether local
   val reaches mAP@50 ≥ 0.80 and AP@50 ≥ 0.80 for every class.
4. **Calibrate the threshold** that maximizes F1 on local val.
5. **One test evaluation** of the chosen model (`ml/evaluate.py`):
   - **local test** and **foreign test** separately
   - per class and overall precision, recall, F1, AP@50, mAP@50, plus a
     confusion matrix for each
   - print clearly whether the local test reaches **mAP@50 ≥ 0.80 overall and
     AP@50 ≥ 0.80 per class**
6. **Deploy:** save as `ml/models/best.pt`, set the calibrated threshold in the
   config, restart the server, and process one recording end to end to prove
   it works.

**Fallbacks:** if step 1 is not finished by Wednesday 6 AM, use its best
checkpoint so far. If step 2 cannot finish, skip it. If neither beats
`safety.pt` on local val, deploy `safety.pt`. **If 0.80 is not reached, report
it honestly.** Do not tune on the test set.

## Step 7 · Wednesday: results for the manuscript (time box: 3 h)

1. **Pseudo-label quality:** on the reviewed val/test frames, compare the
   auto-labels with the reviewed labels: precision and recall per class at IoU
   0.50, the number of boxes the CLIP filter removed, and how many of those the
   reviewers confirmed were not damage.
2. `results/chapter5_tables.md`, with paste-ready tables:
   - local dataset summary (recordings, route groups, frames per split,
     instances per class)
   - country comparison
   - final training settings
   - final test results (local and foreign)
   - pseudo-label quality
3. **Sir Neri's form:** `annotation_sample.py` takes 25 random boxes per class
   from the **reviewed val/test labels** (all if fewer). One image per box, in
   random order, with a neutral box color and only an ID; plus a zoomed
   close-up. It writes `answer_key.csv` (kept private).
   `tools/make_validation_form.gs` builds the Google Form: an image item plus a
   required choice of D00 / D10 / D20 / D40 / Not road damage per box, without
   the form's shuffle setting. `annotation_agreement.py` computes percent
   agreement and Cohen's kappa per class from his responses. **If his check
   leads to label corrections in val/test, re-run only Step 6.5** and report
   both the before and after numbers.

---

## After Wednesday (already specified earlier; do not start before the model is deployed)

- **Ethics build of the app:** remove Save to Photos / Share, and offer
  Delete from phone after a confirmed upload.
- **Bulk-upload the 21 recordings** to the server as surveys using `best.pt`,
  for the field and damage-log checks.
- **Field checks:**
  - `sample_validation_sites.py`
  - `reference_points.py` (averages the `VAL-` stationary recordings,
    Haversine distance; `VAL-` surveys excluded from everything else)
  - `damage_log_sample.py` and its scoring script
- `gpx_stats.py` and `start_gap_tool.py`
- **Online copy for the DPWH evaluation:** HTTPS, evaluator accounts, a new
  admin password
- `tools/uat_analysis.py` (with and without the annotation validator)

## Report back

After each step, report: done / partly / not done, files changed, how it was
tested, GPU time used, and anything that could not be verified. Put all tables
in `results/`. Update `CLAUDE.md`.
