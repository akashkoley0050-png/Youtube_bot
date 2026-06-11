from __future__ import annotations

import os
import time
from pathlib import Path
import httpx

STYLE_SUFFIX = (
    ", cinematic digital illustration, detailed scene art, strong composition, "
    "professional youtube visual quality, no text, no captions, no watermark, no logos"
)

DEFAULT_NEGATIVE = (
    "blurry, low quality, watermark, logo, text, title, signature, ugly, grainy, "
    "gore, blood, nudity, child-unsafe"
)


def full_visual_prompt(scene: str, style_suffix: str | None = None) -> str:
    """Combine the scene description with a channel-specific style suffix."""
    return f"{scene.strip()}{(style_suffix or STYLE_SUFFIX)}"


def save_scene_image(
    index: int,
    prompt: str,
    out_path: Path,
    *,
    width: int = 768,
    height: int = 768,
    negative: str = DEFAULT_NEGATIVE,
) -> tuple[str, str]:
    """Generate and save one image using Hugging Face free tier inference gateway."""
    
    # Accept either token assignment name
    api_key = os.environ.get("DEAPI_TOKEN", "").strip() or os.environ.get("HF_TOKEN", "").strip()
    if not api_key:
        return "fail", "DEAPI_TOKEN not set"

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Free high-quality Stable Diffusion XL engine hosted by Hugging Face
    HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative,
            "width": width,
            "height": height
        }
    }

    # Give the model up to 3 context retries in case the cold machine engine is spinning up
    with httpx.Client(timeout=90.0) as client:
        for attempt in range(1, 4):
            try:
                resp = client.post(HF_API_URL, json=payload, headers=headers)
                
                # 503 means model is loading into memory, wait it out
                if resp.status_code == 503:
                    print(f"  🤖 Hugging Face model is loading... waiting 15s (attempt {attempt}/3)")
                    time.sleep(15)
                    continue
                    
                resp.raise_for_status()
                out_path.write_bytes(resp.content)
                return "ok", "huggingface"
                
            except Exception as e:
                if attempt == 3:
                    return "fail", f"HF Engine Exception: {str(e)}"
                time.sleep(5)
                
    return "fail", "Hugging Face model took too long to load"
