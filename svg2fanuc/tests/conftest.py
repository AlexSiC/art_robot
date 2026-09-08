from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from svg2fanuc.profile import parse_profile

DATA = Path(__file__).parent / "data"
PROFILE_YAML = Path(__file__).parents[1] / "profiles" / "example_cell.yaml"


@pytest.fixture
def profile_dict() -> dict:
    return copy.deepcopy(yaml.safe_load(PROFILE_YAML.read_text()))


@pytest.fixture
def profile(profile_dict):
    # give the dev profile a real CONFIG so `generate` is allowed
    profile_dict["robot"]["config"] = "N U T, 0, 0, 0"
    raw = yaml.safe_dump(profile_dict).encode()
    return parse_profile(profile_dict, raw_bytes=raw, source_path=str(PROFILE_YAML))


@pytest.fixture
def make_profile(profile_dict):
    def _make(**overrides):
        d = copy.deepcopy(profile_dict)
        for dotted, value in overrides.items():
            node = d
            *parents, leaf = dotted.split(".")
            for p in parents:
                node = node[p]
            node[leaf] = value
        raw = yaml.safe_dump(d).encode()
        return parse_profile(d, raw_bytes=raw, source_path="<test>")

    return _make


def data(name: str) -> Path:
    return DATA / name
