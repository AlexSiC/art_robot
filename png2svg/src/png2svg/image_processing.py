from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError

from .errors import BudgetError, EmptyImageError, ImageReadError
from .models import ProcessingStats


def load_grayscale(
    path: Path, profile: dict[str, Any], stats: ProcessingStats
) -> np.ndarray:
    limit = int(profile["limits"]["max_input_bytes"])
    try:
        size_bytes = path.stat().st_size
    except OSError as exc:
        raise ImageReadError(f"Не удалось прочитать {path}: {exc}", code="IMAGE_READ") from exc
    if size_bytes > limit:
        raise BudgetError(
            f"Файл занимает {size_bytes} байт, лимит {limit}", code="INPUT_BYTES_LIMIT"
        )
    try:
        with Image.open(path) as source:
            source.load()
            width, height = source.size
            if width <= 0 or height <= 0:
                raise ImageReadError("Нулевой размер изображения", code="IMAGE_SIZE")
            max_pixels = int(profile["limits"]["max_image_pixels"])
            if width * height > max_pixels:
                raise BudgetError(
                    f"Изображение содержит {width * height} пикселей, лимит {max_pixels}",
                    code="IMAGE_PIXELS_LIMIT",
                )
            stats.source_image_size = [width, height]
            original_mode = source.mode
            if original_mode not in {"1", "L", "I", "F"}:
                stats.warn(
                    "COLOR_INPUT",
                    f"Входной режим {original_mode} преобразован в grayscale",
                )
            if "A" in source.getbands() or "transparency" in source.info:
                rgba = source.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                background.alpha_composite(rgba)
                gray_image = background.convert("L")
            else:
                gray_image = source.convert("L")

            min_short = int(profile["image"]["upscale_min_short_side"])
            short_side = min(width, height)
            factor = max(1.0, min_short / short_side) if min_short else 1.0
            if factor > 1.0:
                new_size = (
                    max(1, round(width * factor)),
                    max(1, round(height * factor)),
                )
                if new_size[0] * new_size[1] > max_pixels:
                    raise BudgetError(
                        "Апскейл превышает limits.max_image_pixels",
                        code="UPSCALE_PIXELS_LIMIT",
                    )
                gray_image = gray_image.resize(new_size, Image.Resampling.BICUBIC)
            stats.upscale_factor = factor
            stats.working_image_size = list(gray_image.size)
            return np.asarray(gray_image, dtype=np.uint8)
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ImageReadError(
            f"Не удалось декодировать изображение: {exc}", code="IMAGE_DECODE"
        ) from exc


def otsu_threshold(gray: np.ndarray) -> int:
    histogram = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    total = gray.size
    sum_total = np.dot(np.arange(256, dtype=np.float64), histogram)
    weight_background = 0.0
    sum_background = 0.0
    best_variance = -1.0
    best_threshold = 127
    for threshold in range(256):
        weight_background += histogram[threshold]
        if weight_background == 0:
            continue
        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break
        sum_background += threshold * histogram[threshold]
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        variance = weight_background * weight_foreground * (
            mean_background - mean_foreground
        ) ** 2
        if variance > best_variance:
            best_variance = variance
            best_threshold = threshold
    return best_threshold


def adaptive_mask(gray: np.ndarray, block_size: int, offset: float) -> np.ndarray:
    block_size = max(3, int(block_size) | 1)
    radius = block_size // 2
    padded = np.pad(gray.astype(np.float64), radius, mode="reflect")
    integral = np.pad(padded, ((1, 0), (1, 0)), mode="constant").cumsum(0).cumsum(1)
    height, width = gray.shape
    y0 = np.arange(height)
    y1 = y0 + block_size
    x0 = np.arange(width)
    x1 = x0 + block_size
    sums = (
        integral[y1[:, None], x1[None, :]]
        - integral[y0[:, None], x1[None, :]]
        - integral[y1[:, None], x0[None, :]]
        + integral[y0[:, None], x0[None, :]]
    )
    means = sums / float(block_size * block_size)
    return gray.astype(np.float64) < (means - float(offset))


def _shift(mask: np.ndarray, dy: int, dx: int) -> np.ndarray:
    result = np.zeros_like(mask, dtype=bool)
    y_src_start = max(0, -dy)
    y_src_end = mask.shape[0] - max(0, dy)
    x_src_start = max(0, -dx)
    x_src_end = mask.shape[1] - max(0, dx)
    y_dst_start = max(0, dy)
    y_dst_end = mask.shape[0] - max(0, -dy)
    x_dst_start = max(0, dx)
    x_dst_end = mask.shape[1] - max(0, -dx)
    result[y_dst_start:y_dst_end, x_dst_start:x_dst_end] = mask[
        y_src_start:y_src_end, x_src_start:x_src_end
    ]
    return result


def binary_dilation(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask.copy()
    result = np.zeros_like(mask, dtype=bool)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                result |= _shift(mask, dy, dx)
    return result


def binary_erosion(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask.copy()
    result = np.ones_like(mask, dtype=bool)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                result &= _shift(mask, dy, dx)
    return result


def binary_closing(mask: np.ndarray, radius: int) -> np.ndarray:
    return binary_erosion(binary_dilation(mask, radius), radius)


def remove_small_components(mask: np.ndarray, min_size: int) -> tuple[np.ndarray, int]:
    if min_size <= 1:
        return mask.copy(), count_components(mask)
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    output = mask.copy()
    components = 0
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys.tolist(), xs.tolist()):
        if visited[sy, sx]:
            continue
        components += 1
        queue: deque[tuple[int, int]] = deque([(sy, sx)])
        visited[sy, sx] = True
        pixels: list[tuple[int, int]] = []
        while queue:
            y, x = queue.popleft()
            pixels.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and mask[ny, nx]
                        and not visited[ny, nx]
                    ):
                        visited[ny, nx] = True
                        queue.append((ny, nx))
        if len(pixels) < min_size:
            for y, x in pixels:
                output[y, x] = False
    return output, components


def count_components(mask: np.ndarray) -> int:
    _, count = remove_small_components(mask, 2)
    return count


def make_mask(
    gray: np.ndarray, profile: dict[str, Any], stats: ProcessingStats
) -> np.ndarray:
    cfg = profile["image"]
    if cfg.get("adaptive"):
        mask = adaptive_mask(
            gray, int(cfg.get("adaptive_block_size", 35)), float(cfg.get("adaptive_offset", 5.0))
        )
        stats.threshold = None
    else:
        threshold = otsu_threshold(gray)
        stats.threshold = float(threshold)
        mask = gray <= threshold
    radius = int(cfg.get("bridge_gap_px", 0))
    if radius:
        mask = binary_closing(mask, radius)
    mask, components = remove_small_components(
        mask, int(cfg.get("remove_small_objects_px", 0))
    )
    stats.connected_components = components
    stats.foreground_pixels = int(mask.sum())
    if not mask.any():
        raise EmptyImageError(
            "После бинаризации и фильтрации не осталось штрихов",
            code="EMPTY_AFTER_THRESHOLD",
        )
    if components > 100:
        stats.warn(
            "MANY_COMPONENTS",
            f"После бинаризации найдено много компонент: {components}",
        )
    foreground_ratio = stats.foreground_pixels / mask.size
    if foreground_ratio > 0.5:
        stats.warn(
            "DENSE_FOREGROUND",
            f"Штрихи занимают {foreground_ratio:.1%} кадра; проверьте полярность и заливки",
        )
    return mask
