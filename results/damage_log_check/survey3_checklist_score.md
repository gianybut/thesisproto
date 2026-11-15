# Damage log correctness: survey3_checklist.csv

50 sampled records. Rates are yes / answered; blank or "unsure" answers are left out of that rate. 95% Wilson intervals.

| Measure | Yes | No | Not answered | Rate | 95% CI |
|---|---|---|---|---|---|
| Record precision (box shows real road damage) | 30 | 20 | 0 | 60.0% | 46.2% to 72.4% |
| Type correct, among real-damage records | 30 | 0 | 0 | 100.0% | 88.6% to 100.0% |
| Time correct | 50 | 0 | 0 | 100.0% | 92.9% to 100.0% |
| Location correct | 50 | 0 | 0 | 100.0% | 92.9% to 100.0% |
| Duplicate (rate = duplicate rate) | 0 | 50 | 0 | 0.0% | 0.0% to 7.1% |

Fully correct (real damage, right type, right time and location, not a duplicate): 30 of 50 fully answered records = 60.0% (95% CI 46.2% to 72.4%).

Per recorded type:

| Recorded type | Records | Real damage | Not damage | Type correct (of real) |
|---|---|---|---|---|
| Alligator crack (D20) | 5 | 1 | 4 | 1 of 1 |
| Longitudinal crack (D00) | 10 | 6 | 4 | 6 of 6 |
| Pothole (D40) | 27 | 18 | 9 | 18 of 18 |
| Transverse crack (D10) | 8 | 5 | 3 | 5 of 5 |

## Flagged records (survey3_flagged_checklist.csv)

36 records the AI check flagged as "likely not road damage" (score below 0.6).

| Recorded type | Records | Real damage | Not damage | Not answered | Real damage rate | 95% CI |
|---|---|---|---|---|---|---|
| Alligator crack (D20) | 7 | 0 | 7 | 0 | 0.0% | 0.0% to 35.4% |
| Longitudinal crack (D00) | 5 | 3 | 2 | 0 | 60.0% | 23.1% to 88.2% |
| Pothole (D40) | 11 | 5 | 6 | 0 | 45.5% | 21.3% to 72.0% |
| Transverse crack (D10) | 13 | 6 | 7 | 0 | 46.2% | 23.2% to 70.9% |
| **All** | 36 | 14 | 22 | 0 | 38.9% | 24.8% to 55.1% |

The flag was right (not road damage) for 22 of 36 answered flagged records (61.1%); 14 flagged records show real damage.

19 flagged records are also in the 50-record sample; the two answers differ for 0.
