#!/usr/bin/env python3
"""
Generate a single cover image via Nano Banana Pro (gemini-3-pro-image-preview).
Usage: python3 gen_cover.py <slug> <output_path> <prompt>
"""
import sys
import os
import base64
import json
import urllib.request
import urllib.error
import io

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
    if not key:
        env_file = "/home/max/MAVII_AGENTS/secrets/google_ai.env"
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        if k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_AI_API_KEY"):
                            key = v.strip()
                            break
    return key

def save_image(img_bytes: bytes, output_path: str, quality: int = 92):
    """Save raw image bytes as JPEG, resizing to at least 2048x1152 (16:9 2K) if needed."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        target_w, target_h = 2048, 1152
        w, h = img.size
        # Upscale only if smaller than target
        if w < target_w or h < target_h:
            img = img.resize((max(w, target_w), max(h, target_h)), Image.LANCZOS)
        img.save(output_path, "JPEG", quality=quality, optimize=True)
        return img.size
    except ImportError:
        # Pillow not available — save raw bytes as-is (may already be JPEG)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        return (0, 0)

def generate_cover(slug, output_path, prompt, model="gemini-3-pro-image-preview"):
    api_key = get_api_key()
    if not api_key:
        return False, "No API key found"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    full_prompt = (
        prompt.rstrip(".") +
        ". Aspect ratio 16:9, wide cinematic crop, ultra detailed, "
        "ultra realistic editorial photography quality, 2048x1152 minimum resolution."
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return False, f"HTTP {e.code}: {err_body[:500]}"
    except Exception as e:
        return False, str(e)

    try:
        candidates = body.get("candidates", [])
        if not candidates:
            return False, f"No candidates in response: {json.dumps(body)[:400]}"

        parts = candidates[0].get("content", {}).get("parts", [])
        image_data = None
        mime = "image/jpeg"
        for part in parts:
            if "inlineData" in part:
                image_data = part["inlineData"]["data"]
                mime = part["inlineData"].get("mimeType", "image/jpeg")
                break

        if not image_data:
            return False, f"No image in response parts: {json.dumps(parts)[:400]}"

        img_bytes = base64.b64decode(image_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        dims = save_image(img_bytes, output_path, quality=92)
        size_kb = os.path.getsize(output_path) // 1024
        usage = body.get("usageMetadata", {})
        return True, f"OK — {size_kb} KB — dims {dims[0]}x{dims[1]} — usage: {usage}"

    except Exception as e:
        return False, f"Parse/save error: {e} | body: {json.dumps(body)[:300]}"


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: gen_cover.py <slug> <output_path> <prompt>")
        sys.exit(1)

    slug = sys.argv[1]
    output_path = sys.argv[2]
    prompt = sys.argv[3]

    print(f"[{slug}] Generating with Nano Banana Pro (gemini-3-pro-image-preview)...", flush=True)
    ok, msg = generate_cover(slug, output_path, prompt)

    if not ok:
        print(f"[{slug}] FAILED on first try: {msg}", flush=True)
        print(f"[{slug}] Retrying once...", flush=True)
        ok, msg = generate_cover(slug, output_path, prompt)

    if ok:
        print(f"[{slug}] SUCCESS: {msg}", flush=True)
        sys.exit(0)
    else:
        print(f"[{slug}] FINAL FAILURE: {msg}", flush=True)
        sys.exit(1)
