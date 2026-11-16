# long-haul-training

A repo backbone for planning and analyzing your own training with an AI coach. It's built mostly for endurance and running, but it isn't limited to them.

The idea: your training lives in plain Markdown files. An AI assistant that can read and edit files (e.g. [Claude Code](https://claude.com/claude-code)) acts as your coach. It reads your profile, your principles and last week's data, then writes the next week's plan with you. **You always have the final say.**

Nothing here prescribes a training philosophy. You (or your coach) pick the intensity system, the weekly structure and the rules, and write them down in `coaching_principles.md`.

## Need help setting it up?

Contact [@hannarud](https://github.com/hannarud) on GitHub. Hanna can help you set this repo up, and can also build a training plan with you if you'd like to try this way of training.

## Structure

| Path | What's in it |
|---|---|
| `CLAUDE.md` | Instructions for the AI coach: what to read, how the weekly loop works, how to update files. |
| `athlete_profile.md` | Who you are as an athlete: history, PRs, zones, paces, health, preferences. **Source of truth.** |
| `coaching_principles.md` | How you train: philosophy, intensity system, weekly template, progression, guardrails. |
| `season_YYYY-YY/season_overview.md` | The season: goals, races and fixed points, phases. Rename the folder (e.g. `season_2026-27`). |
| `season_YYYY-YY/weeks/YYYY-Www.md` | One file per week (ISO weeks, e.g. `2026-W47.md`): the plan on top, the review at the bottom. |
| `library/` | Reusable sessions: strength, mobility, travel workouts, drills. |
| `analysis/` | Reviews and analyses: season reviews, race analyses, and `wellness_log.md` (recovery metrics + reading rules). |
| `scripts/garmin_week.py` | Optional. Pulls a week of Garmin data (HRV, resting HR, sleep, Body Battery, stress, activities with load and HR zones). |
| `reference/garmin_personal_api/` | Guide to the Garmin Connect Personal API used by the script. |
| `data/` | Your exports and pulls (Strava CSVs, Garmin data, screenshots). **Gitignored**, so it stays local. |

## Setup

1. **Use this repo as a template** (or fork it). If your copy will hold real health data, make it **private**.
2. **Fill in `athlete_profile.md`.** The more honest the history and health sections, the better the plans. You can also ask the coach to interview you and fill it in.
3. **Write `coaching_principles.md`.** Pick your intensity system (pace, HR, power, RPE, or a mix), your weekly template and your rules. If you're not sure, talk it through with the coach first.
4. **Set up the season:** rename `season_YYYY-YY/`, list your races and fixed points, sketch the phases.
5. **Plan the first week:** copy `season_YYYY-YY/weeks/YYYY-Www.md` to the current week and ask the coach to fill it in.
6. **Optional: connect your data.**
   - **Strava:** if your AI assistant has a Strava connector, the coach can read your activities and notes directly. Otherwise drop CSV exports in `data/`.
   - **Garmin:** create a personal API key ([Garmin Connect Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api/)), copy `.env.example` to `.env`, paste the key in, and run `python3 scripts/garmin_week.py`. Python 3.9+, no packages needed. Without the API, share screenshots instead.

## Weekly loop

1. **End of the week:** review the week, then write the next week's plan. The coach asks for anything on the checklist below that's missing.
2. **During the week:** adjust as needed. Session notes go in your training log (e.g. Strava descriptions); the coach reads them.
3. **Every 4 weeks (or each block):** look at load, consistency, health trend and test results; update the profile and paces.

### Weekly review checklist

**A. Recovery data:** run `python3 scripts/garmin_week.py` (last complete week, or e.g. `2026-W47`), or share screenshots of your HRV, resting HR and sleep trends.

**B. How it felt (one line each):** energy 1–5, anything you track for your health (e.g. sleep quality, gut, cycle), niggles and pain, life load (work, travel, short nights, illness).

**C. Training:** what changed from the plan and why; habits (strength, mobility, anything you're building).

**D. Next week:** fixed points such as races, group sessions, travel, work peaks.

## Privacy

- `.env` (API keys) and `data/` are gitignored. Keep it that way.
- Your profile and week files will contain health information. Keep your own copy private unless you're comfortable sharing it.
