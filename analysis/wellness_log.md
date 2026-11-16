# Wellness log

> Recovery metrics over time, the rules for reading them, and the patterns you've learned about yourself. The coach adds a dated snapshot after each weekly review.

## Reading rules
The thresholds below are **examples**. Set them from your own baseline (a few weeks of data), and keep `scripts/garmin_week.py` in sync (constants at the top).

- **Green (train as planned):** HRV 7-day average inside your baseline band, resting HR ≤ ___ (e.g. your normal + 2), sleep score ≥ ___ (e.g. 75), you feel fine.
- **Yellow (swap quality for easy):** any 2 of the following.
  - HRV "unbalanced" for 2+ days and trending down
  - resting HR ≥ ___ (e.g. 5 bpm over your normal) for 2+ mornings
  - sleep score < ___ (e.g. 65)
  - a health marker you track is off (e.g. energy ≤ 2/5)
- **Red (rest, walk, or mobility):** HRV "low" (below baseline), or fever / illness.
- Judge the trend over 3–5 days, not a single number.

## Snapshot YYYY-MM-DD (end of week NN)

Source: `data/garmin/YYYY-Www_garmin.md` or screenshots.

**HRV, 7-day average** (baseline ___–___ ms)

| Date | 7-day avg | Status |
|---|---|---|
| | | |

**Resting HR / daily high:**

**Sleep:** average score, range, duration, bedtimes.

**Subjective:** energy, health notes, niggles.

**Interpretation:** GREEN / YELLOW / RED, and why.

## Known patterns
- e.g. how sleep debt, travel, illness or hard weeks show up in your numbers, and how long the dip lasts.
