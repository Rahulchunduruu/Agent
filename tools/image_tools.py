"""Image analysis tool: image_describe."""

import os

import requests
from langchain_core.tools import tool

from config import Config


def _local_image_analysis(image_bytes: bytes, source: str) -> str:
    """Fallback: basic image info via PIL when the vision API is unavailable."""
    import io as _io
    from collections import Counter
    from PIL import Image
    img = Image.open(_io.BytesIO(image_bytes))
    width, height = img.size
    fmt = img.format or "unknown"
    mode = img.mode
    small = img.convert("RGB").resize((50, 50))
    pixels = list(small.getdata())

    def bucket(p):
        return (p[0] // 32 * 32, p[1] // 32 * 32, p[2] // 32 * 32)

    counts = Counter(bucket(p) for p in pixels)
    top = counts.most_common(3)
    color_names = ["RGB({},{},{})".format(r, g, b) for (r, g, b), _ in top]
    return (
        "[Local analysis - vision API unavailable]\n"
        "Source: {}\n"
        "Dimensions: {}x{} px\n"
        "Format: {} | Mode: {}\n"
        "Dominant colors: {}".format(source, width, height, fmt, mode, ", ".join(color_names))
    )


@tool
def image_describe(image_path: str = None, image_url: str = None, prompt: str = "Describe this image in detail.") -> str:
    """Describe/analyze an image using a vision AI model.
    Provide either a local file path (image_path) or a web URL (image_url).
    Optionally customize what to look for via the prompt parameter.
    Falls back to basic local analysis (dimensions, colors) if the vision API is unavailable.
    """
    import base64 as _b64
    import io as _io
    from PIL import Image
    try:
        if not image_path and not image_url:
            return "Error: Provide either image_path (local file) or image_url (web link)."

        if image_path:
            if not os.path.exists(image_path):
                return "Error: File not found: {}".format(image_path)
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            source = image_path
        else:
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            image_bytes = resp.content
            source = image_url

        if len(image_bytes) > 10 * 1024 * 1024:
            return "Error: Image too large (max 10 MB)."

        img = Image.open(_io.BytesIO(image_bytes))
        fmt = (img.format or "PNG").upper()
        mime = {"JPEG": "image/jpeg", "JPG": "image/jpeg", "PNG": "image/png",
                "GIF": "image/gif", "WEBP": "image/webp", "BMP": "image/bmp"}.get(fmt, "image/png")

        if img.width > 1500 or img.height > 1500:
            img.thumbnail((1500, 1500))
            buf = _io.BytesIO()
            if fmt in ("JPEG", "JPG"):
                img.convert("RGB").save(buf, format="JPEG")
                mime = "image/jpeg"
            else:
                img.save(buf, format="PNG")
                mime = "image/png"
            image_bytes = buf.getvalue()

        b64_data = _b64.b64encode(image_bytes).decode()
        data_url = "data:{};base64,{}".format(mime, b64_data)

        api_resp = requests.post(
            Config.KIMI_BASE_URL + "/chat/completions",
            headers={"Authorization": "Bearer " + Config.KIMI_API_KEY, "Content-Type": "application/json"},
            json={
                "model": Config.VISION_MODEL,
                "max_tokens": 500,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]}],
            },
            timeout=90,
        )

        if api_resp.status_code == 200:
            description = api_resp.json()["choices"][0]["message"]["content"]
            return "Image analysis ({}):\n\n{}".format(source, description)

        err_msg = api_resp.text[:200]
        fallback = _local_image_analysis(image_bytes, source)
        return "Vision API error ({}): {}\n\n{}".format(api_resp.status_code, err_msg, fallback)

    except Exception as e:
        return "Error analyzing image: {}".format(str(e))
