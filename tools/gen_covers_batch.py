#!/usr/bin/env python3
"""
Batch cover generation for AnimaLife via Nano Banana Pro (gemini-3-pro-image-preview).
Saves JPG to specified paths. No text overlay. cover_verify gate included.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
import io

# Pillow for image save + verify
try:
    from PIL import Image
except ImportError:
    os.system("pip install Pillow -q")
    from PIL import Image

# API key is read from the environment — never hardcode secrets in the repo
# (GitHub push protection blocks committed keys). Set GOOGLE_AI_API_KEY or put it
# in secrets/google_ai.env (GOOGLE_AI_API_KEY=...). See tools/DZEN_CONTENT_RULES.md siblings.
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
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent"
TARGET_W, TARGET_H = 2048, 1152

COVERS = [
    {
        "slug": "cat-zoomies-3am",
        "path": "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles/cat-zoomies-3am/images/cover.jpg",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A young domestic short-hair tabby cat captured mid-zoom, mid-air leap above a warm wooden floor "
            "in a dim cosy living room at night. Motion blur on paws, tack-sharp focus on the cat face, "
            "eyes wide with pupils fully dilated. Soft cool blue moonlight from a window creates a rim light "
            "on the fur, a warm tungsten lamp glows softly in the background corner. "
            "No humans. No text, no letters, no watermarks, no logos, no UI elements. "
            "Ultra realistic, National Geographic level, depth of field, premium photography."
        ),
        "retry_prompt": (
            "Photorealistic editorial photography, 16:9. Tabby cat in mid-leap above hardwood floor at night, "
            "motion blur on legs, sharp eyes with dilated pupils, cool moonlight rim, warm lamp background. "
            "No text, no watermark, no humans, no CGI look. Ultra realistic."
        ),
        "animal": "cat",
    },
    {
        "slug": "dog-coprophagia-stop",
        "path": "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles/dog-coprophagia-stop/images/cover.jpg",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A medium-size mixed breed dog sitting attentively on lush green spring grass in a city park, "
            "looking directly up at the camera with intelligent expressive eyes. "
            "Soft warm golden hour sunlight from the left, blurred background of green trees and park path. "
            "Calm, trustworthy, vet-educational mood. No humans visible. "
            "No text, no letters, no watermarks, no logos. Ultra realistic, premium documentary photography."
        ),
        "retry_prompt": (
            "Photorealistic photo, 16:9. Mixed breed dog sitting on green park grass, looking up at camera, "
            "golden hour sunlight, blurred green background. No text, no watermark. Ultra realistic."
        ),
        "animal": "dog",
    },
    {
        "slug": "dog-tail-language-decoded",
        "path": "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles/dog-tail-language-decoded/images/cover.jpg",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "Close-up rear three-quarter view of a Labrador-type dog standing on a soft autumn lawn, "
            "tail clearly visible held high and slightly curled in a confident posture. "
            "Sharp focus on the tail and back posture, softly blurred autumn background with fallen leaves. "
            "Warm afternoon sunlight, golden tones. Natural pet photography aesthetic. "
            "No humans. No text, no letters, no watermarks, no logos. Ultra realistic, premium quality."
        ),
        "retry_prompt": (
            "Photorealistic photo, 16:9. Labrador dog from behind, tail held high, autumn lawn, warm sunlight. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
        "animal": "dog",
    },
    {
        "slug": "cat-scratching-furniture-fix",
        "path": "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles/cat-scratching-furniture-fix/images/cover.jpg",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A grey domestic shorthair cat stretching up tall against a vertical sisal scratching post "
            "in a bright cosy Scandinavian-style living room. Cat's claws visibly extended, body fully stretched upward. "
            "Soft natural daylight through a large window, beige sofa softly blurred in background, "
            "warm neutral interior tones. Calm domestic scene. "
            "No humans. No text, no letters, no watermarks, no logos. Ultra realistic, premium interior photography."
        ),
        "retry_prompt": (
            "Photorealistic photo, 16:9. Grey cat scratching a sisal post in Scandinavian living room, "
            "claws extended, natural daylight, beige sofa blurred background. No text, no watermark. Ultra realistic."
        ),
        "animal": "cat",
    },
    {
        "slug": "dog-summer-dehydration",
        "path": "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles/dog-summer-dehydration/images/cover.jpg",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A panting golden retriever lying relaxed on green grass in dappled tree shade on a hot summer day, "
            "drinking water from a shiny metal bowl held by a single human hand (only the hand and bowl visible, "
            "no face or body). Bright warm summer sunlight in soft-focus background, "
            "caring attentive atmosphere, health-education aesthetic. "
            "No text, no letters, no watermarks, no logos. Ultra realistic, premium documentary photography."
        ),
        "retry_prompt": (
            "Photorealistic photo, 16:9. Golden retriever panting on grass in shade, drinking from metal bowl "
            "held by a hand (hand only visible). Summer sunlight background. No text, no watermark. Ultra realistic."
        ),
        "animal": "dog",
    },
]


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
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"    HTTP {e.code}: {err_body[:300]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"    Request error: {e}", file=sys.stderr)
        return None

    # Extract image bytes
    try:
        parts = body["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        print(f"    No inlineData in response. Keys: {list(body.keys())}", file=sys.stderr)
        # Print usage if available
        if "usageMetadata" in body:
            print(f"    usageMetadata: {body['usageMetadata']}", file=sys.stderr)
        return None
    except (KeyError, IndexError) as e:
        print(f"    Parse error: {e}. Response snippet: {str(body)[:300]}", file=sys.stderr)
        return None


def cover_verify(img: Image.Image, animal: str) -> tuple[bool, str]:
    """Basic sanity checks: min resolution, aspect ratio roughly 16:9, no obvious issues."""
    w, h = img.size
    if w < 1920 or h < 1080:
        return False, f"resolution too small: {w}x{h}"
    ratio = w / h
    if not (1.6 <= ratio <= 1.9):
        return False, f"aspect ratio off: {ratio:.2f} (expected ~1.78)"
    # Check image is not mostly uniform color (blank/failed generation)
    import statistics
    r, g, b = img.convert("RGB").split()
    pixels_r = list(r.getdata())
    if statistics.stdev(pixels_r) < 5:
        return False, "image appears blank/uniform"
    return True, "ok"


def process_image(img_bytes: bytes, out_path: str, animal: str) -> tuple[bool, str]:
    try:
        img = Image.open(io.BytesIO(img_bytes))
    except Exception as e:
        return False, f"cannot open image bytes: {e}"

    # Resize to 2048x1152 if needed, maintaining aspect
    orig_w, orig_h = img.size
    target_ratio = TARGET_W / TARGET_H
    cur_ratio = orig_w / orig_h

    if abs(cur_ratio - target_ratio) > 0.1:
        # Crop to 16:9
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

    ok, reason = cover_verify(img, animal)
    if not ok:
        return False, reason

    img = img.convert("RGB")
    img.save(out_path, "JPEG", quality=85, optimize=True)
    return True, "ok"


def generate_cover(cover: dict) -> tuple[str, bool, str]:
    slug = cover["slug"]
    print(f"  [{slug}] Generating (attempt 1)...")
    img_bytes = call_api(cover["prompt"])
    if img_bytes:
        ok, reason = process_image(img_bytes, cover["path"], cover["animal"])
        if ok:
            print(f"  [{slug}] OK - saved to {cover['path']}")
            return slug, True, "OK"
        else:
            print(f"  [{slug}] cover_verify FAIL: {reason} — retrying...")
    else:
        print(f"  [{slug}] API returned no image — retrying with revised prompt...")

    # Retry
    print(f"  [{slug}] Generating (attempt 2 / retry prompt)...")
    img_bytes2 = call_api(cover["retry_prompt"])
    if img_bytes2:
        ok2, reason2 = process_image(img_bytes2, cover["path"], cover["animal"])
        if ok2:
            print(f"  [{slug}] OK (retry) - saved to {cover['path']}")
            return slug, True, "OK (retry)"
        else:
            return slug, False, f"FAIL after retry: {reason2}"
    else:
        return slug, False, "FAIL: API returned no image on retry"


if __name__ == "__main__":
    print("=== AnimaLife Cover Batch Generation 2026-06-04 ===")
    results = []
    for cover in COVERS:
        slug, ok, msg = generate_cover(cover)
        results.append((slug, ok, msg))

    print("\n=== RESULTS ===")
    for slug, ok, msg in results:
        status = "OK" if ok else "FAIL"
        print(f"{slug} -> {status} ({msg})")
