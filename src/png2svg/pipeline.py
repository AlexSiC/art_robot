from __future__ import annotations

import copy
import hashlib
import io
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .emit import (
    clean_svg_bytes,
    json_bytes,
    manifest_bytes,
    preview_svg_bytes,
    quantize_and_validate,
    validate_clean_svg,
)
from .errors import (
    BudgetError,
    ConfigurationError,
    EmptyImageError,
    IntegrationError,
    ValidationError,
    VectorizationError,
)
from .geometry import (
    bbox,
    filter_short_strokes,
    merge_strokes,
    simplify_strokes,
    sort_strokes,
    travel_length,
)
from .graph import vectorize_skeleton
from .image_processing import load_grayscale, make_mask
from .models import ProcessingStats, Stroke
from .profile import canonical_profile_bytes, load_profile, validate_profile
from .skeleton import skeletonize_mask


@dataclass(slots=True)
class GenerateOptions:
    image: Path
    profile: Path
    out: Path
    engine: str | None = None
    simplify_vb: float | None = None
    canvas_hint_mm: tuple[float, float] | None = None
    simplify_mm: float | None = None
    dry_run: bool = False
    strict: bool = False
    debug: bool = False
    adaptive: bool | None = None
    bridge_gap_px: int | None = None
    smooth_iterations: int | None = None
    fills: str | None = None
    hatch_pitch: float | None = None
    hatch_angle: float | None = None
    verify_with_svg2fanuc: bool = False
    svg2fanuc_profile: Path | None = None


@dataclass(slots=True)
class GenerateResult:
    out: Path
    artifacts: list[str]
    stats: dict[str, Any]


def _apply_options(profile: dict[str, Any], options: GenerateOptions) -> dict[str, Any]:
    effective = copy.deepcopy(profile)
    if options.engine is not None:
        effective["skeleton"]["engine"] = options.engine
    if options.simplify_vb is not None:
        effective["simplify"]["tolerance_vb"] = options.simplify_vb
    if options.adaptive is not None:
        effective["image"]["adaptive"] = options.adaptive
    if options.bridge_gap_px is not None:
        effective["image"]["bridge_gap_px"] = options.bridge_gap_px
    if options.smooth_iterations is not None:
        effective["skeleton"]["smooth_chaikin_iterations"] = options.smooth_iterations
    if options.fills is not None:
        effective["fills"]["enabled"] = options.fills != "off"
    if options.hatch_pitch is not None:
        effective["fills"]["hatch_pitch_vb"] = options.hatch_pitch
    if options.hatch_angle is not None:
        effective["fills"]["hatch_angle_deg"] = options.hatch_angle
    if options.verify_with_svg2fanuc:
        effective["output"]["verify_with_svg2fanuc"] = True
    validate_profile(effective)
    if effective["skeleton"]["engine"] == "autotrace":
        if shutil.which("autotrace") is None:
            raise ConfigurationError(
                "autotrace не установлен; используйте --engine skeleton",
                code="AUTOTRACE_NOT_FOUND",
            )
        raise ConfigurationError(
            "Backend autotrace зарезервирован, но не реализован в MVP; используйте skeleton",
            code="AUTOTRACE_NOT_IMPLEMENTED",
        )
    return effective


def _validate_output_target(out: Path) -> None:
    if out.exists():
        if not out.is_dir():
            raise ConfigurationError(
                f"--out указывает не на директорию: {out}", code="OUTPUT_NOT_DIRECTORY"
            )
        if any(out.iterdir()):
            raise ConfigurationError(
                f"Каталог --out должен отсутствовать или быть пустым: {out}",
                code="OUTPUT_NOT_EMPTY",
            )
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(
            f"Не удалось создать родительский каталог: {exc}", code="OUTPUT_CREATE"
        ) from exc


def _skeleton_png_bytes(skeleton: np.ndarray) -> bytes:
    pixels = np.where(skeleton, 0, 255).astype(np.uint8)
    image = Image.fromarray(pixels, mode="L")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def _compute_final_stats(
    stats: ProcessingStats, strokes: list[Stroke], width: int, height: int
) -> None:
    stats.strokes = len(strokes)
    stats.points = sum(len(stroke.points) for stroke in strokes)
    stats.open_strokes = sum(not stroke.closed for stroke in strokes)
    stats.closed_strokes = sum(stroke.closed for stroke in strokes)
    stats.total_length_vb = sum(stroke.length for stroke in strokes)
    stats.bbox_vb = bbox(strokes)
    stats.viewbox = [0.0, 0.0, float(width), float(height)]


def _verify_external(
    clean_path: Path, profile_path: Path | None, verify_out: Path
) -> None:
    executable = shutil.which("svg2fanuc")
    if executable is None:
        raise IntegrationError(
            "--verify-with-svg2fanuc задан, но svg2fanuc не найден в PATH",
            code="SVG2FANUC_NOT_FOUND",
        )
    if profile_path is None:
        raise ConfigurationError(
            "Для интеграционной проверки нужен --svg2fanuc-profile",
            code="SVG2FANUC_PROFILE_REQUIRED",
        )
    completed = subprocess.run(
        [
            executable,
            "inspect",
            str(clean_path),
            "--profile",
            str(profile_path),
            "--out",
            str(verify_out),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout).strip()[-2000:]
        raise IntegrationError(
            f"svg2fanuc inspect завершился с кодом {completed.returncode}: {details}",
            code="SVG2FANUC_REJECTED",
        )


def _publish(out: Path, files: dict[str, bytes]) -> list[str]:
    stage = Path(tempfile.mkdtemp(prefix=".png2svg-", dir=out.parent))
    try:
        for name, data in files.items():
            (stage / name).write_bytes(data)
        out.mkdir(parents=True, exist_ok=True)
        for name in sorted(files):
            os.replace(stage / name, out / name)
        return sorted(files)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def generate(options: GenerateOptions) -> GenerateResult:
    _validate_output_target(options.out)
    if options.simplify_vb is not None and options.simplify_mm is not None:
        raise ConfigurationError(
            "--simplify и --simplify-mm взаимоисключающие", code="SIMPLIFY_CONFLICT"
        )
    if options.simplify_mm is not None and options.canvas_hint_mm is None:
        raise ConfigurationError(
            "--simplify-mm требует --canvas-hint WxH", code="CANVAS_HINT_REQUIRED"
        )
    if options.image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
        raise ConfigurationError(
            "Поддерживаются только PNG, JPG/JPEG и BMP", code="IMAGE_EXTENSION"
        )

    profile, profile_source = load_profile(options.profile)
    profile = _apply_options(profile, options)
    stats = ProcessingStats()
    gray = load_grayscale(options.image, profile, stats)
    height, width = gray.shape

    if options.simplify_mm is not None:
        canvas_w, canvas_h = options.canvas_hint_mm or (0.0, 0.0)
        if canvas_w <= 0 or canvas_h <= 0 or options.simplify_mm < 0:
            raise ConfigurationError(
                "Размеры canvas и simplify-mm должны быть положительными",
                code="CANVAS_HINT_VALUE",
            )
        profile["simplify"]["tolerance_vb"] = options.simplify_mm * min(
            width / canvas_w, height / canvas_h
        )

    mask = make_mask(gray, profile, stats)
    skeleton = skeletonize_mask(mask, profile, stats)
    strokes = vectorize_skeleton(
        skeleton,
        spur_len_px=float(profile["skeleton"]["spur_len_px"]),
        smooth_iterations=int(profile["skeleton"]["smooth_chaikin_iterations"]),
        stats=stats,
    )
    stats.points_before_simplify = sum(len(stroke.points) for stroke in strokes)

    tolerance = float(profile["simplify"]["tolerance_vb"])
    epsilon = float(profile["simplify"]["dedupe_epsilon_vb"])
    max_points = int(profile["limits"]["max_points"])
    simplified: list[Stroke] = []
    removed = 0
    loss_ratio = 0.0
    max_deviation = 0.0
    for attempt in range(9):
        simplified, removed, loss_ratio, max_deviation = simplify_strokes(
            strokes, tolerance, epsilon
        )
        if sum(len(stroke.points) for stroke in simplified) <= max_points:
            break
        tolerance = max(0.1, tolerance * 1.5)
        if attempt == 0:
            stats.warn(
                "SIMPLIFY_TOLERANCE_RAISED",
                "Допуск упрощения автоматически увеличен для бюджета точек",
            )
    else:
        raise BudgetError(
            f"Не удалось уложить траекторию в {max_points} точек",
            code="POINT_BUDGET",
        )
    if not simplified:
        raise EmptyImageError(
            "После упрощения не осталось штрихов", code="EMPTY_AFTER_SIMPLIFY"
        )
    stats.points_removed_by_simplify = removed
    stats.simplify_tolerance_vb = tolerance
    stats.length_loss_ratio = loss_ratio
    stats.max_simplify_deviation_vb = max_deviation
    if loss_ratio > float(profile["simplify"]["max_length_loss_ratio"]):
        stats.warn(
            "SIMPLIFY_LENGTH_LOSS",
            f"Потеря длины {loss_ratio:.3%} превышает профильный предел",
        )

    merged, merged_count = merge_strokes(
        simplified, float(profile["paths"]["merge_tol_vb"])
    )
    stats.strokes_merged = merged_count
    filtered, dropped = filter_short_strokes(
        merged, float(profile["paths"]["min_stroke_len_vb"])
    )
    stats.dropped_short_strokes = dropped
    if not filtered:
        raise EmptyImageError(
            "После фильтра минимальной длины не осталось штрихов",
            code="EMPTY_AFTER_FILTER",
        )
    stats.travel_length_before = travel_length(filtered)
    ordered = sort_strokes(
        filtered,
        reloop=bool(profile["paths"].get("reloop", True)),
        two_opt=bool(profile["paths"].get("linesort_two_opt", True)),
    )
    stats.travel_length_after = travel_length(ordered)

    decimals = int(profile["output"]["decimal_places"])
    final_strokes, rounded_drops = quantize_and_validate(
        ordered, width, height, decimals, epsilon
    )
    stats.dropped_short_strokes += rounded_drops
    max_strokes = int(profile["limits"]["max_strokes"])
    point_count = sum(len(stroke.points) for stroke in final_strokes)
    if len(final_strokes) > max_strokes or point_count > max_points:
        raise BudgetError(
            f"Результат превышает лимиты: strokes={len(final_strokes)}, points={point_count}",
            code="OUTPUT_BUDGET",
        )
    _compute_final_stats(stats, final_strokes, width, height)

    clean_data = clean_svg_bytes(final_strokes, width, height, profile)
    validate_clean_svg(clean_data)
    preview_data = preview_svg_bytes(final_strokes, width, height, profile)

    if options.strict and stats.warnings:
        codes = ", ".join(item["code"] for item in stats.warnings)
        raise ValidationError(
            f"--strict: обнаружены warnings: {codes}", code="STRICT_WARNING"
        )

    files: dict[str, bytes] = {
        "preview.svg": preview_data,
        "stats.json": json_bytes(stats.as_dict()),
    }
    if not options.dry_run:
        files["clean.svg"] = clean_data
    if options.debug:
        files["skeleton.png"] = _skeleton_png_bytes(skeleton)

    effective_profile = canonical_profile_bytes(profile)
    files["manifest.json"] = manifest_bytes(
        input_name=options.image.name,
        input_hash=hashlib.sha256(options.image.read_bytes()).hexdigest(),
        source_profile_hash=hashlib.sha256(profile_source).hexdigest(),
        effective_profile_hash=hashlib.sha256(effective_profile).hexdigest(),
        artifacts=files,
        dry_run=options.dry_run,
    )

    if profile["output"].get("verify_with_svg2fanuc"):
        if options.dry_run:
            raise ConfigurationError(
                "Интеграционная проверка несовместима с --dry-run",
                code="VERIFY_DRY_RUN",
            )
        stage = Path(tempfile.mkdtemp(prefix=".png2svg-verify-", dir=options.out.parent))
        try:
            clean_path = stage / "clean.svg"
            clean_path.write_bytes(clean_data)
            _verify_external(clean_path, options.svg2fanuc_profile, stage / "inspect")
        finally:
            shutil.rmtree(stage, ignore_errors=True)

    artifacts = _publish(options.out, files)
    return GenerateResult(options.out, artifacts, stats.as_dict())
