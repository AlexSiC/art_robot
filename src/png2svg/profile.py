from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigurationError


DEFAULT_PROFILE: dict[str, Any] = {
    "schema_version": 1,
    "profile_id": "raster_default_v1",
    "image": {
        "upscale_min_short_side": 900,
        "otsu": True,
        "adaptive": False,
        "adaptive_block_size": 35,
        "adaptive_offset": 5.0,
        "remove_small_objects_px": 20,
        "bridge_gap_px": 1,
    },
    "skeleton": {
        "engine": "skeleton",
        "method": "auto",
        "spur_len_px": 12.0,
        "node_merge_dist_px": 4.0,
        "collinear_deg": 4.0,
        "smooth_chaikin_iterations": 0,
    },
    "simplify": {
        "tolerance_vb": 0.8,
        "dedupe_epsilon_vb": 0.05,
        "max_length_loss_ratio": 0.03,
    },
    "paths": {
        "merge_tol_vb": 0.5,
        "min_stroke_len_vb": 2.0,
        "linesort_two_opt": True,
        "reloop": True,
    },
    "fills": {
        "enabled": False,
        "fill_area_px": 4000,
        "hatch_pitch_vb": 3.0,
        "hatch_angle_deg": 45.0,
    },
    "output": {
        "emit_ids": True,
        "stroke_width": 1.0,
        "decimal_places": 2,
        "verify_with_svg2fanuc": False,
    },
    "limits": {
        "max_input_bytes": 33_554_432,
        "max_image_pixels": 40_000_000,
        "max_strokes": 20_000,
        "max_points": 400_000,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_profile(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigurationError(
            f"Не удалось прочитать профиль {path}: {exc}", code="PROFILE_READ"
        ) from exc
    try:
        loaded = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Некорректный YAML профиля: {exc}", code="PROFILE_YAML"
        ) from exc
    if not isinstance(loaded, dict):
        raise ConfigurationError("Корень профиля должен быть mapping", code="PROFILE_TYPE")
    profile = _deep_merge(DEFAULT_PROFILE, loaded)
    validate_profile(profile)
    return profile, raw


def validate_profile(profile: dict[str, Any]) -> None:
    if profile.get("schema_version") != 1:
        raise ConfigurationError(
            "Поддерживается только schema_version: 1", code="PROFILE_SCHEMA"
        )
    engine = profile["skeleton"].get("engine")
    if engine not in {"skeleton", "autotrace"}:
        raise ConfigurationError(
            "skeleton.engine должен быть skeleton или autotrace",
            code="PROFILE_ENGINE",
        )
    method = profile["skeleton"].get("method")
    if method not in {"auto", "zhang", "lee"}:
        raise ConfigurationError(
            "skeleton.method должен быть auto, zhang или lee", code="PROFILE_METHOD"
        )
    numeric_positive = [
        ("image.upscale_min_short_side", profile["image"]["upscale_min_short_side"], True),
        ("simplify.tolerance_vb", profile["simplify"]["tolerance_vb"], False),
        ("simplify.dedupe_epsilon_vb", profile["simplify"]["dedupe_epsilon_vb"], False),
        ("paths.merge_tol_vb", profile["paths"]["merge_tol_vb"], False),
        ("paths.min_stroke_len_vb", profile["paths"]["min_stroke_len_vb"], False),
        ("limits.max_input_bytes", profile["limits"]["max_input_bytes"], True),
        ("limits.max_image_pixels", profile["limits"]["max_image_pixels"], True),
        ("limits.max_strokes", profile["limits"]["max_strokes"], True),
        ("limits.max_points", profile["limits"]["max_points"], True),
    ]
    for name, value, strict in numeric_positive:
        if not isinstance(value, (int, float)) or (value <= 0 if strict else value < 0):
            op = "> 0" if strict else ">= 0"
            raise ConfigurationError(f"{name} должно быть числом {op}", code="PROFILE_VALUE")
    decimals = profile["output"].get("decimal_places")
    if not isinstance(decimals, int) or not 0 <= decimals <= 8:
        raise ConfigurationError(
            "output.decimal_places должен быть целым от 0 до 8",
            code="PROFILE_VALUE",
        )
    if profile["fills"].get("enabled"):
        raise ConfigurationError(
            "Модуль заливок относится к Этапу 4 и в MVP не реализован",
            code="FILLS_NOT_IMPLEMENTED",
        )


def canonical_profile_bytes(profile: dict[str, Any]) -> bytes:
    return json.dumps(
        profile, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

