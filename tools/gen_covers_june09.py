#!/usr/bin/env python3
"""
Generate 10 covers for AnimaLife — June 9, 2026.
Runs up to 3 concurrent API calls; 1 retry max per cover.
"""
import os
import sys
import json
import base64
import urllib.request
import urllib.error
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss"

COVERS = [
    {
        "slug": "cat-slow-blink-bonding",
        "prompt": (
            "Close-up portrait of a tabby cat with half-closed eyes, doing a slow blink, "
            "lying on a soft linen blanket near a sunny window. "
            "Light: gentle diffused morning window light from the right, warm golden tones, "
            "soft bokeh living room background. "
            "Camera: 85mm portrait lens, f/1.8, very shallow depth of field, eyes in soft focus. "
            "Composition: face fills two-thirds of frame, negative space to the left, "
            "slightly tilted head, intimate eye contact. "
            "Style: editorial magazine photography, ultra realistic, National Geographic warmth. "
            "Color palette: warm cream, amber, soft caramel. "
            "No text, no watermarks, no logos, no AI artifacts, no humans."
        ),
    },
    {
        "slug": "dog-howl-sirens-music",
        "prompt": (
            "Medium shot of a Pembroke Welsh Corgi or Siberian Husky mid-howl, "
            "head raised, mouth open in a perfect O shape, sitting on a wooden floor "
            "in a cozy living room. "
            "Light: warm sunset light streaming through a side window, golden hour glow. "
            "Camera: 50mm, f/2.8, shallow depth of field, dog in sharp focus. "
            "Composition: dog centered, head slightly back, expressive face, "
            "soft blurred interior behind. "
            "Style: editorial magazine photography, ultra realistic, charming candid moment. "
            "Color palette: warm amber, honey, soft wood tones. "
            "No text, no watermarks, no logos, no AI artifacts, no humans."
        ),
    },
    {
        "slug": "cat-paper-sitting-magic",
        "prompt": (
            "A tabby or orange cat sitting perfectly upright on a single sheet of white paper "
            "placed on a wooden desk or table, looking directly at camera with dignified posture. "
            "Light: soft diffused side light from a nearby window, gentle shadows on wood. "
            "Camera: slightly elevated angle (45 degrees from above), 50mm, f/2.8. "
            "Composition: cat on paper in center-left, some negative space on the right, "
            "natural wood texture visible. "
            "Style: editorial magazine photography, ultra realistic, warm and whimsical. "
            "Color palette: warm wood browns, soft white paper, cat fur earth tones. "
            "No text, no watermarks, no logos, no AI artifacts, no humans, no writing on paper."
        ),
    },
    {
        "slug": "dog-sniff-walk-decompression",
        "prompt": (
            "A Labrador or Border Collie on a long loose leash sniffing lush green grass "
            "along a forest trail at golden hour, nose to the ground, tail raised. "
            "Light: warm backlit golden hour sunlight filtering through trees, "
            "rim lighting on dog's fur, lens flare. "
            "Camera: 35mm, f/2.8, shallow depth of field, dog in focus, bokeh forest behind. "
            "Composition: dog in lower third, path leading into soft bokeh background, "
            "leash gently curving out of frame. "
            "Style: editorial outdoor photography, ultra realistic, peaceful and serene. "
            "Color palette: golden amber, deep green, warm brown. "
            "No text, no watermarks, no logos, no AI artifacts, no humans visible."
        ),
    },
    {
        "slug": "cat-window-chattering-birds",
        "prompt": (
            "A cat sitting on a windowsill, wide eyes and mouth slightly open mid-chatter, "
            "intently watching blurred bird silhouettes on a branch outside the window. "
            "Light: warm morning sunlight coming through window, cat backlit with warm rim glow, "
            "soft interior light. "
            "Camera: 85mm, f/2.0, cat in focus, outside window heavily blurred. "
            "Composition: cat in profile on the right third, birds as soft bokeh shapes "
            "on the left, window frame visible. "
            "Style: editorial magazine photography, ultra realistic, magical observational moment. "
            "Color palette: warm golden morning light, soft cream interior, "
            "muted greens outside. "
            "No text, no watermarks, no logos, no AI artifacts, no humans."
        ),
    },
    {
        "slug": "dog-paw-shake-trick-training",
        "prompt": (
            "Close-up of a Jack Russell Terrier or mixed breed small dog placing its paw "
            "into an open human hand — a classic handshake trick. "
            "Light: warm indoor light, soft window light from the side, cozy interior. "
            "Camera: 50mm macro, f/2.0, extremely shallow depth of field, "
            "paw and hand in sharp focus. "
            "Composition: hands and paw filling most of the frame, dog slightly blurred "
            "in background with happy expression visible. "
            "Style: editorial magazine photography, ultra realistic, heartwarming connection. "
            "Color palette: warm skin tones, soft beige, golden light. "
            "No text, no watermarks, no logos, no AI artifacts."
        ),
    },
    {
        "slug": "cat-suddenly-avoids-owner",
        "prompt": (
            "A grey or tabby cat peeking cautiously from under a couch or from a shadowed corner, "
            "ears slightly back, eyes wide, body low, watching something in the distance. "
            "Background: soft blurred silhouette of a person standing in a warmly lit room. "
            "Light: dramatic but gentle — warm background light contrasting with "
            "cooler shadow where cat hides, not scary, just mysterious. "
            "Camera: 35mm, f/2.0, cat in focus, background person heavily blurred. "
            "Composition: cat in lower foreground, blurred human figure in upper background, "
            "diagonal depth composition. "
            "Style: editorial magazine photography, ultra realistic, thoughtful narrative. "
            "Color palette: warm amber background, cool grey shadows, natural tones. "
            "No text, no watermarks, no logos, no AI artifacts."
        ),
    },
    {
        "slug": "dog-frap-zoomies-after-bath",
        "prompt": (
            "A wet medium-sized dog mid-zoomies, shaking its head and running across "
            "a bright living room floor after a bath, water droplets flying, motion blur on paws, "
            "joyful expression, tongue out. "
            "Light: bright natural indoor daylight, clean and cheerful. "
            "Camera: 35mm, f/4, motion blur on moving parts, face somewhat sharp. "
            "Composition: dog in dynamic diagonal motion across frame, "
            "water droplets catching light. "
            "Style: editorial magazine photography, ultra realistic, energetic and joyful. "
            "Color palette: bright whites, warm wood floor, sparkling water droplets. "
            "No text, no watermarks, no logos, no AI artifacts, no humans."
        ),
    },
    {
        "slug": "cat-fetch-play-breeds",
        "prompt": (
            "A sleek Siamese or Bengal cat running low across a hardwood floor, "
            "carrying a small plush toy in its mouth, mid-stride, tail up. "
            "Light: warm side window light, golden afternoon, low angle. "
            "Camera: very low angle (floor level), 35mm, f/2.8, cat in focus, "
            "floor perspective stretching behind. "
            "Composition: cat in sharp focus at center, floor leading lines, "
            "low perspective emphasizes speed and elegance. "
            "Style: editorial magazine photography, ultra realistic, dynamic action shot. "
            "Color palette: warm honey wood tones, cat markings, natural light. "
            "No text, no watermarks, no logos, no AI artifacts, no humans."
        ),
    },
    {
        "slug": "dog-watches-tv-screens",
        "prompt": (
            "A medium-sized dog (Golden Retriever or similar) sitting on a couch "
            "in a dark living room, head tilted slightly to one side, "
            "intently watching a glowing television screen that casts blue-white light. "
            "Light: dark room, primary light source is the TV screen glow — "
            "cool blue-white illuminating the dog's face from the front. "
            "Camera: 50mm, f/2.8, dog in focus. "
            "Composition: dog in center-right, TV screen partially visible or implied "
            "by the glow from left, dark atmospheric background. "
            "Style: editorial magazine photography, ultra realistic, cinematic mood. "
            "Color palette: cool blue TV glow, warm dog fur, dark room shadows. "
            "No text, no watermarks, no logos, no AI artifacts, no humans on screen."
        ),
    },
]


def get_api_key():
    key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        env_file = "/home/max/MAVII_AGENTS/secrets/google_ai.env"
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        if k in ("GOOGLE_AI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
                            key = v.strip()
                            break
    return key


def save_jpeg(img_bytes, output_path, quality=88):
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        target_w, target_h = 2048, 1152
        if w < target_w or h < target_h:
            scale = max(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        img.save(output_path, "JPEG", quality=quality, optimize=True)
        return img.size
    except ImportError:
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        return (0, 0)


def call_api(slug, prompt, api_key, model="gemini-3-pro-image-preview"):
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    full_prompt = (
        prompt.rstrip(".")
        + ". Aspect ratio 16:9, ultra detailed, ultra realistic editorial photography, "
        "minimum 2048x1152 resolution, no text, no watermarks, no logos."
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_one(item, api_key):
    slug = item["slug"]
    output_path = os.path.join(BASE, "articles", slug, "images", "cover.jpg")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    for attempt in range(1, 3):
        try:
            print(f"[{slug}] attempt {attempt}...", flush=True)
            body = call_api(slug, item["prompt"], api_key)
            candidates = body.get("candidates", [])
            if not candidates:
                raise ValueError(f"No candidates: {json.dumps(body)[:300]}")
            parts = candidates[0].get("content", {}).get("parts", [])
            img_b64 = None
            for part in parts:
                if "inlineData" in part:
                    img_b64 = part["inlineData"]["data"]
                    break
            if not img_b64:
                raise ValueError(f"No image data in parts: {json.dumps(parts)[:300]}")
            img_bytes = base64.b64decode(img_b64)
            dims = save_jpeg(img_bytes, output_path, quality=88)
            size_kb = os.path.getsize(output_path) // 1024
            usage = body.get("usageMetadata", {})
            print(f"[{slug}] OK — {size_kb} KB — {dims[0]}x{dims[1]} — {usage}", flush=True)
            return slug, True, size_kb, dims
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            print(f"[{slug}] HTTP {e.code} on attempt {attempt}: {err[:300]}", flush=True)
            if attempt == 2:
                return slug, False, 0, (0, 0)
            time.sleep(5)
        except Exception as e:
            print(f"[{slug}] Error on attempt {attempt}: {e}", flush=True)
            if attempt == 2:
                return slug, False, 0, (0, 0)
            time.sleep(5)
    return slug, False, 0, (0, 0)


def main():
    api_key = get_api_key()
    if not api_key:
        print("ERROR: No API key found", flush=True)
        sys.exit(1)

    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(generate_one, item, api_key): item["slug"] for item in COVERS}
        for future in as_completed(futures):
            slug, ok, size_kb, dims = future.result()
            results[slug] = (ok, size_kb, dims)

    print("\n=== RESULTS ===")
    for item in COVERS:
        slug = item["slug"]
        ok, size_kb, dims = results.get(slug, (False, 0, (0, 0)))
        mark = "OK" if ok else "FAIL"
        print(f"[{mark}] {slug} — {size_kb} KB — {dims[0]}x{dims[1]}")


if __name__ == "__main__":
    main()
