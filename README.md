# Smart Learning Lab — Content Engine

A standalone JSON-driven social content engine for Smart Learning Lab. It generates high-resolution 1600×2000 educational posts and publishes them to Facebook and Instagram.

## What is included

- Existing **Daily Challenge** collection: 3,000 records.
- **15 new content formats**, 2,000 records each = 30,000 new records.
- Total available records: **33,000**.
- A dedicated visual layout for every format.
- The approved premium visual direction: large hero, strong hierarchy, answer cards, CTA, decorative illustrations and high-resolution output.
- **10 new premium themes only**. The old theme system is not used.
- Theme rotation is global, so consecutive posts receive different visual treatments.
- Facebook Page + Instagram publishing.
- No Cloudflare R2 and no R2 credentials.
- GitHub Actions: push, manual run, and 16 scheduled IST slots.
- Per-content-type state so every JSON collection advances independently.

## Content formats and schedule (Asia/Kolkata)

| Time | Format | Data |
|---|---|---|
| 08:00 | Daily Challenge | `data/challenges.json` — 3,000 |
| 09:00 | Crack the Code | `data/crack_the_code.json` — 2,000 |
| 10:00 | AI Detective | `data/ai_detective.json` — 2,000 |
| 11:00 | Predict the Code | `data/predict_the_code.json` — 2,000 |
| 12:00 | Spot the Mistake | `data/spot_the_mistake.json` — 2,000 |
| 13:00 | Logic Puzzle | `data/logic_puzzle.json` — 2,000 |
| 14:00 | 60-Second Tech Tip | `data/tech_tip.json` — 2,000 |
| 15:00 | Build It | `data/build_it.json` — 2,000 |
| 16:00 | AI Challenge | `data/ai_challenge.json` — 2,000 |
| 17:00 | This or That | `data/this_or_that.json` — 2,000 |
| 18:00 | Tech Explained | `data/tech_explained.json` — 2,000 |
| 19:00 | Weekly Mission | `data/weekly_mission.json` — 2,000 |
| 20:00 | Science Challenge | `data/science_challenge.json` — 2,000 |
| 21:00 | Cyber Safety Challenge | `data/cyber_safety.json` — 2,000 |
| 22:00 | Learn in 60 Seconds | `data/learn_60_seconds.json` — 2,000 |
| 23:00 | Weekly Challenge Result | `data/weekly_result.json` — 2,000 |

The schedule is configuration-driven in `schedule.json`. Scheduled GitHub runs pass the exact cron expression to the publisher, so a delayed scheduled run still maps to the intended format.

## Files to edit later

- `data/*.json` — content.
- `schedule.json` — times and format mapping.
- `themes.json` — the 10 visual themes.
- `config.json` — image and project settings.

No Python code changes are required to add or edit normal content records.

## 10 premium themes

1. Sunset Coral
2. Ocean Blue
3. Royal Violet
4. Emerald Fresh
5. Electric Indigo
6. Mango Sun
7. Berry Pink
8. Teal Mint
9. Gold Navy
10. Midnight Neon

The old theme definitions/layouts have been removed from the active renderer.

## Local generation

Install:

```bash
pip install -r requirements.txt
```

Generate one item:

```bash
python app.py --content-type crack_the_code --index 1
```

Generate an existing Daily Challenge:

```bash
python app.py --content-type daily_challenge --index 1
```

Generate a selected theme explicitly:

```bash
python app.py --content-type ai_detective --index 1 --theme 4
```

## Publishing

Publish the next item for the current schedule slot:

```bash
python publish_daily.py
```

Publish a specific format:

```bash
python publish_daily.py --content-type predict_the_code
```

The publisher updates `state.json`, maintaining a separate next index for every content type.

## Required GitHub Secrets

```text
META_GRAPH_VERSION
FACEBOOK_PAGE_ID
FACEBOOK_PAGE_ACCESS_TOKEN
INSTAGRAM_USER_ID
INSTAGRAM_ACCESS_TOKEN
```

`TIMEZONE=Asia/Kolkata` is configured by the workflow.

There are **no R2 secrets**.

## GitHub Actions

The workflow runs on:

1. `git push` to `main`.
2. Manual **Run workflow**.
3. 16 scheduled runs from 08:00 to 23:00 IST.

For a manual run, choose `content_type` or leave it as `auto` to select the current schedule slot.

The workflow commits the updated `state.json` back to `main`. Its own state commit uses:

```text
chore: update content state
```

and is explicitly excluded from the push trigger, preventing an infinite publish loop.

The state push refreshes `origin/main` and retries up to five times to handle concurrent repository changes.

## Instagram image hosting

For Instagram image publishing, the project stages the image as an unpublished Facebook Page photo and uses the returned Meta CDN image URL for the Instagram media container. This removes the Cloudflare R2 dependency.

## Safety/content notes

Cyber-safety content is defensive and educational. It does not provide instructions for harmful activity. AI content asks users to verify important claims and treat generated output as a draft.

## State compatibility fix

The content engine supports both the new multi-content `state.json` format and the original Daily Challenge format where `next_index` was a single integer. If an existing repository still contains the old format, the publisher automatically migrates that value to `next_index.daily_challenge` instead of failing with `AttributeError: 'int' object has no attribute 'get'`.

`publish_daily.py` also forwards `SCHEDULE_CRON` to the publisher so scheduled GitHub Actions runs select the exact content type associated with the scheduled slot.
