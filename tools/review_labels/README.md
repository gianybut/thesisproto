# Label review

All frames are reviewed by one person, Gian Paolo Ybut (team decision 2026-11-10).

Batches: 1 (240 val/test frames, done), 2 (300 val/test frames), "train" (376 train frames with the
teacher's boxes as drafts) and, later, "AL" (about 150 train frames chosen with model B v1).

## Start

```powershell
powershell -ExecutionPolicy Bypass -File tools\start_review.ps1          # this computer only
powershell -ExecutionPolicy Bypass -File tools\start_review.ps1 -Lan     # other laptops on the same Wi-Fi
```

Open http://127.0.0.1:8770 and choose your name at the top (there is no default; nothing saves
without it). Everything saves as you go.

## Views

1. **To review**: batch 2 (val first, then test), then the train batch, then the AL batch. Training
   starts by itself as soon as batch-2 val and the whole train batch are reviewed; it does not wait
   for batch-2 test or the self-check.
2. **Self-check**: test frames of batches 1 and 2 that were accepted as "no damage". Look again, fix
   anything missed, press Enter (also when nothing changed). The log records self_check_done and
   self_check_changed. Changes here only affect the final test evaluation, not training.

## Keys

| Key | What it does |
|---|---|
| Enter | Accept the frame as it is now, go to the next one |
| Click a box, then Delete | Remove the box |
| Click a box, then 1 / 2 / 3 / 4 | Set it to D00 / D10 / D20 / D40 |
| Drag | Draw a new box, then press 1-4 for its class |
| B | No damage in this frame (removes all boxes) |
| ← / → | Previous / next frame |
| Mouse wheel, right-drag, 0 | Zoom, pan, reset zoom |

**Rubric.** Draw any damage the drafts missed, especially cracks. Patches/repairs are not damage
unless they contain an actual pothole or crack.

**Boxes.** One tight box per continuous crack (D00 along the road, D10 across it). D20: one box
around the whole cracked area. D40: the box follows the edge of the hole. Patches are not damage.
Examples: "See 8 box examples" in the tool.
