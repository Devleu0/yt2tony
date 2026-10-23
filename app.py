from pathlib import Path
import sqlite3

import streamlit as st

from pipeline import (
    create_history_entry,
    gpu_description,
    launch_tony,
    list_history,
    process_video,
    update_history_entry,
    validate_youtube_url,
)


st.set_page_config(page_title="YouTube Vocal Splitter", page_icon="🎵", layout="wide")
st.title("YouTube Vocal Splitter")
st.caption(
    "Split a YouTube song into vocals and instrumental, then open a track in Tony."
)
st.info(gpu_description())

with st.form("process_video", clear_on_submit=False):
    url = st.text_input(
        "YouTube video link",
        placeholder="https://www.youtube.com/watch?v=...",
    )
    submitted = st.form_submit_button(
        "Split track and open vocals in Tony",
        type="primary",
        use_container_width=True,
    )

if submitted:
    try:
        url = validate_youtube_url(url)
    except ValueError as error:
        st.error(str(error))
    else:
        entry_id = create_history_entry(url)
        with st.status("Getting ready...", expanded=True) as status:
            try:
                result = process_video(
                    url,
                    on_status=lambda message: status.update(label=message),
                    on_title=lambda title: update_history_entry(
                        entry_id, title=title
                    ),
                )
                update_history_entry(
                    entry_id,
                    title=result.title,
                    status="completed",
                    vocal_path=result.vocal_path,
                    instrumental_path=result.instrumental_path,
                )
            except (RuntimeError, OSError, sqlite3.Error) as error:
                update_history_entry(
                    entry_id,
                    status="failed",
                    error=str(error),
                )
                status.update(label="Something went wrong.", state="error")
                st.error(str(error))
            else:
                status.update(label="Track split complete.", state="complete")
                st.success(f"Done: {result.title}")
                try:
                    launch_tony(result.vocal_path)
                    st.info("Vocals are open in Tony.")
                except FileNotFoundError as error:
                    st.warning(
                        f"{error}\n\nYou can open the saved tracks from History."
                    )

st.divider()
st.subheader("History")
history = list_history()

if not history:
    st.caption("No tracks yet. Paste a YouTube link above to get started.")
else:
    status_labels = {
        "completed": "Done",
        "processing": "Working",
        "failed": "Failed",
    }
    entries = {item["id"]: item for item in history}

    def format_entry(entry_id):
        item = entries[entry_id]
        timestamp = item["created_at"].replace("T", " ")
        label = status_labels.get(item["status"], item["status"])
        return f'{timestamp}  |  {item["title"]}  |  {label}'

    selected_id = st.selectbox(
        "Choose a track",
        options=list(entries),
        format_func=format_entry,
    )
    selected = entries[selected_id]
    if selected["url"]:
        st.markdown(f"[Open the YouTube video]({selected['url']})")
    else:
        st.caption("The original video link is not available.")

    if selected["status"] == "failed" and selected["error"]:
        st.error(selected["error"])
    elif selected["status"] == "completed":
        vocal_path = Path(selected["vocal_path"] or "")
        instrumental_path = Path(selected["instrumental_path"] or "")
        vocal_button, instrumental_button = st.columns(2)
        with vocal_button:
            if st.button(
                "Open vocals in Tony",
                key=f"open_vocal_{selected_id}",
                use_container_width=True,
                disabled=not vocal_path.is_file(),
            ):
                try:
                    launch_tony(vocal_path)
                except (FileNotFoundError, OSError) as error:
                    st.error(str(error))
                else:
                    st.success("Vocals are open in Tony.")
        with instrumental_button:
            if st.button(
                "Open instrumental in Tony",
                key=f"open_instrumental_{selected_id}",
                use_container_width=True,
                disabled=not instrumental_path.is_file(),
            ):
                try:
                    launch_tony(instrumental_path)
                except (FileNotFoundError, OSError) as error:
                    st.error(str(error))
                else:
                    st.success("Instrumental is open in Tony.")
