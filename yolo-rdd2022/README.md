---
license: cc-by-4.0
pipeline_tag: object-detection
base_model:
  - ultralytics/ultralytics
tags:
  - object-detection
  - road-damage-detection
  - yolo
  - benchmark
  - rdd2022
datasets:
  - sreekaraditya/rdd2022-yolo-crackscan-v2
model-index:
- name: YOLOv12s-RDD2022
  results:
  - task:
      type: object-detection
    dataset:
      name: RDD2022
      type: sreekaraditya/rdd2022-yolo-crackscan-v2
    metrics:
    - type: map50
      value: 0.4763
      name: Mean mAP50 (7 country partitions)
    - type: map50
      value: 0.6162
      name: Global Val mAP50 (3-seed mean)
- name: YOLOv12m-RDD2022
  results:
  - task:
      type: object-detection
    dataset:
      name: RDD2022
      type: sreekaraditya/rdd2022-yolo-crackscan-v2
    metrics:
    - type: map50
      value: 0.4752
      name: Mean mAP50 (7 country partitions)
    - type: map50
      value: 0.6325
      name: Global Val mAP50 (seed 0)
---

# YOLO × RDD2022 Benchmark

A systematic benchmark of **8 YOLO variants** (YOLOv5s through YOLOv12m) on the [Road Damage Detection 2022 (RDD2022)](https://github.com/sekilab/RoadDamageDetector) dataset, evaluated across **7 country partitions** with full multi-seed replication and statistical significance testing.

This repository hosts the trained model weights (`best.pt`) for all benchmark runs.

**Code & Scripts:** [github.com/SreekarAditya/yolo-rdd2022-benchmark](https://github.com/SreekarAditya/yolo-rdd2022-benchmark)

---

## Benchmark Summary

| Model | Mean mAP50 | 3-Seed Mean | 3-Seed Std | Friedman Rank |
|---|---|---|---|---|
| YOLOv12m | 0.4752 | — | — | 2.29 |
| **YOLOv12s** | **0.4763** | **0.6162** | 0.0028 | **2.14** |
| YOLOv9s | 0.4580 | 0.6142 | 0.0019 | 4.86 |
| YOLOv8s | 0.4643 | 0.5995 | 0.0015 | 3.43 |
| YOLOv11s | 0.4509 | 0.6042 | 0.0009 | 4.71 |
| YOLOv5s | 0.4480 | 0.5938 | 0.0030 | 5.14 |
| YOLOv10s† | 0.4253 | 0.5713 | 0.0015 | 6.57 |
| YOLOv12n | 0.4222 | — | — | 6.86 |

> † YOLOv10s evaluated with its default NMS-free head. Applying standard NMS post-processing recovers +5.43 mAP50 points (0.5694 → 0.6193), making it competitive with YOLOv9s.
>
> Mean mAP50 = average across 7 country partitions. 3-Seed Mean/Std = global val mAP50 across seeds 0, 42, 123 (YOLOv12m and YOLOv12n have seed 0 only).

---

## Dataset

**RDD2022** covers road damage images from 7 geographic partitions with 4 damage classes:

| Class | Code | Description |
|---|---|---|
| 0 | D00 | Longitudinal Crack |
| 1 | D10 | Transverse Crack |
| 2 | D20 | Alligator / Fatigue Crack |
| 3 | D40 | Pothole |

### Country Partition Statistics

| Country | Total Annotations | Dominant Class | Notes |
|---|---|---|---|
| Japan | 2,465 | D20 (37.65%) | Largest; most balanced |
| Norway | 1,697 | D00 (77.49%) | Hardest partition; extreme D00 dominance |
| US | 1,675 | D00 (61.55%) | D40-sparse (1.67%) |
| India | 1,079 | D40 (48.56%) | Near-zero D10 (0.74%) |
| China (Motorbike) | 684 | D00 (57.16%) | Ground-level viewpoint |
| China (Drone) | 486 | D00 (48.15%) | Aerial viewpoint |
| Czech | 241 | D00 (54.77%) | Smallest partition |

---

## Results by Country Partition

### mAP50

| Model | Japan | India | Czech | Norway | US | China MB | China Drone | **Mean** |
|---|---|---|---|---|---|---|---|---|
| YOLOv5s | 0.4409 | 0.2611 | 0.2772 | 0.2207 | 0.5144 | 0.8799 | 0.5415 | 0.4480 |
| YOLOv8s | 0.4549 | 0.3096 | 0.2988 | 0.2188 | 0.5440 | 0.9030 | 0.5211 | 0.4643 |
| YOLOv9s | 0.4735 | 0.2711 | 0.2552 | 0.2173 | 0.5510 | 0.8866 | 0.5510 | 0.4580 |
| YOLOv10s | 0.4284 | 0.2681 | 0.2680 | 0.1612 | 0.4769 | 0.8871 | 0.4874 | 0.4253 |
| YOLOv11s | 0.4397 | 0.2662 | 0.2741 | 0.1928 | 0.5197 | 0.9024 | 0.5612 | 0.4509 |
| YOLOv12n | 0.4244 | 0.2461 | 0.1977 | 0.1603 | 0.4794 | 0.8917 | 0.5558 | 0.4222 |
| **YOLOv12s** | 0.4767 | 0.2808 | 0.2738 | 0.2197 | 0.5514 | **0.9265** | **0.6053** | **0.4763** |
| **YOLOv12m** | **0.4975** | 0.2798 | 0.2597 | **0.2462** | **0.5570** | 0.9069 | 0.5795 | 0.4752 |

### F1 (at Optimal Confidence Threshold)

| Model | Japan | India | Czech | Norway | US | China MB | China Drone | Optimal Conf | Peak F1 |
|---|---|---|---|---|---|---|---|---|---|
| YOLOv5s | 0.5846 | 0.3790 | 0.4456 | 0.3724 | 0.6591 | 0.8970 | 0.6457 | 0.20 | 0.6105 |
| YOLOv8s | 0.5937 | 0.4530 | 0.4449 | 0.3740 | 0.6475 | 0.9035 | 0.6472 | 0.10 | 0.6124 |
| YOLOv9s | 0.5959 | 0.3854 | 0.4037 | 0.3676 | 0.6550 | 0.8976 | 0.6635 | 0.20 | 0.6146 |
| YOLOv10s | 0.5570 | 0.3742 | 0.4238 | 0.2802 | 0.5976 | 0.8486 | 0.5898 | 0.10 | 0.5712 |
| YOLOv11s | 0.5808 | 0.3841 | 0.4093 | 0.3473 | 0.6465 | 0.9079 | 0.6773 | 0.20 | 0.6117 |
| YOLOv12n | 0.5669 | 0.3695 | 0.3377 | 0.2935 | 0.5853 | 0.8932 | 0.6822 | 0.10 | 0.5995 |
| YOLOv12s | 0.5941 | 0.3924 | 0.4262 | 0.3709 | 0.6405 | 0.9159 | 0.7148 | 0.10 | 0.6182 |
| **YOLOv12m** | **0.6149** | 0.3970 | 0.3982 | **0.4060** | **0.6611** | 0.9110 | 0.6765 | 0.10 | **0.6280** |

> All optimal confidence thresholds cluster at 0.10–0.20, well below the YOLO default of 0.25. Using default conf=0.25 reduces F1 for most models.

---

## Statistical Analysis

**Test:** Friedman + Nemenyi post-hoc (α = 0.05), N = 7 country partitions, k = 8 YOLO variants.  
**Critical Difference = 3.97** (Demšar 2006).

### Mean Ranks (lower = better)

| Rank | Model | Mean Rank |
|---|---|---|
| 1 | YOLOv12s | 2.14 |
| 2 | YOLOv12m | 2.29 |
| 3 | YOLOv8s | 3.43 |
| 4 | YOLOv11s | 4.71 |
| 5 | YOLOv9s | 4.86 |
| 6 | YOLOv5s | 5.14 |
| 7 | YOLOv10s | 6.57 |
| 8 | YOLOv12n | 6.86 |

### Significant Pairwise Differences (Nemenyi, p < 0.05)

| Pair | p-value |
|---|---|
| YOLOv12s vs YOLOv10s | 0.008 |
| YOLOv12s vs YOLOv12n | 0.011 |
| YOLOv12m vs YOLOv10s | 0.017 |
| YOLOv12m vs YOLOv12n | 0.024 |

YOLOv12s and YOLOv12m are statistically indistinguishable from each other and from YOLOv8s/YOLOv9s. Only separation from YOLOv10s and YOLOv12n reaches significance.

---

## Seed Replication & Stability

Multi-seed replication (seeds 0, 42, 123) was run for 6 of the 8 models. YOLOv12m and YOLOv12n have seed 0 only.

| Model | Seed 0 | Seed 42 | Seed 123 | 3-Seed Mean | 3-Seed Std |
|---|---|---|---|---|---|
| YOLOv5s | 0.5977 | 0.5931 | 0.5905 | 0.5938 | 0.0030 |
| YOLOv8s | 0.6017 | 0.5985 | 0.5983 | 0.5995 | 0.0015 |
| YOLOv9s | 0.6159 | 0.6115 | 0.6153 | 0.6142 | 0.0019 |
| YOLOv10s | 0.5694 | 0.5729 | 0.5716 | 0.5713 | 0.0015 |
| YOLOv11s | 0.6045 | 0.6030 | 0.6050 | 0.6042 | 0.0009 |
| YOLOv12s | 0.6192 | 0.6169 | 0.6125 | 0.6162 | 0.0028 |
| YOLOv12m | 0.6325 | — | — | — | — |
| YOLOv12n | 0.5827 | — | — | — | — |

Maximum inter-seed std is 0.0030 (YOLOv5s). The 15× ratio of architectural spread to max seed variance confirms that model rankings are robust to seed choice for all pairs except YOLOv9s vs YOLOv12s (Δ = 0.0020, ~0.7σ — genuinely ambiguous).

---

## Resolution Ablation (YOLOv12s)

| Resolution | Best mAP50 | Best Epoch | Best mAP50-95 | Precision | Recall |
|---|---|---|---|---|---|
| 480px | 0.5822 | 82 | 0.2962 | 0.6494 | 0.5388 |
| **640px** (default) | **0.6192** | **74** | **0.3215** | **0.6595** | **0.5677** |
| 800px | 0.6259 | 66 | 0.3286 | 0.6582 | 0.5816 |

800px yields +4.37 mAP50 points over 480px and converges faster (epoch 66 vs 82). All benchmark results use the default 640px unless otherwise noted.

---

## Per-Class AP50 — Hardest Partitions (YOLOv12s)

### Norway

| Class | Name | AP50 | Dataset % |
|---|---|---|---|
| D00 | Longitudinal Crack | 0.2708 | 77.49% |
| D10 | Transverse Crack | 0.1689 | 16.03% |
| D20 | Alligator Crack | 0.3619 | 3.01% |
| D40 | Pothole | 0.0773 | 3.48% |

### India

| Class | Name | AP50 | Dataset % |
|---|---|---|---|
| D00 | Longitudinal Crack | 0.2936 | 20.85% |
| D10 | Transverse Crack | **0.0000** | 0.74% |
| D20 | Alligator Crack | 0.4737 | 29.84% |
| D40 | Pothole | 0.3557 | 48.56% |

India D10 is completely undetected (only 8 instances in the partition). Norway D40 (pothole) is near-zero despite being a safety-critical class.

---

## India Fine-Tuning Experiment

Starting from the global YOLOv12s checkpoint, fine-tuning on a fraction of India-labeled data was tested across 3 seeds and 3 data percentages.

| Subset | India mAP50 | Japan mAP50 | US mAP50 |
|---|---|---|---|
| Baseline (no FT) | 0.2808 | 0.4767 | 0.5514 |
| 10% (mean) | **0.2906** | 0.4790 | 0.5446 |
| 15% (mean) | 0.2790 | 0.4687 | 0.5440 |
| 20% (mean) | 0.2651 | 0.4541 | 0.5346 |

Fine-tuning on 10% India data yields a marginal +0.98 pp gain on India mAP50, but increasing the fine-tune fraction past 10% causes degradation — both on India (overfitting) and on other partitions (catastrophic forgetting).

---

## Model Weights

All `best.pt` files are available in the Files tab. File naming convention:

```
{model}_seed{seed}_best.pt              # e.g. yolov12s_seed0_best.pt
{model}_seed{seed}_best.pt              # e.g. yolov8s_seed42_best.pt
yolov12s_480px_seed0_best.pt            # resolution ablation
yolov12s_800px_seed0_best.pt            # resolution ablation
india_ft_{pct}pct_seed{seed}_best.pt    # India fine-tune variants
```

---

## Reproduction

### Requirements

```bash
pip install ultralytics
```

For YOLOv9, install the [WongKinYiu/yolov9](https://github.com/WongKinYiu/yolov9) fork. All other models use the `ultralytics` package.

### Dataset Setup

Download RDD2022 from the [official source](https://github.com/sekilab/RoadDamageDetector) and structure it as:

```
rdd2022/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

Create a `rdd2022.yaml` data config pointing to your local paths.

### Training

```python
from ultralytics import YOLO

model = YOLO("yolov12s.pt")  # pretrained backbone — downloaded automatically by Ultralytics on first run
model.train(
    data="rdd2022.yaml",
    epochs=100,
    imgsz=640,
    seed=0,
    optimizer="auto",
)
```

### Evaluation

```python
model = YOLO("yolov12s_seed0_best.pt")  # load from this repo
metrics = model.val(data="rdd2022.yaml", imgsz=640, conf=0.10)
print(metrics.box.map50)
```

> Use `conf=0.10` for optimal F1 (see F1 sweep results). Default `conf=0.25` underperforms for this dataset.

### YOLOv10s NMS Patch

YOLOv10s uses an NMS-free detection head by default. To reproduce the patched results (+5.43 mAP50):

```python
from ultralytics import YOLO
model = YOLO("yolov10s_seed0_best.pt")
# Enable standard NMS post-processing
metrics = model.val(data="rdd2022.yaml", conf=0.10, iou=0.45, agnostic_nms=False)
```

---

## Key Findings

- **YOLOv12s ranks #1** by Friedman mean rank (2.14) but is statistically indistinguishable from YOLOv12m and the YOLOv8s/YOLOv9s cluster.
- **Norway is the hardest partition** across all models (max mAP50 = 0.2462 by YOLOv12m). Maximum achievable recall on Norway is only 0.6577 even at confidence threshold = 0 — a structural detection ceiling likely driven by extreme class imbalance (77.5% D00) and challenging imaging conditions.
- **China (Motorbike) is the easiest partition** (all models > 0.88 mAP50). The 70.7 pp spread between hardest and easiest partition is 15.8× the inter-model spread, meaning dataset difficulty dominates architecture choice.
- **YOLOv10s significantly underperforms** due to its NMS-free head in standard evaluation. With standard NMS applied, it becomes competitive (+5.43 mAP50 points).
- **YOLOv12n is the weakest model** and the only v12 variant that fails to improve over the v5/v8/v11 generation.
- **Optimal confidence for this dataset is 0.10–0.20**, not the YOLO default of 0.25.
- **India fine-tuning yields diminishing returns**: 10% data gives a marginal +1 pp gain; more data causes catastrophic forgetting.

---

## Training Configuration

| Parameter | Value |
|---|---|
| Epochs | 100 |
| Image size | 640px (default) |
| Optimizer | auto |
| Seeds | 0, 42, 123 |
| Framework | Ultralytics |
| YOLOv10s NMS | Default NMS-free (patch available) |

---

## Citation

If you use these weights or results, please cite the RDD2022 dataset:

```bibtex
@article{arya2022rdd2022,
  title={RDD2022: A multi-national image dataset for automatic Road Damage Detection},
  author={Arya, Deeksha and Maeda, Hiroya and Ghosh, Sanjay Kumar and Toshniwal, Durga and Mraz, Alexander and Kashiyama, Takehiro and Sekimoto, Yoshihide},
  journal={arXiv preprint arXiv:2209.08538},
  year={2022}
}
```

---

## License

Model weights and benchmark data are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
