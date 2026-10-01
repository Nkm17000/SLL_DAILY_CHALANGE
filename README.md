# Smart Learning Lab — Daily Challenge

Standalone project for 3,000 interactive learning posts.

## Main content file

`data/challenges.json` is the only file you normally need to edit. Change questions, options, answers, hints, explanations, difficulty, time limits, CTAs and hashtags.

## Generate only

```bash
pip install -r requirements.txt
python app.py --index 1
python app.py --index 250
python app.py --index 1 --count 10
```

## Publish

Copy `.env.example` to `.env` or configure the same variables in your hosting platform's Secrets/Environment Variables.

Generate + Facebook:

```bash
python publisher.py --index 1 --facebook
```

Generate + Instagram:

```bash
python publisher.py --index 1 --instagram
```

Generate + both:

```bash
python publisher.py --index 1 --both
```

For Instagram, the generated PNG is uploaded to Cloudflare R2 first so Instagram can access it through a public HTTPS URL.

## Daily scheduler

```bash
python publish_daily.py
```

The state is stored in `state.json`. Every successful run advances to the next challenge. After #3000 it starts again at #1.

## Secrets

- META_GRAPH_VERSION
- FACEBOOK_PAGE_ID
- FACEBOOK_PAGE_ACCESS_TOKEN
- INSTAGRAM_USER_ID
- INSTAGRAM_ACCESS_TOKEN
- R2_ENDPOINT
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET
- R2_PUBLIC_BASE_URL
- TIMEZONE (optional)

Never commit `.env`, access tokens, R2 secrets, or `state.json` to a public repository.

## Architecture

JSON library -> HD image generator -> R2 public image -> Facebook Page / Instagram -> state tracking.

This project is independent from any previous quiz-video, inspiration-story, or technical-blog project.
