#!/usr/bin/env python3
"""Generate a daily tech & AI news brief as Markdown.

Pulls recent headlines from a few public RSS feeds, asks Gemini to pick and
summarize the most important stories, and writes the result to
briefs/YYYY/MM/YYYY-MM-DD.md and LATEST.md.

If Gemini is unavailable (no key, quota, outage), it falls back to a plain
list of headlines so the daily brief is never empty.
"""

import calendar
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser

# --- Settings you can tweak -------------------------------------------------

TIMEZONE = ZoneInfo("America/Los_Angeles")
LOOKBACK_HOURS = 30   # only include stories newer than this
MAX_PER_FEED = 8      # cap per source so one feed can't dominate
MAX_ITEMS = 40        # total stories sent to Gemini

# Add, remove, or swap feeds here. A feed that fails is skipped, not fatal.
FEEDS = {
    "Hacker News": "https://hnrss.org/frontpage?points=150",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "MIT Technology Review": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
}

DEFAULT_MODEL = "gemini-3.8-flash"

PROMPT = """You are writing a short daily tech and AI brief for a new-grad \
software engineer who works with robotics and machine learning data and wants \
to stay current for work and job interviews.

From the stories below, pick the 6 to 10 most significant ones. Skip \
duplicates, minor product updates, and promotional posts.

Group them under these Markdown headings, leaving out any heading with no stories:
## AI & Machine Learning
## Robotics
## Industry & Big Tech
## Developer Tools & Engineering

For each story, write one bullet:
- **[Headline in your own words](URL)** (Source): one or two sentences on what \
happened and why it matters.

Rules:
- Use only the information provided below. Do not invent numbers, names, or details.
- Write summaries in your own words. Do not copy sentences from the descriptions.
- Keep the URL exactly as given.
- For (Source), use exactly the source name shown in parentheses for that story.

End with:
## Worth knowing
One or two sentences on the single most important takeaway today, phrased so it \
could come up naturally in a tech interview conversation.

Output Markdown only. Do not add a title.

Stories:
{stories}
"""

# ---------------------------------------------------------------------------


def clean(text, limit=300):
    """Strip HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def published_at(entry):
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime.fromtimestamp(calendar.timegm(value), tz=timezone.utc)
    return None


def fetch_items():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    items, seen = [], set()

    for source, url in FEEDS.items():
        try:
            feed = feedparser.parse(url, agent="daily-tech-brief/1.0")
        except Exception as exc:  # network or parsing failure
            print(f"warning: {source} failed: {exc}", file=sys.stderr)
            continue

        count = 0
        for entry in feed.entries:
            title = clean(entry.get("title"), 200)
            link = entry.get("link")
            if not title or not link:
                continue
            if title.lower() in seen:
                continue
            when = published_at(entry)
            if when and when < cutoff:
                continue

            seen.add(title.lower())
            items.append({
                "source": source,
                "title": title,
                "link": link,
                "summary": clean(entry.get("summary")),
            })
            count += 1
            if count >= MAX_PER_FEED:
                break

        print(f"{source}: {count} stories", file=sys.stderr)

    return items[:MAX_ITEMS]


def summarize_with_gemini(items):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("warning: GEMINI_API_KEY not set, using headline fallback", file=sys.stderr)
        return None

    from google import genai

    model = os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
    stories = "\n".join(
        f"[{i}] ({item['source']}) {item['title']} | {item['summary']} | {item['link']}"
        for i, item in enumerate(items, 1)
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=PROMPT.format(stories=stories),
    )
    text = (response.text or "").strip()

    # Remove a ```markdown fence if the model wrapped its answer in one.
    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text or None


def headline_fallback(items):
    if not items:
        return "_No new stories found in the last day._"

    lines = ["_AI summary unavailable today. Here are the latest headlines._"]
    current = None
    for item in items:
        if item["source"] != current:
            current = item["source"]
            lines += ["", f"## {current}"]
        lines.append(f"- [{item['title']}]({item['link']})")
    return "\n".join(lines).strip()


def main():
    now = datetime.now(TIMEZONE)
    items = fetch_items()

    body = None
    if items:
        try:
            body = summarize_with_gemini(items)
        except Exception as exc:
            print(f"warning: Gemini failed: {exc}", file=sys.stderr)
    if not body:
        body = headline_fallback(items)

    markdown = (
        f"# Tech & AI Brief: {now.strftime('%A, %B %d, %Y')}\n\n"
        f"{body.strip()}\n"
    )

    out_path = Path("briefs") / now.strftime("%Y") / now.strftime("%m") / f"{now:%Y-%m-%d}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    Path("LATEST.md").write_text(markdown, encoding="utf-8")

    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
