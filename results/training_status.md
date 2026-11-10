# Training status  (**ALERT**)

Updated Tue 2026-11-10 15:33 by tools/watch_training.py (every 5 min).

**Check schedule for the team**
- Right after each run starts: confirm the first-epoch sanity check passed (ask Claude Code to "check").
- Every 1-2 hours while awake: open this file, or ask Claude Code to "check".
- Before going to bed on Tuesday: the final run is alive, has no alerts, and its ETA is before Wednesday 6 AM.
- First thing Wednesday morning: check it finished, then continue to Step 6.3.

**What to do on an alert** (never restart a run from scratch if last.pt exists; re-running its
start line resumes it)
| Alert | Action |
|---|---|
| Crash or out-of-memory | Resume from last.pt with a smaller batch: same start line plus `--batch 4` |
| NaN loss | Resume with `--set amp=False lr0=<half the current lr0>` |
| Overheating (GPU > 85 C) | Stop the run, check the PC's airflow (side panel, dust, room), resume |
| Low RAM | Close other apps; the watcher lowers workers to 4 by itself at 85%; else resume with `--workers 2` |
| Stuck (no new epoch) | Stop the run (Task Manager: python.exe running train_run.py) and resume from last.pt |
| No improvement for 5 epochs | Normal; early stopping is near. Nothing to do |

## This PC

- GPU: 0% busy, 439 / 8188 MiB memory, 53 C
- RAM: 63% used (10.0 / 15.9 GB)
- Free disk: 127 GB

## Runs

### v3/S5_v8m_1920  **ALERT**

- State: NOT RUNNING
- Epoch 10 / 40; elapsed 1:42:28; usual epoch 7.3 min; time left to the last epoch 3:40:30 (finish about Tue 19:13); earliest possible early stop in 0:58:48
- Settings: imgsz 1920, batch 2, patience 10, data runs/v3/S5_v8m_1920/data/B.yaml
- Latest train losses: box 1.6914, cls 2.1404, dfl 1.8323
- Latest val: P 0.208, R 0.191, mAP@50 0.148; AP@50 D00 0.303, D10 0.106, D20 0.005, D40 0.178
- Best so far: epoch 8, mAP@50 0.216; AP@50 D00 0.372, D10 0.217, D20 0.003, D40 0.272
- **ALERT: process has died (not finished) after an error in the log**

### v3/S5_v8m_1280

- State: finished 2026-11-10T13:50:09
- Epoch 18 / 40; elapsed 0:43:37
- Settings: imgsz 1280, batch 4, patience 10, data runs/v3/S5_v8m_1280/data/B.yaml
- Latest train losses: box 1.4662, cls 1.5631, dfl 1.5914
- Latest val: P 0.212, R 0.240, mAP@50 0.185; AP@50 D00 0.350, D10 0.218, D20 0.012, D40 0.161
- Best so far: epoch 10, mAP@50 0.189; AP@50 D00 0.396, D10 0.140, D20 0.012, D40 0.210

### v2/Bv2

- State: finished 2026-11-10T11:46:46
- Epoch 26 / 40; elapsed 1:02:18
- Settings: imgsz 1280, batch 4, patience 10, data runs/v2/Bv2/data/B.yaml
- Latest train losses: box 1.5824, cls 1.9069, dfl 1.7229
- Latest val: P 0.205, R 0.212, mAP@50 0.168; AP@50 D00 0.275, D10 0.143, D20 0.016, D40 0.239
- Best so far: epoch 22, mAP@50 0.169; AP@50 D00 0.330, D10 0.141, D20 0.021, D40 0.185

### v2/A

- State: finished 2026-11-10T08:18:54
- Epoch 26 / 40; elapsed 0:18:04
- Settings: imgsz 1280, batch 4, patience 10, data runs/v2/A/data/A.yaml
- Latest train losses: box 1.6123, cls 1.9819, dfl 1.5419
- Latest val: P 0.706, R 0.096, mAP@50 0.100; AP@50 D00 0.305, D10 0.031, D20 0.003, D40 0.062
- Best so far: epoch 24, mAP@50 0.117; AP@50 D00 0.319, D10 0.028, D20 0.001, D40 0.120

### v2/Bv1

- State: finished 2026-11-10T07:56:51
- Epoch 26 / 40; elapsed 0:54:04
- Settings: imgsz 1280, batch 4, patience 10, data runs/v2/Bv1/data/B.yaml
- Latest train losses: box 1.5749, cls 1.8169, dfl 1.7519
- Latest val: P 0.177, R 0.232, mAP@50 0.133; AP@50 D00 0.239, D10 0.108, D20 0.025, D40 0.158
- Best so far: epoch 16, mAP@50 0.134; AP@50 D00 0.239, D10 0.108, D20 0.025, D40 0.165

### teacher/teacher

- State: finished 2026-11-09T21:28:38
- Epoch 30 / 30; elapsed 2:58:07
- Settings: imgsz 960, batch 6, patience 8, data data/rdd2022/teacher/data.yaml
- Latest train losses: box 1.5490, cls 1.5712, dfl 1.6688
- Latest val: P 0.533, R 0.492, mAP@50 0.480; AP@50 D00 0.545, D10 0.463, D20 0.506, D40 0.405
- Best so far: epoch 30, mAP@50 0.480; AP@50 D00 0.545, D10 0.463, D20 0.506, D40 0.405

## Recent watcher actions

- 2026-11-09 18:31:33 runs\teacher\teacher: RAM above 85%: stopped and resumed from last.pt with workers=4
- 2026-11-09 19:03:38 runs\teacher\teacher: RAM 97% (12 loader processes, commit 54/58 GB): stopped by Claude Code, resuming with workers=2
