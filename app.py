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


st.set_page_config(page_title="YouTube 보컬 분리기", page_icon="🎵", layout="wide")
st.title("YouTube 보컬 분리기")
st.caption(
    "YouTube 링크를 입력해 보컬과 반주를 분리하고, 결과를 Tony에서 열 수 있습니다."
)
st.info(gpu_description())

with st.form("process_video", clear_on_submit=False):
    url = st.text_input(
        "YouTube 동영상 링크",
        placeholder="https://www.youtube.com/watch?v=...",
    )
    submitted = st.form_submit_button(
        "보컬 분리 후 Tony 열기",
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
        with st.status("작업을 준비하고 있습니다...", expanded=True) as status:
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
                status.update(label="작업에 실패했습니다.", state="error")
                st.error(str(error))
            else:
                status.update(label="보컬 분리가 완료됐습니다.", state="complete")
                st.success(f"완료: {result.title}")
                try:
                    launch_tony(result.vocal_path)
                    st.info("보컬 트랙을 Tony에서 열었습니다.")
                except FileNotFoundError as error:
                    st.warning(
                        f"{error}\n\n분리된 파일은 아래 이력에서 다시 열 수 있습니다."
                    )

st.divider()
st.subheader("작업 이력")
history = list_history()

if not history:
    st.caption("아직 작업 이력이 없습니다. YouTube 링크를 입력해 시작해 보세요.")
else:
    status_labels = {
        "completed": "완료",
        "processing": "작업 중",
        "failed": "실패",
    }
    entries = {item["id"]: item for item in history}

    def format_entry(entry_id):
        item = entries[entry_id]
        timestamp = item["created_at"].replace("T", " ")
        label = status_labels.get(item["status"], item["status"])
        return f'{timestamp}  |  {item["title"]}  |  {label}'

    selected_id = st.selectbox(
        "이력 선택",
        options=list(entries),
        format_func=format_entry,
    )
    selected = entries[selected_id]
    if selected["url"]:
        st.markdown(f"[원본 YouTube 영상 열기]({selected['url']})")
    else:
        st.caption("이전 결과의 링크 정보는 저장되어 있지 않습니다.")

    if selected["status"] == "failed" and selected["error"]:
        st.error(selected["error"])
    elif selected["status"] == "completed":
        vocal_path = Path(selected["vocal_path"] or "")
        instrumental_path = Path(selected["instrumental_path"] or "")
        vocal_button, instrumental_button = st.columns(2)
        with vocal_button:
            if st.button(
                "보컬을 Tony에서 열기",
                key=f"open_vocal_{selected_id}",
                use_container_width=True,
                disabled=not vocal_path.is_file(),
            ):
                try:
                    launch_tony(vocal_path)
                except (FileNotFoundError, OSError) as error:
                    st.error(str(error))
                else:
                    st.success("보컬 트랙을 Tony에서 열었습니다.")
        with instrumental_button:
            if st.button(
                "반주를 Tony에서 열기",
                key=f"open_instrumental_{selected_id}",
                use_container_width=True,
                disabled=not instrumental_path.is_file(),
            ):
                try:
                    launch_tony(instrumental_path)
                except (FileNotFoundError, OSError) as error:
                    st.error(str(error))
                else:
                    st.success("반주 트랙을 Tony에서 열었습니다.")
