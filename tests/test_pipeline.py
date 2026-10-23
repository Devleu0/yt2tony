import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pipeline import (
    create_history_entry,
    list_history,
    process_video,
    update_history_entry,
)


class PipelineTests(unittest.TestCase):
    def test_process_video_creates_unique_history_compatible_results(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "output"

            def fake_run(command, **_kwargs):
                if command[2] == "yt_dlp":
                    audio_path = Path(command[command.index("-o") + 1])
                    audio_path.parent.mkdir(parents=True, exist_ok=True)
                    audio_path.write_bytes(b"audio")
                    return SimpleNamespace(
                        returncode=0,
                        stdout="__YT2TONY_TITLE__Test Song\n",
                        stderr="",
                    )

                audio_path = Path(command[-1])
                result_dir = (
                    Path(command[command.index("-o") + 1])
                    / "htdemucs"
                    / audio_path.stem
                )
                result_dir.mkdir(parents=True)
                (result_dir / "vocals.mp3").write_bytes(b"vocals")
                (result_dir / "no_vocals.mp3").write_bytes(b"instrumental")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch("subprocess.run", side_effect=fake_run):
                first = process_video(
                    "https://www.youtube.com/watch?v=first", output_dir
                )
                second = process_video("https://youtu.be/second", output_dir)

            self.assertEqual(first.title, "Test Song")
            self.assertTrue(first.vocal_path.is_file())
            self.assertTrue(first.instrumental_path.is_file())
            self.assertNotEqual(first.vocal_path, second.vocal_path)
            self.assertFalse((output_dir / "temp").exists())

    def test_history_tracks_completed_item(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "output"
            entry_id = create_history_entry(
                "https://www.youtube.com/watch?v=example", output_dir
            )
            vocal_path = output_dir / "vocals.mp3"
            instrumental_path = output_dir / "no_vocals.mp3"
            vocal_path.touch()
            instrumental_path.touch()
            update_history_entry(
                entry_id,
                output_dir,
                title="Example song",
                status="completed",
                vocal_path=vocal_path,
                instrumental_path=instrumental_path,
            )

            history = list_history(output_dir)

            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["title"], "Example song")
            self.assertEqual(history[0]["status"], "completed")
            self.assertEqual(Path(history[0]["vocal_path"]), vocal_path)


if __name__ == "__main__":
    unittest.main()
