"""svg2fanuc — cleaned SVG -> trajectory -> FANUC .LS.

Implements the specification
«Спецификация — очищенный SVG в траекторию FANUC.md» (module `svg2fanuc`).

This package never drives a physical robot. Its most advanced output state is
COMPILED_UNVERIFIED. GENERATED != SAFE TO RUN.
"""

from .version import __version__

__all__ = ["__version__"]
