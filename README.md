# Daily Tech & AI Brief

An automated daily briefing on the most important stories in AI, robotics, and tech, summarized by Google Gemini and committed to this repo every morning.

📰 **Today's brief:** [LATEST.md](LATEST.md)
🗂️ **Archive:** [briefs/](briefs/)

## How it works

1. Every morning, a GitHub Actions workflow runs `scripts/daily_brief.py`.
2. The script pulls the last day's headlines from public RSS feeds (Hacker News, TechCrunch AI, The Verge AI, MIT Technology Review, Google AI Blog).
3. Gemini picks the 6 to 10 most significant stories, groups them by topic (AI & ML, Robotics, Industry, Developer Tools), and writes a short summary of each with a link to the source.
4. The brief is saved to `briefs/YYYY/MM/YYYY-MM-DD.md` and `LATEST.md`, then committed.

If Gemini is unavailable, the script falls back to a plain list of headlines, so the daily brief is never empty.

## Why I built it

I wanted a low-effort way to stay current on AI and robotics news for my work in robot learning data and for technical interviews, and a searchable archive I can look back on.

## Tech stack

- **Python** with `feedparser` for RSS and the `google-genai` SDK for Gemini
- **GitHub Actions** for daily scheduling
- **Markdown** for the briefs, readable directly on GitHub

## Setup

1. Add your Gemini API key (from [Google AI Studio](https://aistudio.google.com)) as a repository secret: **Settings → Secrets and variables → Actions → New repository secret**, named `GEMINI_API_KEY`.
2. In `.github/workflows/daily-brief.yml`, replace the commit email with your GitHub noreply email.
3. Optional: to use a different model, add a repository **variable** named `GEMINI_MODEL`.
4. Run it once manually from the **Actions** tab to test.

## Run locally

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"
python scripts/daily_brief.py
```

## Customize

Edit the `FEEDS` list or the `PROMPT` at the top of `scripts/daily_brief.py` to change sources, topics, or the style of the brief.

## Disclaimer

Summaries are AI-generated from headlines and short descriptions. Follow the links for the full stories.
