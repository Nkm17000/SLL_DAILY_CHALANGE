# Smart Learning Lab – Daily Challenge

Standalone project for generating and publishing educational Daily Challenge posts to a Facebook Page and Instagram Professional account.

## What is included

- 3,000 editable Daily Challenge records in `data/challenges.json`
- HD 1600×2000 PNG generation
- Facebook Page publishing
- Instagram image publishing
- Manual publishing
- Daily scheduler entry point
- Persistent `state.json` to continue from the next challenge
- No external object-storage dependency

## Image hosting

This version does not require an external object-storage account.

Instagram's image publishing flow needs a publicly reachable image URL. The project handles that by temporarily uploading the generated image as an **unpublished Facebook Page photo**, retrieving the temporary Facebook CDN image URL, and immediately using that URL to create the Instagram media container.

This means there are no object-storage endpoint, bucket, access-key, secret-key, or public-domain settings in this project.

## Secrets / environment variables

Only these are required for publishing:

```text
META_GRAPH_VERSION=v24.0
FACEBOOK_PAGE_ID=
FACEBOOK_PAGE_ACCESS_TOKEN=
INSTAGRAM_USER_ID=
INSTAGRAM_ACCESS_TOKEN=
TIMEZONE=Asia/Kolkata
```

`TIMEZONE` is a setting, not a secret.

## Install

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and provide the Meta credentials. Load the variables using your deployment platform's secret/environment-variable settings, or your preferred dotenv loader.

## Generate without publishing

```bash
python app.py --index 1
```

Output is created under `output/`.

## Publish to Facebook

```bash
python publisher.py --index 1 --facebook
```

## Publish to Instagram

```bash
python publisher.py --index 1 --instagram
```

Instagram publishing will first create an unpublished Facebook staging photo so the image has a temporary public CDN URL.

## Publish to both

```bash
python publisher.py --index 1 --both
```

## Daily publishing

```bash
python publish_daily.py
```

The project uses `state.json` so the next scheduled run continues with the next challenge instead of repeatedly using challenge 1.

## Main content file

All 3,000 challenges are stored in:

```text
data/challenges.json
```

You can edit/add challenge content there without changing the publishing code.

## Project independence

This project is standalone. It does not import or depend on the previous quiz-video, inspiration-story, or technical-blog projects.

## Notes

- Keep Meta access tokens in deployment secrets/environment variables; do not commit them to Git.
- Instagram publishing requires the appropriate Meta/Instagram account and API permissions.
- The Facebook CDN staging URL is temporary and is intended for the immediate Instagram media-container workflow.
- `META_GRAPH_VERSION` is configurable so the project can be updated when Meta changes API versions.

## GitHub Actions automation

The project includes:

```text
.github/workflows/daily-challenge.yml
```

It publishes the next Daily Challenge to **both Facebook and Instagram** in three ways:

1. **Push** — every repository push runs the workflow (except the workflow's own state-only commit).
2. **Manual** — open GitHub → Actions → Smart Learning Lab Daily Challenge → Run workflow.
3. **Schedule** — automatically runs twice every day:
   - 09:00 IST (03:30 UTC)
   - 19:00 IST (13:30 UTC)

### GitHub repository secrets

Add these under **Settings → Secrets and variables → Actions → New repository secret**:

```text
META_GRAPH_VERSION
FACEBOOK_PAGE_ID
FACEBOOK_PAGE_ACCESS_TOKEN
INSTAGRAM_USER_ID
INSTAGRAM_ACCESS_TOKEN
```

`TIMEZONE` is already set to `Asia/Kolkata` in the workflow.

### Important: Actions permission

The workflow needs repository write permission because it saves `state.json` after a successful post. This ensures the next run uses the next challenge rather than starting from challenge #1 again.

The workflow's own `state.json` commit is excluded from publishing by the workflow condition, preventing an infinite push → publish → push loop.

### Result

```text
Push to GitHub
      ↓
GitHub Actions
      ↓
Generate next challenge
      ↓
Facebook Page + Instagram
      ↓
Update state.json
      ↓
Commit state only
      ↓
No second publishing run
```
