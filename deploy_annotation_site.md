# Task for Claude Code: Make the OCULUBAK annotation site multi-user and deploy it tonight

**Owner:** Gian. **Labelers:** Gian, Janmikael, Kyle (each on their own laptop/browser).
**Deadlines:** working system with a trained model by **Wed Nov 11** (system deadline). Final defense **Mon Nov 16**.
Labeling must stop at fixed **label freeze times** (§7) so there is time left to train. Training plan: §9.

Read this whole file before changing anything. Work in small steps and test after each one.

**Order of work:** §0 (clean the repo) → §2 (inspect) → §3–§6 (build and deploy) → §7–§9 (label and train).

---

## 0. Clean the repository first (do this before anything else)

Earlier prompts left half-finished changes, duplicate files, and things that were never pushed. Clean up **without losing anything**. Moving files is fine; deleting them is not, unless Gian approves.

**Time box: 45 minutes.** The goal is a repo that is organized enough to build on tonight, not a perfect one.

### 0.1 Safety snapshot (before touching anything)
1. Run `git status`, and list uncommitted, untracked, and stashed changes (`git stash list`). Report them to Gian.
2. Commit **everything as it is** to a new branch `backup/pre-cleanup-2026-11-10`. Include untracked code files, but not large data (see 0.4). Push the branch if a remote exists.
3. Copy outside the repo, as a plain folder backup: the current reviewed labels, the split files (`results/step1_split.md` and the files it was made from), and any existing label database.
4. Do the cleanup on a branch `cleanup`. Merge it into the main branch only after 0.6 passes.

### 0.2 Inventory
Produce `CLEANUP_REPORT.md` with a table of every top-level folder and file. For each, give its purpose, whether it is used by the current pipeline (yes / no / unsure), and the proposed action (keep / move / archive / ask Gian).

Flag:
- duplicate or versioned copies (`*_old`, `*_v2`, `copy of`, `final_final`);
- scripts that import missing modules or reference paths that don't exist;
- half-applied changes from failed prompts, such as functions defined twice or broken imports;
- hard-coded absolute paths;
- secrets in code (API keys, passcodes). Move these to `.env` and add `.env` to `.gitignore`.

**Stop and show Gian the report before moving anything** marked unsure or archive.

### 0.3 Target layout
Adapt names to what already exists, and don't rename things that work just to match this:
```
oculubak/
  annotate/        # annotation site (server + frontend)
  system/          # main web system (detection service, map, API)
  ml/
    data/          # export_yolo.py, build_train_list.py, split scripts
    train/         # training configs, run scripts
    eval/          # test_eval.py, val/threshold scripts
    prelabel.py
  results/         # *.md result tables (kept in git)
  configs/         # model_config.json, data.yaml
  scripts/         # start_labeling.bat, backup job, utilities
  archive/         # old/unused code moved here, not deleted
  .env.example     # variable names only, no values
  README.md        # how to run: annotate, train, eval, system
```

### 0.4 Keep large and generated files out of git
Add these to `.gitignore`: frames/images, videos, `runs/`, `*.pt` weights, `labels.db`, `backups/`, `__pycache__/`, `node_modules/`, and `.env`.

They stay on disk, in a fixed data folder outside the repo or an ignored `data/` folder. All paths come from one config or `.env` (`DATA_ROOT`, `FRAMES_DIR`, `LABELS_DB`, `WEIGHTS_DIR`), not hard-coded.

If large files were already committed, **don't rewrite history tonight**. Just stop tracking them (`git rm --cached`).

### 0.5 Protected files (do not change contents)
- The split definitions (which route group is in train/val/test) and the 50 m buffer list.
- The test labels (G05, G13, G15) and `test_eval.py`'s logic. You may move them and fix their paths, nothing else.
- The existing 1,066 reviewed labels.
- `results/local_datasets_nz.md` and `results/step1_split.md`.

### 0.6 Verify after cleanup
1. Fix imports and paths broken by the moves.
2. Count check: the dataset still has 1,066 reviewed frames and 609 near-zone boxes, with the same per-split and per-class counts as `results/local_datasets_nz.md`. Write a small `ml/data/check_counts.py` for this; it is reused after each export.
3. The test file list is identical to before the cleanup (compare hashes).
4. The current main system still starts, and the annotation site still opens locally.
5. Write a short `README.md` with the run commands.
6. Commit to `cleanup`, merge to main, and push.

Only then continue with §2.

---

## 1. Architecture: host on Gian's desktop, share through a tunnel

Do **not** deploy to Vercel, Netlify, or another cloud host. The frames (~9.5k images) live on Gian's Windows 11 desktop. Free cloud hosts have no persistent disk for the images or the label database, and uploading GBs of frames tonight wastes time.

Instead:

```
[Janmikael browser] ┐
[Kyle browser]      ├──> https://<random>.trycloudflare.com ──> cloudflared ──> localhost:PORT
[Gian browser]      ┘                                                   (Gian's desktop)
                                                                         ├─ annotation server (production mode)
                                                                         ├─ labels.db (SQLite, WAL)
                                                                         └─ frames/ (images, read-only)
```

All three people use one server and one database, so sync is automatic. Everyone sees the same state, and no merging is needed.

---

## 2. Step 0: inspect the existing site first

1. Identify the stack (framework, server, how it runs), where images are read from, and **where labels are currently saved**.
2. If labels are saved in the browser (localStorage, IndexedDB, downloads), that **must change**. Labels must be stored on the server (§3.1).
3. Report a short summary of the current structure before editing.

---

## 3. Required changes (acceptance criteria)

### 3.1 Server-side storage
- Store labels in a SQLite database `labels.db` with WAL mode enabled. Every write must go through the server.
- Tables (adapt names to the existing code):
  - `frames(frame_id, recording, route_group, split, tier, priority, status, locked_by, lock_expires, version)`
  - `boxes(frame_id, class_id, cx, cy, w, h, source)`, where `source` is `model` or `human`
  - `events(frame_id, user, action, timestamp)` as an audit log
- `status` values: `todo`, `in_progress`, `labeled`, `skipped`.
- A frame with zero boxes and status `labeled` is a **confirmed negative**. Keep that distinct from `todo`.

### 3.2 Users
- A simple login: pick a name (Gian / Janmikael / Kyle) plus a shared passcode from the env var `ANNOTATE_PASSCODE`.
- The URL is public, so **every route except the login page requires the passcode session**. That includes image routes.
- Every save records the user and a timestamp.

### 3.3 Work queue with locking (prevents collisions)
- `GET /next` gives the user the highest-priority `todo` frame and **locks it to that user for 10 minutes**.
- While a frame is open, the client sends a heartbeat every 60 s to extend the lock.
- An expired lock returns the frame to `todo`.
- Two users must never receive the same frame.
- **Never serve test-group frames (G05, G13, G15).** The test set is frozen.
- Already-reviewed frames (the existing 1,066) are excluded from the queue.

### 3.4 Saving
- Save on "next" and on an explicit save.
- Use an optimistic version check: the client sends the `version` it loaded. If the server version differs, reject the save and show a message.
- After a save, the server returns the next frame immediately to keep the flow fast.

### 3.5 Pre-labels
- Load model predictions (YOLO txt, conf ≥ 0.15) as editable starting boxes with `source=model`. If a frame isn't pre-labeled yet, run `prelabel.py` (§5) first.
- Draw model boxes dashed. When the labeler saves, store every kept box as `source=human`.

### 3.6 Hotkeys (speed matters for 9k frames)

| Key | Action |
|---|---|
| `Enter` | Accept the current boxes, save, and go to the next frame |
| `N` | No damage: clear all boxes, save as a negative, next |
| `1` `2` `3` `4` | Set class D00 / D10 / D20 / D40 (for the selected box or the next drawn box) |
| `Del` / `Backspace` | Delete the selected box |
| `Z` | Undo |
| `S` | Skip (unsure) and go to the next frame |
| `←` | Go back to the user's previous frame (re-locks it) |

Show the hotkey legend on screen.

### 3.7 Images over the tunnel
- Serve a resized JPEG (longest side ~1280 px, quality ~85) cached on first request. Do not send originals.
- Prefetch the next frame in the background.
- Boxes stay in normalized coordinates, so resizing does not affect labels.

### 3.8 Progress dashboard (`/stats`)
Show:
- frames done per user,
- remaining frames by tier,
- box counts per class per split (train/val), compared against the old counts,
- labels per hour.

The team uses this to check pace.

### 3.9 Export
`python export_yolo.py` should:
- write YOLO txt files for `labeled` frames into the dataset folders by split, merged with the existing reviewed labels,
- re-apply the existing near-zone filter,
- apply the 50 m buffer rule for val frames against train frames,
- regenerate `results/local_datasets_nz.md` with the new counts table.

It must be runnable at any time (for the mid-sprint snapshot training).

### 3.10 Backups
Every 30 minutes, copy `labels.db` to `backups/labels_<timestamp>.db` using the SQLite backup API, not a raw file copy. Also copy it to the synced Google Drive folder if one exists.

---

## 4. Queue priority

When the frame table is built, set `priority` so that whatever is finished by the freeze is the most useful work:

1. Train groups, T1: frames with any D20 or D10 pre-label prediction.
2. Val groups, T1.
3. Train groups, T2: max prediction confidence in 0.15–0.5, any class.
4. Val groups, T2.
5. Everything else (T3), interleaved train/val.

Thin near-duplicate frames: within each recording, keep at most 1 frame per ~5 m of GPS track. Frames dropped by thinning are not queued.

---

## 5. Pre-labeling

`prelabel.py`:
- Run the current best model over all queued frames at conf 0.15 (imgsz as trained). Write YOLO txt.
- Set `tier` and `priority` from the predictions.
- Use the GPU and batch the inference. It should run in well under an hour on the RTX 4060.

---

## 6. Deploy steps (Windows 11)

1. Run the server in **production mode** (not a dev/hot-reload server), bound to `127.0.0.1:PORT`. Set `ANNOTATE_PASSCODE`.
2. Install cloudflared: `winget install --id Cloudflare.cloudflared`
3. Start the tunnel: `cloudflared tunnel --url http://localhost:PORT`. It prints a `https://….trycloudflare.com` URL. Send that URL and the passcode to the team in the GC.
4. **The URL changes every time cloudflared restarts.** If it restarts, post the new URL.
5. Power settings: set sleep to **Never** while plugged in, and keep the desktop on wired internet if possible. If the desktop sleeps or goes offline, everyone stops.
6. Provide `start_labeling.bat`, which starts the server, the backup job, and the tunnel in one go.

### Test before sharing
- Open the site in two different browsers as two different users. Confirm they receive different frames.
- Save in one, reload in the other, and confirm the state is consistent.
- Kill the browser mid-frame and confirm the lock expires and the frame returns to `todo`.
- Run `export_yolo.py` on a handful of labeled frames and open the txt files to check the coordinates.

---

## 7. Schedule through the defense

The site stays up after Wednesday. Wednesday's model (**v1**) is what the system ships with. Labeling then continues until Friday night for a better final model (**v2**) before Monday.

| When | What |
|---|---|
| **Tue Nov 10, evening** | Claude Code: §0 repo cleanup (45 min), then §3 changes, `prelabel.py`, test, deploy. Gian runs pre-labeling. Team starts labeling after a 10-minute warm-up: everyone labels the same 20 frames, compares, and agrees on the rules (§8). |
| **Tue, ~midnight** | **Snapshot 0:** `export_yolo.py`, then start run **v0** overnight (§9.3). Labeling can continue. |
| **Wed Nov 11, morning** | Check v0. It is the fallback model. Keep labeling. |
| **Wed, freeze 1** (system deadline − ~6h) | **Label freeze 1.** Export → train **v1** (§9.3). Gian integrates the model while it trains (§9.6). |
| **Wed, before deadline** | Put v1 into the system (or v0 if v1 isn't done). Pick the threshold on **val** (§9.5). Demo-check on one recording. **Do not run test yet.** |
| **Thu Nov 12 – Fri Nov 13** | Keep labeling. Focus on the D20/D10 tiers and val frames. Optional: 3-fold run for Chapter 4 (§9.4). |
| **Fri Nov 13, ~22:00** | **Label freeze 2 (final).** Export. Start **v2** overnight. |
| **Sat Nov 14** | Pick the v2 threshold on val. **Run `test_eval.py` once on v2.** Swap v2 into the system. Update Ch. 4–5 numbers and tables. |
| **Sun Nov 15** | Defense slides and rehearsal. **No more training or relabeling.** |
| **Mon Nov 16** | Defense. |

**Test-once rule:** only the final model is test-evaluated. If Wednesday's submission *requires* a test score, then run `test_eval.py` once on v1. In that case v1 is the reported model, and any v2 numbers are only val/k-fold results, labeled as such.

---

## 8. Labeling rules (short version; show on screen)

- **Near zone only.** Ignore damage beyond the boundary.
- **D00:** a crack running along the direction of travel. **D10:** a crack running across the lane. One box per continuous crack. Start a new box if it bends more than ~45° or has a gap larger than ~1 m.
- **D20:** an interconnected crack network forming closed blocks. Box the whole patch. Cracks touching it belong to the patch.
- **D40:** box the edge of the hole, not the cracks around it.
- **Don't label:** sealed or patched cracks, joints, road markings, shadows, manholes, wet streaks.
- **Unsure:** press `S` rather than guessing.

---

## 9. Training plan (local dataset only)

### 9.1 Rules
- **Training data:** human-labeled local frames only (the existing 1,066 reviewed frames + newly labeled frames). No RDD2022 images in any v0/v1/v2 run.
- **Test set:** groups G05, G13, G15 stay untouched. Score them once, with `test_eval.py`, on the final model only (§7).
- **Model selection:** decisions use **val** only (or k-fold). With a small val set, differences of about 0.03 mAP are noise. Don't chase them.
- **Reproducibility:** each run is tied to a data snapshot, the `labels_<timestamp>.db` backup used for the export. Log it.

### 9.2 Data preparation (`export_yolo.py` + `build_train_list.py`)
1. `export_yolo.py` (§3.9) writes `images/` + `labels/` per split and regenerates the counts table.
2. `build_train_list.py` writes `train_list.txt`:
   - each frame containing **D20 ×4**, each containing **D10 ×3**, each containing **D40 ×2**, the rest ×1 (use the frame's rarest class);
   - cap negatives (no-box frames) at ~40% of the list by random sampling, with a fixed seed.
3. `data.yaml`: `train: train_list.txt`, `val:` the val image folder, `names: {0: D00, 1: D10, 2: D20, 3: D40}`. Match the existing class ids exactly.
4. Print and save the class counts **per epoch** (after oversampling) to `results/train_list_counts.md`.

### 9.3 Runs (Ultralytics YOLO, RTX 4060 8 GB)

Start from **COCO-pretrained weights** of the same family the earlier runs used (e.g. `yolov8s.pt` or `yolo11s.pt`), so results stay comparable. Pretrained COCO weights are not RDD data, so the "local only" claim holds.

| Run | Data | imgsz | epochs (patience) | Purpose |
|---|---|---|---|---|
| **v0** | Snapshot 0 | 640 | 80 (25) | Fast fallback model, ready Wed morning |
| **v1** | Freeze 1 | 1024 if time allows, else 640 | 120 (30) | Ships with the system Wed |
| **v2** | Freeze 2 | best setting from v1 vs v0 | 150 (40) | Final model for test + defense |

Common settings:
```
yolo detect train model=yolov8s.pt data=data.yaml imgsz=1024 epochs=120 patience=30 \
  batch=-1 workers=4 cos_lr=True close_mosaic=10 \
  mosaic=1.0 fliplr=0.5 flipud=0.0 degrees=0 scale=0.5 translate=0.1 \
  hsv_h=0.015 hsv_s=0.7 hsv_v=0.4 seed=0 deterministic=True \
  project=runs/local name=v1
```
- `batch=-1` lets Ultralytics pick a batch size that fits 8 GB. If it runs out of memory, set a fixed `batch=8` (1024) or `16` (640).
- No vertical flip and no rotation, because they break road perspective. Don't rely on `copy_paste`: in Ultralytics it needs segmentation masks, and our labels are boxes only. The oversampling in §9.2 covers that need instead.
- **Time check:** after epoch 2, estimate total time. If it won't finish before its deadline (v1: system deadline − ~2h for integration; v2: Sat morning), restart at imgsz 640 or with fewer epochs. Don't gamble on the deadline.
- If time allows on Thu–Fri: a 2nd seed of the v2 config, to show variance in Chapter 4.

### 9.4 Optional (Thu–Fri): 3-fold check
- Folds = route groups from train + val, split into 3 groups by group, never by frame. Train the v1 config on each fold. Report mean ± std of mAP@50, overall and per class.
- This only gives Chapter 4 a more stable number than the single val set. Skip it if labeling or v2 needs the GPU time.

### 9.5 Picking the deployment threshold (on val)
- From the chosen model's val predictions, pick the confidence threshold that maximizes **overall F1**. Record per-class precision, recall, and F1 at that threshold.
- Save the threshold in the system config (e.g. `model_config.json`: weights path, conf threshold, imgsz, class names). Use the same imgsz as training.

### 9.6 Integration into the system
1. Copy `runs/local/<run>/weights/best.pt` to the system's model folder as `oculubak_<run>.pt`. Keep the previous model file for rollback.
2. Update `model_config.json` (§9.5). The detection service reads weights and threshold from the config, not hard-coded values.
3. **Smoke test:** run detection end-to-end on one held-out recording from val. Check that boxes, classes, GPS mapping, and the web map all display correctly.
4. Note in the system's "About/Model" page which run and data snapshot are deployed.

### 9.7 Results to save for the manuscript and defense
`results/train_runs.md`, one row per run: run id, data snapshot, train boxes per class, imgsz/epochs, val mAP@50 (overall + D00/D10/D20/D40), val mAP@50-95, P/R/F1 at the chosen threshold, training time.

From Ultralytics outputs, keep: `results.png`, the confusion matrix (normalized), PR curve, F1 curve, and 6–8 example val predictions (good detections + typical failures, especially D20). These go straight into Chapter 4 and the defense slides.

After the single test run: `results/test_v2.md` (or `test_v1.md`) with the same metrics, plus the test class mix (few D10, many D20) so the panel can read the per-class numbers in context.

### 9.8 What to tell the panel if a class is below 0.80
Show the per-class box counts next to the per-class AP. Explain that D20 is scarce on the study routes. Present the threshold-based P/R/F1, which reflects how the deployed system actually behaves. Have this slide ready in case it's needed.
