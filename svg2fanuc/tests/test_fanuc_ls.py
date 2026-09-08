from __future__ import annotations

from datetime import date

import pytest

from svg2fanuc.emitters import emit_fanuc_ls
from svg2fanuc.errors import LsProgramTooLargeError
from svg2fanuc.geometry import Stroke
from svg2fanuc.motion_ir import build_trajectory

WHEN = date(2026, 9, 8)


def _traj(profile, n_strokes=3, pts_per=4):
    strokes = []
    for i in range(n_strokes):
        y = 20.0 + i * 5
        strokes.append(Stroke(f"s{i:04d}", [(20.0 + j * 3, y) for j in range(pts_per)]))
    return build_trajectory(strokes, profile)


def test_single_program_structure(profile):
    traj = _traj(profile)
    res = emit_fanuc_ls(traj, profile, job_number=1, when=WHEN)
    assert not res.split
    text = res.master.text
    assert text.startswith("/PROG  ART00001\n")
    assert "/MN\n" in text and "/POS\n" in text and text.rstrip().endswith("/END")
    assert "CALL CELL_IN" in text and "CALL CELL_OUT" in text
    assert "CREATE\t\t= DATE 26-09-08" in text
    assert text.isascii()
    linear = sum(1 for m in traj.motions if m.kind == "LINEAR")
    assert res.master.positions == linear
    assert text.count("P[") >= linear  # one /POS block + references


def test_position_block_has_frame_and_config(profile):
    res = emit_fanuc_ls(_traj(profile), profile, job_number=7, when=WHEN)
    assert "CONFIG : 'N U T, 0, 0, 0'" in res.master.text
    assert "UF : 1, UT : 1" in res.master.text


def test_split_produces_master_and_parts(make_profile):
    prof = make_profile(**{"fanuc_ls.max_motion_lines_per_subprogram": 40})
    traj = _traj(prof, n_strokes=8, pts_per=4)
    res = emit_fanuc_ls(traj, prof, job_number=3, when=WHEN)
    assert res.split
    assert res.master.text.count("CALL ") == len(res.parts) + 2  # + CELL_IN/OUT
    for part in res.parts:
        assert part.text.startswith("/PROG  ")
        assert "CALL CELL_IN" not in part.text
        assert "L P[1]" in part.text  # part starts tool-up with a TRAVEL move


def test_oversized_single_stroke_rejected(make_profile):
    prof = make_profile(**{"fanuc_ls.max_motion_lines_per_subprogram": 30})
    big = Stroke("s0001", [(20.0 + i * 0.5, 20.0) for i in range(60)])
    traj = build_trajectory([big], prof)
    with pytest.raises(LsProgramTooLargeError):
        emit_fanuc_ls(traj, prof, job_number=1, when=WHEN)


def test_speeds_and_terminations_present(profile):
    res = emit_fanuc_ls(_traj(profile), profile, job_number=1, when=WHEN)
    assert "mm/sec FINE" in res.master.text
    assert "mm/sec CNT3" in res.master.text
