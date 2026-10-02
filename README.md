# Smart Learning Lab Content Engine

A standalone JSON-driven Facebook + Instagram content publisher for Smart Learning Lab.

## Final publishing model

There are **16 content formats**, but only **8 scheduled posts per day**.

- **Day 1 / Group A:** formats 1-8
- **Day 2 / Group B:** formats 9-16
- **Day 3:** Group A again
- **Day 4:** Group B again
- The cycle repeats every 2 days.

The same 8 clock slots are used each day: **08:00 through 15:00 IST**.
The active day group decides which format owns each slot.

### Day 1 — Group A

| IST | Format |
|---|---|
| 08:00 | Daily Challenge |
| 09:00 | Crack the Code |
| 10:00 | AI Detective |
| 11:00 | Predict the Code |
| 12:00 | Spot the Mistake |
| 13:00 | Logic Puzzle |
| 14:00 | 60-Second Tech Tip |
| 15:00 | Build It |

### Day 2 — Group B

| IST | Format |
|---|---|
| 08:00 | AI Challenge |
| 09:00 | This or That |
| 10:00 | Tech Explained |
| 11:00 | Weekly Mission |
| 12:00 | Science Challenge |
| 13:00 | Cyber Safety Challenge |
| 14:00 | Learn in 60 Seconds |
| 15:00 | Weekly Challenge Result |

Content records are always read dynamically from `data/*.json`. Each content type has its own `next_index`, so it continues where it stopped.

## Template-specific UX

The renderer no longer randomly selects a generic layout. Each content type has a dedicated UX:

- Daily Challenge → premium 15-second challenge card
- Crack the Code → decode/answer board
- AI Detective → case-file evidence board
- Predict the Code → code-editor + output choices
- Spot the Mistake → error-hunt/correction layout
- Logic Puzzle → pattern challenge board
- 60-Second Tech Tip → tip card + action chips
- Build It → mini-project roadmap
- AI Challenge → prompt + verify checklist
- This or That → split comparison screen
- Tech Explained → one-sentence explainer + fact cards
- Weekly Mission → 7-day roadmap
- Science Challenge → formula/challenge board
- Cyber Safety → safety challenge board
- Learn in 60 Seconds → lesson timeline
- Weekly Challenge Result → answer-reveal board

## Themes

There are exactly 10 premium themes in `themes.json`:

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

Themes are deterministic per template and content index. They are **not randomly assigned**. Each format has a fixed starting theme and then cycles through the 10 themes as its JSON records advance.

## Content

The project contains 33,000 records:

- Daily Challenge: 3,000
- Each of the other 15 formats: 2,000

Edit the JSON files in `data/` to change future posts without changing Python code.

## GitHub Actions

The workflow supports:

- `git push` → one publish using the current active day/slot
- Manual **Run workflow** → one publish; `auto` follows the current active slot
- Scheduled runs → exactly **8 runs per day**, 08:00–15:00 IST

The workflow's own `state.json` commit is ignored by the push trigger, preventing an infinite publish loop.

## Required GitHub Secrets

```text
META_GRAPH_VERSION
FACEBOOK_PAGE_ID
FACEBOOK_PAGE_ACCESS_TOKEN
INSTAGRAM_USER_ID
INSTAGRAM_ACCESS_TOKEN
```

No Cloudflare R2 is required.

## Local generation

```bash
pip install -r requirements.txt
python app.py --content-type daily_challenge --index 1
python app.py --content-type predict_the_code --index 1
```

## Local publish

```bash
python publish_daily.py --content-type auto
```

Or explicitly:

```bash
python publish_daily.py --content-type crack_the_code
```
