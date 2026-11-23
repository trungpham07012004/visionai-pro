from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_COMPONENT = components.declare_component(
    "visionai_interactive_robot",
    path=str(Path(__file__).resolve().parents[1] / "ui" / "vision_robot"),
)
_ALLOWED_STATES = {
    "idle",
    "greeting",
    "listening",
    "thinking",
    "speaking",
    "happy",
    "helping",
    "curious",
    "error",
}


def _render(status, message, compact, height, key):
    status = status if status in _ALLOWED_STATES else "idle"
    click_count = int(st.session_state.get("robot_click_count", 0))
    result = _COMPONENT(
        status=status,
        message=str(message or ""),
        compact=compact,
        chat_open=bool(st.session_state.get("robot_chat_open", False)),
        click_count=click_count,
        height=height,
        key=key,
        default=click_count,
    )
    if not isinstance(result, dict):
        return

    action = result.get("action")
    nonce = result.get("nonce")
    if not isinstance(nonce, int) or nonce <= click_count:
        return
    st.session_state.robot_click_count = nonce
    if action == "chat":
        st.session_state.robot_chat_open = True
        st.session_state.robot_status = "helping"
        st.session_state.robot_message = "Mình đang lắng nghe. Bạn có thể hỏi bằng tiếng Việt."
    else:
        destinations = {
            "analyze": ("📷 Phân tích hình ảnh", "Chọn ảnh để mình bắt đầu phân tích."),
            "ocr": ("🔤 OCR (Nhận diện văn bản)", "Chọn ảnh có chữ rõ nét để mình đọc giúp."),
            "image_chat": ("💬 Hỏi đáp AI", "Mở Hỏi đáp AI để đặt câu hỏi về ảnh."),
        }
        destination = destinations.get(action)
        if destination:
            page, message = destination
            st.session_state.robot_pending_navigation = page
            st.session_state.robot_chat_open = False
            st.session_state.robot_status = "helping"
            st.session_state.robot_message = message
    st.rerun()


def render_dashboard_robot(status, message):
    _render(status, message, compact=False, height=275, key="vision_robot_dashboard")


def render_compact_robot(status, message):
    _render(status, message, compact=True, height=120, key="vision_robot_compact")
