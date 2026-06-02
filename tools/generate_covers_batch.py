#!/usr/bin/env python3
"""
Batch cover generator for AnimaLife articles.
Reads prompts from tools/covers_prompts.json, generates via Gemini image API,
saves to articles/<slug>/images/cover.jpg

Usage: python3 tools/generate_covers_batch.py [--model MODEL] [--slug SLUG]

If --slug is given, generates only that one cover.
Defaults to gemini-3-pro-image-preview, falls back to gemini-3.1-flash-image-preview.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
import time
import argparse
from datetime import datetime

BASE_DIR = "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss"
API_KEY_FILE = "/home/max/MAVII_AGENTS/secrets/google_ai.env"
PROMPTS_FILE = os.path.join(BASE_DIR, "tools/covers_prompts.json")
LOG_FILE = "/home/max/MAVII_AGENTS/logs/activity.log"
ERROR_LOG = "/home/max/MAVII_AGENTS/logs/designer_errors.log"

FALLBACK_MODELS = [
    "gemini-3-pro-image-preview",
    "gemini-3-pro-image",
    "nano-banana-pro-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image",
]


def read_api_key():
    with open(API_KEY_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("GOOGLE_AI_API_KEY="):
                return line.split("=", 1)[1]
    raise ValueError("GOOGLE_AI_API_KEY not found")


def call_api(api_key: str, model: str, prompt: str) -> dict:
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }).encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, headers={
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def extract_image(response_data: dict) -> bytes:
    candidates = response_data.get("candidates", [])
    for candidate in candidates:
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
    raise ValueError("No image found in response")


def log(msg: str, file: str = LOG_FILE):
    os.makedirs(os.path.dirname(file), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file, "a") as f:
        f.write(f"{ts} | {msg}\n")


def generate_one(api_key: str, cover: dict, preferred_model: str = None) -> bool:
    slug = cover["slug"]
    prompt = cover["prompt"]
    out_rel = cover["output"]
    out_path = os.path.join(BASE_DIR, out_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    models = FALLBACK_MODELS[:]
    if preferred_model and preferred_model in models:
        models.remove(preferred_model)
        models.insert(0, preferred_model)

    for model in models:
        print(f"[{slug}] Trying model: {model}")
        try:
            data = call_api(api_key, model, prompt)
            usage = data.get("usageMetadata", {})
            print(f"[{slug}] Token usage: {usage}")
            image_bytes = extract_image(data)
            with open(out_path, "wb") as f:
                f.write(image_bytes)
            print(f"[{slug}] Saved -> {out_path} ({len(image_bytes):,} bytes) via {model}")
            log(f"max-designer-agent | cover generated | slug={slug} | model={model} | file={out_path} | OK")
            return True
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 429:
                retry_match = None
                try:
                    err_data = json.loads(body)
                    for d in err_data.get("error", {}).get("details", []):
                        if d.get("@type", "").endswith("RetryInfo"):
                            retry_match = d.get("retryDelay", "0s")
                except Exception:
                    pass
                print(f"[{slug}] 429 on {model} (retry: {retry_match}), trying next model...")
                log(f"max-designer-agent | 429 quota | slug={slug} | model={model} | retry={retry_match}", ERROR_LOG)
                time.sleep(2)
                continue
            else:
                print(f"[{slug}] HTTP {e.code} on {model}: {body[:200]}")
                log(f"max-designer-agent | HTTP {e.code} | slug={slug} | model={model} | {body[:200]}", ERROR_LOG)
                continue
        except Exception as e:
            print(f"[{slug}] Error on {model}: {e}")
            log(f"max-designer-agent | ERROR | slug={slug} | model={model} | {e}", ERROR_LOG)
            continue

    print(f"[{slug}] All models failed.")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Preferred model to use first")
    parser.add_argument("--slug", default=None, help="Generate only this slug")
    args = parser.parse_args()

    with open(PROMPTS_FILE) as f:
        config = json.load(f)

    covers = config["covers"]
    if args.slug:
        covers = [c for c in covers if c["slug"] == args.slug]
        if not covers:
            print(f"Slug '{args.slug}' not found in prompts file.")
            sys.exit(1)

    api_key = read_api_key()
    results = []

    for i, cover in enumerate(covers):
        if i > 0:
            print(f"Waiting 5s between requests...")
            time.sleep(5)
        success = generate_one(api_key, cover, args.model)
        results.append((cover["slug"], success))

    print("\n--- Results ---")
    for slug, ok in results:
        status = "OK" if ok else "FAILED"
        out = os.path.join(BASE_DIR, next(c["output"] for c in config["covers"] if c["slug"] == slug))
        print(f"  {status}: {slug} -> {out}")

    failed = [s for s, ok in results if not ok]
    if failed:
        print(f"\nFailed: {failed}")
        print("Note: If quota exhausted, retry after UTC midnight (07:00 MSK).")
        sys.exit(1)


if __name__ == "__main__":
    main()
