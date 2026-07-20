# -*- coding: utf-8 -*-
import unittest
import sys
import tempfile
import shutil
from pathlib import Path
from types import SimpleNamespace

# Add directory to sys.path to allow absolute imports when running tests from repo root
sys.path.append(str(Path(__file__).parent.resolve()))

from transcribe_to_srt_whisper import (
    get_device_and_compute_type,
    collect_inputs,
    dedup_segments,
    _norm_text,
)


def seg(text, start=0.0, end=1.0):
    """Make a tiny stand-in segment object with the attributes write_srt needs."""
    return SimpleNamespace(text=text, start=start, end=end)


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


class TestNormText(unittest.TestCase):
    def test_strips_punctuation_and_whitespace(self):
        a = _norm_text("Hello, World!")
        b = _norm_text("Hello World")
        c = _norm_text("hello,  world")
        self.assertEqual(a, b)
        self.assertEqual(a, c)
        self.assertEqual(a, "helloworld")

    def test_cjk_punctuation_normalised(self):
        # Full-width comma vs space should compare equal.
        a = _norm_text("请不吝点赞，订阅")
        b = _norm_text("请不吝点赞 订阅")
        self.assertEqual(a, b)
        self.assertEqual(a, "请不吝点赞订阅")

    def test_empty(self):
        self.assertEqual(_norm_text(""), "")
        self.assertEqual(_norm_text(None), "")
        self.assertEqual(_norm_text("   "), "")


class TestDedupSegments(unittest.TestCase):
    def _ad(self):
        return "请不吝点赞 订阅 打赏支持明镜与点点栏目"

    def test_drops_hallucination_loop(self):
        """The real-world bug: same ad line repeated ~20 times should collapse."""
        ad = self._ad()
        segments = [seg(ad, start=i * 30, end=i * 30 + 30) for i in range(20)]
        cleaned = dedup_segments(segments)
        # max_repeats=2 default -> only the first 2 occurrences are kept.
        self.assertEqual(len(cleaned), 2)
        for s in cleaned:
            self.assertEqual(s.text, ad)

    def test_keeps_genuine_occasional_repeats(self):
        """Repeats that fall outside the rolling window survive.

        With max_repeats=2 and window=8, the same line can appear at most
        twice within any 8-segment window. Once enough other content pushes
        the earlier occurrences out of the window, the line can appear again.
        """
        # 2x "你好" (allowed), then 7 unique lines to flush the window, then
        # another "你好" which is now outside the window -> kept.
        segments = [
            seg("你好", start=0, end=1),
            seg("你好", start=1, end=2),
            seg("一", start=3, end=4),
            seg("二", start=5, end=6),
            seg("三", start=7, end=8),
            seg("四", start=9, end=10),
            seg("五", start=11, end=12),
            seg("六", start=13, end=14),
            seg("七", start=15, end=16),
            seg("你好", start=100, end=101),  # window has moved past the first two
        ]
        cleaned = dedup_segments(segments)
        self.assertEqual(len(cleaned), 10)

    def test_short_window_allows_repeats_outside_window(self):
        """Explicit tiny window lets distant repeats through."""
        segments = [
            seg("x", start=0, end=1),
            seg("x", start=1, end=2),       # 2nd -> allowed (max_repeats=2)
            seg("unique1", start=2, end=3),
            seg("x", start=3, end=4),       # 3rd, but window=2 only sees last 2 kept
        ]
        # With window=2: after [x, x, unique1], recent=[x,x,unique1]; last 2 = [x, unique1].
        # 3rd "x" sees 1 prior x in window -> repeats=1 < 2 -> kept.
        cleaned = dedup_segments(segments, max_repeats=2, window=2)
        self.assertEqual(len(cleaned), 4)

    def test_drops_empty_segments(self):
        segments = [seg("", start=0, end=1), seg("   ", start=1, end=2), seg("ok", start=2, end=3)]
        cleaned = dedup_segments(segments)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0].text, "ok")

    def test_window_resets(self):
        """A burst of repeats followed by unique content should keep the uniques."""
        ad = self._ad()
        burst = [seg(ad, start=i, end=i + 1) for i in range(5)]  # 5 repeats
        tail = [seg("end of show", start=100, end=101)]
        cleaned = dedup_segments(burst + tail)
        # ad kept max_repeats=2 times, then the unique tail.
        self.assertEqual([s.text for s in cleaned], [ad, ad, "end of show"])

    def test_preserves_segment_objects(self):
        """Returned items are the same objects passed in (not copies)."""
        s1, s2 = seg("a"), seg("b")
        cleaned = dedup_segments([s1, s2])
        self.assertIs(cleaned[0], s1)
        self.assertIs(cleaned[1], s2)

    def test_max_repeats_param(self):
        ad = self._ad()
        segments = [seg(ad, start=i, end=i + 1) for i in range(5)]
        # Allow only 1 occurrence -> only the first is kept.
        cleaned = dedup_segments(segments, max_repeats=1)
        self.assertEqual(len(cleaned), 1)


if __name__ == "__main__":
    unittest.main()
