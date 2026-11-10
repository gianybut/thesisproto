# Local frame quality

Extractor: band crop written with `cv2.imwrite(..., [cv2.IMWRITE_JPEG_QUALITY, 95])`, no resize.

## 1. Size and JPEG quality, 5 random frames per split

| Split | Frame | Saved size | Video frame | Band | Expected crop | File KB | JPEG quality (from the file) |
|---|---|---|---|---|---|---|---|
| train | R08_s0473.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 232 | 95 |
| train | R04_s0450.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 356 | 95 |
| train | R13_s0073.jpg | 1920x378 | 1920x1080 | 0.45-0.80 | 1920x378 | 198 | 95 |
| train | R12_s0062.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 281 | 95 |
| train | R11_s0365.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 252 | 95 |
| val | R05_s0354.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 223 | 95 |
| val | R05_s0274.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 289 | 95 |
| val | R05_s0232.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 265 | 95 |
| val | R16_s0176.jpg | 1920x465 | 1920x1080 | 0.44-0.87 | 1920x465 | 239 | 95 |
| val | R05_s0119.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 321 | 95 |
| test | R06_s0089.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 303 | 95 |
| test | R06_s0226.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 323 | 95 |
| test | R06_s0586.jpg | 1920x540 | 1920x1080 | 0.50-1.00 | 1920x540 | 295 | 95 |
| test | R19_s0076.jpg | 1920x465 | 1920x1080 | 0.44-0.87 | 1920x465 | 238 | 95 |
| test | R21_s0516.jpg | 1920x603 | 1920x1080 | 0.44-1.00 | 1920x603 | 492 | 95 |

All 1066 local images: JPEG quality [95], widths [1920] px.

## 2. Saved image vs the same frame decoded from the video (sequential read)

| Split | Frame | Video frame no. | Same size | PSNR dB | Mean abs diff (0-255) | PSNR vs previous video frame |
|---|---|---|---|---|---|---|
| train | R04_s0304.jpg | 9119 | yes | 45.2 | 0.96 | 21.9 |
| val | R05_s0113.jpg | 3390 | yes | 45.6 | 0.89 | 21.4 |
| val | R05_s0228.jpg | 6840 | yes | 45.5 | 0.93 | 21.2 |
| test | R06_s0302.jpg | 9059 | yes | 44.5 | 1.07 | 18.7 |
| test | R06_s0336.jpg | 10079 | yes | 44.3 | 1.09 | 15.8 |
| val | R07_s0448.jpg | 13439 | yes | 43.5 | 1.17 | 17.2 |
| val | R07_s0482.jpg | 14459 | yes | 45.0 | 0.99 | 21.4 |
| val | R07_s0514.jpg | 15419 | yes | 46.5 | 0.82 | 21.8 |
| train | R08_s0082.jpg | 2460 | yes | 43.4 | 1.23 | 17.1 |
| train | R10_s0436.jpg | 13079 | yes | 46.6 | 0.77 | 24.2 |
| train | R10_s0583.jpg | 17489 | yes | 45.9 | 0.89 | 19.6 |
| train | R11_s0138.jpg | 4140 | yes | 46.0 | 0.85 | 22.8 |
| train | R13_s0309.jpg | 9269 | yes | 46.9 | 0.73 | 19.2 |
| train | R13_s0352.jpg | 10559 | yes | 46.9 | 0.74 | 17.4 |
| train | R14_s0261.jpg | 7829 | yes | 45.8 | 0.89 | 25.4 |
| train | R15_s0318.jpg | 9539 | yes | 45.7 | 0.91 | 22.0 |
| train | R15_s0413.jpg | 12389 | yes | 46.2 | 0.83 | 21.0 |
| val | R16_s0115.jpg | 3450 | yes | 45.2 | 0.95 | 20.1 |
| val | R16_s0455.jpg | 13649 | yes | 45.5 | 0.92 | 21.1 |
| test | R19_s0110.jpg | 3300 | yes | 42.3 | 1.17 | 16.7 |

PSNR 42.3-46.9 dB (mean 45.3); mean abs diff 0.73-1.23.

## 3. Sharpness and blockiness of every local image

| | Min | 5% | Median | 95% | Max |
|---|---|---|---|---|---|
| Laplacian variance | 37 | 149 | 441 | 1214 | 2252 |
| Blockiness (1 = none) | 0.943 | 1.008 | 1.065 | 1.198 | 1.565 |

Unusually blurry (Laplacian variance < 79): **4**: R08_s0197.jpg (train, 37), R05_s0459.jpg (val, 54), R05_s0508.jpg (val, 56), R05_s0323.jpg (val, 73).

Unusually blocky (blockiness > 1.187): **60**: R14_s0087.jpg (train, 1.565), R13_s0523.jpg (train, 1.518), R07_s0112.jpg (val, 1.474), R05_s0064.jpg (val, 1.448), R13_s0436.jpg (train, 1.444), R13_s0233.jpg (train, 1.435), R05_s0144.jpg (val, 1.434), R10_s0240.jpg (train, 1.422), R14_s0116.jpg (train, 1.422), R14_s0233.jpg (train, 1.417), R13_s0465.jpg (train, 1.415), R13_s0546.jpg (train, 1.398), R06_s0192.jpg (test, 1.394), R15_s0032.jpg (train, 1.391), R16_s0208.jpg (val, 1.387), R14_s0407.jpg (train, 1.381), R08_s0016.jpg (train, 1.374), R13_s0477.jpg (train, 1.371), R21_s0080.jpg (test, 1.369), R13_s0145.jpg (train, 1.364), R19_s0048.jpg (test, 1.363), R12_s0192.jpg (train, 1.362), R08_s0112.jpg (train, 1.357), R08_s0575.jpg (train, 1.354), R16_s0518.jpg (val, 1.343), R07_s0192.jpg (val, 1.339), R06_s0224.jpg (test, 1.336), R08_s0048.jpg (train, 1.334), R13_s0519.jpg (train, 1.324), R13_s0550.jpg (train, 1.323), R14_s0090.jpg (train, 1.322), R11_s0032.jpg (train, 1.317), R06_s0016.jpg (test, 1.315), R21_s0096.jpg (test, 1.307), R21_s0128.jpg (test, 1.307), R16_s0176.jpg (val, 1.307), R09_s0068.jpg (train, 1.305), R16_s0064.jpg (val, 1.302), R11_s0144.jpg (train, 1.296), R21_s0192.jpg (test, 1.293).

By recording (median Laplacian variance): R04 616, R05 278, R06 510, R07 395, R08 486, R09 233, R10 192, R11 300, R12 405, R13 328, R14 305, R15 429, R16 490, R17 712, R18 595, R19 739, R20 843, R21 1114.

Contact sheet of the 12 least sharp: `results/frame_quality_worst12.jpg`.

## Notes (looked at by eye, 2026-11-10)

- Blockiness comes from the source video, not the extractor: the saved images match the video at 42-47 dB.
  Frames at whole multiples of 16 s are blockier (median 1.151 vs 1.063 for the rest; 26 of the 60
  outliers), a periodic pattern of the phone's encoder.
- The least sharp frames are hazy windshield frames (glare, the dashboard reflected in the glass:
  R05, R07, R08, R10) and smooth concrete with little texture (R13, R14). None is out of focus or broken.
- R13/R14 (train only, 154 frames): the approved band 0.45-0.80 still contains the top of the bonnet at
  the bottom centre of the crop (it starts at about 0.74-0.78 of the frame height, not 0.80), in early and
  late frames alike. No label lies on it. The app crops the same band, so training and the app agree.
