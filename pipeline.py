import os
import sqlite3
import subprocess
import sys
import uuid
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "output"


@dataclass(frozen=True)
class SeparationResult:
    title: str
    vocal_path: Path
    instrumental_path: Path


def history_database(output_dir=DEFAULT_OUTPUT_DIR):
    return Path(output_dir) / "history.sqlite3"


def initialize_history(output_dir=DEFAULT_OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    database = history_database(output_dir)

    with closing(sqlite3.connect(database)) as connection:
        with connection:
            connection.row_factory = sqlite3.Row
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    vocal_path TEXT,
                    instrumental_path TEXT,
                    error TEXT
                )
                """,
            )
            count = connection.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            legacy_vocal = output_dir / "htdemucs" / "input_track" / "vocals.mp3"
            legacy_instrumental = (
                output_dir / "htdemucs" / "input_track" / "no_vocals.mp3"
            )
            if count == 0 and legacy_vocal.is_file() and legacy_instrumental.is_file():
                created_at = datetime.fromtimestamp(
                    max(
                        legacy_vocal.stat().st_mtime,
                        legacy_instrumental.stat().st_mtime,
                    )
                ).astimezone().isoformat(timespec="seconds")
                connection.execute(
                    """
                    INSERT INTO history
                        (title, url, status, created_at, vocal_path, instrumental_path)
                    VALUES (?, NULL, 'completed', ?, ?, ?)
                    """,
                    (
                        "이전 분리 결과 (링크 정보 없음)",
                        created_at,
                        str(legacy_vocal.resolve()),
                        str(legacy_instrumental.resolve()),
                    ),
                )
    return database


def list_history(output_dir=DEFAULT_OUTPUT_DIR):
    database = initialize_history(output_dir)
    with closing(sqlite3.connect(database)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM history ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def create_history_entry(url, output_dir=DEFAULT_OUTPUT_DIR):
    database = initialize_history(output_dir)
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    with closing(sqlite3.connect(database)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO history (title, url, status, created_at)
                VALUES (?, ?, 'processing', ?)
                """,
                ("다운로드 중...", url, created_at),
            )
            return cursor.lastrowid


def update_history_entry(
    entry_id,
    output_dir=DEFAULT_OUTPUT_DIR,
    *,
    title=None,
    status=None,
    vocal_path=None,
    instrumental_path=None,
    error=None,
):
    database = history_database(output_dir)
    fields = {
        "title": title,
        "status": status,
        "vocal_path": str(vocal_path) if vocal_path else None,
        "instrumental_path": str(instrumental_path) if instrumental_path else None,
        "error": error,
    }
    updates = {key: value for key, value in fields.items() if value is not None}
    if not updates:
        return
    assignments = ", ".join(f"{field} = ?" for field in updates)
    with closing(sqlite3.connect(database)) as connection:
        with connection:
            connection.execute(
                f"UPDATE history SET {assignments} WHERE id = ?",
                [*updates.values(), entry_id],
            )


def validate_youtube_url(url):
    parsed = urlparse(url.strip())
    valid_hosts = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in valid_hosts
        or not parsed.path.strip("/")
    ):
        raise ValueError("유효한 YouTube 동영상 URL을 입력해 주세요.")
    return url.strip()


def gpu_description():
    try:
        import torch
    except ImportError:
        return "PyTorch가 설치되지 않았습니다."
    if torch.cuda.is_available():
        return f"CUDA GPU: {torch.cuda.get_device_name(0)}"
    return "GPU를 찾지 못해 CPU 모드로 실행합니다."


def process_video(url, output_dir=DEFAULT_OUTPUT_DIR, on_status=None, on_title=None):
    url = validate_youtube_url(url)
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    temp_dir = output_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_audio = temp_dir / f"{run_id}.mp3"

    def report(message):
        if on_status:
            on_status(message)

    process_env = os.environ.copy()
    process_env["PYTHONUTF8"] = "1"
    process_env["PYTHONIOENCODING"] = "utf-8"

    try:
        report("YouTube 오디오를 MP3로 다운로드하고 있습니다...")
        download = subprocess.run(
            [
                sys.executable,
                "-m",
                "yt_dlp",
                "-x",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "0",
                "--no-playlist",
                "--force-overwrite",
                "-o",
                str(temp_audio),
                "--print",
                "before_dl:__YT2TONY_TITLE__%(title)s",
                url,
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=process_env,
        )
        if download.returncode:
            details = (download.stderr or download.stdout).strip()
            raise RuntimeError(f"YouTube 오디오 다운로드에 실패했습니다.\n{details}")

        title = next(
            (
                line.removeprefix("__YT2TONY_TITLE__").strip()
                for line in download.stdout.splitlines()
                if line.startswith("__YT2TONY_TITLE__")
            ),
            "YouTube 영상",
        )
        if on_title:
            on_title(title)
        if not temp_audio.is_file():
            raise RuntimeError("다운로드가 완료됐지만 오디오 파일을 찾을 수 없습니다.")

        report("Demucs로 보컬과 반주를 분리하고 있습니다...")
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        separate = subprocess.run(
            [
                sys.executable,
                "-m",
                "demucs",
                "--two-stems",
                "vocals",
                "--mp3",
                "-d",
                device,
                "--segment",
                "2",
                "-o",
                str(output_dir),
                str(temp_audio),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=process_env,
        )
        if separate.returncode:
            details = (separate.stderr or separate.stdout).strip()
            raise RuntimeError(f"보컬 분리에 실패했습니다.\n{details}")

        result_dir = output_dir / "htdemucs" / run_id
        vocal_path = result_dir / "vocals.mp3"
        instrumental_path = result_dir / "no_vocals.mp3"
        if not vocal_path.is_file() or not instrumental_path.is_file():
            raise RuntimeError("분리는 완료됐지만 결과 파일을 찾을 수 없습니다.")
        return SeparationResult(title, vocal_path, instrumental_path)
    finally:
        if temp_audio.exists():
            temp_audio.unlink()
        if temp_dir.exists() and not any(temp_dir.iterdir()):
            temp_dir.rmdir()


def launch_tony(audio_path):
    audio_path = Path(audio_path).resolve()
    if not audio_path.is_file():
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

    tony_path = Path(
        os.environ.get("TONY_EXE", r"C:\Program Files\Tony\tony.exe")
    )
    if not tony_path.is_file():
        raise FileNotFoundError(
            f"Tony를 찾을 수 없습니다: {tony_path}\n"
            "TONY_EXE 환경 변수로 tony.exe 경로를 지정할 수 있습니다."
        )
    return subprocess.Popen([str(tony_path), str(audio_path)])
