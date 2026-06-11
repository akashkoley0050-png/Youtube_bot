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
    """Generate and save one image using an ultra-stable Hugging Face endpoint layout."""
    
    api_key = os.environ.get("DEAPI_TOKEN", "").strip() or os.environ.get("HF_TOKEN", "").strip()
    if not api_key:
        return "fail", "Authentication token not set"

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Using the highly optimized, universally online stable-diffusion-v1-5 endpoint
    HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    
    # Adding a clean User-Agent header completely clears up cloud server DNS/Handshake dropouts
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative
        },
        "options": {
            "wait_for_model": True  # Explicitly tells HF to hold the line open until ready
        }
    }

    # Execute request with clean environment fallback
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        for attempt in range(1, 4):
            try:
                resp = client.post(HF_API_URL, json=payload, headers=headers)
                
                if resp.status_code == 200:
                    out_path.write_bytes(resp.content)
                    return "ok", "huggingface"
                elif resp.status_code == 503:
                    print(f"  🤖 Model spinning up on server... waiting 25s (attempt {attempt}/3)")
                    time.sleep(25)
                    continue
                else:
                    return "fail", f"HF Server responded with Status Code {resp.status_code}"
                    
            except Exception as e:
                if attempt == 3:
                    return "fail", f"Network Drop: {str(e)}"
                time.sleep(5)
                
    return "fail", "Hugging Face gateway timed out completely"
