# Example val predictions of v1 (threshold 0.24, app-style input)

White thin box = label; thick box = prediction in its class colour; X = a prediction with no matching label of its class (false alarm). Images in `results/v1_examples/` (gitignored: footage).

Frames where every label was found with no false alarm: 20 of 1,624. Frames with a missed D20 label: 40 (of the 51 D20 boxes, 44 missed; 2 of those found as another class).

| Image | Frame | Set | Kind |
|---|---|---|---|
| good_1.jpg | R05_s0503 | site | all labels found |
| good_2.jpg | R05_s0509 | site | all labels found |
| good_3.jpg | R05_s0450 | site | all labels found |
| good_4.jpg | R05_s0339 | reviewed | all labels found |
| d20_fail_1.jpg | R05_s0352 | site | 1 D20 missed |
| d20_fail_2.jpg | R05_s0505 | site | 1 D20 missed |
| d20_fail_3.jpg | R05_s0142 | reviewed | 1 D20 missed |
| d20_fail_4.jpg | R05_s0148 | site | 1 D20 missed |
