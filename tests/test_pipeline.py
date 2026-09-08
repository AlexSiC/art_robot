from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

from png2svg.errors import EmptyImageError, ImageReadError, ValidationError
from png2svg.pipeline import GenerateOptions, generate


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "tests" / "data" / "test_profile.yaml"
SVG_NS = "http://www.w3.org/2000/svg"


def make_drawing(path: Path, mode: str = "L") -> None:
    background = 255 if mode == "L" else (255, 255, 255)
    foreground = 0 if mode == "L" else (0, 0, 0)
    image = Image.new(mode, (96, 64), background)
    draw = ImageDraw.Draw(image)
    draw.line((8, 14, 86, 14), fill=foreground, width=5)
    draw.line((20, 50, 76, 28), fill=foreground, width=3)
    image.save(path)


class PipelineTests(unittest.TestCase):
    def test_end_to_end_emits_svg_draw_1_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "drawing.png"
            out = root / "job"
            make_drawing(source)
            result = generate(GenerateOptions(source, PROFILE, out, debug=True))

            self.assertEqual(
                set(result.artifacts),
                {"clean.svg", "manifest.json", "preview.svg", "skeleton.png", "stats.json"},
            )
            svg = ET.parse(out / "clean.svg").getroot()
            self.assertEqual(svg.tag, f"{{{SVG_NS}}}svg")
            tags = {element.tag for element in svg.iter()}
            self.assertLessEqual(
                tags,
                {
                    f"{{{SVG_NS}}}svg",
                    f"{{{SVG_NS}}}g",
                    f"{{{SVG_NS}}}polyline",
                    f"{{{SVG_NS}}}polygon",
                },
            )
            geometry = [
                element
                for element in svg.iter()
                if element.tag in {f"{{{SVG_NS}}}polyline", f"{{{SVG_NS}}}polygon"}
            ]
            self.assertGreaterEqual(len(geometry), 2)
            self.assertTrue(all(item.attrib.get("fill") == "none" for item in geometry))
            self.assertTrue(all("transform" not in item.attrib for item in geometry))

            stats = json.loads((out / "stats.json").read_text(encoding="utf-8"))
            self.assertGreater(stats["points_removed_by_simplify"], 0)
            self.assertLessEqual(stats["travel_length_after"], stats["travel_length_before"])
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "production")
            self.assertIn("clean.svg", manifest["artifacts"])

    def test_deterministic_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "drawing.png"
            make_drawing(source)
            first = root / "first"
            second = root / "second"
            generate(GenerateOptions(source, PROFILE, first))
            generate(GenerateOptions(source, PROFILE, second))
            for name in ("clean.svg", "preview.svg", "stats.json", "manifest.json"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_dry_run_omits_clean_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "drawing.png"
            out = root / "dry"
            make_drawing(source)
            result = generate(GenerateOptions(source, PROFILE, out, dry_run=True))
            self.assertNotIn("clean.svg", result.artifacts)
            self.assertFalse((out / "clean.svg").exists())
            self.assertTrue((out / "preview.svg").exists())
            self.assertTrue((out / "stats.json").exists())

    def test_blank_image_is_exit_code_four_domain_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "blank.png"
            Image.new("L", (64, 64), 255).save(source)
            with self.assertRaises(EmptyImageError) as context:
                generate(GenerateOptions(source, PROFILE, root / "job"))
            self.assertEqual(context.exception.exit_code, 4)
            self.assertFalse((root / "job" / "clean.svg").exists())

    def test_corrupt_image_is_exit_code_three_domain_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "broken.png"
            source.write_bytes(b"not a png")
            with self.assertRaises(ImageReadError) as context:
                generate(GenerateOptions(source, PROFILE, root / "job"))
            self.assertEqual(context.exception.exit_code, 3)

    def test_strict_rejects_color_warning_without_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "color.png"
            out = root / "job"
            make_drawing(source, "RGB")
            with self.assertRaises(ValidationError) as context:
                generate(GenerateOptions(source, PROFILE, out, strict=True))
            self.assertEqual(context.exception.exit_code, 7)
            self.assertFalse((out / "clean.svg").exists())


if __name__ == "__main__":
    unittest.main()
