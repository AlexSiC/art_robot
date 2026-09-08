"""Reproducible job manifest (section 11.3)."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .version import __version__

_TRACKED_DEPS = ("svgelements", "defusedxml", "PyYAML")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dep_versions() -> dict[str, str]:
    out = {}
    for name in _TRACKED_DEPS:
        try:
            out[name] = version(name)
        except PackageNotFoundError:  # pragma: no cover
            out[name] = "unknown"
    return out


def build_manifest(
    *,
    command: str,
    input_svg: str | Path | None,
    input_sha: str | None,
    profile_sha: str,
    profile_source: str | None,
    artifacts: dict[str, str],
    job_state: str,
    production: bool,
    extra: dict | None = None,
) -> dict:
    manifest = {
        "schema": "svg2fanuc/manifest@1",
        "command": command,
        "app_version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "dependencies": _dep_versions(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "production": production,
        "job_state": job_state,
        "input": {
            "path": str(input_svg) if input_svg else None,
            "sha256": input_sha,
        },
        "profile": {
            "path": profile_source,
            "sha256": profile_sha,
        },
        "artifacts": {
            name: {"sha256": digest} for name, digest in sorted(artifacts.items())
        },
    }
    if extra:
        manifest["extra"] = extra
    return manifest


def write_json(path: str | Path, data: dict) -> str:
    text = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False)
    Path(path).write_text(text + "\n", encoding="utf-8")
    return sha256_bytes((text + "\n").encode("utf-8"))
