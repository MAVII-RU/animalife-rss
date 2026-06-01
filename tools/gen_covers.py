#!/usr/bin/env python3
"""
Generate 5 covers for AnimaLife Dzen articles via Nano Banana Pro (gemini-3-pro-image-preview).
Saves as cover.jpg in articles/<slug>/images/.
"""

import os
import sys
import json
import base64
import io
import requests
from PIL import Image

# --- Config ---
API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
MODEL = "gemini-3-pro-image-preview"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
BASE_DIR = "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles"
TARGET_W, TARGET_H = 2048, 1152  # 16:9 2K
QUALITY = 88  # JPEG quality targeting ~300-500 KB

COVERS = [
    {
        "slug": "dog-bbq-bones-onion-danger",
        "prompt": (
            "A golden Labrador Retriever dog at a summer dacha barbecue in the evening, "
            "curiously stretching its nose toward shish kebab skewers and a plate of grilled meat on a wooden table. "
            "A blurred person visible in the background by the grill. "
            "Light: warm golden sunset light from the right side, soft dusk atmosphere, gentle bokeh background. "
            "Camera: 85mm portrait lens, f/2.8, shallow depth of field, dog face sharp. "
            "Composition: dog occupies left two-thirds of frame, plate of food on the right in sharp focus, "
            "eye-level perspective, natural candid moment. "
            "Style: editorial documentary photography, ultra realistic, National Geographic quality, "
            "cinematic warm tones, natural color grading. "
            "Color: warm amber and ochre tones, soft shadows, golden hour palette. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no extra limbs. "
            "16:9 cinematic crop, 2048x1152."
        ),
    },
    {
        "slug": "cat-balcony-fall-syndrome",
        "prompt": (
            "A grey tabby cat sitting on a wide apartment windowsill at an open window, "
            "looking down at the city below from a high floor. Sheer white curtain gently billowing in a light breeze. "
            "City skyline and residential buildings visible out of focus far below. "
            "Light: soft diffused daylight from outside, slightly dramatic, overcast sky giving even cool light. "
            "Camera: 50mm lens, f/3.5, cat in sharp focus, cityscape in soft bokeh. "
            "Composition: cat on the left third of frame, open window and sky on the right, "
            "low angle looking slightly up at the cat, curtain framing the scene. "
            "Style: editorial magazine photography, ultra realistic, dramatic but not frightening, "
            "cinematic mood, The Atlantic visual style. "
            "Color: cool neutral tones with soft grey and blue-grey palette. "
            "No text, no letters, no watermarks, no logos, no AI artifacts. "
            "16:9 cinematic crop, 2048x1152."
        ),
    },
    {
        "slug": "cat-meow-types-decoded",
        "prompt": (
            "Close-up portrait of a beautiful orange ginger tabby cat with mouth slightly open mid-meow, "
            "showing expressive bright green eyes and sharp distinct whiskers. "
            "Emotional genuine moment, cat facing the camera, slightly turned head. "
            "Light: soft warm natural window light from the left, clean light background, "
            "gentle fill light, no harsh shadows. "
            "Camera: 100mm macro lens, f/2.0, extremely shallow depth of field, "
            "face and eyes perfectly sharp, ears softly out of focus. "
            "Composition: cat fills 60% of frame, centered with slight right lean, "
            "clean light domestic interior background. "
            "Style: editorial portrait photography, ultra realistic, National Geographic level detail, "
            "magazine quality. "
            "Color: warm natural tones, soft contrast, creamy highlights, natural fur texture. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no extra elements. "
            "16:9 cinematic crop, 2048x1152."
        ),
    },
    {
        "slug": "senior-dog-care",
        "prompt": (
            "An elderly golden retriever dog with a grey-white muzzle lying comfortably on a soft plaid blanket "
            "in front of a glowing fireplace, in a calm dignified pose, head resting on paws, "
            "looking up with warm wise gentle eyes. "
            "Light: warm glowing fireplace light from the right, soft ambient room light, "
            "cozy golden atmosphere, gentle shadows. "
            "Camera: 85mm lens, f/2.4, dog's face and eyes in sharp focus, "
            "fireplace background in warm bokeh. "
            "Composition: dog centered-left on the plaid, fireplace glow on the right, "
            "low perspective at dog's eye level, intimate framing. "
            "Style: editorial lifestyle photography, ultra realistic, deeply emotional, warm and peaceful, "
            "cinematic quality. "
            "Color: rich warm ochres, amber firelight, deep comfortable shadows, earthy tones. "
            "No text, no letters, no watermarks, no logos, no AI artifacts. "
            "16:9 cinematic crop, 2048x1152."
        ),
    },
    {
        "slug": "dog-mushrooms-poisonous",
        "prompt": (
            "A curious border collie dog on a forest trail leaning down to sniff a cluster of red Amanita muscaria "
            "fly agaric mushrooms growing from mossy forest floor. "
            "Morning forest light, rays of sunlight filtering through tall pine and birch trees, "
            "green moss carpet on the ground. "
            "Light: dappled morning sunlight through forest canopy, golden rays, soft forest shadows, "
            "atmospheric mist in background. "
            "Camera: 70mm lens, f/3.5, dog face and mushrooms both sharp, "
            "forest background in soft bokeh with light rays. "
            "Composition: dog on the left, mushrooms in foreground center-right, "
            "slightly low angle, forest depth behind. "
            "Style: editorial nature documentary photography, ultra realistic, National Geographic quality, "
            "natural cinematic look. "
            "Color: lush greens, warm golden sunrays, bright red mushroom caps with white spots, "
            "natural forest palette. "
            "No text, no letters, no watermarks, no logos, no AI artifacts. "
            "16:9 cinematic crop, 2048x1152."
        ),
    },
]


def generate_image(prompt: str) -> bytes:
    """Call Nano Banana Pro API and return raw image bytes (PNG from base64)."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    resp = requests.post(ENDPOINT, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:500]}")

    data = resp.json()

    # Extract usage metadata
    usage = data.get("usageMetadata", {})
    print(f"    Usage: {usage}")

    # Navigate response structure
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates in response: {json.dumps(data)[:500]}")

    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        if "inlineData" in part:
            inline = part["inlineData"]
            mime = inline.get("mimeType", "")
            b64data = inline.get("data", "")
            if b64data:
                return base64.b64decode(b64data), mime
    raise RuntimeError(f"No image data found in response parts: {json.dumps(parts)[:500]}")


def save_cover(img_bytes: bytes, mime: str, slug: str) -> str:
    """Convert to 2048x1152 JPG and save. Returns file path."""
    out_path = os.path.join(BASE_DIR, slug, "images", "cover.jpg")

    # Load image from bytes
    img = Image.open(io.BytesIO(img_bytes))
    print(f"    Source image size: {img.size}, mode: {img.mode}")

    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize/crop to exact 2048x1152 (16:9)
    target_ratio = TARGET_W / TARGET_H
    src_w, src_h = img.size
    src_ratio = src_w / src_h

    if abs(src_ratio - target_ratio) > 0.01:
        # Crop to target ratio first
        if src_ratio > target_ratio:
            # Image is wider — crop sides
            new_w = int(src_h * target_ratio)
            x_offset = (src_w - new_w) // 2
            img = img.crop((x_offset, 0, x_offset + new_w, src_h))
        else:
            # Image is taller — crop top/bottom
            new_h = int(src_w / target_ratio)
            y_offset = (src_h - new_h) // 2
            img = img.crop((0, y_offset, src_w, y_offset + new_h))

    # Resize to target dimensions with high quality
    img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)

    # Save as JPG with target quality
    img.save(out_path, "JPEG", quality=QUALITY, optimize=True, progressive=True)

    file_size = os.path.getsize(out_path)
    print(f"    Saved: {out_path} ({file_size // 1024} KB)")
    return out_path


def main():
    if not API_KEY:
        print("ERROR: GOOGLE_AI_API_KEY not set")
        sys.exit(1)

    results = []
    errors = []

    for i, cover in enumerate(COVERS, 1):
        slug = cover["slug"]
        print(f"\n[{i}/5] Generating: {slug}")
        print(f"    Prompt length: {len(cover['prompt'])} chars")

        try:
            print("    Calling Nano Banana Pro API...")
            img_bytes, mime = generate_image(cover["prompt"])
            print(f"    Received {len(img_bytes)} bytes ({mime})")

            out_path = save_cover(img_bytes, mime, slug)
            results.append({"slug": slug, "path": out_path, "status": "OK"})
            print(f"    SUCCESS: {slug}")

        except Exception as e:
            print(f"    ERROR: {slug} — {e}")
            errors.append({"slug": slug, "error": str(e)})
            # Per instructions: no more than 1 retry, stop and report
            print(f"    Attempting 1 retry for {slug}...")
            try:
                img_bytes, mime = generate_image(cover["prompt"])
                out_path = save_cover(img_bytes, mime, slug)
                results.append({"slug": slug, "path": out_path, "status": "OK (retry)"})
                errors.pop()
                print(f"    RETRY SUCCESS: {slug}")
            except Exception as e2:
                print(f"    RETRY FAILED: {slug} — {e2}")
                errors[-1]["retry_error"] = str(e2)

    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    for r in results:
        print(f"  OK  [{r['status']}] {r['slug']}")
        print(f"       {r['path']}")
    for e in errors:
        print(f"  FAIL {e['slug']}: {e.get('retry_error', e['error'])}")

    return len(errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
