"""Domain errors and process exit codes.

Exit codes follow section 4.2 of the specification; domain error codes follow
section 11.1.
"""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0
    CLI_OR_PROFILE = 2
    SVG_INVALID = 3
    GEOMETRY = 4
    BUDGET = 5
    LS_EMIT = 6
    MAKETP = 7
    MANIFEST = 8
    INTERNAL = 9


# domain code -> exit code
_CODE_TO_EXIT: dict[str, ExitCode] = {
    "CLI_ERROR": ExitCode.CLI_OR_PROFILE,
    "PROFILE_INVALID": ExitCode.CLI_OR_PROFILE,
    "PROFILE_NOT_QUALIFIED": ExitCode.CLI_OR_PROFILE,
    "SVG_XML_UNSAFE": ExitCode.SVG_INVALID,
    "SVG_ELEMENT_UNSUPPORTED": ExitCode.SVG_INVALID,
    "SVG_ATTRIBUTE_UNSUPPORTED": ExitCode.SVG_INVALID,
    "SVG_VIEWBOX_REQUIRED": ExitCode.SVG_INVALID,
    "SVG_FILL_UNSUPPORTED": ExitCode.SVG_INVALID,
    "SVG_PARSE_FAILED": ExitCode.SVG_INVALID,
    "SVG_EMPTY": ExitCode.GEOMETRY,
    "GEOM_NONFINITE": ExitCode.GEOMETRY,
    "GEOM_OUT_OF_BOUNDS": ExitCode.GEOMETRY,
    "GEOM_FLATTEN_LIMIT": ExitCode.GEOMETRY,
    "GEOM_DEGENERATE": ExitCode.GEOMETRY,
    "MOTION_INVALID_PHASE": ExitCode.GEOMETRY,
    "GEOM_POINT_BUDGET": ExitCode.BUDGET,
    "LS_PROGRAM_TOO_LARGE": ExitCode.BUDGET,
    "LS_EMIT_FAILED": ExitCode.LS_EMIT,
    "MAKETP_FAILED": ExitCode.MAKETP,
    "MANIFEST_MISMATCH": ExitCode.MANIFEST,
    "INTERNAL": ExitCode.INTERNAL,
}


class Svg2FanucError(Exception):
    """Base class for every expected (non-bug) failure."""

    code = "INTERNAL"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        element_id: str | None = None,
        detail: dict | None = None,
    ) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code
        self.message = message
        self.element_id = element_id
        self.detail = detail or {}

    @property
    def exit_code(self) -> ExitCode:
        return _CODE_TO_EXIT.get(self.code, ExitCode.INTERNAL)

    def as_dict(self) -> dict:
        d = {"code": self.code, "message": self.message}
        if self.element_id:
            d["element_id"] = self.element_id
        if self.detail:
            d["detail"] = self.detail
        return d


class CliError(Svg2FanucError):
    code = "CLI_ERROR"


class ProfileError(Svg2FanucError):
    code = "PROFILE_INVALID"


class ProfileNotQualifiedError(Svg2FanucError):
    code = "PROFILE_NOT_QUALIFIED"


class SvgSecurityError(Svg2FanucError):
    code = "SVG_XML_UNSAFE"


class SvgUnsupportedError(Svg2FanucError):
    code = "SVG_ELEMENT_UNSUPPORTED"


class SvgViewBoxRequiredError(Svg2FanucError):
    code = "SVG_VIEWBOX_REQUIRED"


class SvgFillError(Svg2FanucError):
    code = "SVG_FILL_UNSUPPORTED"


class SvgEmptyError(Svg2FanucError):
    code = "SVG_EMPTY"


class GeometryError(Svg2FanucError):
    code = "GEOM_NONFINITE"


class OutOfBoundsError(Svg2FanucError):
    code = "GEOM_OUT_OF_BOUNDS"


class FlattenLimitError(Svg2FanucError):
    code = "GEOM_FLATTEN_LIMIT"


class BudgetError(Svg2FanucError):
    code = "GEOM_POINT_BUDGET"


class MotionPhaseError(Svg2FanucError):
    code = "MOTION_INVALID_PHASE"


class LsProgramTooLargeError(Svg2FanucError):
    code = "LS_PROGRAM_TOO_LARGE"


class LsEmitError(Svg2FanucError):
    code = "LS_EMIT_FAILED"


class MakeTpError(Svg2FanucError):
    code = "MAKETP_FAILED"


class ManifestMismatchError(Svg2FanucError):
    code = "MANIFEST_MISMATCH"
