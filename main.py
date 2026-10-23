import sqlite3

from pipeline import (
    DEFAULT_OUTPUT_DIR,
    create_history_entry,
    launch_tony,
    process_video,
    update_history_entry,
    validate_youtube_url,
)


def main():
    print("YouTube Vocal Splitter")
    url = input("YouTube URL: ").strip()
    try:
        url = validate_youtube_url(url)
    except ValueError as error:
        print(f"[Error] {error}")
        return 1

    entry_id = create_history_entry(url)
    try:
        result = process_video(
            url,
            on_status=lambda message: print(f"[Process] {message}"),
            on_title=lambda title: update_history_entry(entry_id, title=title),
        )
        update_history_entry(
            entry_id,
            title=result.title,
            status="completed",
            vocal_path=result.vocal_path,
            instrumental_path=result.instrumental_path,
        )
    except (RuntimeError, OSError, sqlite3.Error) as error:
        update_history_entry(entry_id, status="failed", error=str(error))
        print(f"[Error] {error}")
        return 1

    print(f"[Info] Vocal track: {result.vocal_path}")
    print(f"[Info] Instrumental: {result.instrumental_path}")
    try:
        launch_tony(result.vocal_path)
        print("[Info] Vocal track opened in Tony.")
    except FileNotFoundError as error:
        print(f"[Warning] {error}")
        print(f"[Info] Results are saved under: {DEFAULT_OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
