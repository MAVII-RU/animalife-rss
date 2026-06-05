#!/usr/bin/env python3
"""
Dzen "Медицинская тематика" linter for AnimaLife articles.

Yandex Dzen restricts reach (subscribers-only) and disables monetization for
content it classifies as medical advice: symptoms, diagnosis, treatment,
first-aid, drug names and dosages. This scans every article's TITLE +
DESCRIPTION + BODY for the lexical signals that trip that classifier and
prints a weighted risk report so we can reframe an article BEFORE it ships.

Goal of a clean article: write about behaviour, prevention, owner decisions
and "when to see a vet" — NOT diagnosis/treatment/dosages. The vet does the
medicine; we help the owner notice and decide.

Usage:
  python3 tools/dzen_lint.py                 # report all articles, sorted by risk
  python3 tools/dzen_lint.py <slug> [...]    # report only these slugs (full hits)
  python3 tools/dzen_lint.py --fail 8        # exit 1 if any article scores >= 8

Exit code is 0 unless --fail THRESHOLD is given and exceeded (for CI/cron).
"""
import os
import re
import sys
import html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(REPO, "articles")

# (regex, weight, label). Weight reflects how strongly the token reads as
# "medical advice" to Dzen. Title/description hits are counted x3 (the
# classifier weighs the card heading far more than buried body text).
PATTERNS = [
    # --- HIGH: explicit drug names / dosages / clinical treatment ---
    (r"\bмг/кг\b|\bмг на кг\b|\bмл/кг\b", 5, "доза (мг/кг)"),
    (r"\b\d+\s*мг\b|\b\d+\s*мл\b(?!\s*вод)", 4, "доза в мг/мл"),
    (r"силимарин|ацетилцистеин|эспумизан|эспарокс|симетикон|"
     r"празиквантел|пирантел|фенбендазол|мильбемицин|"
     r"амоксициллин|метронидазол|цефтриаксон|но-шпа|дротаверин|"
     r"активированн\w+ угол|сорбент|энтеросгел|смект", 5, "название препарата"),
    (r"антибиотик|инъекц|внутривенн|внутримышечн|подкожн\w+ введени|капельниц", 4, "инъекции/в-в"),
    (r"дозиров|дозу\b|дозы\b|по схеме приёма|кратность приёма", 4, "дозировка"),
    # --- HIGH: diagnosis / treatment framing ---
    (r"как лечить|чем лечить|схема лечени|курс лечени|лечени[ея]\b|вылечит", 4, "лечение"),
    (r"первая помощь|неотложн|реанимац|купировать", 4, "первая помощь"),
    (r"диагноз|диагностик|поставить диагноз", 3, "диагноз"),
    (r"передозиров|интоксикац|отравлени", 3, "отравление/интоксикация"),
    (r"дегельминтизац|глистогон", 3, "дегельминтизация"),
    # --- MEDIUM: symptom-list / "what to do when sick" framing ---
    (r"симптом", 2, "симптомы"),
    (r"что делать при\s+(отравлени|заворот|присту|болезн|температур|рвот|поноc|судорог)", 3,
     "«что делать при <болезни>»"),
    (r"признаки\s+(болезн|отравлени|инфекц|заболеван)", 2, "признаки болезни"),
    (r"вызвать рвоту|когда не вызывать рвоту", 3, "вызвать рвоту"),
    (r"некроз|аритми|токсическ\w+ шок", 2, "тяжёлая клиника"),
    # --- LOW: clinical vocabulary that adds up (small weights — common words) ---
    (r"гипертерми|гипотерми", 2, "температура тела"),
    (r"патологи|синдром\b", 1, "клинич. лексика"),
]

COMPILED = [(re.compile(p, re.I), w, lbl) for p, w, lbl in PATTERNS]

# Reframing hints printed alongside the worst categories.
HINTS = {
    "название препарата": "убери конкретные названия и дозы → «препарат подбирает ветеринар»",
    "доза (мг/кг)": "убери дозы полностью — это прямой сигнал мед.совета",
    "доза в мг/мл": "убери цифровые дозы",
    "дозировка": "убери дозировки",
    "лечение": "не «как лечить», а «когда вести к ветеринару» / «как снизить риск»",
    "первая помощь": "переформулируй в «что заметить и когда срочно к врачу»",
    "симптомы": "не «симптомы», а «на что обращать внимание» / «сигналы тревоги»",
    "отравление/интоксикация": "сделай акцент на профилактике и «как отучить подбирать»",
    "дегельминтизация": "пиши «профилактика», расписание подбирает ветеринар",
    "диагноз": "убери диагностику — это поле ветеринара",
    "вызвать рвоту": "убери инструкции по экстренным манипуляциям",
}


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def fields(doc, slug):
    m = re.search(r"<title>(.*?)</title>", doc, re.S | re.I)
    title = html.unescape(m.group(1).strip()) if m else slug
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', doc, re.S | re.I)
    desc = html.unescape(m.group(1).strip()) if m else ""
    # body text only (strip tags) from <h1> onward
    s = re.search(r"<h1", doc, re.I)
    body = doc[s.start():] if s else doc
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html.unescape(body)
    return title, desc, body


def scan(slug):
    doc = read(os.path.join(ART, slug, "index.html"))
    title, desc, body = fields(doc, slug)
    card = title + " \n " + desc          # weighted x3
    score = 0
    cats = {}            # label -> count
    card_hits = set()
    for rx, w, lbl in COMPILED:
        c = len(rx.findall(card))
        b = len(rx.findall(body))
        if c:
            score += w * 3 * c
            card_hits.add(lbl)
        if b:
            score += w * b
        if c + b:
            cats[lbl] = cats.get(lbl, 0) + c + b
    return score, cats, card_hits, title


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    fail_at = None
    if "--fail" in sys.argv:
        i = sys.argv.index("--fail")
        fail_at = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) else 8
        argv = [a for a in argv if a != str(fail_at)]

    slugs = argv or sorted(
        s for s in os.listdir(ART)
        if os.path.isfile(os.path.join(ART, s, "index.html")))

    results = [(scan(s), s) for s in slugs]
    results.sort(key=lambda r: r[0][0], reverse=True)

    def band(sc):
        if sc >= 35:
            return "🔴 ВЫСОКИЙ"
        if sc >= 18:
            return "🟠 средний"
        if sc >= 8:
            return "🟡 низкий"
        return "🟢 чисто"

    worst = 0
    for (score, cats, card_hits, title), slug in results:
        worst = max(worst, score)
        if score < 8 and not argv:
            continue  # hide clean ones in full-feed mode
        print(f"{band(score):>12}  {score:>3}  {slug}")
        if score >= 3 or argv:
            print(f"               «{title}»")
            top = sorted(cats.items(), key=lambda x: -x[1])
            tags = ", ".join(f"{l}×{n}{' [в карточке]' if l in card_hits else ''}"
                             for l, n in top)
            print(f"               {tags}")
            for lbl, _ in top[:3]:
                if lbl in HINTS:
                    print(f"               → {HINTS[lbl]}")
        print()

    clean = sum(1 for (sc, *_), _ in results if sc < 8)
    print(f"Итого: {len(results)} статей · 🟢 чисто (<8): {clean} · худший балл: {worst}")
    print("Шкала: <8 чисто · 8–17 низкий · 18–34 средний · ≥35 высокий (Дзен урежет охват)")

    if fail_at is not None and worst >= fail_at:
        print(f"FAIL: есть статья с баллом ≥ {fail_at}")
        sys.exit(1)


if __name__ == "__main__":
    main()
