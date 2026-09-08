"""Golden end-to-end checks (section 12.3)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from svg2fanuc import pipeline

from .conftest import data

CASES = ["lines.svg", "square.svg", "grid_diagonal.svg"]


@pytest.mark.parametrize("name", CASES)
def test_generate_invariants(tmp_path, profile, name):
    out = tmp_path / name.replace(".svg", "")
    rep = pipeline.run_generate(
        data(name), profile, out,
        production=False, allow_distortion=False, job_number=1,
        when=date(2026, 9, 8), force=False,
    )
    m = rep["metrics"]

    # 1. every point inside the qualified area
    xmin, ymin, xmax, ymax = m["bbox_mm"]
    b = profile.canvas.bounds_mm
    assert b[0] - 1e-6 <= xmin and xmax <= b[2] + 1e-6
    assert b[1] - 1e-6 <= ymin and ymax <= b[3] + 1e-6

    # 2. flatten error within tolerance
    assert m["max_flatten_error_mm"] <= profile.geometry.flatness_mm + 1e-9

    # 3. routing never worse than document order
    assert m["travel_length_after_mm"] <= m["travel_length_before_mm"] + 1e-6

    # 4. all validation checks passed
    assert rep["validation"]["ok"]

    # 5. LS is ASCII and well-formed
    ls = (out / (rep["fanuc_ls"]["master"] + ".LS")).read_text()
    assert ls.startswith("/PROG  ") and ls.rstrip().endswith("/END")
    assert ls.isascii()

    # 6. trajectory.json matches the LS position count (single-program case)
    if not rep["fanuc_ls"]["split"]:
        traj = json.loads((out / "trajectory.json").read_text())
        linear = sum(1 for mo in traj["motions"] if mo["kind"] == "LINEAR")
        assert rep["fanuc_ls"]["programs"][0]["positions"] == linear


@pytest.mark.parametrize("name", CASES)
def test_deterministic_geometry(tmp_path, profile, name):
    outs = []
    for i in range(2):
        out = tmp_path / f"{name}_{i}"
        pipeline.run_generate(
            data(name), profile, out,
            production=False, allow_distortion=False, job_number=1,
            when=date(2026, 9, 8), force=False,
        )
        outs.append(out)
    a = (outs[0] / "trajectory.json").read_text()
    b = (outs[1] / "trajectory.json").read_text()
    assert a == b
    la = (outs[0] / "ART00001.LS").read_text()
    lb = (outs[1] / "ART00001.LS").read_text()
    assert la == lb


def test_grid_diagonal_intersections_are_separate_strokes(tmp_path, profile):
    out = tmp_path / "grid"
    rep = pipeline.run_generate(
        data("grid_diagonal.svg"), profile, out,
        production=False, allow_distortion=False, job_number=1,
        when=date(2026, 9, 8), force=False,
    )
    # 8 source elements -> 8 strokes (crossings are not merged/split)
    assert rep["metrics"]["strokes"] == 8
