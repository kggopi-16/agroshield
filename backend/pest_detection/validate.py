from PIL import Image
import io

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_SIZE_MB = 10
MIN_DIMENSION = 64  # pixels

def validate_image(file_bytes: bytes, content_type: str) -> dict:
    # Check file type
    if content_type not in ALLOWED_TYPES:
        return {"valid": False, "error": "Only JPG, PNG, WEBP allowed"}

    # Check file size
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        return {"valid": False, "error": f"File too large ({size_mb:.1f}MB). Max 10MB"}

    # Try to open as image
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
    except Exception:
        return {"valid": False, "error": "Corrupted or invalid image file"}

    # Check dimensions
    img = Image.open(io.BytesIO(file_bytes))
    w, h = img.size
    if w < MIN_DIMENSION or h < MIN_DIMENSION:
        return {"valid": False, "error": f"Image too small ({w}x{h}px). Min 64x64"}

    # Check if it looks like a crop/plant image (basic RGB check)
    img_rgb = img.convert("RGB")
    r, g, b = 0, 0, 0
    pixels = list(img_rgb.getdata())
    for pr, pg, pb in pixels[:500]:  # sample 500 pixels
        r += pr; g += pg; b += pb
    count = len(pixels[:500])
    avg_g = g / count
    avg_r = r / count
    # If green channel is very low — likely not a crop image
    if avg_g < 30 and avg_r < 30:
        return {"valid": False, "error": "Image too dark. Upload a clear crop photo"}

    return {"valid": True, "error": None}