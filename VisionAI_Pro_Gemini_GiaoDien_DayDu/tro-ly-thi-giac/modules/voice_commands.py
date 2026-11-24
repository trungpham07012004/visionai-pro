import re
import unicodedata


_PAGES = {
    "trang chu": "🏠 Trang chính",
    "phan tich anh": "📷 Phân tích hình ảnh",
    "phan tich hinh anh": "📷 Phân tích hình ảnh",
    "ocr": "🔤 OCR (Nhận diện văn bản)",
    "doc chu": "🔤 OCR (Nhận diện văn bản)",
    "camera": "📸 Camera",
    "hoi dap": "💬 Hỏi đáp AI",
    "lich su": "🕘 Lịch sử",
    "huong dan": "ℹ️ Hướng dẫn",
    "cai dat": "⚙️ Cài đặt",
    "ho tro di chuyen": "🧭 Hỗ trợ di chuyển",
    "tro ly giong noi": "🎙️ Trợ lý giọng nói",
}


def _normalize(text):
    normalized = unicodedata.normalize("NFD", str(text or "").lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", normalized.replace("đ", "d")).strip()


def parse_voice_command(text):
    """Parse only explicit, short Vietnamese commands; return None for normal questions."""
    command = _normalize(text)
    if not command:
        return None

    if command in {"doc lai", "doc lai ket qua", "nhac lai ket qua"}:
        return {"action": "replay"}
    if command in {"tro giup", "giup toi", "cac lenh", "huong dan lenh"}:
        return {"action": "help"}

    for prefix in ("tim ", "hay tim ", "tim giup toi "):
        if command.startswith(prefix):
            target = command[len(prefix):].strip(" .?!")
            if target:
                return {"action": "find_object", "target": target}

    for prefix in ("mo ", "chuyen den ", "di den "):
        if command.startswith(prefix):
            destination = command[len(prefix):].strip(" .?!")
            for phrase, page in _PAGES.items():
                if destination == phrase or destination.endswith(phrase):
                    return {"action": "navigate", "page": page}

    return None


VOICE_COMMAND_HELP = (
    "Bạn có thể nói: “mở camera”, “mở OCR”, “mở phân tích ảnh”, "
    "“mở lịch sử”, “tìm cái cốc”, “đọc lại kết quả” hoặc “trợ giúp”. "
    "Các lệnh chỉ được xử lý sau khi bạn chủ động ghi âm và bấm nhận diện."
)
