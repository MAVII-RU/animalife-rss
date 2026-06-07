#!/usr/bin/env python3
"""
Generate 10 AnimaLife article covers via Nano Banana Pro (gemini-3-pro-image-preview).
Saves each as articles/<slug>/images/cover.jpg at 2048x1152 (16:9 2K).
"""

import os
import sys
import json
import base64
import io
import time
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image

# --- Config ---
API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "").strip()
MODEL = "gemini-3-pro-image-preview"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
BASE_DIR = Path("/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles")
LOG_DIR = Path("/home/max/MAVII_AGENTS/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
ERROR_LOG = LOG_DIR / "designer_errors.log"
ACTIVITY_LOG = LOG_DIR / "activity.log"
TARGET_W, TARGET_H = 2048, 1152   # 16:9 2K
QUALITY = 88                       # JPEG quality

COVERS = [
    {
        "slug": "cat-brings-prey-home",
        "prompt": (
            "A sleek grey domestic shorthair cat sitting proudly on a warm wooden hallway parquet floor "
            "near the front door, a small soft toy mouse lying on the floor directly in front of her. "
            "The cat holds a self-satisfied, regal expression gazing upward, tail curled neatly around her paws. "
            "Light: warm golden afternoon sunlight streaming through a frosted glass door panel on the left, "
            "casting soft long shadows across the parquet. "
            "Camera: 35mm lens, f/2.8, low angle at floor level shooting upward slightly, "
            "shallow depth of field, hallway beyond softly blurred into warm tones. "
            "Composition: cat positioned center-left frame, toy mouse in lower foreground, "
            "generous empty negative space in the upper half and right third for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, National Geographic quality, "
            "warm earth tones, natural saturation, soft contrast. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people, no human faces or hands. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "dog-licks-paws-obsessive",
        "prompt": (
            "A golden retriever lying relaxed on a light cream hardwood floor, "
            "head bent intently down to lick its front left paw with focused concentration. "
            "Fur is clean, full and fluffy. "
            "Light: soft diffused morning window light from the right side of frame, "
            "no harsh shadows, warm and even illumination. "
            "Camera: 50mm prime lens, f/2.2, eye-level angle close to the floor, "
            "shallow depth of field, cozy living room sofa and plant in background softly blurred. "
            "Composition: dog occupies the left two-thirds of frame, right third open negative space, "
            "generous empty space in upper portion above the dog for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, warm tones, natural colors, "
            "Kinfolk magazine aesthetic, high detail fur texture. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "cat-bites-during-petting",
        "prompt": (
            "An orange tabby cat lying fully on its side on a cream fabric sofa cushion, "
            "tail slightly twitching mid-curl, ears flattened back slightly, eyes wide with tension "
            "and overstimulation — captured at the precise moment of 'I have had enough petting'. "
            "No human hands or people visible anywhere in the frame. "
            "Light: soft natural afternoon daylight from a window just off-frame to the right, "
            "warm tone, gentle directional shadows on the sofa cushion. "
            "Camera: 50mm lens, f/2.0, eye-level with the cat lying on the sofa, "
            "shallow depth of field, sofa fabric texture and living room beyond softly blurred. "
            "Composition: cat fills the lower two-thirds of frame, upper third left open and bright "
            "for headline overlay, cat positioned slightly left of center. "
            "Style: editorial magazine photography, ultra realistic, warm muted palette, "
            "earth tones, National Geographic level quality. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people, no hands. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "kitten-cries-first-nights",
        "prompt": (
            "A tiny 8-week-old grey tabby kitten sitting alone on a thick soft knitted blanket on a bed, "
            "next to a small glowing warm-white nightlight on a wooden nightstand beside the bed. "
            "The kitten has a forlorn and wistful expression — wide reflective eyes, slightly hunched small body, "
            "a look of quiet loneliness but not extreme distress. "
            "Light: very soft warm amber glow emanating from the nightlight as the primary light source, "
            "dim overall scene, intimate and gentle nighttime atmosphere, deep shadows in the room corners. "
            "Camera: 50mm lens, f/1.8, slightly above eye-level angle looking down gently at the kitten, "
            "bedroom interior in deep soft bokeh behind. "
            "Composition: kitten positioned lower-center frame, nightlight to its right in soft focus, "
            "the upper half of frame in deep dark negative space for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, intimate nighttime mood, "
            "warm amber and deep shadow tones, no flash, high quality low-light photography. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "dog-steals-socks",
        "prompt": (
            "A beagle in full sprint down a bright light-filled home hallway, "
            "a white cotton sock firmly gripped in its mouth, "
            "ears flying back from motion, eyes bright and gleeful with mischief. "
            "Light: natural daylight flooding from a window at the far end of the hallway, "
            "bright and airy, light wooden floorboards reflecting soft warm light. "
            "Camera: 35mm lens, f/2.8, natural motion blur on the dog's legs and ears conveying speed, "
            "hallway walls and background compressed and slightly blurred. "
            "Composition: dog running from right to left across the full width of frame, "
            "centered vertically, ample empty space above in bright hallway ceiling for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, dynamic joyful energy, "
            "warm light palette, The Dodo editorial quality. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "dog-digs-yard-holes",
        "prompt": (
            "A chocolate labrador retriever standing on a lush green summer garden lawn directly next to "
            "a freshly excavated hole in the dark earth, paws visibly dirty with soil, "
            "head turned to face forward with a guilty and sheepish expression. "
            "Light: warm golden summer afternoon sunlight, soft dappled shadows from nearby garden foliage, "
            "rich and saturated greens. "
            "Camera: 50mm lens, f/2.5, low angle close to ground level, "
            "garden lawn, flowerbeds and a wooden fence in soft focus background. "
            "Composition: dog positioned right of center, dug hole in foreground lower-left, "
            "sky and upper garden serving as open negative space for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, vibrant warm summer tones, "
            "rich earth browns and lush greens, National Geographic quality. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "cat-jumps-on-counters",
        "prompt": (
            "A British Shorthair grey cat sitting composed and calm on a clean white marble kitchen countertop, "
            "positioned next to a small white ceramic bowl containing green apples and a single lemon, "
            "gazing downward with serene curiosity. "
            "Light: bright soft natural daylight streaming from a large window above the kitchen sink, "
            "clean and even illumination, white cabinet reflections, modern airy kitchen. "
            "Camera: 35mm lens, f/2.8, angle slightly below countertop level looking up at the cat, "
            "kitchen background bright and softly out of focus. "
            "Composition: cat occupies the left third of frame, fruit bowl positioned to its right, "
            "upper portion of frame in open white-grey negative space for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, clean minimalist aesthetic, "
            "cool whites and warm greys, Kinfolk or Bon Appetit magazine quality. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "cat-bath-needed-or-not",
        "prompt": (
            "A fluffy Maine Coon cat wrapped snugly in a large oversized cream-white terry bath towel, "
            "sitting on the edge of a white ceramic bathtub, fur slightly damp and pleasantly tousled, "
            "wearing a calm and dignified expression looking gently to the side. "
            "Light: warm soft bathroom lighting, flattering and gentle, faint steam in the air, "
            "white subway tiles and chrome faucet fittings visible in background. "
            "Camera: 50mm lens, f/2.2, eye-level aligned with the sitting cat, "
            "bathroom background pleasantly and evenly blurred. "
            "Composition: cat centered in frame, towel forming a soft organic framing element around it, "
            "upper third of frame light and open for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, spa-like warmth and serenity, "
            "cream and warm white palette, high quality pet photography. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people, no human hands visible. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "dog-rainy-walks-routine",
        "prompt": (
            "A black Labrador Retriever wearing a bright yellow waterproof dog raincoat "
            "standing on a wet glistening city sidewalk pavement in light autumn rain, "
            "puddles forming and reflecting the soft grey overcast sky, "
            "fallen amber and golden-yellow leaves scattered on the wet pavement around its paws. "
            "Light: overcast soft diffused autumn daylight, no harsh shadows, "
            "moody and atmospheric yet still warm in tone. "
            "Camera: 35mm lens, f/2.8, low angle at the dog's height level, "
            "rainy street and building facades softly blurred with wet pavement bokeh. "
            "Composition: dog positioned slightly left of center, "
            "looking ahead or slightly away from camera, "
            "upper third of frame open overcast sky serving as negative space for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, moody autumn atmosphere, "
            "muted blues contrasting with the bright yellow coat, golden wet leaf tones, "
            "National Geographic quality. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
    {
        "slug": "pet-ac-fan-summer-safety",
        "prompt": (
            "A tabby cat and a golden retriever lying peacefully side by side on cool smooth light grey floor tiles "
            "in a bright sunny living room, both stretched out and relaxed, "
            "a large white modern standing floor fan visible in the background gently in operation. "
            "Warm summer sunlight streaming through sheer white curtains, "
            "casting soft diffused patterns on the tile floor. "
            "Light: bright warm summer daylight, soft and even fill, "
            "white walls reflecting ambient light throughout the room. "
            "Camera: 35mm lens, f/3.5, low angle at floor level, "
            "both animals spread out comfortably, background living room furniture softly blurred. "
            "Composition: both animals fill the lower two-thirds of frame, "
            "fan and bright curtained window visible in upper background, "
            "ample open bright space above the pets for headline overlay. "
            "Style: editorial magazine photography, ultra realistic, light airy summer mood, "
            "warm whites, soft greys and golden tones, Kinfolk quality. "
            "No text, no letters, no watermarks, no logos, no AI artifacts, no people. "
            "16:9 cinematic crop, 2048x1152 pixels."
        ),
    },
]


def log_error(slug: str, msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [designer] [{slug}] {msg}\n"
    print(f"  ERROR: {msg}", file=sys.stderr)
    with open(ERROR_LOG, "a") as f:
        f.write(line)


def log_activity(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ACTIVITY_LOG, "a") as f:
        f.write(f"[{ts}] | max-designer-agent | {msg}\n")


def generate_image(prompt: str, slug: str):
    """Call Nano Banana Pro API. Returns (bytes, mime_type) or raises RuntimeError."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    resp = requests.post(ENDPOINT, headers=headers, json=payload, timeout=180)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:600]}")

    data = resp.json()
    usage = data.get("usageMetadata", {})
    if usage:
        print(f"  [usage] prompt={usage.get('promptTokenCount','?')} "
              f"total={usage.get('totalTokenCount','?')}")

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates in response: {json.dumps(data)[:400]}")

    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        if "inlineData" in part:
            inline = part["inlineData"]
            mime = inline.get("mimeType", "image/png")
            b64 = inline.get("data", "")
            if b64:
                return base64.b64decode(b64), mime

    raise RuntimeError(f"No image inlineData in parts: {json.dumps(parts)[:400]}")


def save_cover(img_bytes: bytes, mime: str, slug: str) -> str:
    """Resize/crop to 2048x1152, save as JPEG. Returns absolute path."""
    out_path = BASE_DIR / slug / "images" / "cover.jpg"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(io.BytesIO(img_bytes))
    print(f"  Source: {img.size} {img.mode}")

    if img.mode != "RGB":
        img = img.convert("RGB")

    target_ratio = TARGET_W / TARGET_H
    src_w, src_h = img.size
    src_ratio = src_w / src_h

    if abs(src_ratio - target_ratio) > 0.01:
        if src_ratio > target_ratio:
            # Too wide — crop sides
            new_w = int(src_h * target_ratio)
            x_off = (src_w - new_w) // 2
            img = img.crop((x_off, 0, x_off + new_w, src_h))
        else:
            # Too tall — crop top/bottom
            new_h = int(src_w / target_ratio)
            y_off = (src_h - new_h) // 2
            img = img.crop((0, y_off, src_w, y_off + new_h))

    img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    img.save(str(out_path), "JPEG", quality=QUALITY, optimize=True, progressive=True)

    size_kb = out_path.stat().st_size // 1024
    print(f"  Saved: {out_path} ({size_kb} KB)")
    return str(out_path)


def main():
    if not API_KEY:
        print("ERROR: GOOGLE_AI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print(f"Nano Banana Pro cover generation — {len(COVERS)} articles")
    print(f"Model: {MODEL}")
    print(f"Target: {TARGET_W}x{TARGET_H} JPEG q{QUALITY}\n")

    saved = []
    failed = []

    for i, cover in enumerate(COVERS, 1):
        slug = cover["slug"]
        print(f"[{i:02d}/10] {slug}")
        print(f"  Prompt: {len(cover['prompt'])} chars")

        success = False
        for attempt in range(1, 3):  # up to 2 attempts
            try:
                img_bytes, mime = generate_image(cover["prompt"], slug)
                print(f"  API returned {len(img_bytes)} bytes ({mime})")
                out_path = save_cover(img_bytes, mime, slug)
                saved.append(out_path)
                log_activity(
                    f"Generated cover for {slug} -> {out_path} "
                    f"({Path(out_path).stat().st_size // 1024} KB)"
                )
                success = True
                break
            except Exception as e:
                log_error(slug, f"Attempt {attempt}: {e}")
                if attempt < 2:
                    print(f"  Retrying in 5s...")
                    time.sleep(5)

        if not success:
            failed.append(slug)

        # Pause between images to respect rate limits
        if i < len(COVERS):
            time.sleep(4)

    print("\n" + "=" * 60)
    print(f"DONE: {len(saved)} saved, {len(failed)} failed")
    print("=" * 60)
    for p in saved:
        print(f"  OK  {p}")
    for s in failed:
        print(f"  FAIL  {s}")

    log_activity(
        f"Batch complete — saved {len(saved)}/10. "
        f"Failed: {failed if failed else 'none'}"
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
