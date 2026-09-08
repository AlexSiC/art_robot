from __future__ import annotations

from typing import Any

import numpy as np

from .errors import ConfigurationError, VectorizationError
from .models import ProcessingStats


def _neighbors(mask: np.ndarray) -> tuple[np.ndarray, ...]:
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    return (
        padded[:-2, 1:-1],   # p2 north
        padded[:-2, 2:],     # p3 north-east
        padded[1:-1, 2:],    # p4 east
        padded[2:, 2:],      # p5 south-east
        padded[2:, 1:-1],    # p6 south
        padded[2:, :-2],     # p7 south-west
        padded[1:-1, :-2],   # p8 west
        padded[:-2, :-2],    # p9 north-west
    )


def zhang_suen(mask: np.ndarray, *, max_iterations: int = 10000) -> np.ndarray:
    """Vectorized Zhang-Suen thinning for a boolean foreground mask."""
    image = mask.astype(bool, copy=True)
    for _ in range(max_iterations):
        changed = False
        for phase in (0, 1):
            n = _neighbors(image)
            count = sum(item.astype(np.uint8) for item in n)
            transitions = sum(
                (~n[i] & n[(i + 1) % 8]).astype(np.uint8) for i in range(8)
            )
            common = image & (count >= 2) & (count <= 6) & (transitions == 1)
            if phase == 0:
                marker = common & ~(n[0] & n[2] & n[4]) & ~(n[2] & n[4] & n[6])
            else:
                marker = common & ~(n[0] & n[2] & n[6]) & ~(n[0] & n[4] & n[6])
            if marker.any():
                image[marker] = False
                changed = True
        if not changed:
            return image
    raise VectorizationError(
        "Скелетизация не сошлась до лимита итераций",
        code="SKELETON_ITERATION_LIMIT",
    )


def skeletonize_mask(
    mask: np.ndarray, profile: dict[str, Any], stats: ProcessingStats
) -> np.ndarray:
    method = str(profile["skeleton"].get("method", "auto"))
    try:
        from skimage.morphology import skeletonize as sk_skeletonize  # type: ignore
    except ImportError:
        sk_skeletonize = None

    if method == "lee" and sk_skeletonize is None:
        raise ConfigurationError(
            "Метод lee требует optional dependency scikit-image",
            code="SKIMAGE_REQUIRED",
        )
    if sk_skeletonize is not None:
        chosen = "lee" if method == "lee" else None
        result = sk_skeletonize(mask, method=chosen)
    else:
        result = zhang_suen(mask)
    result = np.asarray(result, dtype=bool)
    stats.skeleton_pixels = int(result.sum())
    if not result.any():
        raise VectorizationError("Скелет пуст", code="EMPTY_SKELETON")
    return result
