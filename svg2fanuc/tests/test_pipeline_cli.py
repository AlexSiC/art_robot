from __future__ import annotations

import json
from datetime import date

import pytest

from svg2fanuc import pipeline
from svg2fanuc.cli import main
from svg2fanuc.errors import ManifestMismatchError, ProfileNotQualifiedError

from .conftest import data


def test_generate_full_job(tmp_path, profile):
    out = tmp_path / "job_001"
    rep = pipeline.run_generate(
        data("lines.svg"), profile, out,
        production=False, allow_distortion=False, job_number=1,
        when=date(2026, 9, 8), force=False,
    )
    assert rep["job_state"] == "GENERATED_UNCOMPILED"
    assert (out / "ART00001.LS").exists()
    assert (out / "trajectory.json").exists()
    assert (out / "preview.svg").exists()
    assert (out / "report.json").exists()
    assert (out / "manifest.json").exists()
    traj = json.loads((out / "trajectory.json").read_text())
    assert traj["schema"] == "svg2fanuc/trajectory@1"
    assert traj["frame"]["config"] == "N U T, 0, 0, 0"


def test_inspect_makes_no_ls(tmp_path, profile):
    out = tmp_path / "job_i"
    pipeline.run_inspect(
        data("lines.svg"), profile, out, allow_distortion=False, force=False
    )
    assert not list(out.glob("*.LS"))
    assert (out / "report.json").exists()


def test_verify_detects_tampering(tmp_path, profile):
    out = tmp_path / "job_v"
    pipeline.run_generate(
        data("square.svg"), profile, out,
        production=False, allow_distortion=False, job_number=1,
        when=date(2026, 9, 8), force=False,
    )
    pipeline.run_verify(out / "manifest.json")  # clean
    (out / "ART00001.LS").write_text("tampered")
    with pytest.raises(ManifestMismatchError):
        pipeline.run_verify(out / "manifest.json")


def test_existing_out_dir_requires_force(tmp_path, profile):
    out = tmp_path / "job_x"
    out.mkdir()
    with pytest.raises(Exception):
        pipeline.run_inspect(
            data("lines.svg"), profile, out, allow_distortion=False, force=False
        )


def test_production_blocks_on_tbd(tmp_path, make_profile):
    prof = make_profile(**{"robot.model": "TBD", "robot.controller": "TBD"})
    with pytest.raises(ProfileNotQualifiedError):
        pipeline.run_generate(
            data("lines.svg"), prof, tmp_path / "p",
            production=True, allow_distortion=False, job_number=1,
            when=date(2026, 9, 8), force=False,
        )


def test_partial_job_not_committed(tmp_path, make_profile):
    # tiny point budget -> BudgetError mid-pipeline, output dir must not appear
    prof = make_profile(**{"geometry.max_points": 5})
    out = tmp_path / "job_fail"
    with pytest.raises(Exception):
        pipeline.run_generate(
            data("lines.svg"), prof, out,
            production=False, allow_distortion=False, job_number=1,
            when=date(2026, 9, 8), force=False,
        )
    assert not out.exists()
    assert not out.with_name(out.name + ".tmp").exists()


@pytest.mark.parametrize(
    "name,code",
    [("bad_text.svg", 3), ("no_viewbox.svg", 3), ("filled.svg", 3)],
)
def test_cli_exit_codes(tmp_path, name, code):
    rc = main([
        "inspect", str(data(name)),
        "--profile", str(_write_concrete_profile(tmp_path)),
        "--out", str(tmp_path / "o"), "--force",
    ])
    assert rc == code


def test_cli_generate_success(tmp_path):
    rc = main([
        "generate", str(data("lines.svg")),
        "--profile", str(_write_concrete_profile(tmp_path)),
        "--out", str(tmp_path / "ok"), "--date", "2026-09-08",
    ])
    assert rc == 0
    assert (tmp_path / "ok" / "ART00001.LS").exists()


def _write_concrete_profile(tmp_path):
    import yaml

    from .conftest import PROFILE_YAML

    d = yaml.safe_load(PROFILE_YAML.read_text())
    d["robot"]["config"] = "N U T, 0, 0, 0"
    p = tmp_path / "cell.yaml"
    p.write_text(yaml.safe_dump(d))
    return p
