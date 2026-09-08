from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
from pathlib import Path

from .errors import Png2SvgError
from .pipeline import GenerateOptions, generate


def _canvas_hint(value: str) -> tuple[float, float]:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError("ожидается WxH, например 800x600")
    width, height = float(match.group(1)), float(match.group(2))
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("размеры должны быть положительными")
    return width, height


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="png2svg", description="Преобразование растровых штрихов в centerline SVG"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    command = subparsers.add_parser("generate", help="создать clean.svg и отчет")
    command.add_argument("image", type=Path)
    command.add_argument("--profile", type=Path, required=True)
    command.add_argument("--out", type=Path, required=True)
    command.add_argument("--engine", choices=("skeleton", "autotrace"))
    command.add_argument("--simplify", dest="simplify_vb", type=float)
    command.add_argument("--canvas-hint", type=_canvas_hint)
    command.add_argument("--simplify-mm", type=float)
    command.add_argument("--dry-run", action="store_true")
    command.add_argument("--strict", action="store_true")
    command.add_argument("--debug", action="store_true")
    command.add_argument("--adaptive", action="store_true", default=None)
    command.add_argument("--bridge-gap", dest="bridge_gap_px", type=int)
    command.add_argument("--smooth", dest="smooth_iterations", type=int)
    command.add_argument("--fills", choices=("off", "hatch"))
    command.add_argument("--hatch-pitch", type=float)
    command.add_argument("--hatch-angle", type=float)
    command.add_argument("--verify-with-svg2fanuc", action="store_true")
    command.add_argument("--svg2fanuc-profile", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "generate":
        parser.error("Неизвестная команда")
    try:
        result = generate(
            GenerateOptions(
                image=args.image,
                profile=args.profile,
                out=args.out,
                engine=args.engine,
                simplify_vb=args.simplify_vb,
                canvas_hint_mm=args.canvas_hint,
                simplify_mm=args.simplify_mm,
                dry_run=args.dry_run,
                strict=args.strict,
                debug=args.debug,
                adaptive=args.adaptive,
                bridge_gap_px=args.bridge_gap_px,
                smooth_iterations=args.smooth_iterations,
                fills=args.fills,
                hatch_pitch=args.hatch_pitch,
                hatch_angle=args.hatch_angle,
                verify_with_svg2fanuc=args.verify_with_svg2fanuc,
                svg2fanuc_profile=args.svg2fanuc_profile,
            )
        )
    except Png2SvgError as exc:
        print(
            json.dumps(
                {"status": "error", "code": exc.code, "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - final CLI boundary
        if os.environ.get("PNG2SVG_DEBUG"):
            traceback.print_exc()
        print(
            json.dumps(
                {"status": "error", "code": "INTERNAL_ERROR", "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 9
    print(
        json.dumps(
            {
                "status": "ok",
                "out": str(result.out),
                "artifacts": result.artifacts,
                "strokes": result.stats["strokes"],
                "points": result.stats["points"],
                "warnings": result.stats["warnings"],
            },
            ensure_ascii=False,
        )
    )
    return 0

