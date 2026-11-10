# Cleanup report — 2026-11-10

Branch `cleanup`, made from the backup snapshot `backup/pre-cleanup-2026-11-10` (pushed; the
footage-derived `results/*.jpg` and `JGB19333.pdf` are not in it).
Plain-folder backup of the labels and split: `C:\Users\GIAN\Documents\oculubak_backup_2026-11-10`
(`reviewed/` 2,132 files, `splits.csv`, `route_groups.csv`, `route_overlap.csv`, `review_*.csv`,
`recordings.csv`, `near_zone_bands.csv`, `road_band_overrides.csv`, `recording_mounts.csv`,
`step1_split.md`, `local_datasets_nz.md`).

Layout decision (Gian, 2026-11-10): **keep the current layout**. Nothing is renamed or moved into
`system/` / `annotate/`; the annotation site is built by extending `tools/review_labels/`.

## Top level

| Item | Purpose | Used now | Action |
|---|---|---|---|
| `backend/` | Flask API (system) | yes | keep |
| `frontend/` | React web app (system) | yes | keep |
| `mobile/` | Expo capture app | yes | keep |
| `ml/` | RDD2022 prep, training, benchmark scripts | yes | keep |
| `ml/local/` | local dataset pipeline (ingest → split → review → build → train → eval) | yes | keep; was untracked, now committed |
| `ml/models/` | weights the backend loads (Git LFS) | yes | keep |
| `tools/` | review tool, training queue/watch, upload helper | yes | keep; was untracked |
| `tools/review_labels/` | label review site (server.py + index.html) | yes | keep; becomes the multi-user annotation site |
| `results/` | result tables (*.md, *.csv) | yes | keep; `*.jpg` now gitignored (footage) |
| `launcher/`, `install_*`, `start_*`, `share_online.bat` | app launchers | yes | keep |
| `figures/`, `Documents/` | thesis diagrams and chapter PDFs | docs | keep |
| `yolo-rdd2022/` | 32 RDD2022 benchmark weights (561 MB) + README | reference only | keep on disk; `*.pt` gitignored, README tracked |
| `CHAPTER3_*.md`, `SYSTEM_CHANGES_FOR_CHAPTERS_1-4.md`, `DEPLOY.md`, `MODEL_SWAP.md`, `STARTUP_GUIDE.md`, `README.md` | docs | docs | keep (README/backend docs are stale, see CLAUDE.md) |
| `TRAINING_TASK_WEDNESDAY.md`, `deploy_annotation_site.md` | task briefs | yes | keep |
| `Kyle.gpx` | sample GPS track | sample | keep |
| `JGB19333.pdf` | unknown PDF | no | **ask Gian**; gitignored meanwhile, untouched |
| `data/`, `runs/`, `VID+GPX/`, `RDD2022_raw/`, `pothole_dataset/`, `.oculubak/`, `.venv/`, `yolo26n.pt`, `yolov8m.pt` | data, runs, footage, envs, base weights | yes | already gitignored, stay on disk |

## Checks

| Check | Result |
|---|---|
| Duplicate/versioned copies (`_old`, `copy`, `final_final`) | none. `runs_v2.py`, `pipeline_v2.py`, `training_plan_v2.md` are the current versions, not copies |
| Syntax (`py_compile` on every tracked .py) | all pass |
| Missing imports | none in `.venv` (`jwt`, `gpxpy`, `transformers` are only missing from the system Python) |
| Functions defined twice / half-applied edits | none found |
| Hard-coded absolute paths (`C:\Users…`) in code | none; scripts use `ROOT = Path(__file__)…` |
| Secrets in code | none. `SECRET_KEY` already comes from env / gitignored `backend/.secret_key` |
| Large files tracked | none outside Git LFS |

## Changes made on `cleanup`

- `.gitignore`: `results/*.jpg`, `JGB19333.pdf`, `yolo-rdd2022/*.pt`, `__pycache__/`; annotation
  additions (`labels.db*`, `backups/`, `.env`) come with the annotation site commit.
- Nothing moved, nothing deleted. Protected files (§0.5) untouched.

## Verification (§0.6)

- `ml/local/check_counts.py`: 1,066 frames, 609 boxes, per split/class identical to
  `results/local_datasets_nz.md`. Test hash (file names + label contents) baseline:
  `f35382d3d92b5c65e01c2924ce5791518b223690508763ba0fbd12fe4ea7140c`.
- Backend boots (`create_app`, migration), admin login and `/api/dashboard/stats` return 200.
- `CLAUDE.md` training paragraph updated for the §9 decision; `README.md` has a current run table.

## Open

- A training queue is configured in `runs/queue.txt` (Step 5: `S5_v8m_1920`, `S5_v12s_1024`).
  Pre-labeling (§5) needs the GPU; check that queue is not running before starting it.
