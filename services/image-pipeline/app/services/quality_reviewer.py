"""CLIP-based quality review for generated images.

CLIP requires downloading model weights (~600MB). If not available, we fall back
to a heuristic check (file size + format validity).
"""
from __future__ import annotations

import io
import structlog

logger = structlog.get_logger()

CLIP_THRESHOLD = 0.25
_clip_available: bool | None = None


def _check_clip_available() -> bool:
    global _clip_available
    if _clip_available is None:
        try:
            import torch  # noqa: F401
            import clip  # noqa: F401
            _clip_available = True
        except ImportError:
            _clip_available = False
            logger.info("clip_not_available", reason="torch/clip not installed, using heuristic fallback")
    return _clip_available


async def compute_clip_score(image_bytes: bytes, prompt: str) -> float | None:
    """Compute CLIP similarity score between image and prompt.

    Returns float in [0, 1], or None if CLIP is unavailable.
    """
    if not _check_clip_available():
        return None

    try:
        import torch
        import clip
        from PIL import Image

        device = "cpu"
        model, preprocess = clip.load("ViT-B/32", device=device)

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_input = preprocess(img).unsqueeze(0).to(device)
        text_input = clip.tokenize([prompt[:77]], truncate=True).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            similarity = (image_features @ text_features.T).item()

        # Normalize cosine similarity from [-1,1] to [0,1]
        return (similarity + 1.0) / 2.0

    except Exception as exc:
        logger.warning("clip_score_failed", error=str(exc))
        return None


def heuristic_quality_check(image_bytes: bytes) -> bool:
    """Minimal sanity check: non-empty, valid image header."""
    if len(image_bytes) < 1024:
        return False
    # PNG header
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    # JPEG header
    if image_bytes[:2] == b"\xff\xd8":
        return True
    # WebP header
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return True
    return False


async def review_image(image_bytes: bytes, prompt: str) -> tuple[str, float | None]:
    """Return (status, clip_score).

    status: "approved" | "needs_review" | "failed"
    """
    if not heuristic_quality_check(image_bytes):
        return "failed", None

    clip_score = await compute_clip_score(image_bytes, prompt)

    if clip_score is None:
        # No CLIP — trust heuristic pass
        return "approved", None

    if clip_score >= CLIP_THRESHOLD:
        return "approved", clip_score
    else:
        return "needs_review", clip_score
