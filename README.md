# Newsletter Aggregator & Content Pipeline

Autonomous daily pipeline that fetches newsletters from Gmail, deduplicates topics with Claude AI, and generates LinkedIn posts and short-form video scripts — all written to a Google Sheet for review and approval.

## What it does

1. **Fetches emails** from configured newsletter senders (last 24h) via Gmail API
2. **Deduplicates topics** — multiple newsletters covering the same story become one topic
3. **Writes to Sheets** — unique topics saved to the `Topics` tab
4. **Generates content** per topic using your brand voice:
   - LinkedIn post (copy + visual suggestion)
   - Short-form video script (hook + narration + storyboard notes)
5. **Populates drafts** into `LinkedIn Drafts` and `Video Scripts` tabs with `PENDING` status for your approval

Runs automatically once per day via Railway cron at 7 AM UTC.

## Project Structure

```
newsletter-aggregator/
├── railway.toml                  # Railway cron config
├── config/
│   └── settings.py               # Senders list, model, sheet tab names
├── docs/
│   ├── brand_brain.md            # Your brand voice & identity
│   ├── linkedin_rules.md         # LinkedIn content rules
│   └── video_script_rules.md    # Video script rules
├── src/
│   ├── pipeline.py               # Main orchestrator
│   ├── gmail_client.py           # Gmail OAuth2 fetch
│   ├── claude_client.py          # Anthropic SDK wrapper (retry logic)
│   ├── topic_extractor.py        # Dedup + topic extraction via Claude
│   ├── content_agents.py         # LinkedIn + video script agents
│   ├── sheets_client.py          # Google Sheets append
│   └── brand_loader.py           # Loads docs/ with lru_cache
├── scripts/
│   └── gmail_auth_setup.py       # One-time OAuth flow → refresh token
├── requirements.txt
└── .env.example
```

## Google Sheets Schema

**Topics** tab: `Date | Topic Title | Summary | Source Newsletters | Source URLs | Topic ID | Run Timestamp`

**LinkedIn Drafts** tab: `Date | Topic ID | Topic Title | Post Copy | Visual Suggestion | Approval Status | Run Timestamp`

**Video Scripts** tab: `Date | Topic ID | Topic Title | Hook | Narration Script | Storyboard Notes | Approval Status | Notes | Run Timestamp`

Change `Approval Status` from `PENDING` → `APPROVED` or `REJECTED` in the sheet.

## Setup

### 1. Google Cloud Project

1. Create a project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable **Gmail API** and **Google Sheets API**
3. Create **OAuth 2.0 credentials** (Desktop app type) → note `client_id` and `client_secret`

### 2. Get OAuth Refresh Token (one-time, local)

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env
python scripts/gmail_auth_setup.py
# Copy the printed GMAIL_REFRESH_TOKEN and GOOGLE_SHEETS_REFRESH_TOKEN into .env
```

### 3. Google Spreadsheet

Create a spreadsheet with 3 tabs: `Topics`, `LinkedIn Drafts`, `Video Scripts`. Add header rows matching the schema above. Copy the spreadsheet ID from the URL into `SPREADSHEET_ID` in `.env`.

### 4. Configure Senders & Brand Docs

- `config/settings.py` → add newsletter sender addresses to `NEWSLETTER_SENDERS`
- `docs/brand_brain.md` → your brand voice and identity
- `docs/linkedin_rules.md` → LinkedIn content rules
- `docs/video_script_rules.md` → video script rules

### 5. Run Locally

```bash
python -m src.pipeline
```

## Deploy to Railway

1. Create a new project in Railway → connect this GitHub repo
2. Add a **Cron Service** (Railway auto-reads `railway.toml` for schedule + command)
3. Add these environment variables under **Variables**:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `GMAIL_CLIENT_ID` | From Google Cloud OAuth2 creds |
| `GMAIL_CLIENT_SECRET` | From Google Cloud OAuth2 creds |
| `GMAIL_REFRESH_TOKEN` | From `gmail_auth_setup.py` output |
| `GOOGLE_SHEETS_REFRESH_TOKEN` | Same value as `GMAIL_REFRESH_TOKEN` |
| `SPREADSHEET_ID` | From your Google Sheet URL |

4. Push to GitHub → Railway auto-deploys. Use **Run Now** in the dashboard to trigger manually.

## Environment Variables

Copy `.env.example` to `.env` and fill in all values. Never commit `.env` — it's gitignored.

## Tech Stack

- **Python 3.11+**
- **Anthropic Claude** (`claude-haiku-4-5`) — topic extraction + content generation
- **Gmail API** — OAuth2 read-only email fetch
- **Google Sheets API** — OAuth2 row appends
- **Railway** — cron deployment
- **tenacity** — retry with exponential backoff
