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

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
    if not key:
        # try reading from env file
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

def generate_cover(slug, output_path, prompt, model="gemini-3-pro-image-preview", retry=False):
    api_key = get_api_key()
    if not api_key:
        return False, "No API key found"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    # Enhance prompt with 16:9 2K instruction
    full_prompt = (
        prompt.rstrip(".") +
        ". Aspect ratio 16:9, wide cinematic crop, 2560x1440 resolution equivalent, "
        "ultra detailed, ultra realistic editorial photography quality."
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
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
        return False, f"HTTP {e.code}: {err_body[:300]}"
    except Exception as e:
        return False, str(e)

    # Parse response — find image data
    try:
        candidates = body.get("candidates", [])
        if not candidates:
            return False, f"No candidates in response: {json.dumps(body)[:300]}"

        parts = candidates[0].get("content", {}).get("parts", [])
        image_data = None
        for part in parts:
            if "inlineData" in part:
                image_data = part["inlineData"]["data"]
                mime = part["inlineData"].get("mimeType", "image/jpeg")
                break

        if not image_data:
            return False, f"No image in response parts: {json.dumps(parts)[:300]}"

        img_bytes = base64.b64decode(image_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_bytes)

        size_kb = len(img_bytes) // 1024
        usage = body.get("usageMetadata", {})
        return True, f"OK — {size_kb}KB — usage: {usage}"

    except Exception as e:
        return False, f"Parse error: {e} | body: {json.dumps(body)[:300]}"


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: gen_cover.py <slug> <output_path> <prompt>")
        sys.exit(1)

    slug = sys.argv[1]
    output_path = sys.argv[2]
    prompt = sys.argv[3]

    print(f"[{slug}] Generating with Nano Banana Pro...", flush=True)
    ok, msg = generate_cover(slug, output_path, prompt)

    if not ok:
        print(f"[{slug}] FAILED on first try: {msg}", flush=True)
        print(f"[{slug}] Retrying...", flush=True)
        ok, msg = generate_cover(slug, output_path, prompt)

    if ok:
        print(f"[{slug}] SUCCESS: {msg}", flush=True)
        sys.exit(0)
    else:
        print(f"[{slug}] FINAL FAILURE: {msg}", flush=True)
        sys.exit(1)
