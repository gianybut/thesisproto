# Pretrained road-damage checkpoints (step 3, 2026-11-10)

Downloaded with `huggingface_hub` into `data/pretrained/<owner>__<repo>/` (gitignored). Before
anything was loaded, every pickle inside each `.pt` was listed opcode by opcode without executing it
(`pickletools`): all four import only `torch`, `ultralytics`, `collections` and `set`. Every class
they reference exists in the installed Ultralytics 8.4.48.

| Checkpoint | Source (Hugging Face) | Revision | License | Architecture | Trained with | Classes (index order) | Reported metrics |
|---|---|---|---|---|---|---|---|
| YOLOv12m | https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark, file `yolo-rdd2022-benchmark/yolo12m_seed0_best.pt` | 6bec4bbcf7 (2026-04-24) | CC BY 4.0 | yolov12m.yaml, 4 classes | Ultralytics 8.4.24, 2026-03-22; 640 px, 100 epochs, batch 64, optimizer auto, seed 0 | longitudinal_crack, transverse_crack, alligator_crack, pothole | RDD2022 global val mAP@50 0.6325 (seed 0); mean of 7 country partitions 0.4752 |
| YOLOv12s | same repository, `yolo-rdd2022-benchmark/yolo12s_seed0_best.pt` | 6bec4bbcf7 | CC BY 4.0 | yolov12s.yaml, 4 classes | Ultralytics 8.4.24, 2026-03-21; 640 px, 100 epochs, batch 64, seed 0 | as above | global val mAP@50 0.6192 (seed 0; 3-seed mean 0.6162); 7-partition mean 0.4763 |
| YOLOv8m | https://huggingface.co/dronefreak/rdd2022-yolov8m, file `best.pt` | 40684513b3 (2026-10-01) | AGPL-3.0 | YOLOv8m, 4 classes, 25.9 M parameters | Ultralytics 8.4.153, 2026-09-19 (DetectionBench); 640 px, 50 epochs, batch 16, Adam lr0 0.001, seed 0 | longitudinal_crack, transverse_crack, alligator_crack, pothole | RDD2022 own 15% test split: mAP@50 0.6203, mAP@50-95 0.3408, P 0.6561, R 0.5742; per class AP@50 0.5597 / 0.5552 / 0.6250 / 0.7415 |
| Teacher (ours, reference) | `runs/teacher/teacher/weights/best.pt` | 2026-11-09 | ours | YOLOv8m, 4 classes | Ultralytics 8.4.48; six-country RDD2022 (our split), 960 px, 30 epochs, batch 6 | D00, D10, D20, D40 | our foreign val mAP@50 0.472 (results/teacher_foreign_val.md) |

**Class mapping.** All four use the CRDDC 2022 order, so index i maps directly: longitudinal_crack ->
D00, transverse_crack -> D10, alligator_crack -> D20, pothole -> D40. Nothing is dropped. Fine-tuned
models take the names D00-D40 from our data file.

**Caveats for Chapter III/V.**
- The reported metrics are each author's own splits at 640 px; they are not comparable with each
  other or with ours. SreekarAditya's RDD2022 copy includes China (Drone), which ours does not.
- Both external models were trained on RDD2022 images that very likely include images of OUR
  six-country foreign val and test splits (random 15% slices of the same public data). A foreign
  val/test score of a model fine-tuned from them is therefore not a held-out result. The local
  val/test sets (our own recordings) are unaffected.
- Licenses: CC BY 4.0 requires attribution (cite the repository and RDD2022). AGPL-3.0 (dronefreak;
  also Ultralytics itself) applies to distribution of the weights/software, including over a network.
- The RDD2022 images are CC BY-SA 4.0 (dronefreak model card).

**Loading.** A full load (unpickling) of the downloaded files was stopped by the permission check
on 2026-11-10 ~12:30 and waits for the team's go-ahead; status of each checkpoint in the zero-shot
table below once evaluated.
