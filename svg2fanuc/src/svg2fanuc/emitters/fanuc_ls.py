"""FANUC LS emitter (section 8).

Consumes only a validated :class:`Trajectory` plus the profile. Produces one
master ``.LS`` and, when the motion count exceeds the configured per-subprogram
limit, a set of part programs the master ``CALL``s in order. Positions are
numbered independently inside each file. A single stroke that cannot fit one
subprogram is rejected (LS_PROGRAM_TOO_LARGE).

Generating valid-looking text is *not* proof of controller compatibility — that
is confirmed by MakeTP against the real ``robot.ini`` (section 8.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date

from ..errors import LsEmitError, LsProgramTooLargeError
from ..motion_ir import KIND_CALL, KIND_LINEAR, PHASE_TRAVEL, Motion, Trajectory
from ..profile import Profile

_TAB = "\t"


@dataclass
class LsProgram:
    name: str
    text: str
    motion_lines: int
    positions: int


@dataclass
class EmitResult:
    master: LsProgram
    parts: list[LsProgram] = field(default_factory=list)
    split: bool = False

    @property
    def all_programs(self) -> list[LsProgram]:
        return [self.master, *self.parts]

    def to_json(self) -> dict:
        return {
            "split": self.split,
            "master": self.master.name,
            "parts": [p.name for p in self.parts],
            "programs": [
                {"name": p.name, "motion_lines": p.motion_lines, "positions": p.positions}
                for p in self.all_programs
            ],
        }


@dataclass
class _StrokeBlock:
    stroke_id: str | None
    moves: list[Motion]


def emit_fanuc_ls(
    traj: Trajectory,
    profile: Profile,
    *,
    job_number: int,
    when: _date | None = None,
) -> EmitResult:
    fl = profile.fanuc_ls
    when = when or _date.today()
    date_str = f"{when.year % 100:02d}-{when.month:02d}-{when.day:02d}"

    entry_calls = [m for m in traj.motions if m.kind == KIND_CALL and m.phase == "ENTRY"]
    exit_calls = [m for m in traj.motions if m.kind == KIND_CALL and m.phase == "EXIT"]
    entry_prog = entry_calls[0].target if entry_calls else profile.motion.entry_program
    exit_prog = exit_calls[0].target if exit_calls else profile.motion.exit_program

    blocks = _stroke_blocks(traj)
    total_moves = sum(len(b.moves) for b in blocks)

    master_name = _master_name(profile, job_number)

    if total_moves + 4 <= fl.max_motion_lines_per_subprogram:
        text, npos = _render_program(
            master_name, blocks, profile, date_str,
            entry_prog=entry_prog, exit_prog=exit_prog, comment=f"svg2fanuc job {job_number}",
        )
        return EmitResult(
            master=LsProgram(master_name, text, total_moves, npos), split=False
        )

    # split on stroke boundaries
    if fl.program_name_max_chars < 8:
        raise LsProgramTooLargeError(
            "job needs splitting but program_name_max_chars < 8 leaves no room "
            "for part names"
        )
    groups = _group_blocks(blocks, fl.max_motion_lines_per_subprogram - 2)

    parts: list[LsProgram] = []
    for k, group in enumerate(groups, start=1):
        pname = _part_name(profile, job_number, k)
        ptext, npos = _render_program(
            pname, group, profile, date_str,
            entry_prog=None, exit_prog=None, comment=f"job {job_number} part {k}",
        )
        parts.append(LsProgram(pname, ptext, sum(len(b.moves) for b in group), npos))

    master_text = _render_master(
        master_name, [p.name for p in parts], profile, date_str,
        entry_prog=entry_prog, exit_prog=exit_prog,
        comment=f"svg2fanuc job {job_number} (master)",
    )
    master = LsProgram(master_name, master_text, len(parts) + 4, 0)
    return EmitResult(master=master, parts=parts, split=True)


# --------------------------------------------------------------------------- #
# blocks
# --------------------------------------------------------------------------- #
def _stroke_blocks(traj: Trajectory) -> list[_StrokeBlock]:
    blocks: list[_StrokeBlock] = []
    current: _StrokeBlock | None = None
    for m in traj.motions:
        if m.kind != KIND_LINEAR:
            continue
        if m.phase == PHASE_TRAVEL:
            if current is not None:
                blocks.append(current)
            current = _StrokeBlock(m.stroke_id, [m])
        else:
            if current is None:
                current = _StrokeBlock(m.stroke_id, [])
            current.moves.append(m)
    if current is not None:
        blocks.append(current)
    return blocks


def _group_blocks(blocks: list[_StrokeBlock], budget: int) -> list[list[_StrokeBlock]]:
    groups: list[list[_StrokeBlock]] = []
    cur: list[_StrokeBlock] = []
    used = 0
    for b in blocks:
        n = len(b.moves)
        if n > budget:
            raise LsProgramTooLargeError(
                f"stroke {b.stroke_id} needs {n} moves, exceeds subprogram budget "
                f"{budget}; raise geometry.flatness_mm or split the stroke before "
                "cleaning the SVG",
                detail={"stroke_id": b.stroke_id, "moves": n, "budget": budget},
            )
        if used + n > budget and cur:
            groups.append(cur)
            cur, used = [], 0
        cur.append(b)
        used += n
    if cur:
        groups.append(cur)
    return groups


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def _render_program(
    name: str,
    blocks: list[_StrokeBlock],
    profile: Profile,
    date_str: str,
    *,
    entry_prog: str | None,
    exit_prog: str | None,
    comment: str,
) -> tuple[str, int]:
    fl = profile.fanuc_ls
    frame = profile.frames

    mn: list[str] = []
    pos: list[str] = []
    ln = 0

    def line(body: str) -> None:
        nonlocal ln
        ln += 1
        mn.append(f"{ln:4d}:{body} ;")

    line(f"  UFRAME_NUM={frame.uframe_num}")
    line(f"  UTOOL_NUM={frame.utool_num}")
    if entry_prog:
        line(f"  CALL {entry_prog}")

    pindex = 0
    for b in blocks:
        for m in b.moves:
            pindex += 1
            pos.append(_render_position(pindex, m, profile))
            term = m.termination if m.termination == "FINE" else f"CNT{int(m.cnt or 0)}"
            speed = max(1, int(round(float(m.speed)))) if m.speed is not None else 1
            line(f"L P[{pindex}] {speed}mm/sec {term}")

    if exit_prog:
        line(f"  CALL {exit_prog}")

    text = _wrap(name, comment, date_str, profile, mn, pos)
    _assert_encoding(text, fl.encoding)
    return text, pindex


def _render_master(
    name: str,
    part_names: list[str],
    profile: Profile,
    date_str: str,
    *,
    entry_prog: str,
    exit_prog: str,
    comment: str,
) -> str:
    frame = profile.frames
    mn: list[str] = []
    ln = 0

    def line(body: str) -> None:
        nonlocal ln
        ln += 1
        mn.append(f"{ln:4d}:{body} ;")

    line(f"  UFRAME_NUM={frame.uframe_num}")
    line(f"  UTOOL_NUM={frame.utool_num}")
    line(f"  CALL {entry_prog}")
    for pn in part_names:
        line(f"  CALL {pn}")
    line(f"  CALL {exit_prog}")

    text = _wrap(name, comment, date_str, profile, mn, [])
    _assert_encoding(text, profile.fanuc_ls.encoding)
    return text


def _render_position(index: int, m: Motion, profile: Profile) -> str:
    dm = profile.fanuc_ls.decimal_places_mm
    dd = profile.fanuc_ls.decimal_places_deg
    x, y, z = m.xyz_mm  # type: ignore[misc]
    w, p, r = m.wpr_deg  # type: ignore[misc]
    uf = profile.frames.uframe_num
    ut = profile.frames.utool_num
    cfg = profile.robot.config
    return (
        f"P[{index}]{{\n"
        f"{_TAB}GP1:\n"
        f"{_TAB}UF : {uf}, UT : {ut},{_TAB}{_TAB}CONFIG : '{cfg}',\n"
        f"{_TAB}X = {x:.{dm}f}  mm,{_TAB}Y = {y:.{dm}f}  mm,{_TAB}Z = {z:.{dm}f}  mm,\n"
        f"{_TAB}W = {w:.{dd}f} deg,{_TAB}P = {p:.{dd}f} deg,{_TAB}R = {r:.{dd}f} deg\n"
        f"}};"
    )


def _wrap(
    name: str,
    comment: str,
    date_str: str,
    profile: Profile,
    mn_lines: list[str],
    pos_blocks: list[str],
) -> str:
    header = (
        f"/PROG  {name}\n"
        "/ATTR\n"
        f"OWNER{_TAB}{_TAB}= MNEDITOR;\n"
        f'COMMENT{_TAB}{_TAB}= "{comment}";\n'
        f"PROG_SIZE{_TAB}= 0;\n"
        f"CREATE{_TAB}{_TAB}= DATE {date_str}  TIME 12:00:00;\n"
        f"MODIFIED{_TAB}= DATE {date_str}  TIME 12:00:00;\n"
        f"FILE_NAME{_TAB}= ;\n"
        f"VERSION{_TAB}{_TAB}= 0;\n"
        f"LINE_COUNT{_TAB}= {len(mn_lines)};\n"
        f"MEMORY_SIZE{_TAB}= 0;\n"
        f"PROTECT{_TAB}{_TAB}= READ_WRITE;\n"
        f"TCD:  STACK_SIZE{_TAB}= 0,\n"
        f"      TASK_PRIORITY{_TAB}= 50,\n"
        f"      TIME_SLICE{_TAB}= 0,\n"
        f"      BUSY_LAMP_OFF{_TAB}= 0,\n"
        f"      ABORT_REQUEST{_TAB}= 0,\n"
        f"      PAUSE_REQUEST{_TAB}= 0;\n"
        f"DEFAULT_GROUP{_TAB}= 1,*,*,*,*;\n"
        f"CONTROL_CODE{_TAB}= 00000000 00000000;\n"
        "/MN\n"
    )
    body = "\n".join(mn_lines) + "\n"
    pos_section = "/POS\n" + ("".join(b + "\n" for b in pos_blocks))
    return header + body + pos_section + "/END\n"


def _assert_encoding(text: str, encoding: str) -> None:
    try:
        text.encode(encoding or "ascii")
    except UnicodeEncodeError as exc:
        raise LsEmitError(
            f"generated LS text is not {encoding}-encodable: {exc}"
        ) from exc


def _master_name(profile: Profile, job_number: int) -> str:
    prefix = profile.fanuc_ls.program_name_prefix
    name = f"{prefix}{job_number:05d}"
    if len(name) > profile.fanuc_ls.program_name_max_chars:
        raise LsEmitError(
            f"master program name {name!r} exceeds "
            f"program_name_max_chars={profile.fanuc_ls.program_name_max_chars}"
        )
    return name


def _part_name(profile: Profile, job_number: int, part: int) -> str:
    prefix = profile.fanuc_ls.program_name_prefix[:1]
    name = f"{prefix}{job_number:05d}{part:02d}"
    if len(name) > profile.fanuc_ls.program_name_max_chars:
        raise LsProgramTooLargeError(
            f"part program name {name!r} exceeds program_name_max_chars"
        )
    return name
