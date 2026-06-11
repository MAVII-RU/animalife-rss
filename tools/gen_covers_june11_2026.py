#!/usr/bin/env python3
"""
Batch cover generation for AnimaLife — 2026-06-11.
10 covers: cat kneading, loaf pose, ear positions, prefers one person,
           summer window safety, dog leans on owner, play bow, shake off stress,
           eats too fast, begs at table.
Model: gemini-3-pro-image-preview (Nano Banana Pro).
Output: 2048x1152 JPEG, quality=85.
No text on image — clean photo only.
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

# --- API Key ---
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
BASE = "/home/max/MAVII_AGENTS/projects/animalife/repos/animalife-rss/articles"

COVERS = [
    {
        "slug": "cat-kneading-blanket",
        "animal": "cat",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A grey or cream medium-age domestic cat slowly kneading a white or light-beige knitted wool blanket "
            "on a cosy sofa, eyes half-closed in blissful pleasure, paws alternating in soft rhythmic motion. "
            "Camera angle: slightly above and to the side, showing the cat's face and both front paws clearly. "
            "Light: soft warm morning sunlight streaming from a window at the left, creating gentle highlights on the fur. "
            "Lens: 50mm, f/2.2, shallow depth of field, blanket texture sharp, background sofa softly blurred. "
            "Composition: cat in left two-thirds, negative space on the right, eye-level intimacy. "
            "Color: warm cream and grey tones, soft contrast, natural saturation. "
            "No humans. No text, no letters, no watermarks, no logos, no UI elements. "
            "Ultra realistic, National Geographic editorial level, premium photography."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Grey cat kneading a knitted blanket on a sofa, "
            "eyes half-closed, morning window light from left, shallow depth of field. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    },
    {
        "slug": "cat-loaf-pose-meaning",
        "animal": "cat",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "An orange or tabby domestic cat sitting in a perfect 'loaf' pose — all four paws tucked completely "
            "underneath the body, tail wrapped neatly around — resting on a warm window ledge or soft wool throw. "
            "The cat's expression is calm, neutral, ears relaxed and slightly to the sides, eyes half-open. "
            "Light: warm golden-hour sunlight from a low window angle, creating rich amber highlights on the fur. "
            "Lens: 85mm portrait, f/1.8, beautifully blurred warm-toned background. "
            "Composition: cat centred slightly right, low camera angle at cat-eye level, negative space left. "
            "Color: warm amber, terracotta, cream — AnimaLife palette. "
            "No humans. No text, no letters, no watermarks, no logos. "
            "Ultra realistic, The Atlantic magazine level photography."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Orange tabby cat in loaf pose on warm windowsill, "
            "golden hour light, eyes half-open, shallow depth of field, warm blurred background. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    },
    {
        "slug": "cat-ear-positions-decoded",
        "animal": "cat",
        "prompt": (
            "Photorealistic editorial portrait photograph, 16:9 cinematic crop. "
            "Close three-quarter portrait of a short-haired domestic cat, ears clearly visible in the 'radar' position "
            "— one ear slightly rotated outward to the left, the other forward-right — showing the natural mobility "
            "of cat ears. The cat has clear green eyes, well-defined whiskers pointing forward, soft coat texture. "
            "Light: clean soft studio-style natural daylight from a large window on the left side, "
            "gentle fill from the right, portrait-quality catchlights in the eyes. "
            "Background: clean light warm grey or blurred soft bokeh, uncluttered. "
            "Lens: 85mm portrait, f/2.0, eyes and ears tack sharp, fur detail crisp. "
            "Composition: face filling upper half of frame, ears clearly silhouetted against background. "
            "No humans. No text, no letters, no watermarks, no logos. "
            "Ultra realistic, Vogue editorial portrait level."
        ),
        "retry_prompt": (
            "Photorealistic portrait photo, 16:9. Short-hair cat three-quarter view, "
            "ears rotated in radar position, green eyes, whiskers sharp, soft grey background, "
            "natural window light. No text, no watermark, no humans. Ultra realistic."
        ),
    },
    {
        "slug": "cat-prefers-one-person",
        "animal": "cat",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A grey-and-white or black domestic cat affectionately rubbing its cheek and face against "
            "the hand or shoulder of one person (only the hand or upper shoulder visible in frame, no face). "
            "In the soft background a second blurred human figure is visible but out of focus. "
            "Interior: cosy warm living room, evening lamp light, neutral tones. "
            "Light: warm indoor ambient light, soft shadows, intimate domestic mood. "
            "Lens: 50mm, f/1.8, cat and hand sharp, background figure softly blurred at f/1.8 depth of field. "
            "Composition: cat fills left two-thirds of frame, rubbing motion captured naturally. "
            "Color: warm neutral tones, soft shadow, intimate. "
            "No full faces visible. No text, no letters, no watermarks, no logos. "
            "Ultra realistic, The New York Times Magazine level."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Grey-white cat rubbing cheek against a person's hand, "
            "second blurred figure in background, warm indoor light, shallow depth of field. "
            "No text, no watermark, no faces. Ultra realistic."
        ),
    },
    {
        "slug": "cat-summer-windows-safety",
        "animal": "cat",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A domestic cat sitting peacefully on an indoor window ledge in summer, gazing outside through "
            "a window fitted with a fine metal mesh anti-cat screen (mosquito net type, clearly visible grid). "
            "A lightweight white or cream curtain beside the window gently moves as if in a light summer breeze. "
            "Outside: bright summer daylight, soft green trees visible through the mesh. "
            "Light: warm bright summer sunlight coming through the window, cat slightly rim-lit, interior side soft shadow. "
            "Lens: 35mm, f/2.8, cat and mesh sharp, outdoor scene softly blurred. "
            "Composition: cat in right-center frame, curtain on left, window mesh crossing the right side of image. "
            "No humans. No text, no letters, no watermarks, no logos. "
            "Ultra realistic, home decor magazine quality."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Cat on windowsill looking out through metal mesh screen, "
            "summer sunlight, curtain swaying, soft outdoor bokeh. No text, no watermark, no humans. Ultra realistic."
        ),
    },
    {
        "slug": "dog-leans-on-owner",
        "animal": "dog",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A large Labrador retriever or shepherd-mix dog sitting calmly on a park path, leaning its full body weight "
            "sideways against the leg of a seated person (person visible from waist down — jeans, no face visible). "
            "The person's hand rests gently on the dog's back. Dog expression: calm, trusting, peaceful eyes. "
            "Setting: beautiful urban park, late afternoon, dappled light through trees. "
            "Light: warm golden afternoon sunlight filtering through tree canopy, soft dappled shadows on grass. "
            "Lens: 50mm, f/2.0, dog and hand sharp, park background bokeh. "
            "Composition: dog in center-left, person's leg on right, park stretching behind in soft focus. "
            "Color: warm green park tones, golden light, earthy neutrals. "
            "No faces visible. No text, no letters, no watermarks, no logos. "
            "Ultra realistic, National Geographic Dogs level photography."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Labrador leaning against owner's leg in a park, "
            "hand on dog's back, golden afternoon light through trees, shallow depth of field. "
            "No text, no watermark, no faces. Ultra realistic."
        ),
    },
    {
        "slug": "dog-play-bow-decoded",
        "animal": "dog",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A border collie or medium mixed-breed dog in a perfect textbook play-bow position on a lush green meadow: "
            "front legs fully stretched forward and flat on the ground, rear end raised high, tail wagging (slight motion blur on tail). "
            "The dog's gaze is direct, bright, inviting — full of playful energy. Mouth slightly open, tongue just visible. "
            "Setting: open green meadow in warm afternoon light, no obstacles or other animals. "
            "Light: warm bright afternoon sun from the side, grass in vibrant green, slight rim light on the dog's back. "
            "Lens: 70mm, f/2.8, dog sharp end-to-end, meadow background softly blurred. "
            "Composition: dog fills the frame from left third to center, low camera angle (ground level or slightly above). "
            "No humans. No text, no letters, no watermarks, no logos. "
            "Ultra realistic, Dog Fancy magazine editorial level."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Border collie in play bow on green meadow, "
            "front paws flat, rear raised, tail wagging, low camera angle, warm afternoon sunlight. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    },
    {
        "slug": "dog-shake-off-stress",
        "animal": "dog",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A Siberian husky or husky-type mixed breed dog in the middle of a full-body shake: "
            "fur and ears flying in all directions with natural motion blur, capturing the exact split second of release. "
            "The dog is standing on an outdoor path or gravel after a walk, no water involved — this is a dry stress-shake. "
            "Expression: eyes closed or squinting, body in mid-shake S-curve. "
            "Light: bright overcast outdoor daylight, even soft shadows, cool blue-grey sky implied in background. "
            "Lens: 100mm, 1/500s frozen-motion but deliberate soft fur motion blur, f/2.8. "
            "Composition: dog centered, shake motion fills the frame dynamically, background neutral blurred path. "
            "No humans. No text, no letters, no watermarks, no logos. "
            "Ultra realistic, wildlife motion photography level."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Husky dog full-body shaking on outdoor path, "
            "fur and ears in mid-motion blur, bright overcast daylight. "
            "No text, no watermark, no humans, no water. Ultra realistic."
        ),
    },
    {
        "slug": "dog-eats-too-fast",
        "animal": "dog",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A golden retriever or mixed-breed dog standing at a slow-feeder puzzle bowl (maze-pattern interior) "
            "on a kitchen floor, nosing and licking at the maze channels with focused interest. "
            "Beside the slow feeder, an ordinary empty smooth bowl is visible — for comparison. "
            "Setting: bright clean modern kitchen, natural daylight from a nearby window. "
            "Light: soft even natural daylight, warm white kitchen tones, no harsh shadows. "
            "Lens: 35mm, f/2.8, dog and bowls sharp, kitchen background softly blurred. "
            "Composition: dog and both bowls in frame, dog's face angled down into the slow-feeder, eye contact with bowl. "
            "No humans. No text, no letters, no watermarks, no logos, no brand labels on bowls. "
            "Ultra realistic, editorial food-and-pet photography level."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Golden retriever eating from a slow feeder maze bowl in a kitchen, "
            "plain empty bowl beside it, natural daylight, dog face angled down. "
            "No text, no watermark, no humans. Ultra realistic."
        ),
    },
    {
        "slug": "dog-begs-at-table",
        "animal": "dog",
        "prompt": (
            "Photorealistic editorial magazine photograph, 16:9 cinematic crop. "
            "A medium-size calm dog (mixed breed or labrador-type) lying peacefully on a soft mat or dog bed "
            "a few metres away from a family dining table. At the table, slightly out-of-focus figures of a family "
            "having dinner are visible — warm plates and glasses on the table. The dog is calm, head resting on paws, "
            "not begging — the image illustrates correct, trained relaxed behaviour. "
            "Setting: warm family dining room, evening, warm lamp light. "
            "Light: warm indoor evening light from overhead dining lamp, soft glow on the table, dog in softer ambient light. "
            "Lens: 35mm, f/2.2, dog on mat sharp in foreground, family table blurred in midground. "
            "Composition: dog fills lower foreground, table and family in the background depth. "
            "No faces clearly visible (family blurred). No text, no letters, no watermarks, no logos. "
            "Ultra realistic, New York Times Home editorial level."
        ),
        "retry_prompt": (
            "Photorealistic editorial photo, 16:9. Calm dog lying on a mat near a dining table where blurred family eats, "
            "warm evening lamp light, dog relaxed and not begging. "
            "No text, no watermark, no clear faces. Ultra realistic."
        ),
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
        print(f"    HTTP {e.code}: {err_body[:400]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"    Request error: {e}", file=sys.stderr)
        return None

    # Extract image bytes
    try:
        parts = body["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                data = base64.b64decode(part["inlineData"]["data"])
                if "usageMetadata" in body:
                    print(f"    usageMetadata: {body['usageMetadata']}")
                return data
        print(f"    No inlineData. Keys: {list(body.keys())}", file=sys.stderr)
        if "usageMetadata" in body:
            print(f"    usageMetadata: {body['usageMetadata']}")
        # Show candidate finish reason if any
        try:
            fr = body["candidates"][0].get("finishReason", "?")
            print(f"    finishReason: {fr}", file=sys.stderr)
        except Exception:
            pass
        return None
    except (KeyError, IndexError) as e:
        print(f"    Parse error: {e}. Response: {str(body)[:400]}", file=sys.stderr)
        return None


def cover_verify(img: Image.Image) -> tuple[bool, str]:
    w, h = img.size
    if w < 1920 or h < 1080:
        return False, f"resolution too small: {w}x{h}"
    ratio = w / h
    if not (1.6 <= ratio <= 1.9):
        return False, f"aspect ratio off: {ratio:.2f}"
    import statistics
    r, g, b = img.convert("RGB").split()
    if statistics.stdev(list(r.getdata())) < 5:
        return False, "image appears blank"
    return True, "ok"


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

    if img.size[0] < TARGET_W:
        img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    elif img.size != (TARGET_W, TARGET_H):
        img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)

    ok, reason = cover_verify(img)
    if not ok:
        return False, reason

    img = img.convert("RGB")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "JPEG", quality=85, optimize=True)
    return True, "ok"


def generate_cover(cover: dict) -> tuple[str, bool, str, int]:
    slug = cover["slug"]
    out_path = f"{BASE}/{slug}/images/cover.jpg"
    print(f"\n[{slug}] Generating (attempt 1)...")
    img_bytes = call_api(cover["prompt"])
    if img_bytes:
        ok, reason = process_image(img_bytes, out_path)
        if ok:
            size_kb = os.path.getsize(out_path) // 1024
            print(f"[{slug}] OK — {out_path} ({size_kb} KB)")
            return slug, True, "OK", size_kb
        else:
            print(f"[{slug}] verify FAIL: {reason} — retrying...")
    else:
        print(f"[{slug}] No image returned — retrying...")

    print(f"[{slug}] Generating (attempt 2, retry prompt)...")
    img_bytes2 = call_api(cover["retry_prompt"])
    if img_bytes2:
        ok2, reason2 = process_image(img_bytes2, out_path)
        if ok2:
            size_kb = os.path.getsize(out_path) // 1024
            print(f"[{slug}] OK (retry) — {out_path} ({size_kb} KB)")
            return slug, True, "OK (retry)", size_kb
        else:
            return slug, False, f"FAIL: {reason2}", 0
    else:
        return slug, False, "FAIL: no image on retry", 0


if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: GOOGLE_AI_API_KEY not found", file=sys.stderr)
        sys.exit(1)

    print("=== AnimaLife Cover Batch — 2026-06-11 (10 covers) ===")
    print(f"Model: {ENDPOINT.split('/models/')[1].split(':')[0]}")
    print(f"Target: {TARGET_W}x{TARGET_H} JPEG q=85\n")

    results = []
    for cover in COVERS:
        slug, ok, msg, size_kb = generate_cover(cover)
        results.append((slug, ok, msg, size_kb))

    print("\n\n=== FINAL RESULTS ===")
    for slug, ok, msg, size_kb in results:
        status = "OK" if ok else "FAIL"
        path = f"{BASE}/{slug}/images/cover.jpg"
        size_str = f"{size_kb} KB" if ok else "—"
        print(f"{status:4s} | {slug:<35} | {path} | {size_str} | {msg}")
