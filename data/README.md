# data/: OcuLubak dataset (local only)

> **The data files are not in this repository.** The `data/` folder is 12.6 GB (117,624 files) and holds
> frames taken from the team's road survey videos. It is stored
> on the team's training PC and listed in `.gitignore`. Only this README is pushed, so that the folder
> structure, split sizes and label counts can be checked without the images.
>
> Counts and sizes below were measured on the training PC on 2026-11-17.

## Where the data comes from

| Source | What it is | Where it is kept |
|---|---|---|
| Team survey recordings | 18 phone videos with a GPX track each, recorded from a mounted phone (R04-R21), 78.3 km of road, 162.8 min in total, Cavite (Mendez, Alfonso, Indang, Tagaytay). R01-R03 were hand-held and are excluded. | `VID+GPX/` at the repo root (18 `.mov` + 18 `.gpx`, 8.1 GB, local only) |
| RDD2022 (CRDDC 2022) | Public road damage dataset (Arya et al.), six countries, used for the teacher model and the foreign test | `data/rdd2022/` |
| Pretrained weights | Two public YOLOv8 RDD2022 checkpoints used as starting points (see `results/pretrained_sources.md`) | `data/pretrained/` |

Damage classes (RDD2022 codes, YOLO index order): `0 D00` longitudinal crack, `1 D10` transverse crack,
`2 D20` alligator crack, `3 D40` pothole.

## Folder tree

```
data/                                          117,624 files   12.6 GB
├── local/                                      73,853 files   10.4 GB   team dataset (R04-R21)
│   ├── recordings.csv                                                   one row per recording: video, GPX, mount, duration, route km, road band, status
│   ├── route_groups.csv / route_groups.html                             recordings grouped into 15 route groups (G01-G15); the split is by group
│   ├── route_overlap.csv                                                where routes of different groups overlap
│   ├── splits.csv                                                       9,590 frames: split, route group, distance to nearest train frame
│   ├── manifest.csv / frames_all.csv                                    kept frames / every second with the reason a frame was dropped
│   ├── near_zone_bands.csv                                              near-zone crop per recording
│   ├── review_log.csv, review_frames.csv, review_events.csv, ...        label review records
│   │
│   ├── frames/                                  9,590 .jpg     2.6 GB   1 frame/s, upright, cropped to the road band
│   ├── frames_full/                             9,590 .jpg     3.7 GB   same frames, whole picture (input of the CLIP check)
│   ├── frames_nz/                               9,590 .jpg     1.9 GB   same frames, near-zone crop (the training images)
│   ├── autolabels/                              9,590 .txt    24 KB     draft boxes from the teacher model (never used as ground truth)
│   ├── autolabel_parts/                            18 .csv     72 KB     draft-label log per recording
│   │
│   ├── reviewed/                                2,132 files  650 KB     human-reviewed labels (single reviewer)
│   │   ├── labels/                              1,066 .txt              YOLO boxes
│   │   └── state/                               1,066 .json             review state per frame
│   ├── annotate/                               12,809 files  377 MB     shared annotation site
│   │   ├── cache/                               6,400 .jpg              images served to annotators
│   │   └── prelabels/                           6,400 .txt              pre-filled boxes shown to annotators
│   │
│   ├── yolo_nz/                                14,948 files   1.4 GB   ★ dataset used for the deployed models (near zone, human labels only)
│   │   ├── images/train/                        5,571 .jpg     1.0 GB
│   │   ├── images/val/                          1,624 .jpg     307 MB
│   │   ├── images/test/                           270 .jpg      73 MB
│   │   ├── labels/{train,val,test}/             7,465 .txt              one YOLO label file per image
│   │   ├── *.txt                                                        image lists (see table below)
│   │   └── *.yaml                                                       Ultralytics dataset files (A, B_noreplay, v1, val, val_reviewed, test, ...)
│   ├── yolo/                                    2,145 files  297 MB     earlier version (reviewed frames only, road-band crop)
│   │   ├── images/{train,val,test}/        526 / 270 / 270 .jpg
│   │   └── labels/{train,val,test}/        526 / 270 / 270 .txt
│   │
│   ├── classification/                          3,162 files   25 MB     box crops per class for the damage classifier
│   │   ├── train/{D00,D10,D20,D40}/   1,450 / 556 / 152 / 779 .jpg
│   │   ├── val/{D00,D10,D20,D40}/        30 /  23 /  17 /  52 .jpg
│   │   └── test/{D00,D10,D20,D40}/       36 /   8 /  34 /  21 .jpg
│   │
│   ├── teacher/, teacher_dets/                     10 files  1.2 MB     teacher-model detections and fitted label thresholds
│   ├── system_eval/                                14 .json   1.9 MB     system-level evaluation outputs
│   ├── validation_sheet/                            8 files   14 MB     expert validation sheet (40 boxes) and certification letter
│   ├── annotation_form/                           102 files   25 MB     100-image sample for the expert agreement check (+ answer key)
│   ├── spotcheck/                                 101 files   11 MB     100 frames + HTML page for a visual spot check
│   ├── contact/, band_check/                       20 .jpg    7.4 MB     contact sheets and road-band check images
│   └── logs/                                        8 .log    111 KB     extraction / labelling logs
│
├── rdd2022/                                    43,753 files   2.1 GB   RDD2022, four classes kept
│   ├── images/                                 21,848 .jpg     2.1 GB
│   │   ├── China_MotorBike/                     1,934         143 MB
│   │   ├── Czech/                               1,072          74 MB
│   │   ├── India/                               3,223         204 MB
│   │   ├── Japan/                               7,900         608 MB
│   │   ├── Norway/                              2,914         816 MB
│   │   └── United_States/                       4,805         342 MB
│   ├── labels/<same six countries>/            21,848 .txt    2.7 MB   YOLO boxes
│   ├── lists/                                      18 .txt    1.8 MB   train/val image lists
│   ├── eval/                                       28 files   1.1 MB   foreign test lists and yamls
│   └── teacher/                                     5 files   836 KB   teacher-model training lists
│
└── pretrained/                                     18 files   107 MB   public RDD2022 YOLOv8 checkpoints
    ├── dronefreak__rdd2022-yolov8m/                 9 files    50 MB
    └── SreekarAditya__yolo-rdd2022-benchmark/       9 files    57 MB
```

## How the frames were split

1. One frame per second was taken from each of the 18 recordings, and near-duplicate frames (car
   standing still) were dropped: **9,590 frames**.
2. Recordings were grouped into 15 route groups, and whole groups were assigned to train, val or test,
   so the same stretch of road never appears in two splits: 6,103 train, 1,736 val, 1,751 test frames
   (`splits.csv`).
3. Val and test frames within 50 m of any train frame were dropped.
4. Only human-reviewed labels are used. The teacher model's draft boxes (`autolabels/`) are never
   ground truth.

## Splits used for training and evaluation (`local/yolo_nz/`)

| List | Images | No damage | D00 | D10 | D20 | D40 | Boxes | Used for |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `local_train.txt` | 5,571 | 4,044 | 1,450 | 556 | 152 | 779 | 2,937 | all labelled train frames |
| `v1_train.txt` | 3,027 unique (4,783 per epoch) | 1,500 | 1,450 | 556 | 152 | 779 | 2,937 | training list of the deployed models (v1, v2b, v3; empty frames sub-sampled, rare classes repeated) |
| `val.txt` | 1,624 | 1,314 | 214 | 150 | 51 | 244 | 659 | validation during training |
| `val_reviewed.txt` | 270 | 207 | 30 | 23 | 17 | 52 | 122 | subset of val reviewed by one person; used to choose the final model and the confidence threshold |
| `test.txt` | 270 | 207 | 36 | 8 | 34 | 21 | 99 | held-out test set, evaluated once (`results/test_evaluation.md`) |

To check these numbers again on the training PC, run `python ml/local/check_counts.py`.

## Rebuilding the folder

The scripts that produce `data/local/` are in `ml/local/` and run in this order: `ingest_local.py` →
`route_groups.py` → `extract_frames.py` → `autolabel.py` → `split_local.py` → (review in
`tools/review_labels/`) → `build_local_yolo.py`. They need the original recordings in `VID+GPX/`.
`ml/download_rdd2022.py` fetches RDD2022 into `data/rdd2022/`.
