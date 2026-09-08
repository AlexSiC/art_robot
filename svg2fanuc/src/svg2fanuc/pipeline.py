"""Orchestration for the four CLI verbs (section 5 architecture).

Output is written to a temporary sibling directory and moved into place only on
success (section 4.2): ``.LS`` / ``.TP`` never appear in a partial job.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path

from . import report as report_mod
from .emitters import emit_fanuc_ls
from .compilers import compile_ls
from .errors import CliError, ManifestMismatchError, ProfileNotQualifiedError
from .manifest import build_manifest, sha256_bytes, sha256_file, write_json
from .motion_ir import build_trajectory
from .preview import render_preview
from .profile import Profile, load_profile
from .routing import route
from .security import gate_svg
from .strokes import build_strokes
from .svg_reader import read_svg
from .transform import plan_placement
from .validate import run_validation


@dataclass
class Prepared:
    input_sha: str
    placement: object
    strokes: list
    routing: object
    trajectory: object
    validation: object
    read_stats: dict
    stroke_stats: dict
    normalized_svg: str


def _prepare(image_path: Path, profile: Profile, *, allow_distortion: bool) -> Prepared:
    gate = gate_svg(image_path, profile.security)
    read = read_svg(gate.normalized_svg)
    placement = plan_placement(
        read.src_bbox, profile.canvas, allow_distortion=allow_distortion
    )
    sbr = build_strokes(read, placement, profile)
    routing = route(sbr.strokes, profile.routing)
    traj = build_trajectory(routing.strokes, profile)
    validation = run_validation(routing.strokes, traj, profile)
    return Prepared(
        input_sha=sha256_file(image_path),
        placement=placement,
        strokes=routing.strokes,
        routing=routing,
        trajectory=traj,
        validation=validation,
        read_stats=read.stats,
        stroke_stats=sbr.stats,
        normalized_svg=gate.normalized_svg,
    )


def _profile_summary(profile: Profile) -> dict:
    return {
        "cell_id": profile.cell_id,
        "sha256": profile.sha256,
        "robot": {
            "model": profile.robot.model,
            "controller": profile.robot.controller,
            "config": profile.robot.config,
        },
        "canvas_mm": [profile.canvas.width_mm, profile.canvas.height_mm],
        "margin_mm": profile.canvas.margin_mm,
        "routing_mode": profile.routing.mode,
    }


def _metrics(prep: Prepared) -> dict:
    tr = prep.routing
    return {
        **prep.read_stats,
        **prep.stroke_stats,
        "trajectory": prep.trajectory.stats,
        "travel_length_before_mm": round(tr.travel_before_mm, 3),
        "travel_length_after_mm": round(tr.travel_after_mm, 3),
        "strokes_reversed_by_routing": tr.reversed_count,
        "bbox_mm": _bbox(prep.strokes),
    }


def _bbox(strokes: list) -> list[float]:
    xs = [x for s in strokes for x, _ in s.points]
    ys = [y for s in strokes for _, y in s.points]
    return [round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]


def _fresh_workdir(out_dir: Path, force: bool) -> tuple[Path, Path]:
    out_dir = out_dir.resolve()
    if out_dir.exists():
        if not force:
            raise CliError(f"output directory already exists: {out_dir} (use --force)")
        shutil.rmtree(out_dir)
    tmp = out_dir.with_name(out_dir.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    return out_dir, tmp


def _commit(tmp: Path, final: Path) -> None:
    os.replace(tmp, final)


# --------------------------------------------------------------------------- #
def run_inspect(
    image_path: Path, profile: Profile, out_dir: Path, *, allow_distortion: bool,
    force: bool,
) -> dict:
    final, tmp = _fresh_workdir(out_dir, force)
    try:
        prep = _prepare(image_path, profile, allow_distortion=allow_distortion)
        job_id = final.name
        artifacts: dict[str, str] = {}

        artifacts["normalized.svg"] = _write_text(
            tmp / "normalized.svg", prep.normalized_svg
        )
        preview = render_preview(
            prep.strokes, profile, prep.placement, job_id=job_id,
            travel_start_xy=profile.routing.travel_start_xy_mm,
        )
        artifacts["preview.svg"] = _write_text(tmp / "preview.svg", preview)
        artifacts["trajectory.json"] = _write_text(
            tmp / "trajectory.json", _json(prep.trajectory.to_json())
        )
        rep = report_mod.build_report(
            command="inspect", job_id=job_id,
            profile_summary=_profile_summary(profile),
            placement=prep.placement.describe(), metrics=_metrics(prep),
            validation=prep.validation.to_json(), emit=None, maketp=None,
            job_state="INSPECTED", warnings=prep.validation.warnings,
        )
        artifacts["report.json"] = _write_text(tmp / "report.json", _json(rep))

        manifest = build_manifest(
            command="inspect", input_svg=image_path, input_sha=prep.input_sha,
            profile_sha=profile.sha256, profile_source=profile.source_path,
            artifacts=artifacts, job_state="INSPECTED", production=False,
        )
        _write_text(tmp / "manifest.json", _json(manifest))
        _commit(tmp, final)
        return rep
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def run_generate(
    image_path: Path, profile: Profile, out_dir: Path, *,
    production: bool, allow_distortion: bool, job_number: int,
    when: _date | None, force: bool,
) -> dict:
    if production:
        profile.ensure_production_ready()
    elif profile.robot.config == "TBD":
        raise ProfileNotQualifiedError(
            "robot.config is TBD; set a verified CONFIG string before `generate`"
        )

    final, tmp = _fresh_workdir(out_dir, force)
    try:
        prep = _prepare(image_path, profile, allow_distortion=allow_distortion)
        job_id = final.name
        emit = emit_fanuc_ls(
            prep.trajectory, profile, job_number=job_number, when=when
        )
        artifacts: dict[str, str] = {}

        for prog in emit.all_programs:
            fname = prog.name + ".LS"
            artifacts[fname] = _write_text(tmp / fname, prog.text, newline="\r\n")

        artifacts["normalized.svg"] = _write_text(
            tmp / "normalized.svg", prep.normalized_svg
        )
        preview = render_preview(
            prep.strokes, profile, prep.placement, job_id=job_id,
            travel_start_xy=profile.routing.travel_start_xy_mm,
        )
        artifacts["preview.svg"] = _write_text(tmp / "preview.svg", preview)
        artifacts["trajectory.json"] = _write_text(
            tmp / "trajectory.json", _json(prep.trajectory.to_json())
        )

        maketp_json = None
        job_state = report_mod.STATE_GENERATED_UNCOMPILED
        if profile.compile.enabled:
            ls_paths = [tmp / (p.name + ".LS") for p in emit.all_programs]
            outcome = compile_ls(ls_paths, tmp, profile.compile)
            maketp_json = outcome.to_json()
            for tp in outcome.tp_files:
                tpp = Path(tp)
                artifacts[tpp.name] = sha256_file(tpp)
            job_state = report_mod.STATE_COMPILED_UNVERIFIED

        rep = report_mod.build_report(
            command="generate", job_id=job_id,
            profile_summary=_profile_summary(profile),
            placement=prep.placement.describe(), metrics=_metrics(prep),
            validation=prep.validation.to_json(), emit=emit.to_json(),
            maketp=maketp_json, job_state=job_state,
            warnings=prep.validation.warnings,
        )
        artifacts["report.json"] = _write_text(tmp / "report.json", _json(rep))

        manifest = build_manifest(
            command="generate", input_svg=image_path, input_sha=prep.input_sha,
            profile_sha=profile.sha256, profile_source=profile.source_path,
            artifacts=artifacts, job_state=job_state, production=production,
            extra={"programs": emit.to_json(), "job_number": job_number},
        )
        _write_text(tmp / "manifest.json", _json(manifest))
        _commit(tmp, final)
        return rep
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def run_compile(manifest_path: Path) -> dict:
    job_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile_path = (manifest.get("profile") or {}).get("path")
    if not profile_path or not Path(profile_path).exists():
        raise CliError("cannot compile: profile path from manifest is unavailable")
    profile = load_profile(profile_path)
    if profile.sha256 != manifest["profile"]["sha256"]:
        raise ManifestMismatchError("profile has changed since the job was generated")
    if not profile.compile.enabled:
        raise CliError("profile.compile.enabled is false")

    ls_files = sorted(job_dir.glob("*.LS"))
    if not ls_files:
        raise CliError(f"no .LS files found in {job_dir}")
    outcome = compile_ls(ls_files, job_dir, profile.compile)
    result = {
        "schema": "svg2fanuc/compile@1",
        "job_dir": str(job_dir),
        "maketp": outcome.to_json(),
        "job_state": report_mod.STATE_COMPILED_UNVERIFIED,
    }
    write_json(job_dir / "compile_result.json", result)
    return result


def run_verify(manifest_path: Path) -> dict:
    job_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches: list[str] = []
    for name, meta in manifest.get("artifacts", {}).items():
        f = job_dir / name
        if not f.exists():
            mismatches.append(f"{name}: missing")
            continue
        actual = sha256_file(f)
        if actual != meta.get("sha256"):
            mismatches.append(f"{name}: sha256 changed")
    src = (manifest.get("input") or {}).get("path")
    src_note = None
    if src and Path(src).exists():
        if sha256_file(src) != manifest["input"]["sha256"]:
            src_note = "input SVG has changed since generation"
    if mismatches:
        raise ManifestMismatchError("; ".join(mismatches))
    return {
        "schema": "svg2fanuc/verify@1",
        "job_dir": str(job_dir),
        "artifacts_ok": True,
        "input_note": src_note,
    }


# --------------------------------------------------------------------------- #
def _json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _write_text(path: Path, text: str, *, newline: str = "\n") -> str:
    data = text.replace("\r\n", "\n")
    if newline != "\n":
        data = data.replace("\n", newline)
    b = data.encode("utf-8")
    path.write_bytes(b)
    return sha256_bytes(b)
