#!/usr/bin/env python3
"""
Batch cover generation — AnimaLife — 2026-06-10
10 covers via Nano Banana Pro (gemini-3-pro-image-preview).
16:9, 2K (2048x1152), JPG, no text/logos/watermarks.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
import io
import concurrent.futures

try:
    from PIL import Image
except ImportError:
    os.system("pip install Pillow -q")
    from PIL import Image

# --- API key ---
API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
if not API_KEY:
    _envf = os.path.join(os.path.dirname(__file__), "..", "secrets", "google_ai.env")
    try:
        with open(_envf) as _f:
            for _line in _f:
                _line = _line.strip()
                if "=" in _line and not _line.startswith("#"):
                    k, v = _line.split("=", 1)
                    if k.strip() in ("GOOGLE_AI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
                        API_KEY = v.strip().strip('"').strip("'")
                        break
    except OSError:
        pass

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent"
TARGET_W, TARGET_H = 2048, 1152
BASE = "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles"


def p(slug, path, animal, prompt, retry_prompt):
    return {"slug": slug, "path": path, "animal": animal,
            "prompt": prompt, "retry_prompt": retry_prompt}


COVERS = [
    p(
        "cat-head-pillow-sleeping",
        f"{BASE}/cat-head-pillow-sleeping/images/cover.jpg",
        "cat",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A fluffy grey tabby cat sleeping peacefully beside a human head on a white pillow "
            "in a cozy bedroom, curled up close, eyes closed, paws tucked. "
            "Soft warm morning light streaming through sheer curtains from a nearby window, "
            "gentle bokeh, warm cream and beige tones. "
            "Cat occupies the center-right of frame, pillow and bedding fill the left. "
            "Ultra realistic, National Geographic / NYT Magazine editorial quality, "
            "shallow depth of field, natural color grading. "
            "No text, no letters, no watermarks, no logos, no UI elements, no faces of people."
        ),
        (
            "Photorealistic photo, 16:9. Grey tabby cat sleeping on white pillow in cozy bedroom, "
            "morning light, warm tones, bokeh background. No text, no watermark, no human faces. Ultra realistic."
        ),
    ),
    p(
        "cat-whisker-fatigue-bowl",
        f"{BASE}/cat-whisker-fatigue-bowl/images/cover.jpg",
        "cat",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A calico adult cat eating from a flat wide white ceramic plate on a kitchen floor, "
            "low angle close-up on the cat's face and long prominent whiskers. "
            "Natural soft daylight from a window to the side, clean minimal kitchen in the blurred background. "
            "Cat positioned in center-right of frame, whiskers sharp and detailed, warm neutral tones. "
            "Ultra realistic, premium pet photography, shallow depth of field. "
            "No text, no letters, no watermarks, no logos, no UI elements, no humans."
        ),
        (
            "Photorealistic photo, 16:9. Calico cat eating from flat white ceramic plate on kitchen floor, "
            "close-up on face and whiskers, natural daylight, minimal kitchen background blurred. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    ),
    p(
        "cat-stares-at-wall-night",
        f"{BASE}/cat-stares-at-wall-night/images/cover.jpg",
        "cat",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A black and white tuxedo cat sitting perfectly upright on a wooden floor in a dim living room at night, "
            "staring intently at a plain wall. The cat's silhouette is clearly visible against a soft warm amber glow "
            "from a table lamp off to the side. Moody, quiet, slightly mysterious atmosphere. "
            "Cat positioned center-left of frame, wall takes up right portion of background. "
            "Warm tungsten tones, deep shadows, ultra realistic editorial photography. "
            "No text, no letters, no watermarks, no logos, no UI elements, no humans."
        ),
        (
            "Photorealistic photo, 16:9. Black and white cat sitting upright staring at a wall in dark living room, "
            "warm lamp light creating soft silhouette, moody night atmosphere. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    ),
    p(
        "cat-summer-hydration-tricks",
        f"{BASE}/cat-summer-hydration-tricks/images/cover.jpg",
        "cat",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A ginger orange cat lapping water from a small pet drinking fountain on a bright kitchen countertop. "
            "Water droplets frozen mid-air around the cat's muzzle, backlit by warm summer sunlight from a window. "
            "Fresh green potted herbs blurred softly in the background. "
            "Cat positioned center of frame, mouth open at the water stream, eyes half-closed in concentration. "
            "Warm, bright, fresh summer mood. Ultra realistic, premium editorial photography, 1/1000s frozen motion. "
            "No text, no letters, no watermarks, no logos, no UI elements, no humans."
        ),
        (
            "Photorealistic photo, 16:9. Ginger cat drinking from pet water fountain on kitchen counter, "
            "water droplets in air, summer sunlight, green plants blurred background. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    ),
    p(
        "cat-greeting-tail-up",
        f"{BASE}/cat-greeting-tail-up/images/cover.jpg",
        "cat",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A fluffy orange or grey tabby cat walking confidently toward the camera with its tail held high "
            "like a flagpole, in a bright modern apartment hallway. "
            "Cat making direct eye contact with the viewer, mid-stride, expressive face. "
            "Warm natural light from a window at the end of the corridor creating a gentle backlight halo. "
            "Cat positioned center-left of frame walking into center, hallway recedes into background. "
            "Ultra realistic, editorial magazine quality, warm tones, bokeh. "
            "No text, no letters, no watermarks, no logos, no UI elements, no humans."
        ),
        (
            "Photorealistic photo, 16:9. Tabby cat walking toward camera with tail up in bright apartment hallway, "
            "eye contact, warm light, bokeh background. No text, no watermark, no humans. Ultra realistic."
        ),
    ),
    p(
        "dog-eats-grass-walk",
        f"{BASE}/dog-eats-grass-walk/images/cover.jpg",
        "dog",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A Labrador or border collie dog sniffing and chewing fresh green grass in a sunny city park, "
            "close-up on the dog's face and tongue, grass blades visible between teeth. "
            "Soft warm morning sunlight, blurred lush green park background with trees. "
            "Dog positioned center-right of frame, low camera angle, eye-level with the dog on the ground. "
            "Ultra realistic, National Geographic quality, warm summer tones, shallow depth of field. "
            "No text, no letters, no watermarks, no logos, no UI elements, no humans."
        ),
        (
            "Photorealistic photo, 16:9. Labrador dog eating grass on green park lawn, close-up on face and mouth, "
            "morning sunlight, blurred green background. No text, no watermark, no humans. Ultra realistic."
        ),
    ),
    p(
        "dog-circles-before-lying",
        f"{BASE}/dog-circles-before-lying/images/cover.jpg",
        "dog",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A medium-sized beagle or mixed breed dog in the middle of turning circles on a soft plaid blanket "
            "on a living room floor, slight motion blur on the tail and hindquarters, "
            "sharp focus on the dog's face showing concentration. "
            "Warm tungsten lamp light, cozy domestic interior, blurred sofa and bookshelf in background. "
            "Dog positioned in center of frame, blanket fills foreground, warm earth tones. "
            "Ultra realistic, premium pet photography, editorial quality. "
            "No text, no letters, no watermarks, no logos, no UI elements, no humans."
        ),
        (
            "Photorealistic photo, 16:9. Beagle dog circling on a soft plaid blanket in cozy living room, "
            "slight motion blur on tail, sharp face, warm lamp light. No text, no watermark, no humans. Ultra realistic."
        ),
    ),
    p(
        "dog-leg-twitching-sleep",
        f"{BASE}/dog-leg-twitching-sleep/images/cover.jpg",
        "dog",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A Jack Russell terrier or dachshund sleeping deeply on its side on a plush sofa, "
            "legs slightly bent and extended as if running, "
            "face totally relaxed with eyes closed, one ear flopped forward. "
            "Soft warm table lamp light in the background, cozy home interior, blanket texture visible. "
            "Dog fills center-right of frame, sleeping diagonally for visual dynamism. "
            "Ultra realistic, editorial quality, warm amber tones, beautiful fur detail. "
            "No text, no letters, no watermarks, no logos, no UI elements, no humans."
        ),
        (
            "Photorealistic photo, 16:9. Jack Russell terrier sleeping on its side on a sofa, "
            "legs bent as if running, relaxed face, warm lamp light, cozy home interior. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    ),
    p(
        "puppy-bite-inhibition-train",
        f"{BASE}/puppy-bite-inhibition-train/images/cover.jpg",
        "dog",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A 3-month-old Labrador puppy playfully tugging a thick rope toy, "
            "a single human hand (no face, no body beyond wrist) holds the other end of the rope. "
            "Puppy's eyes bright and playful, ears floppy, tail implied to be wagging. "
            "Bright airy living room with soft natural daylight, light wood floor, "
            "blurred warm neutral interior background. "
            "Puppy positioned center-left, rope extends toward right where hand appears. "
            "Playful safe joyful mood, no aggression. Ultra realistic, editorial photography quality. "
            "No text, no letters, no watermarks, no logos, no UI elements, no human face or body."
        ),
        (
            "Photorealistic photo, 16:9. Yellow Labrador puppy tugging rope toy, one human hand only visible "
            "holding other end, bright living room, playful mood. No text, no watermark, no human faces. Ultra realistic."
        ),
    ),
    p(
        "dog-crate-training-week",
        f"{BASE}/dog-crate-training-week/images/cover.jpg",
        "dog",
        (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop, 2048x1152. "
            "A golden retriever or mixed breed young dog lying relaxed and calm inside an open wire crate "
            "with a soft plush dog bed inside, a chew toy visible beside it. "
            "The crate door is open, dog is voluntarily resting inside, completely at ease. "
            "Warm natural daylight from a nearby window, cozy home environment, blurred interior background. "
            "Dog and crate positioned center of frame, safe sanctuary feeling. "
            "Ultra realistic, editorial magazine quality, warm tones. "
            "No text, no letters, no watermarks, no logos, no UI elements, no humans."
        ),
        (
            "Photorealistic photo, 16:9. Golden retriever lying relaxed inside an open dog crate with soft bed, "
            "chew toy nearby, warm daylight, cozy home interior. No text, no watermark, no humans. Ultra realistic."
        ),
    ),
]


def call_api(prompt: str) -> bytes | None:
    if not API_KEY:
        print("  ERROR: No API key found", file=sys.stderr)
        return None
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]}
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code}: {err_body[:400]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Request error: {e}", file=sys.stderr)
        return None

    try:
        parts = body["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                usage = body.get("usageMetadata", {})
                print(f"  usageMetadata: {usage}", file=sys.stderr)
                return base64.b64decode(part["inlineData"]["data"])
        print(f"  No inlineData. Keys: {list(body.keys())} snippet: {str(body)[:300]}", file=sys.stderr)
        return None
    except (KeyError, IndexError) as e:
        print(f"  Parse error: {e}. Response: {str(body)[:300]}", file=sys.stderr)
        return None


def process_image(img_bytes: bytes, out_path: str) -> tuple[bool, str]:
    try:
        img = Image.open(io.BytesIO(img_bytes))
    except Exception as e:
        return False, f"cannot open image: {e}"

    orig_w, orig_h = img.size
    target_ratio = TARGET_W / TARGET_H
    cur_ratio = orig_w / orig_h

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

    # Sanity check — not blank
    import statistics
    r, g, b = img.convert("RGB").split()
    if statistics.stdev(list(r.getdata())) < 5:
        return False, "image appears blank/uniform"

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=88, optimize=True)
    size_kb = os.path.getsize(out_path) // 1024
    return True, f"saved {img.size[0]}x{img.size[1]} {size_kb}KB"


def generate_cover(cover: dict) -> tuple[str, bool, str]:
    slug = cover["slug"]
    out = cover["path"]
    print(f"[{slug}] attempt 1 ...", flush=True)
    img_bytes = call_api(cover["prompt"])
    if img_bytes:
        ok, msg = process_image(img_bytes, out)
        if ok:
            print(f"[{slug}] OK — {msg}", flush=True)
            return slug, True, f"OK — {msg}"
        print(f"[{slug}] verify fail: {msg} — retrying", flush=True)
    else:
        print(f"[{slug}] no image on attempt 1 — retrying", flush=True)

    print(f"[{slug}] attempt 2 (retry prompt) ...", flush=True)
    img_bytes2 = call_api(cover["retry_prompt"])
    if img_bytes2:
        ok2, msg2 = process_image(img_bytes2, out)
        if ok2:
            print(f"[{slug}] OK (retry) — {msg2}", flush=True)
            return slug, True, f"OK (retry) — {msg2}"
        return slug, False, f"FAIL verify after retry: {msg2}"
    return slug, False, "FAIL: API returned no image on both attempts"


if __name__ == "__main__":
    print(f"=== AnimaLife Cover Batch 2026-06-10 — {len(COVERS)} covers ===")
    print(f"API key loaded: {'YES' if API_KEY else 'NO'}")

    results = []
    # Run up to 3 in parallel to respect API rate limits
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(generate_cover, c): c["slug"] for c in COVERS}
        for fut in concurrent.futures.as_completed(futures):
            slug, ok, msg = fut.result()
            results.append((slug, ok, msg))

    print("\n=== FINAL RESULTS ===")
    for slug, ok, msg in sorted(results, key=lambda x: x[0]):
        print(f"{'OK' if ok else 'FAIL'}  articles/{slug}/images/cover.jpg  ({msg})")
