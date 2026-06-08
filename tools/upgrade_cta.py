#!/usr/bin/env python3
"""Rewrite every article's in-article CTA block(s) to the bold button-style component
with rotated app-install offers (see tools/cta.py). Idempotent — re-running re-renders
the same deterministic offer per (slug, position). Run from repo root.

Usage: python3 tools/upgrade_cta.py [slug ...]   (no args = all articles)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cta

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(REPO, "articles")


def main(slugs):
    if not slugs:
        slugs = sorted(d for d in os.listdir(ART)
                       if os.path.isfile(os.path.join(ART, d, "index.html")))
    total_files = total_cta = 0
    for slug in slugs:
        p = os.path.join(ART, slug, "index.html")
        if not os.path.isfile(p):
            print(f"skip (no index): {slug}")
            continue
        doc = open(p, encoding="utf-8").read()
        new, n = cta.upgrade_html(slug, doc)
        # also ensure a subscribe-to-channel nudge at the end (Dzen audience growth)
        new, _ = cta.ensure_subscribe(new)
        if new != doc:
            open(p, "w", encoding="utf-8").write(new)
            total_files += 1
            total_cta += n
            print(f"upgraded {slug}: {n} app CTA(s) + subscribe nudge")
        elif n:
            print(f"unchanged {slug}: {n} CTA(s) + subscribe already current")
        else:
            print(f"subscribe nudge ensured (no app CTA): {slug}")
    print(f"\nDONE: {total_cta} CTA blocks across {total_files} files updated")


if __name__ == "__main__":
    main(sys.argv[1:])
