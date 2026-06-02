#!/usr/bin/env python3
"""
Generate cover image via Nano Banana Pro (gemini-3-pro-image-preview).
Usage: python3 generate_cover.py <slug> <prompt_file_or_inline>
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error

API_KEY_FILE = "/home/max/MAVII_AGENTS/secrets/google_ai.env"
BASE_DIR = "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles"
LOG_FILE = "/home/max/MAVII_AGENTS/logs/activity.log"
ERROR_LOG = "/home/max/MAVII_AGENTS/logs/designer_errors.log"
MODEL = "gemini-3-pro-image-preview"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def read_api_key():
    with open(API_KEY_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("GOOGLE_AI_API_KEY="):
                return line.split("=", 1)[1]
    raise ValueError("GOOGLE_AI_API_KEY not found in secrets file")


def generate_image(api_key: str, prompt: str) -> bytes:
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]}
    }).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def save_cover(slug: str, image_bytes: bytes):
    out_path = os.path.join(BASE_DIR, slug, "images", "cover.jpg")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(image_bytes)
    return out_path


def log_activity(message: str):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{ts} | {message}\n")


def log_error(slug: str, error: str):
    os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    with open(ERROR_LOG, "a") as f:
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{ts} | slug={slug} | {error}\n")


def extract_image_from_response(response_data: dict) -> bytes:
    """Extract base64-encoded image bytes from Gemini API response."""
    candidates = response_data.get("candidates", [])
    if not candidates:
        raise ValueError("No candidates in response")

    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        if "inlineData" in part:
            mime = part["inlineData"].get("mimeType", "")
            b64 = part["inlineData"].get("data", "")
            return base64.b64decode(b64)

    raise ValueError(f"No image in response parts. Parts: {[list(p.keys()) for p in parts]}")


def run(slug: str, prompt: str):
    print(f"[{slug}] Starting generation...")
    api_key = read_api_key()

    try:
        raw = generate_image(api_key, prompt)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        log_error(slug, f"HTTPError {e.code}: {body[:500]}")
        print(f"[{slug}] ERROR: HTTP {e.code} — {body[:300]}")
        return None
    except Exception as e:
        log_error(slug, str(e))
        print(f"[{slug}] ERROR: {e}")
        return None

    response_data = json.loads(raw)

    # Log token usage
    usage = response_data.get("usageMetadata", {})
    print(f"[{slug}] Token usage: {usage}")

    try:
        image_bytes = extract_image_from_response(response_data)
    except Exception as e:
        log_error(slug, f"extract error: {e} | response keys: {list(response_data.keys())}")
        print(f"[{slug}] ERROR extracting image: {e}")
        # Dump partial response for debugging
        print(f"[{slug}] Response preview: {str(response_data)[:500]}")
        return None

    out_path = save_cover(slug, image_bytes)
    log_activity(f"max-designer-agent | Generated cover for {slug} | {out_path} | OK")
    print(f"[{slug}] Saved -> {out_path} ({len(image_bytes)} bytes)")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: generate_cover.py <slug> <prompt>")
        sys.exit(1)
    slug_arg = sys.argv[1]
    prompt_arg = " ".join(sys.argv[2:])
    result = run(slug_arg, prompt_arg)
    sys.exit(0 if result else 1)
