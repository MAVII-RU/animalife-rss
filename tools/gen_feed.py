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
import urllib.request
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime, parsedate_to_datetime
from xml.sax.saxutils import escape

try:
    from PIL import Image
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False

BASE = "https://mavii-ru.github.io/animalife-rss"
MSK = timezone(timedelta(hours=3))

# Yandex Dzen draws its own grey placeholder instead of the card cover when the
# image is narrower than ~1280px. Upscale any undersized cover to MIN_COVER_W so
# every card renders. Aspect is preserved; the cache-buster (?v=<filesize>) updates
# automatically once the file changes, so Dzen re-fetches the fixed image.
MIN_COVER_W = 1920


def ensure_cover_size(cov):
    """Upscale a cover narrower than MIN_COVER_W in place. No-op without PIL."""
    if not _HAS_PIL:
        return
    try:
        with Image.open(cov) as im:
            w, h = im.size
            if w >= MIN_COVER_W:
                return
            nh = round(h * MIN_COVER_W / w)
            im.convert("RGB").resize((MIN_COVER_W, nh), Image.LANCZOS).save(
                cov, "JPEG", quality=90)
    except Exception:
        pass

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
    # UTM: feed (Dzen) copies carry source=dzen; the on-site HTML keeps source=github
    body = re.sub(r'(https://t\.me/animalifebot)\?start=[a-z0-9_]+', r'\1?start=dzen', body)
    # CTA cards -> Dzen-friendly blockquote (Dzen strips the button chrome anyway; keep
    # the bold title, text and links). The CTA is the only <div> in articles and has no
    # nested div, so .*? stops at its own </div>.
    body = re.sub(r'<div class="cta"[^>]*>(.*?)</div>', r'<blockquote>\1</blockquote>', body, flags=re.S)
    # subscribe-to-channel nudge -> same Dzen-friendly blockquote (no nested div)
    body = re.sub(r'<div class="subcta"[^>]*>(.*?)</div>', r'<blockquote>\1</blockquote>', body, flags=re.S)
    # drop class/style attributes (cosmetic, Dzen ignores/sanitizes them)
    body = re.sub(r'\s+(?:class|style)="[^"]*"', "", body)
    # collapse excess blank lines
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


def ensure_cover(slug, art_dir, title):
    """Best-effort self-heal: if an article has no cover, generate a real AI one now
    (Vertex/Nano Banana, animal-verified) so a coverless card NEVER surfaces on Dzen.
    Returns True if a cover exists afterwards. Safe no-op on any failure (then the
    article is simply held back until a cover is produced)."""
    cov = os.path.join(art_dir, "images", "cover.jpg")
    if os.path.exists(cov):
        return True
    try:
        sys.path.insert(0, "/home/max/MAVII_AGENTS/scripts/site_publish")
        from ai_cover import generate
        os.makedirs(os.path.dirname(cov), exist_ok=True)
        if generate(slug, title, cov):
            sys.stderr.write(f"[gen_feed] self-healed missing cover: {slug}\n")
            return True
    except Exception as e:
        sys.stderr.write(f"[gen_feed] cover gen failed for {slug}: {e}\n")
    return os.path.exists(cov)


def cover_live(slug):
    """True if the cover is already fetchable on GitHub Pages (HTTP 200).

    The ultimate guard against grey Dzen cards: even when a cover exists locally and
    its enclosure URL is in the feed, Dzen imports a GREY card (and caches it forever)
    if it crawls the feed before that cover has propagated to Pages. So a NEWLY
    surfacing item is held back until its cover URL actually resolves; it surfaces on
    the next tick (≤1h later) once the cover is live. Already-surfaced items are kept.
    """
    url = f"{BASE}/articles/{slug}/images/cover.jpg"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception:
        return False


def cover_enclosure(slug, art_dir):
    cov = os.path.join(art_dir, "images", "cover.jpg")
    if os.path.exists(cov):
        ensure_cover_size(cov)
        return f"{BASE}/articles/{slug}/images/cover.jpg", os.path.getsize(cov)
    return None, 0


def build_item(slug, art_dir, prev, now):
    doc = read(os.path.join(art_dir, "index.html"))
    pub = resolve_pubdate(slug, art_dir, prev)
    if pub > now:
        return None, pub, "future"  # future-dated: surface later
    title = extract_title(doc, slug)
    if not ensure_cover(slug, art_dir, title):
        return None, pub, "nocover"  # hold back: never surface a blank Dzen card
    # A newly surfacing item must have its cover already LIVE on Pages, or Dzen
    # caches a grey card forever. Held-back items surface next tick once the cover
    # (committed+pushed this run by publish_tick) has propagated. prev = already live.
    if slug not in prev and not cover_live(slug):
        return None, pub, "nocover"
    desc = extract_description(doc)
    body = clean_body(extract_body(doc), slug)
    link = f"{BASE}/articles/{slug}/"
    cov_url, cov_len = cover_enclosure(slug, art_dir)
    # cache-bust cover URL by file size so Dzen / caches re-fetch when the image changes
    if cov_url:
        cov_url = f"{cov_url}?v={cov_len}"
        body = body.replace(f"{BASE}/articles/{slug}/images/cover.jpg",
                            f"{BASE}/articles/{slug}/images/cover.jpg?v={cov_len}")

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
    return "\n".join(parts), pub, "ok"


def main():
    now = datetime.now(MSK)
    feed_path = os.path.join(REPO, "feed.xml")
    prev = existing_pubdates(feed_path)
    art_root = os.path.join(REPO, "articles")

    rows = []
    skipped_future = 0
    nocover = []
    for slug in sorted(os.listdir(art_root)):
        art_dir = os.path.join(art_root, slug)
        if not os.path.isfile(os.path.join(art_dir, "index.html")):
            continue
        item, pub, status = build_item(slug, art_dir, prev, now)
        if status == "future":
            skipped_future += 1
            continue
        if status == "nocover":
            nocover.append(slug)
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
    msg = f"feed.xml written: {len(rows)} items, {skipped_future} future-dated skipped"
    if nocover:
        msg += f", {len(nocover)} held back (no cover): {', '.join(nocover)}"
    print(msg)


if __name__ == "__main__":
    main()
