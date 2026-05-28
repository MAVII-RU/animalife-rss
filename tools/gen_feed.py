#!/usr/bin/env python3
"""
Deterministic, Yandex Dzen-compliant RSS generator for AnimaLife.

Scans articles/<slug>/index.html and rebuilds feed.xml so EVERY item has:
  - full article body in <content:encoded> (absolute URLs, cleaned tags)
  - <enclosure> for the cover image
  - a stable, non-future <pubDate>

pubDate resolution order per slug:
  1. articles/<slug>/pubdate.txt  (RFC-822 line, written by the publish job)
  2. pubDate already present in the current feed.xml  (preserve history)
  3. mtime of index.html

Items with pubDate in the future are skipped (Dzen rejects future dates),
so articles can be written ahead of time and surface through the day.

Usage: python3 tools/gen_feed.py   (run from repo root)
"""
import os
import re
import sys
import html
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime, parsedate_to_datetime
from xml.sax.saxutils import escape

BASE = "https://mavii-ru.github.io/animalife-rss"
MSK = timezone(timedelta(hours=3))

CHANNEL = {
    "title": "AnimaLife — про кошек и собак",
    "link": BASE + "/",
    "description": ("Медиа AnimaLife: статьи о жизни с кошками и собаками, "
                    "AI-переводчике звуков, ветеринарии и уходе. "
                    "Бесплатное AI-приложение в Telegram и MAX мессенджере."),
    "language": "ru",
    "creator": "AnimaLife",
}

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def existing_pubdates(feed_path):
    """slug -> datetime from the current feed.xml (to preserve assigned dates)."""
    out = {}
    if not os.path.exists(feed_path):
        return out
    txt = read(feed_path)
    for item in re.findall(r"<item>.*?</item>", txt, re.S):
        m_link = re.search(r"<link>(.*?)</link>", item)
        m_date = re.search(r"<pubDate>(.*?)</pubDate>", item)
        if not (m_link and m_date):
            continue
        slug = m_link.group(1).rstrip("/").split("/")[-1]
        try:
            out[slug] = parsedate_to_datetime(m_date.group(1).strip())
        except Exception:
            pass
    return out


def resolve_pubdate(slug, art_dir, prev):
    pf = os.path.join(art_dir, "pubdate.txt")
    if os.path.exists(pf):
        try:
            return parsedate_to_datetime(read(pf).strip())
        except Exception:
            pass
    if slug in prev:
        return prev[slug]
    ts = os.path.getmtime(os.path.join(art_dir, "index.html"))
    return datetime.fromtimestamp(ts, MSK)


def extract_title(doc, slug):
    m = re.search(r"<title>(.*?)</title>", doc, re.S | re.I)
    if m:
        return html.unescape(m.group(1).strip())
    m = re.search(r"<h1[^>]*>(.*?)</h1>", doc, re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip()) if m else slug


def extract_description(doc):
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', doc, re.S | re.I)
    if m:
        return html.unescape(m.group(1).strip())
    m = re.search(r'<p class="lead">(.*?)</p>', doc, re.S | re.I)
    if m:
        return html.unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip())
    return ""


def extract_body(doc):
    """Body = from end of </h1> up to the first <hr>/<footer>/'Все статьи' nav."""
    start = re.search(r"</h1>", doc, re.I)
    s = start.end() if start else 0
    tail = doc[s:]
    end_markers = [r"<hr\b", r"<footer", r'<p>\s*<a href="/animalife-rss/archive\.html">\s*←']
    cut = len(tail)
    for pat in end_markers:
        m = re.search(pat, tail, re.I)
        if m:
            cut = min(cut, m.start())
    return tail[:cut].strip()


def absolutize(body, slug):
    art = f"{BASE}/articles/{slug}"
    # relative asset src/href (e.g. images/cover.jpg) -> absolute under the article
    body = re.sub(r'(src|href)="(?!https?://|/|#|mailto:)([^"]+)"',
                  lambda m: f'{m.group(1)}="{art}/{m.group(2)}"', body)
    # root-absolute paths (/animalife-rss/...) -> full URL
    body = re.sub(r'(src|href)="/animalife-rss/', f'\\1="{BASE}/', body)
    return body


def clean_body(body, slug):
    body = absolutize(body, slug)
    # CTA divs -> blockquote (Dzen-friendly); these are the only <div> in articles
    body = body.replace('<div class="cta">', "<blockquote>").replace("</div>", "</blockquote>")
    # drop class attributes (cosmetic, Dzen ignores them)
    body = re.sub(r'\s+class="[^"]*"', "", body)
    # collapse excess blank lines
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


def cover_enclosure(slug, art_dir):
    cov = os.path.join(art_dir, "images", "cover.jpg")
    if os.path.exists(cov):
        return f"{BASE}/articles/{slug}/images/cover.jpg", os.path.getsize(cov)
    return None, 0


def build_item(slug, art_dir, prev, now):
    doc = read(os.path.join(art_dir, "index.html"))
    pub = resolve_pubdate(slug, art_dir, prev)
    if pub > now:
        return None, pub  # future-dated: surface later
    title = extract_title(doc, slug)
    desc = extract_description(doc)
    body = clean_body(extract_body(doc), slug)
    link = f"{BASE}/articles/{slug}/"
    cov_url, cov_len = cover_enclosure(slug, art_dir)

    parts = [
        "    <item>",
        f"      <title>{escape(title)}</title>",
        f"      <link>{link}</link>",
        f'      <guid isPermaLink="true">{link}</guid>',
        f"      <pubDate>{format_datetime(pub)}</pubDate>",
        f"      <dc:creator>{escape(CHANNEL['creator'])}</dc:creator>",
        f"      <description><![CDATA[{desc}]]></description>",
    ]
    if cov_url:
        parts.append(f'      <enclosure url="{cov_url}" length="{cov_len}" type="image/jpeg"/>')
    parts.append(f"      <content:encoded><![CDATA[{body}]]></content:encoded>")
    parts.append("    </item>")
    return "\n".join(parts), pub


def main():
    now = datetime.now(MSK)
    feed_path = os.path.join(REPO, "feed.xml")
    prev = existing_pubdates(feed_path)
    art_root = os.path.join(REPO, "articles")

    rows = []
    skipped_future = 0
    for slug in sorted(os.listdir(art_root)):
        art_dir = os.path.join(art_root, slug)
        if not os.path.isfile(os.path.join(art_dir, "index.html")):
            continue
        item, pub = build_item(slug, art_dir, prev, now)
        if item is None:
            skipped_future += 1
            continue
        rows.append((pub, item))

    rows.sort(key=lambda r: r[0], reverse=True)
    items_xml = "\n\n".join(r[1] for r in rows)
    last_build = format_datetime(rows[0][0]) if rows else format_datetime(now)

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(CHANNEL['title'])}</title>
    <link>{CHANNEL['link']}</link>
    <description>{escape(CHANNEL['description'])}</description>
    <language>{CHANNEL['language']}</language>
    <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{last_build}</lastBuildDate>

{items_xml}
  </channel>
</rss>
"""
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"feed.xml written: {len(rows)} items, {skipped_future} future-dated skipped")


if __name__ == "__main__":
    main()
