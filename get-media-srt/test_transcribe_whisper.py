import unittest
import sys
import tempfile
import shutil
from pathlib import Path

# Add directory to sys.path to allow absolute imports when running tests from repo root
sys.path.append(str(Path(__file__).parent.resolve()))

from transcribe_to_srt_whisper import get_device_and_compute_type, collect_inputs


class TestTranscribe(unittest.TestCase):
    def test_get_device_and_compute_type(self):
        device, compute_type = get_device_and_compute_type()
        self.assertIn(device, ["cuda", "cpu"])
        self.assertIn(compute_type, ["float16", "int8", "int8_float16"])

    def test_collect_inputs(self):
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create some dummy files
            file1 = temp_dir / "audio1.mp3"
            file2 = temp_dir / "audio2.wav"
            file3 = temp_dir / "text.txt"
            file4 = temp_dir / "audio1.srt"
            
            file1.touch()
            file2.touch()
            file3.touch()
            file4.touch()
            
            # Case 1: collect all matching audio files, skipping those with existing srt (default)
            collected = collect_inputs(temp_dir, skip_existing=True)
            # file1.mp3 has file1.srt, so it should be skipped. file2.wav does not have srt, so it should be included.
            self.assertEqual(len(collected), 1)
            self.assertEqual(collected[0].name, "audio2.wav")
            
            # Case 2: collect all matching audio files, including those with existing srt
            collected_all = collect_inputs(temp_dir, skip_existing=False)
            self.assertEqual(len(collected_all), 2)
            self.assertEqual([f.name for f in collected_all], ["audio1.mp3", "audio2.wav"])
            
            # Case 3: single file input
            collected_single = collect_inputs(file1)
            self.assertEqual(collected_single, [file1.resolve()])
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
