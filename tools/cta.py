#!/usr/bin/env python3
"""Bold, button-style in-article CTA for AnimaLife — matched to what the article is about.

One source of truth for the CTA used both on the site (animaapp.ru) and in the
Dzen feed. The markup is FLAT (div > p,p,p > a,a — no nested divs) and uses INLINE
styles so it renders as a bright orange card with real buttons everywhere external
CSS is honoured, and degrades cleanly to a bold blockquote+links inside Dzen
(gen_feed.clean_body strips class/style and wraps it in <blockquote>).

WHY topic-matched (директива Максима 18.08.2026): раньше CTA был общий («Первая
помощь — всегда под рукой») и не имел отношения к тому, что человек только что
читал. Статья на 153 визита давала 0 переходов. Теперь CTA продолжает мысль
статьи: в статье про симптом — «проверьте симптом», в породной — «план ухода под
породу», в поведенческой — «разберите поведение». Человек читает про свою
проблему и в том же месте получает конкретный способ её закрыть.

Тема и животное берутся из самой статьи: строка `<p class="meta">… · Поведение ·
Собаки</p>` и `<h1>`. Порода — из части заголовка до двоеточия. Никаких
Date/random: один и тот же вход даёт один и тот же выход.
"""
import re
import zlib

# --- что показываем в зависимости от темы статьи -------------------------------
# {A_WITH} — «с собакой», {A_ACC} — «свою собаку», {A_GEN} — «вашей собаки»,
# {A_NOM} — «собака», {BREED} — название породы из заголовка.
TOPICS = {
    "health": [
        {"title": "Не уверены, что {A_WITH} всё в порядке?",
         "text": "Опишите симптом в AnimaLife или пришлите фото — AI-ветеринар за минуту скажет, "
                 "можно ли наблюдать дома или ехать к врачу сегодня. Бесплатно, круглосуточно, без записи.",
         "tg": "Проверить симптом", "max": "Проверить в MAX"},
        {"title": "Проверьте {A_ACC}, пока помните",
         "text": "Откройте AnimaLife, опишите, что беспокоит, — получите разбор и понятный план действий. "
                 "Ответ за минуту, бесплатно и без очередей.",
         "tg": "Спросить AI-ветеринара", "max": "Спросить в MAX"},
    ],
    "breed": [
        {"title": "У вас {BREED}?",
         "text": "AnimaLife соберёт уход под породу: к каким болезням есть склонность, что проверять "
                 "по возрасту, чем кормить и когда пора к врачу. Бесплатно, прямо в мессенджере.",
         "tg": "Собрать план ухода", "max": "Собрать в MAX"},
        {"title": "Ваш питомец — {BREED}?",
         "text": "Заведите профиль в AnimaLife: приложение запомнит породу, возраст и вес и будет "
                 "подсказывать по уходу именно для неё. Вопросы AI-ветеринару — круглосуточно и бесплатно.",
         "tg": "Завести профиль", "max": "Завести в MAX"},
    ],
    "behavior": [
        {"title": "Хотите понять, что {A_NOM} говорит вам?",
         "text": "Опишите ситуацию или пришлите видео в AnimaLife — AI разберёт поведение вашего питомца "
                 "и подскажет, что делать. Бесплатно, ответ за минуту.",
         "tg": "Разобрать поведение", "max": "Разобрать в MAX"},
        {"title": "У {A_GEN} так же?",
         "text": "Расскажите в AnimaLife, как ведёт себя ваш питомец, — приложение объяснит причину "
                 "и даст пошаговый план. Бесплатно, без записи к специалисту.",
         "tg": "Разобрать свой случай", "max": "Разобрать в MAX"},
    ],
    "feeding": [
        {"title": "Не уверены, что рацион подходит?",
         "text": "Напишите в AnimaLife, чем кормите, — приложение покажет, чего не хватает, и рассчитает "
                 "порцию под вес, возраст и активность. Бесплатно.",
         "tg": "Проверить рацион", "max": "Проверить в MAX"},
        {"title": "Соберите рацион под {A_ACC}",
         "text": "AnimaLife учитывает породу, возраст, вес и образ жизни и подсказывает, сколько и чем кормить. "
                 "Плюс напоминания о кормлении и контроль веса.",
         "tg": "Собрать рацион", "max": "Собрать в MAX"},
    ],
    "care": [
        {"title": "Чтобы уход не держать в голове",
         "text": "AnimaLife напомнит, когда стричь когти, вычёсывать, купать и обрабатывать от паразитов, "
                 "и заведёт дневник по вашему питомцу. Бесплатно.",
         "tg": "Настроить напоминания", "max": "Настроить в MAX"},
        {"title": "Заведите дневник ухода за {A_INSTR}",
         "text": "Вес, шерсть, обработки, прививки — всё в одном месте. А если что-то смущает, "
                 "AI-ветеринар ответит круглосуточно и бесплатно.",
         "tg": "Завести дневник", "max": "Завести в MAX"},
    ],
    "training": [
        {"title": "Застряли на этом этапе воспитания?",
         "text": "Опишите ситуацию в AnimaLife — получите разбор причины и пошаговый план на неделю "
                 "под возраст вашего питомца. Бесплатно.",
         "tg": "Получить план", "max": "Получить в MAX"},
        {"title": "Разберите свой случай в AnimaLife",
         "text": "AI подскажет, что закрепляет нежелательное поведение и как переучить без наказаний. "
                 "Ответ за минуту, круглосуточно и бесплатно.",
         "tg": "Разобрать случай", "max": "Разобрать в MAX"},
    ],
    "safety": [
        {"title": "Что делать, если что-то пойдёт не так",
         "text": "AnimaLife подскажет первые шаги при отравлении, травме, перегреве или укусе — "
                 "ещё до того, как вы доедете до врача. Пусть будет под рукой.",
         "tg": "Открыть первую помощь", "max": "Открыть в MAX"},
        {"title": "Поставьте приложение заранее",
         "text": "Первая помощь, дневник здоровья и AI-ветеринар 24/7 — в одном месте. Бесплатно: "
                 "установите, пока не понадобилось.",
         "tg": "Установить AnimaLife", "max": "Открыть в MAX"},
    ],
    "general": [
        {"title": "Спросите AI-ветеринара о {A_GEN}",
         "text": "AnimaLife отвечает на вопросы о кошках и собаках круглосуточно, ведёт дневник здоровья "
                 "и напоминает о прививках. Бесплатно, без записи.",
         "tg": "Открыть AnimaLife", "max": "Открыть в MAX"},
        {"title": "Всё о вашем питомце — в одном приложении",
         "text": "AI-ветеринар, дневник здоровья, напоминания об уходе и прививках. Бесплатно, "
                 "в Telegram и MAX.",
         "tg": "Установить AnimaLife", "max": "Открыть в MAX"},
    ],
}

# Теги из строки meta статьи → тема CTA. Порядок = приоритет.
TAG_TOPIC = [
    ("health", ("здоровье", "неотложка", "профилактика", "паразиты", "стоматолог",
                "пищеварен", "гериатр", "болезн", "аллерг")),
    ("breed", ("пород",)),
    ("feeding", ("питание", "корм", "рацион")),
    ("training", ("воспитание", "дрессировка", "щенки", "котята")),
    ("care", ("уход", "груминг", "гигиена", "шерсть")),
    ("safety", ("безопасность", "лето", "зима", "дача", "прогулки", "быт", "документы", "путешеств")),
    ("behavior", ("поведение", "характер", "коммуникац", "психолог", "игра", "стресс",
                  "наблюдение", "общение")),
]

ANIMALS = {
    "dog": {"A_NOM": "собака", "A_ACC": "свою собаку", "A_GEN": "вашей собаки",
            "A_WITH": "с собакой", "A_INSTR": "собакой"},
    "cat": {"A_NOM": "кошка", "A_ACC": "свою кошку", "A_GEN": "вашей кошки",
            "A_WITH": "с кошкой", "A_INSTR": "кошкой"},
    None: {"A_NOM": "питомец", "A_ACC": "своего питомца", "A_GEN": "вашего питомца",
           "A_WITH": "с питомцем", "A_INSTR": "питомцем"},
}

MAX_URL = "https://max.ru/id235606731027_5_bot"
APPSTORE_URL = "https://apps.apple.com/ru/app/animalife/id6786551354"

H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
META_RE = re.compile(r'<p class="meta">(.*?)</p>', re.S)
TAGS_RE = re.compile(r"<[^>]+>")

# «Алабай дома», «Бигль не идёт на отзыв», «Бенгальская кошка в квартире» →
# режем хвост, оставляем название породы.
BREED_CUT = re.compile(r"\s+(?:в|на|не|и|с|для|дома|у|как|почему|это)\b.*$", re.I)


def _text(html_fragment):
    return TAGS_RE.sub("", html_fragment or "").replace("&nbsp;", " ").strip()


def parse_article(doc):
    """Вытащить из HTML статьи заголовок и теги (строка meta)."""
    m = H1_RE.search(doc)
    title = _text(m.group(1)) if m else ""
    m = META_RE.search(doc)
    meta = _text(m.group(1)) if m else ""
    tags = [t.strip() for t in meta.split("·")][2:]
    return title, tags


def topic_of(tags):
    # Совпадение только с НАЧАЛА слова, иначе «воспитание» ловится ключом «питание».
    joined = " ".join(tags).lower()
    for name, keys in TAG_TOPIC:
        if any(re.search(r"\b" + re.escape(k), joined) for k in keys):
            return name
    return "general"


def animal_of(title, tags, slug=""):
    hay = (" ".join(tags) + " " + title + " " + slug.replace("-", " ")).lower()
    dog = any(k in hay for k in ("собак", "пёс", "пес ", "щен", "dog", "puppy"))
    cat = any(k in hay for k in ("кош", "кот", "котён", "cat", "kitten"))
    if dog and not cat:
        return "dog"
    if cat and not dog:
        return "cat"
    return None


def breed_of(title, animal):
    """Название породы из заголовка «<Порода>: <хук>». Падает в общее, если не уверены."""
    if ":" not in title:
        return None
    head = title.split(":")[0].strip()
    head = re.sub(r"\s*\([^)]*\)", "", head).strip()  # убрать «(American Wirehair)»
    head = BREED_CUT.sub("", head).strip(" ,—-")
    if not head or len(head.split()) > 4 or len(head) < 4:
        return None
    return head[0].lower() + head[1:]


def _fill(s, vals):
    for k, v in vals.items():
        s = s.replace("{" + k + "}", v)
    return s


def _tg_url(slug):
    # underscore the slug so gen_feed (Dzen ->?start=dzen) and gen_article (site ->?start=site)
    # link-rewrites, which match [a-z0-9_]+, capture the whole tag.
    return f"https://t.me/animalifebot?start=dzen_{slug.replace('-', '_')}"


def pick(slug, n=0, topic="general"):
    """n-й оффер по теме статьи. crc32 от slug решает, с какого варианта начать."""
    variants = TOPICS.get(topic, TOPICS["general"])
    idx = (zlib.crc32(slug.encode("utf-8")) + n) % len(variants)
    return variants[idx]


def render(slug, n=0, title="", tags=None):
    """Вернуть HTML блока CTA под тему конкретной статьи."""
    tags = tags or []
    topic = topic_of(tags)
    animal = animal_of(title, tags, slug)
    vals = dict(ANIMALS[animal])
    if topic == "breed":
        breed = breed_of(title, animal)
        if breed:
            vals["BREED"] = breed
        else:
            # породу из заголовка не вытащили — не выдумываем, уходим в общий оффер
            topic = "general"

    o = pick(slug, n, topic)
    tg = _tg_url(slug)
    title_txt = _fill(o["title"], vals)
    body_txt = _fill(o["text"], vals)
    tg_label = _fill(o["tg"], vals)
    max_label = _fill(o["max"], vals)
    return (
        '<div class="cta" style="background:linear-gradient(135deg,#FF8A2B 0%,#F4731F 55%,#E8590C 100%);'
        'border:0;border-radius:18px;padding:22px 24px;margin:30px 0;'
        'box-shadow:0 16px 34px -14px rgba(232,89,12,.6)">\n'
        f'<p style="margin:0 0 6px;font-size:20px;line-height:1.25;color:#ffffff;font-weight:800">'
        f'<b style="color:#ffffff">🐾 {title_txt}</b></p>\n'
        f'<p style="margin:0 0 16px;font-size:15.5px;line-height:1.55;color:#ffffff;opacity:.96">{body_txt}</p>\n'
        '<p style="margin:0">'
        f'<a href="{tg}" style="display:inline-block;background:#ffffff;color:#E8590C;font-weight:800;'
        'font-size:15px;line-height:1;padding:14px 22px;border-radius:9999px;text-decoration:none;'
        f'margin:4px 8px 4px 0;box-shadow:0 8px 18px -8px rgba(0,0,0,.35)">{tg_label} →</a> '
        f'<a href="{MAX_URL}" style="display:inline-block;background:rgba(255,255,255,.18);color:#ffffff;'
        'font-weight:700;font-size:15px;line-height:1;padding:14px 22px;border-radius:9999px;'
        f'text-decoration:none;margin:4px 0;border:1.5px solid rgba(255,255,255,.65)">{max_label} →</a>'
        '</p>\n'
        f'<p style="margin:12px 0 0;font-size:13.5px;line-height:1.5;color:#ffffff;opacity:.9">У вас iPhone? '
        f'<a href="{APPSTORE_URL}" style="color:#ffffff;text-decoration:underline">'
        'AnimaLife есть в App Store</a></p>\n'
        '</div>'
    )


# Match a whole CTA block: the legacy flat <div class="cta">…</div> OR a previously
# upgraded one <div class="cta" style="…">…</div>. Inner has no nested <div>, so the
# first </div> is the block's own close.
CTA_RE = re.compile(r'<div class="cta"[^>]*>.*?</div>', re.S)


# --- Subscribe-to-channel CTA (Dzen audience growth) ----------------------------
# Distinct from the app-install CTA above: this one asks the reader to SUBSCRIBE to
# the Dzen channel so the channel grows its own audience (the real bottleneck — Dzen
# only distributes a channel that retains & gains subscribers). No external link: in
# the Dzen reader the native «Подписаться» button sits right under the article, so a
# verbal nudge converts; on the site it's a soft reminder card. Light card so it does
# not compete visually with the bright orange app CTA. clean_body() in gen_feed wraps
# class="subcta" into a Dzen <blockquote> just like the app CTA.
SUB_TITLE = "Понравился разбор?"
SUB_TEXT = ("Подпишитесь на канал — каждый день разбираем по одному тревожному "
            "симптому у кошек и собак: что в пределах нормы, а когда пора к врачу. "
            "Подпишитесь, чтобы не пропустить разбор, который может спасти здоровье "
            "вашего питомца.")


def render_subscribe():
    """Return the subscribe-to-channel nudge block (one per article, at the end)."""
    return (
        '<div class="subcta" style="background:#FFF6EE;border:2px solid #FF8A2B;'
        'border-radius:16px;padding:20px 22px;margin:34px 0 8px">\n'
        f'<p style="margin:0 0 6px;font-size:18px;line-height:1.3;color:#E8590C;'
        f'font-weight:800"><b style="color:#E8590C">🐾 {SUB_TITLE}</b></p>\n'
        f'<p style="margin:0;font-size:15.5px;line-height:1.55;color:#3a3a3a">{SUB_TEXT}</p>\n'
        '</div>'
    )


SUBCTA_RE = re.compile(r'<div class="subcta"[^>]*>.*?</div>', re.S)


def ensure_subscribe(doc):
    """Ensure exactly one subscribe nudge sits at the END of the article body.
    Idempotent: replaces an existing one (refreshes copy) or appends before the
    article's closing wrapper. Returns (new_doc, present_bool)."""
    block = render_subscribe()
    if SUBCTA_RE.search(doc):
        return SUBCTA_RE.sub(lambda _m: block, doc, count=1), True
    # Append after the last app CTA if present, else before </article>/</body>.
    last = None
    for m in CTA_RE.finditer(doc):
        last = m
    if last:
        return doc[:last.end()] + "\n" + block + doc[last.end():], True
    for tag in ("</article>", "</main>", "</body>"):
        i = doc.rfind(tag)
        if i != -1:
            return doc[:i] + block + "\n" + doc[i:], True
    return doc + "\n" + block, True


def upgrade_html(slug, doc):
    """Replace every CTA block in an article's HTML with a freshly rendered bold CTA
    matched to that article's topic. Returns (new_doc, count)."""
    title, tags = parse_article(doc)
    n = [0]

    def repl(_m):
        block = render(slug, n[0], title, tags)
        n[0] += 1
        return block

    return CTA_RE.sub(repl, doc), n[0]
