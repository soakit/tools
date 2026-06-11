import unittest
import sys
from pathlib import Path

# Add directory to sys.path to allow absolute imports when running tests from repo root
sys.path.append(str(Path(__file__).parent.resolve()))

from transcribe_to_srt_whisper import get_device_and_compute_type

class TestTranscribe(unittest.TestCase):
    def test_get_device_and_compute_type(self):
        device, compute_type = get_device_and_compute_type()
        self.assertIn(device, ["cuda", "cpu"])
        self.assertIn(compute_type, ["float16", "int8", "int8_float16"])

if __name__ == "__main__":
    unittest.main()
