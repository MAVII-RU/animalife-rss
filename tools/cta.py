#!/usr/bin/env python3
"""Bold, button-style in-article CTA for AnimaLife with a pool of varied app-install offers.

One source of truth for the CTA used both on the site (animaapp.ru) and in the
Dzen feed. The markup is FLAT (div > p,p,p > a,a — no nested divs) and uses INLINE
styles so it renders as a bright orange card with real buttons everywhere external
CSS is honoured, and degrades cleanly to a bold blockquote+links inside Dzen
(gen_feed.clean_body strips class/style and wraps it in <blockquote>).

Offers rotate deterministically per (slug, position) so an article's two CTAs differ
and the whole site shows the full range of offers. No Date/random — crc32 keeps it
reproducible across runs.
"""
import re
import zlib

# Each offer is written to drive an app install, broadly relevant to any pet topic.
OFFERS = [
    {"title": "Спросите AI-ветеринара прямо сейчас",
     "text": "AnimaLife — приложение, где AI-ветеринар отвечает на вопросы о кошке или собаке 24/7. Бесплатно, без записи и очередей.",
     "tg": "Открыть в Telegram", "max": "Открыть в MAX"},
    {"title": "Дневник здоровья питомца — в кармане",
     "text": "Вес, прививки, симптомы и напоминания в одном приложении. AnimaLife следит за здоровьем питомца вместо вас.",
     "tg": "Завести дневник", "max": "Открыть в MAX"},
    {"title": "Не уверены, что это опасно?",
     "text": "Опишите симптом в AnimaLife — AI-ветеринар за минуту подскажет, что в пределах нормы, а когда пора к врачу.",
     "tg": "Спросить AI-ветеринара", "max": "Спросить в MAX"},
    {"title": "Питомец ведёт себя странно?",
     "text": "AnimaLife расшифрует поведение кошки и собаки и подскажет, что делать. Попробуйте бесплатно прямо в мессенджере.",
     "tg": "Открыть в Telegram", "max": "Открыть в MAX"},
    {"title": "Здоровье питомца под контролем",
     "text": "AI-ветеринар, дневник здоровья и персональные советы для вашего питомца — установите AnimaLife бесплатно.",
     "tg": "Установить AnimaLife", "max": "Открыть в MAX"},
    {"title": "Первая помощь — всегда под рукой",
     "text": "AnimaLife подскажет, что делать в тревожной ситуации с питомцем ещё до визита к врачу. Откройте в один тап.",
     "tg": "Открыть AnimaLife", "max": "Открыть в MAX"},
    {"title": "Экономьте на лишних визитах к врачу",
     "text": "Сначала спросите AI-ветеринара в AnimaLife — часто этого достаточно, чтобы понять, нужен ли визит к врачу.",
     "tg": "Спросить бесплатно", "max": "Спросить в MAX"},
    {"title": "Всё о вашем питомце — в одном приложении",
     "text": "AI-ветеринар, дневник, напоминания о прививках и уходе. Установите AnimaLife — это бесплатно, в Telegram и MAX.",
     "tg": "Открыть в Telegram", "max": "Открыть в MAX"},
]

MAX_URL = "https://max.ru/id235606731027_5_bot"


def _tg_url(slug):
    # underscore the slug so gen_feed (Dzen ->?start=dzen) and gen_article (site ->?start=site)
    # link-rewrites, which match [a-z0-9_]+, capture the whole tag.
    return f"https://t.me/animalifebot?start=dzen_{slug.replace('-', '_')}"


def pick(slug, n=0):
    idx = (zlib.crc32(slug.encode("utf-8")) + n) % len(OFFERS)
    return OFFERS[idx]


def render(slug, n=0):
    """Return the bold CTA HTML for the n-th CTA in an article."""
    o = pick(slug, n)
    tg = _tg_url(slug)
    return (
        '<div class="cta" style="background:linear-gradient(135deg,#FF8A2B 0%,#F4731F 55%,#E8590C 100%);'
        'border:0;border-radius:18px;padding:22px 24px;margin:30px 0;'
        'box-shadow:0 16px 34px -14px rgba(232,89,12,.6)">\n'
        f'<p style="margin:0 0 6px;font-size:20px;line-height:1.25;color:#ffffff;font-weight:800">'
        f'<b style="color:#ffffff">🐾 {o["title"]}</b></p>\n'
        f'<p style="margin:0 0 16px;font-size:15.5px;line-height:1.55;color:#ffffff;opacity:.96">{o["text"]}</p>\n'
        '<p style="margin:0">'
        f'<a href="{tg}" style="display:inline-block;background:#ffffff;color:#E8590C;font-weight:800;'
        'font-size:15px;line-height:1;padding:14px 22px;border-radius:9999px;text-decoration:none;'
        f'margin:4px 8px 4px 0;box-shadow:0 8px 18px -8px rgba(0,0,0,.35)">{o["tg"]} →</a> '
        f'<a href="{MAX_URL}" style="display:inline-block;background:rgba(255,255,255,.18);color:#ffffff;'
        'font-weight:700;font-size:15px;line-height:1;padding:14px 22px;border-radius:9999px;'
        f'text-decoration:none;margin:4px 0;border:1.5px solid rgba(255,255,255,.65)">{o["max"]} →</a>'
        '</p>\n'
        '</div>'
    )


# Match a whole CTA block: the legacy flat <div class="cta">…</div> OR a previously
# upgraded one <div class="cta" style="…">…</div>. Inner has no nested <div>, so the
# first </div> is the block's own close.
CTA_RE = re.compile(r'<div class="cta"[^>]*>.*?</div>', re.S)


def upgrade_html(slug, doc):
    """Replace every CTA block in an article's HTML with a freshly rendered bold CTA.
    Returns (new_doc, count)."""
    n = [0]

    def repl(_m):
        block = render(slug, n[0])
        n[0] += 1
        return block

    return CTA_RE.sub(repl, doc), n[0]
