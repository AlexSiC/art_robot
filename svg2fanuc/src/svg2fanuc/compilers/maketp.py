"""MakeTP wrapper (section 8.3).

`MakeTP` ships with FANUC WinOLPC / ROBOGUIDE (Windows). This module only shells
out to it; it never uploads or runs anything. When ``compile.enabled`` is false
the step is skipped and the job stays GENERATED_UNCOMPILED.

    MakeTP [/p] infile [outfile] [/config robot.ini]
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..errors import MakeTpError
from ..profile import CompileSpec


@dataclass
class MakeTpOutcome:
    attempted: bool
    ok: bool
    tp_files: list[str]
    log: str

    def to_json(self) -> dict:
        return {
            "attempted": self.attempted,
            "ok": self.ok,
            "tp_files": list(self.tp_files),
            "log": self.log[-4000:],
        }


def compile_ls(ls_files: list[Path], out_dir: Path, spec: CompileSpec) -> MakeTpOutcome:
    if not spec.enabled:
        return MakeTpOutcome(False, False, [], "compile.enabled is false; skipped")

    exe = Path(spec.maketp_exe or "")
    ini = Path(spec.robot_ini or "")
    if not exe.exists():
        raise MakeTpError(f"MakeTP executable not found: {exe}")
    if not ini.exists():
        raise MakeTpError(f"robot.ini not found: {ini}")

    tp_files: list[str] = []
    logs: list[str] = []
    for ls in ls_files:
        tp = out_dir / (ls.stem + ".TP")
        cmd = [str(exe), str(ls), str(tp), "/config", str(ini)]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, check=False
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise MakeTpError(f"failed to run MakeTP: {exc}") from exc
        logs.append(f"$ {' '.join(cmd)}\n{proc.stdout}\n{proc.stderr}")
        if proc.returncode != 0 or not tp.exists():
            raise MakeTpError(
                f"MakeTP rejected {ls.name} (exit {proc.returncode})",
                detail={"log": "\n".join(logs)[-4000:]},
            )
        tp_files.append(str(tp))

    return MakeTpOutcome(True, True, tp_files, "\n".join(logs))
