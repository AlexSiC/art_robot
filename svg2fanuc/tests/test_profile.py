from __future__ import annotations

import pytest

from svg2fanuc.errors import ProfileError
from svg2fanuc.profile import load_profile

from .conftest import PROFILE_YAML


def test_example_profile_loads():
    p = load_profile(PROFILE_YAML)
    assert p.cell_id == "example_dev_cell_v0"
    assert p.canvas.area_width_mm == 760.0
    ok, problems = p.qualified_for_production()
    assert not ok and any("TBD" in x for x in problems)


def test_bad_config_string_rejected(make_profile):
    with pytest.raises(ProfileError):
        make_profile(**{"robot.config": "banana"})


def test_zclear_must_exceed_zdraw(make_profile):
    with pytest.raises(ProfileError):
        make_profile(**{"canvas.z_clear_mm": -1.0})


def test_prefix_leaves_room_for_job_number(make_profile):
    with pytest.raises(ProfileError):
        make_profile(**{"fanuc_ls.program_name_prefix": "TOOLONG"})
