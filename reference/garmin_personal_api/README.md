# Garmin Connect Personal API

Read-only access to your own Garmin Connect data. This is a short guide; the full spec is on Garmin's Swagger docs page (linked below). Summarized from spec v1.0.0, November 2026.

- Docs: https://developer.garmin.com/gc-developer-program/personal/personal-api/
- Swagger UI (full spec): https://developer.garmin.com/gc-developer-program/personal/swagger-docs/
- Key management: https://connect.garmin.com/app/settings/personalApiToken

## Auth

Create a key at the key-management link above, then copy `.env.example` to `.env` and paste it as `GARMIN_CONNECT_API_KEY` (`.env` is gitignored). It has an expiry date set at creation; when it lapses, generate a new one at the link above and replace it in `.env`.

1. Exchange the key for an access token:
   ```
   POST https://personal.connectapi.garmin.com/personalapitoken-service/personal-api/personal-api-key/token
   Authorization: ApiKey <GARMIN_CONNECT_API_KEY>
   ```
   The response body is the token itself: a raw JWT as plain text, not JSON. It's valid for 24 hours. Scopes: `CONNECT_READ`, `PERSONAL_API_FITNESS_READ`, `PERSONAL_API_NUTRITION_READ`, `PERSONAL_API_USER_READ`, `PERSONAL_API_WELLNESS_READ`.
2. Call the data endpoints on `https://personal.connectapi.garmin.com` with `Authorization: Bearer <token>`. Confirmed working in November 2026.

## Endpoints (all `GET`)

Dates are `YYYY-MM-DD`. `*` = required.

### Wellness log (HRV, sleep, HR)

| Data | Path | Params |
|---|---|---|
| HRV, range | `/hrv-service/hrv/daily/{fromDate}/{toDate}` | fromDate\*, toDate\* |
| HRV, one night (detail) | `/hrv-service/hrv/{calendarDate}` | calendarDate\* |
| Sleep, range | `/sleep-service/sleep/dailySleepSummariesByDate` | startDate, endDate |
| Sleep, one night | `/sleep-service/sleep/dailySleep` | date |
| Heart rate, one day (incl. resting) | `/wellness-service/wellness/dailyHeartRate` | date |
| HR zones | `/biometric-service/heartRateZones/v2` | generateDefaults |
| Body Battery, range | `/wellness-service/wellness/bodyBattery/reports/daily` | startDate, endDate, chunks |
| Stress, range | `/usersummary-service/stats/stress/daily/{startDate}/{endDate}` | startDate\*, endDate\* |
| SpO2 acclimation | `/wellness-service/wellness/daily/spo2acclimation/{calendarDate}` | calendarDate\* |

### Daily summaries

| Data | Path | Params |
|---|---|---|
| Daily summaries, range | `/usersummary-service/v2/dailysummaries` | startDate, endDate |
| Daily summary, one day | `/usersummary-service/usersummary/daily` | calendarDate |
| Steps | `/usersummary-service/stats/steps/daily/{startDate}/{endDate}` | startDate\*, endDate\* |
| Hydration | `/usersummary-service/stats/hydration/daily/{startDate}/{endDate}` | startDate\*, endDate\* |
| Fitness age | `/fitnessage-service/fitnessage/v2/{calendarDate}` | calendarDate\*, fullHistoryScan |

### Activities

| Data | Path | Params |
|---|---|---|
| Search/list | `/activitylist-service/activities/search/activities` | start, limit, startDate, endDate, activityType, … (many filters) |
| One activity | `/activity-service/activity/{activityId}` | activityId\* |
| Workouts in an activity | `/activity-service/activity/{activityId}/workouts` | activityId\* |
| Original file | `/download-service/files/activity/{activityId}` | activityId\* |
| Activity summary, range | `/wellnessactivity-service/activity/summary/range/{fromDate}/{untilDate}` | fromDate\*, untilDate\* |

### Other

| Data | Path | Params |
|---|---|---|
| Menstrual cycle summary | `/periodichealth-service/menstrualcycle/summary/{calendarDate}` | calendarDate\* |
| Menstrual cycle day view | `/periodichealth-service/menstrualcycle/dayview/{calendarDate}` | calendarDate\*, todayDate, reducedResponse, skipbm, includeAnalysis |
| Weight, range | `/weight-service/weight/range/{startDate}/{endDate}` | startDate\*, endDate\*, includeAll |
| Weight, all | `/weight-service/weight/all/{startDate}/{endDate}` | startDate\*, endDate\* |
| Weight goals | `/goal-service/goal/user/effective/weightgoal/{startDate}/{endDate}` | startDate\*, endDate\* |
| Nutrition log | `/nutrition-service/food/logs/{date}` | date\*, includeGoals, includeNutrition, includeMedia, mealId |
| Profile settings | `/userprofile-service/userprofile/settings` | none |

## Gaps

- No endpoints for training readiness, training status, VO2max trends, race predictions, or respiration. Some may show up inside daily summaries or activity details; check real responses.
- Rate limits and how far back history goes aren't documented.
- Response schemas are thin; the first real calls will show the shapes.
