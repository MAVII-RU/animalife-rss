#!/usr/bin/env python3
"""
Cover batch generation for 10 AnimaLife articles — 2026-06-08.
Model: gemini-3-pro-image-preview (Nano Banana Pro).
Output: articles/<slug>/images/cover.jpg @ 2048x1152 JPEG.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
import io

try:
    from PIL import Image
except ImportError:
    os.system("pip install Pillow -q")
    from PIL import Image

# ── API key ───────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
if not API_KEY:
    _envf = os.path.join(os.path.dirname(__file__), "..", "secrets", "google_ai.env")
    try:
        with open(_envf) as _f:
            for _line in _f:
                if _line.strip().startswith("GOOGLE_AI_API_KEY="):
                    API_KEY = _line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except OSError:
        pass

ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3-pro-image-preview:generateContent"
)
TARGET_W, TARGET_H = 2048, 1152
BASE = "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss"
LOG  = "/home/max/MAVII_AGENTS/logs/activity.log"
ERR  = "/home/max/MAVII_AGENTS/logs/designer_errors.log"


def p(slug, suffix=""):
    return f"{BASE}/articles/{slug}/images/cover.jpg"


COVERS = [
    # 1 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "cat-headbutt-bunting",
        "animal": "cat",
        "path": p("cat-headbutt-bunting"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A short-haired tabby cat gently pressing its forehead against a human hand in a warm indoor setting. "
            "Close-up: cat's eyes half-closed with trust and contentment, fine fur texture razor-sharp. "
            "Light: soft warm window light from the left, golden hour glow, shallow bokeh background of a cozy living room. "
            "Camera: 85mm portrait lens, f/1.8, ultra shallow depth of field. "
            "Composition: cat face and hand filling two-thirds of the frame, negative space on right, eye-level. "
            "Style: National Geographic editorial, ultra realistic. "
            "Palette: terracotta, ochre, cream, warm whites. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no extra limbs."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. Short-hair tabby cat bunting (head-butting) a human hand, "
            "close-up, warm indoor light, bokeh background, 85mm portrait look. "
            "No text, no watermarks, ultra realistic."
        ),
    },
    # 2 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "dog-tilts-head",
        "animal": "dog",
        "path": p("dog-tilts-head"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A Labrador Retriever or Border Collie with floppy ears tilting its head to one side, "
            "looking directly into camera with bright curious eyes, mouth slightly open and relaxed. "
            "Light: soft diffused natural daylight, neutral home background slightly blurred. "
            "Camera: 50mm lens, f/2.2, shallow depth of field, dog in sharp focus. "
            "Composition: dog centered-left, head tilt at 30 degrees, negative space on right, eye-level. "
            "Style: editorial magazine, warm playful mood, ultra realistic. "
            "Palette: warm neutrals, creamy whites, soft earth tones. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. Labrador or Border Collie tilting head sideways, "
            "curious eyes, looking at camera, soft natural daylight background blurred. "
            "No text, no watermarks, ultra realistic."
        ),
    },
    # 3 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "cat-cardboard-box-love",
        "animal": "cat",
        "path": p("cat-cardboard-box-love"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A grey or ginger domestic cat sitting comfortably inside a plain brown cardboard box on a hardwood floor, "
            "peeking out over the edge with calm curious eyes, front paws resting on the box rim. "
            "Light: soft natural daylight from a nearby window, gentle shadows, cozy apartment atmosphere. "
            "Camera: 35mm lens, f/2.8, cat in focus, living room softly blurred. "
            "Composition: box in lower third, cat face at viewer's eye level, rule of thirds. "
            "Style: editorial lifestyle home photography, ultra realistic. "
            "Palette: warm kraft brown, grey/ginger fur tones, cream floor, soft daylight whites. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. Grey cat sitting inside a cardboard box on hardwood floor, "
            "peeking out, daylight from window, cozy home. No text, no watermarks, ultra realistic."
        ),
    },
    # 4 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "dog-mat-relax-training",
        "animal": "dog",
        "path": p("dog-mat-relax-training"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A Golden Retriever lying completely relaxed on a training mat in a bright modern living room, "
            "chin resting on front paws, eyes soft and calm, completely at ease. "
            "Light: soft warm afternoon light from a large window, gentle interior glow. "
            "Camera: 50mm lens, f/2.5, dog in sharp focus, room background pleasantly blurred. "
            "Composition: dog stretched diagonally across the mat, mat slightly off-center, wide breathing room on left. "
            "Style: editorial photography, serene and warm mood, ultra realistic. "
            "Palette: golden fur tones, warm beige mat, cream walls, soft amber light. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. Golden Retriever lying relaxed on a mat in a living room, "
            "chin on paws, calm eyes, warm afternoon light through window. No text, no watermarks, ultra realistic."
        ),
    },
    # 5 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "pet-name-recognition",
        "animal": "cat",
        "path": p("pet-name-recognition"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A young puppy and a kitten sitting side by side on a light wooden floor, "
            "both looking upward attentively toward a human hand just entering the frame from the right, "
            "the hand holding a small treat, both animals in a moment of eager alert response. "
            "Light: warm natural window light, soft interior glow, golden tones. "
            "Camera: 50mm lens, f/2.8, both animals in focus, hand and background softly blurred. "
            "Composition: puppy and kitten center-left, human hand from right edge, eye-level angle. "
            "Style: editorial magazine photography, warm joyful mood, ultra realistic. "
            "Palette: warm neutrals, golden tones, cream and ochre. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. A puppy and kitten side by side on wooden floor, "
            "both looking up eagerly at a treat in a human hand at frame edge, warm light. "
            "No text, no watermarks, ultra realistic."
        ),
    },
    # 6 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "dog-rolling-in-stinky-grass",
        "animal": "dog",
        "path": p("dog-rolling-in-stinky-grass"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A Jack Russell Terrier or Beagle rolling joyfully on its back in lush green summer grass outdoors, "
            "all four legs in the air, mouth open in pure delight, grass blades all around. "
            "Light: bright sunny summer midday light, green grass glowing with natural sunlight. "
            "Camera: 35mm lens, f/4.0, dog in sharp focus, grass in soft near-focus foreground and background. "
            "Composition: dog rolling in center-right, green grass filling the frame, small glimpse of summer sky at top. "
            "Style: editorial magazine photography, joyful outdoor lifestyle mood, ultra realistic. "
            "Palette: vivid green grass, white/tan dog fur, warm summer blues and yellows. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. Jack Russell Terrier rolling on its back in green summer grass, "
            "legs in the air, mouth open happy, bright sunny day. No text, no watermarks, ultra realistic."
        ),
    },
    # 7 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "cat-vertical-territory-shelves",
        "animal": "cat",
        "path": p("cat-vertical-territory-shelves"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A sleek domestic cat resting on the highest level of a multi-level wall-mounted cat shelf system, "
            "looking down calmly with half-lidded eyes, showing ownership and comfort. "
            "Light: warm interior ambient light, cozy home atmosphere, soft shadows. "
            "Camera: 35mm lens, f/2.8, cat in focus, vertical shelf system visible showing multiple levels, wall blurred. "
            "Composition: vertical emphasis showing the height of shelves, cat on top shelf, negative space below, low-angle upward shot. "
            "Style: editorial photography, modern Scandinavian home interior, ultra realistic. "
            "Palette: natural wood tones of shelves, grey/black cat, cream white walls, warm accent lighting. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. Cat resting on top level of wall-mounted cat shelves, "
            "looking down, multiple shelf levels visible, Scandinavian interior, warm light. "
            "No text, no watermarks, ultra realistic."
        ),
    },
    # 8 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "dog-feeding-schedule-2-vs-3",
        "animal": "dog",
        "path": p("dog-feeding-schedule-2-vs-3"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A large German Shepherd or Labrador Retriever eating calmly from a stainless steel dog bowl "
            "on a kitchen floor, relaxed posture, next to a clean measuring cup of dry kibble. "
            "Light: warm domestic kitchen light, morning or afternoon natural light from a window. "
            "Camera: 50mm lens, f/2.8, dog and bowl in focus, kitchen background pleasantly blurred. "
            "Composition: dog eating from bowl in right two-thirds, measuring cup of kibble on the left, low angle near floor level. "
            "Style: editorial photography, calm domestic routine mood, ultra realistic. "
            "Palette: warm kitchen tones, stainless steel bowl, golden dog fur, natural wood floor. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. Labrador eating from stainless steel bowl on kitchen floor, "
            "measuring cup of kibble nearby, warm kitchen light, low angle shot. "
            "No text, no watermarks, ultra realistic."
        ),
    },
    # 9 ─────────────────────────────────────────────────────────────────────
    {
        "slug": "cat-tongue-roughness",
        "animal": "cat",
        "path": p("cat-tongue-roughness"),
        "prompt": (
            "Photorealistic editorial macro photograph, 16:9 cinematic crop, 2048x1152. "
            "Extreme close-up of a cat grooming its paw, mouth open, rough barbed tongue visibly extended mid-lick, "
            "ultra-sharp macro detail of papillae on the tongue surface, fur glistening. "
            "Light: soft directional side light highlighting tongue texture, warm neutral background. "
            "Camera: 100mm macro lens, f/4.0, tongue and paw in razor-sharp focus, blurred warm background. "
            "Composition: cat paw and tongue filling most of the frame, macro detail dominant. "
            "Style: editorial macro photography, National Geographic level detail, ultra realistic. "
            "Palette: soft pink tongue, white/cream fur, warm neutral background. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic macro photo 16:9. Close-up of cat licking its paw, rough tongue with papillae visible, "
            "soft side light, sharp macro focus. No text, no watermarks, ultra realistic."
        ),
    },
    # 10 ────────────────────────────────────────────────────────────────────
    {
        "slug": "dog-sleep-positions-decoded",
        "animal": "dog",
        "path": p("dog-sleep-positions-decoded"),
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A medium-to-large dog sleeping on its back with all four legs in the air, "
            "the classic belly-up position, on a soft warm blanket on a couch or dog bed, "
            "completely relaxed and peaceful, eyes closed. "
            "Light: soft warm indoor light, morning or afternoon glow, cozy home atmosphere. "
            "Camera: 50mm lens, f/2.5, dog in sharp focus, soft blanket texture visible, background gently blurred. "
            "Composition: dog centered with legs up, cozy blanket framing, slightly overhead angle to capture the full pose. "
            "Style: editorial photography, warm and heartwarming mood, ultra realistic. "
            "Palette: warm cream and golden tones of the blanket, natural dog fur tones, soft ambient light. "
            "No text, no letters, no watermarks, no logos, no AI artifacts."
        ),
        "retry_prompt": (
            "Photorealistic photo 16:9. Dog sleeping on its back, legs in the air, on a soft warm blanket, "
            "cozy home, slightly overhead angle, warm light. No text, no watermarks, ultra realistic."
        ),
    },
]


# ── API call ──────────────────────────────────────────────────────────────────
def call_api(prompt: str) -> bytes | None:
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"    HTTP {e.code}: {err_body[:400]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"    Request error: {e}", file=sys.stderr)
        return None

    # Print usage
    if "usageMetadata" in body:
        print(f"    usage: {body['usageMetadata']}")

    try:
        parts = body["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        print(f"    No inlineData. Parts keys: {[list(p.keys()) for p in parts]}", file=sys.stderr)
        return None
    except (KeyError, IndexError) as e:
        print(f"    Parse error: {e}. Snippet: {str(body)[:400]}", file=sys.stderr)
        return None


# ── Image processing ──────────────────────────────────────────────────────────
def process_image(img_bytes: bytes, out_path: str) -> tuple[bool, str]:
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        return False, f"cannot open image: {e}"

    orig_w, orig_h = img.size
    target_ratio = TARGET_W / TARGET_H
    cur_ratio = orig_w / orig_h

    if abs(cur_ratio - target_ratio) > 0.05:
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

    # Sanity: not blank
    import statistics
    r_ch, *_ = img.split()
    if statistics.stdev(list(r_ch.getdata())) < 5:
        return False, "image appears blank/uniform"

    img.save(out_path, "JPEG", quality=88, optimize=True)
    return True, "ok"


# ── Per-cover generator ───────────────────────────────────────────────────────
def generate_cover(cover: dict) -> tuple[str, str, str]:
    slug = cover["slug"]
    for attempt, prompt_key in enumerate(["prompt", "retry_prompt"], 1):
        print(f"  [{slug}] attempt {attempt}...")
        raw = call_api(cover[prompt_key])
        if not raw:
            print(f"  [{slug}] no image bytes on attempt {attempt}")
            continue
        ok, reason = process_image(raw, cover["path"])
        if ok:
            size_kb = os.path.getsize(cover["path"]) // 1024
            print(f"  [{slug}] OK -> {cover['path']} ({size_kb} KB)")
            return slug, "OK" if attempt == 1 else "OK (retry)", cover["path"]
        else:
            print(f"  [{slug}] process_image FAIL: {reason}")
    return slug, "FAILED", "—"


# ── Logging ───────────────────────────────────────────────────────────────────
def log_result(slug: str, status: str):
    import datetime
    ts = datetime.date.today().isoformat()
    line = f"{ts} | gen_covers_june08 | {slug} | {status}\n"
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line)


def log_error(slug: str, msg: str):
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [gen_covers_june08] [{slug}] {msg}\n"
    os.makedirs(os.path.dirname(ERR), exist_ok=True)
    with open(ERR, "a") as f:
        f.write(line)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: GOOGLE_AI_API_KEY not set and secrets/google_ai.env not found")
        sys.exit(1)

    print("=== AnimaLife Cover Batch — 2026-06-08 (10 covers) ===\n")
    results = []

    for i, cover in enumerate(COVERS, 1):
        print(f"\n[{i}/10] {cover['slug']}")
        slug, status, path = generate_cover(cover)
        results.append((slug, status, path))
        log_result(slug, status)
        if "FAIL" in status:
            log_error(slug, status)
        # Small pause between requests
        if i < len(COVERS):
            import time; time.sleep(4)

    print("\n" + "=" * 72)
    print("FINAL RESULTS:")
    print("=" * 72)
    ok_count = 0
    for slug, status, path in results:
        print(f"{slug} | {status} | {path}")
        if "OK" in status:
            ok_count += 1

    print(f"\nSucceeded: {ok_count}/10")
    sys.exit(0 if ok_count == 10 else 1)
