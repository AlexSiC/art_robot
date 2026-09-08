"""Command-line interface (section 4.1).

    svg2fanuc inspect  drawing.svg --profile cell.yaml --out build/job_001
    svg2fanuc generate drawing.svg --profile cell.yaml --out build/job_001
    svg2fanuc compile  build/job_001/manifest.json
    svg2fanuc verify   build/job_001/manifest.json

Physical execution is impossible from this CLI by design.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date as _date
from pathlib import Path

from . import pipeline
from .errors import CliError, ExitCode, Svg2FanucError
from .profile import load_profile
from .version import __version__

_log = logging.getLogger("svg2fanuc")


def _setup_logging(developer: bool) -> None:
    level = logging.DEBUG if developer else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler])


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key in ("job_id", "code", "input_sha"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="svg2fanuc", description=__doc__)
    p.add_argument("--version", action="version", version=f"svg2fanuc {__version__}")
    p.add_argument("--developer", action="store_true", help="verbose logs + tracebacks")
    sub = p.add_subparsers(dest="command", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("image", type=Path, help="cleaned SVG (profile SVG-DRAW-1)")
        sp.add_argument("--profile", type=Path, required=True)
        sp.add_argument("--out", type=Path, required=True, help="job output directory")
        sp.add_argument("--force", action="store_true", help="overwrite existing --out")
        sp.add_argument(
            "--allow-distortion", action="store_true",
            help="permit canvas.fit=stretch (never for production)",
        )

    sp_i = sub.add_parser("inspect", help="validate + preview + report, no FANUC code")
    add_common(sp_i)

    sp_g = sub.add_parser("generate", help="produce trajectory, preview, report and LS")
    add_common(sp_g)
    sp_g.add_argument("--production", action="store_true",
                      help="require a fully qualified profile (no TBD)")
    sp_g.add_argument("--job-number", type=int, default=1)
    sp_g.add_argument("--date", type=_parse_date, default=None,
                      help="YYYY-MM-DD stamped into the LS /ATTR header")

    sp_c = sub.add_parser("compile", help="compile existing LS to TP with MakeTP")
    sp_c.add_argument("manifest", type=Path)

    sp_v = sub.add_parser("verify", help="check a job's artifact checksums")
    sp_v.add_argument("manifest", type=Path)

    return p


def _parse_date(s: str) -> _date:
    try:
        return _date.fromisoformat(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {s!r}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.developer)

    try:
        result = _dispatch(args)
    except Svg2FanucError as exc:
        _log.error(exc.message, extra={"code": exc.code})
        _emit_result({"ok": False, "error": exc.as_dict()})
        if args.developer:
            raise
        return int(exc.exit_code)
    except KeyboardInterrupt:  # pragma: no cover
        return int(ExitCode.INTERNAL)
    except Exception as exc:  # noqa: BLE001
        _log.error(f"internal error: {exc}", extra={"code": "INTERNAL"})
        if args.developer:
            raise
        _emit_result({"ok": False, "error": {"code": "INTERNAL", "message": str(exc)}})
        return int(ExitCode.INTERNAL)

    _emit_result({"ok": True, "result": result})
    return int(ExitCode.OK)


def _dispatch(args: argparse.Namespace) -> dict:
    if args.command in ("inspect", "generate"):
        if not args.image.exists():
            raise CliError(f"input SVG not found: {args.image}")
        profile = load_profile(args.profile)
        if args.command == "inspect":
            return pipeline.run_inspect(
                args.image, profile, args.out,
                allow_distortion=args.allow_distortion, force=args.force,
            )
        return pipeline.run_generate(
            args.image, profile, args.out,
            production=args.production, allow_distortion=args.allow_distortion,
            job_number=args.job_number, when=args.date, force=args.force,
        )
    if args.command == "compile":
        if not args.manifest.exists():
            raise CliError(f"manifest not found: {args.manifest}")
        return pipeline.run_compile(args.manifest)
    if args.command == "verify":
        if not args.manifest.exists():
            raise CliError(f"manifest not found: {args.manifest}")
        return pipeline.run_verify(args.manifest)
    raise CliError(f"unknown command {args.command!r}")  # pragma: no cover


def _emit_result(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
