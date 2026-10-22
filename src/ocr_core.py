"""Pure OCR input/output utilities shared by the desktop workflow."""
import io
import json
from PIL import Image, ImageOps


def validate_port(value):
    try:
        port = int(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("Port must be an integer from 1 to 65535.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("Port must be an integer from 1 to 65535.")
    return port


def image_as_png(source, max_dimension=1536):
    """Return normalized PNG bytes, safely handling alpha, EXIF and tiny images."""
    if max_dimension < 2:
        raise ValueError("max_dimension must be at least 2.")
    image = ImageOps.exif_transpose(source)
    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")
    # Pad rather than resize away the pixels of 1x1 and odd-dimension inputs.
    right = image.width % 2
    bottom = image.height % 2
    if right or bottom:
        image = ImageOps.expand(image, border=(0, 0, right, bottom), fill="white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def response_text(data, backend):
    """Validate and extract recognized text from supported backend responses."""
    if not isinstance(data, dict):
        raise ValueError("OCR backend returned a non-object response.")
    if backend == "ollama":
        result = data.get("response")
    elif backend == "vllm":
        try:
            result = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("vLLM returned an unexpected response.") from exc
    else:
        raise ValueError("Unknown OCR backend.")
    if not isinstance(result, str):
        raise ValueError("OCR backend returned no text.")
    return result


def valid_json_output(entries):
    """Serialize an array without trailing commas."""
    return json.dumps(entries, ensure_ascii=False, indent=2)
