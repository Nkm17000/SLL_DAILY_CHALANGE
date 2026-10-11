# SLL Daily Quiz Challenge

This replaces the old content-format rotation with a quiz-only publisher.

## What it does
- Uses Groq to create four fresh medium-or-harder questions per run: Math, GK & GS, Reasoning, and English.
- Creates four separate 1080×1350 PNGs, named `<quizno>_SLL_DAILY_<SUB>.png`.
- Challenge images show the question and A–D options only; they do not show the answer.
- The next run's captions reveal the previous run's last quiz answer and subject (the last quiz is English), then present the new question.
- Stores question fingerprints and history in `quiz_state.json` to avoid repeats across runs. Keep this file in Git; do not delete it.
- Publishes each subject image to every enabled Facebook Page and Instagram business account listed in `config.json`. Add/remove account objects there to control destinations.
- Includes Smart Learning Lab 247 website, Instagram, YouTube, and Facebook links in every caption.
- Git push triggers a new challenge set; scheduled workflow runs daily at 06:00 IST.

## Required GitHub Secrets
`GROQ_API_KEY` is required. Groq is used because web search alone cannot reliably generate and validate four original, medium-level questions and answer keys.

Configure destinations in `config.json`: add an object to `facebook_accounts` or `instagram_accounts`, set `enabled` to `true`, and specify the environment-secret names for its ID and token. Then add those secrets under **GitHub → Settings → Secrets and variables → Actions** and expose them in `.github/workflows/daily-challenge.yml` under `env`. Example accounts are preconfigured for two Facebook Pages and two Instagram accounts. Never paste actual tokens into `config.json`.

Also set `META_GRAPH_VERSION` (optional; defaults to `v24.0`) and `GROQ_MODEL` (optional; defaults to `openai/gpt-oss-120b`).

Use Page access tokens for Facebook Page publishing, and Instagram professional/business account IDs with appropriate publishing permissions. Instagram image publishing needs a publicly reachable image URL; this code stages the image as an unpublished photo on the first configured Facebook Page to obtain a CDN URL.

## Run locally
```bash
pip install -r requirements.txt
cp .env.example .env  # fill values and export them into your shell
python quiz_challenge.py --dry-run
python quiz_challenge.py
```
`--dry-run` still calls Groq and creates four images, but does not publish.

## Important
- Do not commit real access tokens or API keys.
- Deduplication is based on generated question text stored in `quiz_state.json`; preserve that file between runs.
- API publication is not tested against your real Meta accounts. A rate limit/restriction from Meta can still cause publishing to fail.


## Platform enable/disable behavior

Publishing is controlled by `config.json` only. Set an account's `enabled` to `false` or remove its entry to prevent calls to that account. If a platform has no enabled accounts with both required ID and token secrets, the script skips that platform instead of failing the run. If Instagram accounts are enabled but there is no enabled Facebook account, Instagram publishing is skipped too, because this version uses Facebook to host a public image URL for Instagram. The script will still generate the four images and captions and save quiz history.
