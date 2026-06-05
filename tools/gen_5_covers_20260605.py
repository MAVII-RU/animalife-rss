#!/usr/bin/env python3
"""
Generate 5 new covers for AnimaLife — 2026-06-05.
Slugs: dog-water-intoxication, cat-overgrooming-alopecia, dog-park-fights-prevent,
       cat-vet-visit-stress-free, dog-doorbell-barking-fix

Follows the same gen_covers_batch.py pattern:
  - Nano Banana Pro (gemini-3-pro-image-preview)
  - cover_verify gate (resolution, aspect ratio, non-blank)
  - 2 attempts per cover (primary + retry prompt)
  - Saves to articles/<slug>/images/cover.jpg at 2048x1152 JPEG q=85
"""

import os
import sys
import json
import base64
import io
import statistics
import urllib.request
import urllib.error

try:
    from PIL import Image
except ImportError:
    os.system("pip install Pillow -q")
    from PIL import Image

# ── API key ──────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
if not API_KEY:
    _envf = "/home/max/MAVII_AGENTS/secrets/google_ai.env"
    try:
        with open(_envf) as _f:
            for _line in _f:
                if _line.strip().startswith("GOOGLE_AI_API_KEY="):
                    API_KEY = _line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except OSError:
        pass

ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3-pro-image-preview:generateContent"
)
BASE_DIR = "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles"
LOG_FILE = "/home/max/MAVII_AGENTS/logs/activity.log"
ERR_LOG  = "/home/max/MAVII_AGENTS/logs/designer_errors.log"
TARGET_W, TARGET_H = 2048, 1152

# ── Cover definitions ─────────────────────────────────────────────────────────
COVERS = [
    {
        "slug": "dog-water-intoxication",
        "animal": "dog",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A medium-size mixed-breed dog leaping joyfully into a clear blue lake "
            "on a sunny summer day, mid-air above the water surface, sparkling splashes "
            "exploding around its body. The dog's expression is pure joy — mouth open, "
            "ears back, eyes bright. "
            "Light: bright summer midday sun, strong natural light, blue sky with soft clouds. "
            "Composition: dog centered-left, large splash in foreground, open water and sky "
            "filling the right third. "
            "Color: warm blues, turquoise water, golden sunshine highlights on wet fur. "
            "Style: ultra realistic, National Geographic / Getty editorial quality, "
            "premium outdoor pet photography. "
            "No humans. No text, no letters, no watermarks, no logos, no UI elements."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Dog mid-leap into a lake, splashing water, "
            "sunny summer day, blue sky. Joy, motion blur on paws, sharp face. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    },
    {
        "slug": "cat-overgrooming-alopecia",
        "animal": "cat",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A domestic short-hair cat lying relaxed on its side on a soft beige sofa, "
            "grooming its belly — head bent forward, tongue visible, licking its abdomen. "
            "The fur on the belly appears visibly thinner and slightly sparse compared to "
            "the rest of the coat, suggesting overgrooming. "
            "Light: soft natural daylight from a nearby window, warm afternoon tones, "
            "gentle shadows, cosy apartment atmosphere. "
            "Composition: cat fills most of the frame, eye-level perspective, "
            "warm neutral tones of sofa and wall in background. "
            "Style: ultra realistic, professional pet medical editorial photography, "
            "calm and trustworthy mood. "
            "No humans. No text, no letters, no watermarks, no logos."
        ),
        "retry_prompt": (
            "Photorealistic photo, 16:9. Domestic short-hair cat lying on its side on a beige sofa, "
            "grooming belly, thin sparse fur on abdomen. Soft daylight from window, warm tones. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    },
    {
        "slug": "dog-park-fights-prevent",
        "animal": "dog",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "An off-leash dog park on a bright summer afternoon: 2-3 dogs of different breeds "
            "running and playing freely on green grass. One dog prominently in the foreground "
            "is in a relaxed play-bow posture — front legs stretched forward and low, rear up, "
            "tail loosely wagging — a clear friendly invitation to play. "
            "In the blurred background, calm owners chat or stand relaxed watching the dogs. "
            "Light: bright sunny summer day, soft diffused daylight, lush green grass, leafy trees. "
            "Color: vibrant summer greens, warm daylight, earth tones. "
            "Style: ultra realistic, editorial lifestyle pet photography, National Geographic level. "
            "No text, no letters, no watermarks, no logos, no aggression."
        ),
        "retry_prompt": (
            "Photorealistic photo, 16:9. Dogs playing in off-leash park on summer day, "
            "one dog in play-bow posture on green grass, calm owners in background, "
            "bright sunlight. No text, no watermark. Ultra realistic."
        ),
    },
    {
        "slug": "cat-vet-visit-stress-free",
        "animal": "cat",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A calm, relaxed tabby cat sitting inside an open soft-sided pet carrier on a "
            "clean examination table in a bright modern veterinary clinic. "
            "A veterinarian in a white coat gently places a hand on the cat's back, "
            "examining it softly; only the vet's hands and lower arms visible, no face. "
            "The cat looks relaxed, curious rather than scared — slightly blinking eyes, "
            "ears forward, tail wrapped around itself. "
            "Light: soft diffused clinic lighting, clean white and light-wood interior, "
            "bright and airy atmosphere, no harsh shadows. "
            "Color: muted pastels, whites and light greys, calm clinical-yet-warm palette. "
            "Style: ultra realistic, professional medical editorial photography. "
            "No text, no letters, no watermarks, no logos."
        ),
        "retry_prompt": (
            "Photorealistic photo, 16:9. Tabby cat relaxed in open carrier on vet exam table, "
            "veterinarian hands gently touching the cat, bright modern clinic interior. "
            "Cat looks calm and curious. No text, no watermark. Ultra realistic."
        ),
    },
    {
        "slug": "dog-doorbell-barking-fix",
        "animal": "dog",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A medium-size dog sitting calmly near a front apartment door, "
            "ears pricked forward in alert attention, eyes focused on the door, "
            "mouth closed, body posture composed and expectant — not aggressive. "
            "The door is ajar, letting in a thin sliver of hallway light. "
            "Light: warm indoor daylight from a window to the side, cosy apartment atmosphere, "
            "wooden floor, neutral-toned walls. "
            "Composition: dog fills the left two-thirds of the frame, door on the right, "
            "slight depth-of-field blur on the background. "
            "Color: warm earth tones, creamy walls, natural wood. "
            "Style: ultra realistic, premium lifestyle editorial pet photography. "
            "No humans. No text, no letters, no watermarks, no logos, no aggression."
        ),
        "retry_prompt": (
            "Photorealistic photo, 16:9. Dog sitting alert near apartment front door slightly ajar, "
            "attentive but calm, warm indoor light, wooden floor. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def call_api(prompt: str) -> bytes | None:
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]}
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"    HTTP {e.code}: {err_body[:400]}", file=sys.stderr)
        _log_error("api", f"HTTP {e.code}: {err_body[:400]}")
        return None
    except Exception as e:
        print(f"    Request error: {e}", file=sys.stderr)
        _log_error("api", str(e))
        return None

    usage = body.get("usageMetadata", {})
    print(f"    usageMetadata: {usage}")

    try:
        parts = body["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        print(f"    No inlineData. Response keys: {list(body.keys())}", file=sys.stderr)
        return None
    except (KeyError, IndexError) as e:
        print(f"    Parse error: {e}. Body snippet: {str(body)[:300]}", file=sys.stderr)
        return None


def cover_verify(img: Image.Image) -> tuple[bool, str]:
    w, h = img.size
    if w < 1920 or h < 1080:
        return False, f"resolution too small: {w}x{h}"
    ratio = w / h
    if not (1.6 <= ratio <= 1.9):
        return False, f"aspect ratio off: {ratio:.2f} (expected ~1.78)"
    r_ch, _, _ = img.convert("RGB").split()
    if statistics.stdev(list(r_ch.getdata())) < 5:
        return False, "image appears blank/uniform"
    return True, "ok"


def process_and_save(img_bytes: bytes, out_path: str) -> tuple[bool, str]:
    try:
        img = Image.open(io.BytesIO(img_bytes))
    except Exception as e:
        return False, f"cannot open bytes: {e}"

    orig_w, orig_h = img.size
    target_ratio = TARGET_W / TARGET_H
    cur_ratio = orig_w / orig_h

    # Crop to 16:9 if needed
    if abs(cur_ratio - target_ratio) > 0.1:
        if cur_ratio > target_ratio:
            new_w = int(orig_h * target_ratio)
            offset = (orig_w - new_w) // 2
            img = img.crop((offset, 0, offset + new_w, orig_h))
        else:
            new_h = int(orig_w / target_ratio)
            offset = (orig_h - new_h) // 2
            img = img.crop((0, offset, orig_w, offset + new_h))

    if img.size != (TARGET_W, TARGET_H):
        img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)

    ok, reason = cover_verify(img)
    if not ok:
        return False, reason

    img = img.convert("RGB")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "JPEG", quality=85, optimize=True)
    size_kb = os.path.getsize(out_path) // 1024
    return True, f"{TARGET_W}x{TARGET_H} — {size_kb} KB"


def _log_error(slug: str, msg: str):
    from datetime import datetime
    os.makedirs(os.path.dirname(ERR_LOG), exist_ok=True)
    with open(ERR_LOG, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | slug={slug} | {msg}\n")


def _log_activity(msg: str):
    from datetime import datetime
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {msg}\n")


def generate_one(cover: dict) -> tuple[str, bool, str]:
    slug = cover["slug"]
    out_path = f"{BASE_DIR}/{slug}/images/cover.jpg"

    for attempt, prompt_key in enumerate(["prompt", "retry_prompt"], start=1):
        print(f"  [{slug}] attempt {attempt}...")
        img_bytes = call_api(cover[prompt_key])
        if not img_bytes:
            print(f"  [{slug}] No image bytes on attempt {attempt}")
            continue
        ok, detail = process_and_save(img_bytes, out_path)
        if ok:
            print(f"  [{slug}] SAVED: {out_path} ({detail})")
            _log_activity(
                f"max-designer-agent | cover generated | slug={slug} | {out_path} | {detail} | OK"
            )
            return slug, True, detail
        else:
            print(f"  [{slug}] cover_verify FAIL attempt {attempt}: {detail}")
            _log_error(slug, f"cover_verify fail attempt {attempt}: {detail}")

    _log_activity(f"max-designer-agent | cover FAILED | slug={slug} | FAIL after 2 attempts")
    return slug, False, "FAIL after 2 attempts"


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: GOOGLE_AI_API_KEY not found. Cannot proceed.", file=sys.stderr)
        sys.exit(1)

    print("=== AnimaLife Cover Generation — 2026-06-05 — 5 new articles ===")
    results = []
    for cover in COVERS:
        slug, ok, detail = generate_one(cover)
        results.append((slug, ok, detail))
        print()

    print("=== RESULTS ===")
    all_ok = True
    for slug, ok, detail in results:
        status = "OK  " if ok else "FAIL"
        path = f"{BASE_DIR}/{slug}/images/cover.jpg"
        size_str = ""
        if ok and os.path.exists(path):
            size_kb = os.path.getsize(path) // 1024
            size_str = f" — {size_kb} KB"
        print(f"  {status} | {slug}{size_str} | {detail}")
        if not ok:
            all_ok = False

    sys.exit(0 if all_ok else 1)
