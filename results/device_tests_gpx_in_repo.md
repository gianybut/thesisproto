# Device tests from the recordings (mobile capture app)

`tools/device_tests.py`. Source: GPX files only (durations, where shown, from frontend/public/samples/samples.json full_duration_s; size and bitrate need the videos): frontend/public/samples/aguinaldo-highway-tagaytay/track.gpx, frontend/public/samples/alfonso-bayan-national-road/track.gpx, frontend/public/samples/alfonso-national-bypass-road/track.gpx, frontend/public/samples/palocpoc-municipal-road/track.gpx, frontend/public/samples/santa-rosa-tagaytay-road/track.gpx.

| Rec | Part | Duration (s) | Size (MB) | Bitrate (Mbit/s) | GPS fixes | GPS rate (Hz) | Gaps > 3 s (n / longest s) | Accuracy mean / max (m) | Offset (s) | Skew (ms) | Gap after previous part (s) | Ended early |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R05 | 2 | 590.00 |  |  | 606 | 1.003 | 0 / 0 | 5.0 / 10.0 | 9.314 | 102 | previous part 1 not in this set | no |
| R06 | 3 | 590.04 |  |  | 607 | 1.003 | 0 / 0 | 4.7 / 4.7 | 9.957 | 102 | 0.644 | no |
| R07 | 4 | 590.00 |  |  | 607 | 1.003 | 0 / 0 | 4.7 / 7.9 | 9.607 | 98 | 0.606 | no |
| 20261103T032025-13ow | 1 | 589.17 |  |  | 560 | 0.941 | 4 / 12.0 | 4.7 / 4.7 | 0.131 | 99 |  | no |
| 20261103T033015-slko | 2 | 590.04 |  |  | 607 | 1.003 | 0 / 0 | 4.7 / 4.7 | 9.793 | 98 | 1.490 | no |

Across the recordings:

- Achieved GPS rate (Hz): mean 0.991, SD 0.028, min 0.941, max 1.003 (n = 5)
- GPS gaps longer than 3 s: 4 in 1 of 5 recordings
- Horizontal accuracy, recording means (m): mean 4.762, SD 0.123, min 4.700, max 4.980 (n = 5)
- Time offset (s): mean 7.760, SD 4.272, min 0.131, max 9.957 (n = 5)
- Clock skew (ms): mean 99.800, SD 2.049, min 98.000, max 102.000 (n = 5)
- Video bitrate (Mbit/s): n/a
- Gap between consecutive parts (s): mean 0.913, SD 0.500, min 0.606, max 1.490 (n = 3)

Not performed (cannot be measured from the files): the video start-time gap (stopwatch filmed at the start of a recording), the midday heat test, and observed full-length sessions in a moving vehicle. Whether a part was interrupted by locking the phone is recorded only on the phone (endReason), not in the files.
