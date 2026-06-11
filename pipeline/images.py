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
    
    api_key = os.environ.get("DEAPI_TOKEN", "").strip() or os.environ.get("HF_TOKEN", "").strip()
    if not api_key:
        return "fail", "Authentication token not set"

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Updated, standard stable-diffusion endpoint URL structure
    HF_API_URL = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative
        }
    }

    # Use httpx with explicit proxy bypass and automatic redirect follows enabled
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        for attempt in range(1, 4):
            try:
                resp = client.post(HF_API_URL, json=payload, headers=headers)
                
                if resp.status_code == 200:
                    out_path.write_bytes(resp.content)
                    return "ok", "huggingface"
                elif resp.status_code == 503:
                    print(f"  🤖 Model loading up... waiting 20s (attempt {attempt}/3)")
                    time.sleep(20)
                    continue
                else:
                    return "fail", f"HF Gateway Status Code: {resp.status_code}"
                    
            except Exception as e:
                if attempt == 3:
                    return "fail", f"Connection Error: {str(e)}"
                time.sleep(5)
                
    return "fail", "Hugging Face model timed out"
