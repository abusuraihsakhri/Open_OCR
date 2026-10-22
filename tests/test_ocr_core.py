"""Regression tests for input conversion, backend parsing and export."""
import io
import os
import sys
import unittest

from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from ocr_core import image_as_png, response_text, validate_port, valid_json_output


class CoreTests(unittest.TestCase):
    def test_port_validation(self):
        self.assertEqual(validate_port("11434"), 11434)
        for value in ("0", "65536", "abc", None, "-1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_port(value)

    def test_one_pixel_rgba_is_not_resized_to_zero(self):
        image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        data = image_as_png(image)
        with Image.open(io.BytesIO(data)) as result:
            self.assertEqual(result.size, (2, 2))
            self.assertEqual(result.mode, "RGB")
            self.assertEqual(result.getpixel((0, 0)), (255, 255, 255))

    def test_downscaling_preserves_bounds(self):
        image = Image.new("RGB", (3001, 700))
        data = image_as_png(image)
        with Image.open(io.BytesIO(data)) as result:
            self.assertLessEqual(max(result.size), 1536)
            self.assertEqual(result.width % 2, 0)
            self.assertEqual(result.height % 2, 0)

    def test_backend_response_parsing(self):
        self.assertEqual(response_text({"response": "Hallo"}, "ollama"), "Hallo")
        self.assertEqual(response_text({"choices": [{"message": {"content": "Test"}}]}, "vllm"), "Test")
        for data, kind in [({}, "ollama"), ({}, "vllm"), (None, "ollama")]:
            with self.subTest(data=data, kind=kind), self.assertRaises(ValueError):
                response_text(data, kind)

    def test_json_output_is_parseable(self):
        import json
        source = [{"source": "sample.pdf", "page": 1, "text": "äöü"}]
        self.assertEqual(json.loads(valid_json_output(source)), source)


if __name__ == "__main__":
    unittest.main()
