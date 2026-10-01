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

It publishes the next Daily Challenge to **both Facebook and Instagram** through three triggers:

1. **Git push to `main`** — publishes the next challenge.
2. **Manual** — GitHub → Actions → Smart Learning Lab Daily Challenge → Run workflow.
3. **Schedule** — automatically runs twice every day:
   - 09:00 IST (03:30 UTC)
   - 19:00 IST (13:30 UTC)

The workflow's own state commit is intentionally detected and skipped, so this does not create an infinite publish loop. An empty commit pushed to `main` is also a normal push event and will trigger a publishing run.

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

### Actions permission

The workflow uses:

```yaml
permissions:
  contents: write
```

The repository must allow GitHub Actions to write to repository contents. In GitHub, check **Settings → Actions → General → Workflow permissions** and allow **Read and write permissions**.

### Safe state push

After publishing, the workflow saves `state.json`. It fetches the latest `main`, reapplies the generated state, commits it, and retries the push up to five times if another remote change causes a non-fast-forward error.

The state commit message is:

```text
chore: update daily challenge state
```

A push containing only that workflow-generated state commit starts a workflow run but the publish job is skipped, preventing duplicate social posts.

### Result

```text
Push / Manual Run / Schedule
          ↓
   Generate next challenge
          ↓
 Facebook + Instagram
          ↓
    Update state.json
          ↓
    Commit state.json
          ↓
       Push main
          ↓
   State-only run skipped
```

## Premium visual theme system

The renderer uses **only the new premium 15 Second Challenge design** based on the approved reference layout. The previous simple-card theme system has been removed.

There are exactly **10 new themes** in `themes.json`:

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

Every theme keeps the same approved premium UX structure while changing the color palette, accents, background shapes, and supporting visual treatment.

The layout includes:

- Smart Learning Lab branded header
- Large **15 SECOND CHALLENGE** hero
- Stopwatch illustration
- Daily Challenge number
- Category badge
- Large question card
- 2×2 answer cards
- Time-limit and difficulty panel
- Comment / Tag / Share CTA
- Calculator illustration
- Lightbulb and π accents
- “Small Questions • Big Progress” footer
- High-resolution 1600×2000 PNG output

Themes are selected automatically from `post_number`, so posts cycle through all 10 themes and then restart at theme 1. You do not need to select a theme manually.

To customize the 10 palettes, edit only:

```text
themes.json
```

### Preview locally

```bash
python app.py --index 1
```

Generate all 10 theme previews:

```bash
python app.py --index 1 --count 10
```

## GitHub Actions
The workflow runs on push to `main`, manual `workflow_dispatch`, and twice daily at 09:00 and 19:00 IST. Its own state-only commit is skipped to prevent a publish loop.
