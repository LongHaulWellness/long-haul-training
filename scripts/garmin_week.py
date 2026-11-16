#!/usr/bin/env python3
"""Pull a training week's Garmin data for the Sunday review.

Usage:
    python3 scripts/garmin_week.py            # last complete Mon–Sun week
    python3 scripts/garmin_week.py 2026-W46   # a specific ISO week

Writes data/garmin/YYYY-Www_garmin.md (also printed) and the raw API
responses to data/garmin/raw/YYYY-Www/. Needs GARMIN_CONNECT_API_KEY in .env.
API reference: reference/garmin_personal_api/README.md

Mornings run Tue → Mon: a night belongs to the training day before it,
so the Sun → Mon night shows how the week's last day landed.
"""
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://personal.connectapi.garmin.com"
TOKEN_URL = BASE + "/personalapitoken-service/personal-api/personal-api-key/token"
CONTEXT_WEEKS = 4

# Example thresholds. Set them to your own reading rules in analysis/wellness_log.md.
RHR_GREEN_MAX = 45
RHR_YELLOW = 48
SLEEP_GREEN_MIN = 75
SLEEP_YELLOW = 65


# ---------- API ----------

def load_api_key():
    env = ROOT / ".env"
    if not env.exists():
        sys.exit("No .env in the repo root. Add GARMIN_CONNECT_API_KEY=... to it.")
    for line in env.read_text().splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "GARMIN_CONNECT_API_KEY":
            return value.strip().strip("'\"")
    sys.exit("GARMIN_CONNECT_API_KEY not found in .env.")


def get_token(api_key):
    req = urllib.request.Request(TOKEN_URL, method="POST",
                                 headers={"Authorization": "ApiKey " + api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode().strip()
    except urllib.error.HTTPError as e:
        sys.exit(f"Token exchange failed: HTTP {e.code}. The key may have expired; "
                 "make a new one at https://connect.garmin.com/app/settings/personalApiToken")


class Garmin:
    def __init__(self, token, raw_dir):
        self.token = token
        self.raw_dir = raw_dir

    def get(self, name, path, **params):
        url = BASE + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + self.token})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
        except urllib.error.HTTPError as e:
            print(f"warning: {name} failed with HTTP {e.code}", file=sys.stderr)
            return None
        if not body:  # 204: nothing recorded
            return None
        data = json.loads(body)
        (self.raw_dir / f"{name}.json").write_text(json.dumps(data, indent=1))
        return data


# ---------- helpers ----------

def days(start, end):
    d = start
    while d <= end:
        yield d
        d += dt.timedelta(days=1)


def avg(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def fmt(v, digits=0, suffix=""):
    if v is None:
        return "–"
    return f"{v:.{digits}f}{suffix}"


def hm(seconds):
    if seconds is None:
        return "–"
    m = round(seconds / 60)
    return f"{m // 60}:{m % 60:02d}"


def clock(local_ms):
    # Garmin's "local" timestamps are local wall time encoded as if UTC
    if local_ms is None:
        return "–"
    return dt.datetime.fromtimestamp(local_ms / 1000, dt.timezone.utc).strftime("%H:%M")


def mark(value, bad):
    return f"**{value}**" if bad else str(value)


def sport(activity):
    return activity["activityType"]["typeKey"].removesuffix("_v2").replace("_", " ")


# ---------- fetch ----------

def fetch(api, week_start):
    """Fetch the review week plus CONTEXT_WEEKS-1 earlier weeks in one go."""
    today = dt.date.today()
    first_day = week_start - dt.timedelta(weeks=CONTEXT_WEEKS - 1)
    last_day = week_start + dt.timedelta(days=6)
    last_morning = min(last_day + dt.timedelta(days=1), today)
    first_morning = first_day + dt.timedelta(days=1)

    hrv = api.get("hrv", f"/hrv-service/hrv/daily/{first_morning}/{last_morning}") or {}
    sleep = api.get("sleep", "/sleep-service/sleep/dailySleepSummariesByDate",
                    startDate=first_morning, endDate=last_morning) or []
    daily = api.get("dailysummaries", "/usersummary-service/v2/dailysummaries",
                    startDate=first_day, endDate=last_morning) or {}
    activities = api.get("activities", "/activitylist-service/activities/search/activities",
                         startDate=first_day, endDate=last_day, limit=200) or []

    # Body Battery at wake / overnight charge only comes from the single-day summary
    wake = {}
    for d in days(week_start + dt.timedelta(days=1), last_morning):
        s = api.get(f"usersummary_{d}", "/usersummary-service/usersummary/daily",
                    calendarDate=d) or {}
        wake[str(d)] = s

    return {
        "hrv": {h["calendarDate"]: h for h in hrv.get("hrvSummaries", [])},
        "sleep": {s["calendarDate"]: s for s in sleep},
        "daily": {d["calendarDate"]: d for d in daily.get("data", [])},
        "activities": [a for a in activities if not a.get("parent")],
        "wake": wake,
        "last_morning": last_morning,
    }


# ---------- report ----------

def week_stats(data, week_start):
    mornings = [str(d) for d in days(week_start + dt.timedelta(days=1),
                                     week_start + dt.timedelta(days=7))
                if d <= data["last_morning"]]
    training_days = [str(d) for d in days(week_start, week_start + dt.timedelta(days=6))]
    hrv = [data["hrv"].get(m) for m in mornings]
    last_hrv = next((h for h in reversed(hrv) if h), None)
    sleep = [data["sleep"].get(m) for m in mornings]
    acts = [a for a in data["activities"] if a["startTimeLocal"][:10] in training_days]
    daily = [data["daily"].get(d) for d in training_days]
    return {
        "hrv_night": avg([h and h.get("lastNightAvg") for h in hrv]),
        "hrv_7d_end": last_hrv and last_hrv.get("weeklyAvg"),
        "hrv_status_end": last_hrv and last_hrv.get("status", "").lower(),
        "rhr": avg([data["daily"].get(m, {}).get("heartRate", {}).get("restingValue")
                    for m in mornings]),
        "sleep_score": avg([s and s.get("sleepScores", {}).get("overall", {}).get("value")
                            for s in sleep]),
        "sleep_time": avg([s and s.get("sleepTimeSeconds") for s in sleep]),
        "load": sum(a.get("activityTrainingLoad") or 0 for a in acts),
        "active": sum(a.get("duration") or 0 for a in acts),
        "stress": avg([d and d.get("stress", {}).get("avgLevel") for d in daily]),
        "zones": [sum(a.get(f"hrTimeInZone_{z}") or 0 for a in acts) for z in range(1, 6)],
    }


def report(data, week_start, iso):
    week_end = week_start + dt.timedelta(days=6)
    mornings = [d for d in days(week_start + dt.timedelta(days=1), week_end + dt.timedelta(days=1))
                if d <= data["last_morning"]]
    out = [f"# Garmin data, {iso[0]}-W{iso[1]:02d} ({week_start:%b %-d} – {week_end:%b %-d})",
           "",
           f"Pulled {dt.datetime.now():%Y-%m-%d %H:%M} by `scripts/garmin_week.py`. "
           "Mornings run Tue → Mon (each night follows the training day before it).",
           ""]

    # Mornings
    last_hrv = next((data["hrv"][str(m)] for m in reversed(mornings) if str(m) in data["hrv"]), None)
    if last_hrv:
        b = last_hrv["baseline"]
        out.append(f"HRV baseline (balanced band): **{b['balancedLow']}–{b['balancedUpper']} ms**, "
                   f"low below {b['lowUpper']}.")
        out.append("")
    out += ["## Mornings",
            "",
            "| Morning | HRV night | HRV 7d | Status | RHR | Sleep score | Sleep | Bed → wake "
            "| Deep / REM | Night HR | BB wake (+sleep) | SpO2 | Resp |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in mornings:
        k = str(m)
        h = data["hrv"].get(k, {})
        s = data["sleep"].get(k, {})
        rhr = data["daily"].get(k, {}).get("heartRate", {}).get("restingValue")
        w = data["wake"].get(k, {})
        score = s.get("sleepScores", {}).get("overall", {}).get("value")
        status = (h.get("status") or "–").lower()
        bb = w.get("bodyBatteryAtWakeTime")
        bb_sleep = w.get("bodyBatteryDuringSleep")
        out.append(
            f"| {m:%a %-d} | {h.get('lastNightAvg', '–')} | {h.get('weeklyAvg', '–')} "
            f"| {mark(status, status not in ('balanced', '–'))} "
            f"| {mark(fmt(rhr), rhr is not None and rhr > RHR_GREEN_MAX)} "
            f"| {mark(fmt(score), score is not None and score < SLEEP_GREEN_MIN)} "
            f"| {hm(s.get('sleepTimeSeconds'))} "
            f"| {clock(s.get('sleepStartTimestampLocal'))} → {clock(s.get('sleepEndTimestampLocal'))} "
            f"| {hm(s.get('deepSleepSeconds'))} / {hm(s.get('remSleepSeconds'))} "
            f"| {fmt(s.get('avgHeartRate'))} "
            f"| {fmt(bb)}{'' if bb_sleep is None else f' (+{bb_sleep})'} "
            f"| {fmt(s.get('averageSpO2Value'))} | {fmt(s.get('averageRespirationValue'))} |")
    out += ["", "Bold = outside the green-light range in `analysis/wellness_log.md`.", ""]

    # Days
    out += ["## Days",
            "",
            "| Day | Load | Int. min (mod / vig) | Avg stress | Body Battery (low – high) | Max HR | Steps |",
            "|---|---|---|---|---|---|---|"]
    for d in days(week_start, week_end):
        k = str(d)
        s = data["daily"].get(k, {})
        load = sum(a.get("activityTrainingLoad") or 0 for a in data["activities"]
                   if a["startTimeLocal"][:10] == k)
        im = s.get("intensityMinutes", {})
        bb = s.get("bodyBattery", {})
        out.append(
            f"| {d:%a %-d} | {fmt(load) if load else '–'} "
            f"| {im.get('moderate', '–')} / {im.get('vigorous', '–')} "
            f"| {s.get('stress', {}).get('avgLevel', '–')} "
            f"| {bb.get('minValue', '–')} – {bb.get('maxValue', '–')} "
            f"| {s.get('heartRate', {}).get('maxValue', '–')} "
            f"| {s.get('movement', {}).get('steps', {}).get('value', '–')} |")
    out.append("")

    # Activities
    acts = sorted((a for a in data["activities"]
                   if str(week_start) <= a["startTimeLocal"][:10] <= str(week_end)),
                  key=lambda a: a["startTimeLocal"])
    out += ["## Activities",
            "",
            "Garmin's training load and Training Effect. Notes and how it felt belong in your training log (e.g. Strava).",
            "",
            "| When | Sport | Name | Time | km | Avg / max HR | TE aer / anaer | Label | Load "
            "| Z1–Z5 min |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for a in acts:
        zones = " / ".join(str(round((a.get(f"hrTimeInZone_{z}") or 0) / 60)) for z in range(1, 6))
        km = a.get("distance") or 0
        out.append(
            f"| {a['startTimeLocal'][5:16]} | {sport(a)} | {a.get('activityName', '')} "
            f"| {hm(a.get('duration'))} | {fmt(km / 1000, 1) if km else '–'} "
            f"| {fmt(a.get('averageHR'))} / {fmt(a.get('maxHR'))} "
            f"| {fmt(a.get('aerobicTrainingEffect'), 1)} / {fmt(a.get('anaerobicTrainingEffect'), 1)} "
            f"| {(a.get('trainingEffectLabel') or '–').lower().replace('_', ' ')} "
            f"| {fmt(a.get('activityTrainingLoad'))} | {zones} |")
    out.append("")

    # 4-week context
    out += [f"## Last {CONTEXT_WEEKS} weeks",
            "",
            "| Week | HRV night avg | HRV 7d at end | RHR avg | Sleep score | Sleep avg | Load "
            "| Active time | Avg stress | Time in Z1 / Z2 / Z3 / Z4 / Z5 (h) |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for i in range(CONTEXT_WEEKS - 1, -1, -1):
        ws = week_start - dt.timedelta(weeks=i)
        st = week_stats(data, ws)
        y, w, _ = ws.isocalendar()
        zones = " / ".join(f"{z / 3600:.1f}" for z in st["zones"])
        out.append(
            f"| W{w:02d} ({ws:%b %-d}) | {fmt(st['hrv_night'])} "
            f"| {fmt(st['hrv_7d_end'])} {st['hrv_status_end'] or ''} "
            f"| {fmt(st['rhr'], 1)} | {fmt(st['sleep_score'])} | {hm(st['sleep_time'])} "
            f"| {fmt(st['load'])} | {hm(st['active'])} | {fmt(st['stress'])} | {zones} |")
    out.append("")

    # Rule checks (data side only; how you feel comes from you)
    week_hrv = [data["hrv"].get(str(m), {}) for m in mornings]
    statuses = [(h.get("status") or "").lower() for h in week_hrv]
    rhrs = [data["daily"].get(str(m), {}).get("heartRate", {}).get("restingValue") for m in mornings]
    scores = [data["sleep"].get(str(m), {}).get("sleepScores", {}).get("overall", {}).get("value")
              for m in mornings]
    out += ["## Rule checks (data only)",
            "",
            f"- HRV status: {statuses.count('balanced')} balanced, "
            f"{statuses.count('unbalanced')} unbalanced, {statuses.count('low')} low "
            f"(of {len(mornings)} mornings).",
            f"- Mornings with RHR > {RHR_GREEN_MAX}: {sum(1 for r in rhrs if r and r > RHR_GREEN_MAX)}; "
            f"≥ {RHR_YELLOW}: {sum(1 for r in rhrs if r and r >= RHR_YELLOW)}.",
            f"- Nights with sleep score < {SLEEP_GREEN_MIN}: "
            f"{sum(1 for s in scores if s and s < SLEEP_GREEN_MIN)}; "
            f"< {SLEEP_YELLOW}: {sum(1 for s in scores if s and s < SLEEP_YELLOW)}.",
            ""]
    return "\n".join(out)


def parse_week(arg):
    if arg:
        year, week = arg.upper().split("-W")
        return dt.date.fromisocalendar(int(year), int(week), 1)
    today = dt.date.today()
    return today - dt.timedelta(days=today.weekday() + 7)  # Monday of last complete week


def main():
    week_start = parse_week(sys.argv[1] if len(sys.argv) > 1 else None)
    iso = week_start.isocalendar()
    tag = f"{iso[0]}-W{iso[1]:02d}"
    out_dir = ROOT / "data" / "garmin"
    raw_dir = out_dir / "raw" / tag
    raw_dir.mkdir(parents=True, exist_ok=True)

    api = Garmin(get_token(load_api_key()), raw_dir)
    md = report(fetch(api, week_start), week_start, iso)
    path = out_dir / f"{tag}_garmin.md"
    path.write_text(md)
    print(md)
    print(f"\nSaved to {path.relative_to(ROOT)} (raw JSON in {raw_dir.relative_to(ROOT)}/)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
