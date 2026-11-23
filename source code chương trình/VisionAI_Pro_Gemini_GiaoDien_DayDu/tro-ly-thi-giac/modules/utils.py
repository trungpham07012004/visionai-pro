import base64
import json
import os
import tempfile
import hashlib
import uuid
from io import BytesIO
from PIL import Image, ImageOps
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY_FILE = ROOT / "data" / "history.json"


def image_to_data_url(data, mime="image/jpeg"):
    """Validate and normalize an uploaded image before sending it to Gemini."""
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise ValueError("Tệp ảnh rỗng hoặc không hợp lệ.")
    # Avoid excessive memory/API payloads before Pillow decodes the image.
    if len(data) > 15 * 1024 * 1024:
        raise ValueError("Ảnh lớn hơn 15 MB. Hãy chọn ảnh nhỏ hơn để xử lý ổn định.")
    try:
        with Image.open(BytesIO(data)) as source:
            source.verify()
        with Image.open(BytesIO(data)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=88, optimize=True)
            normalized = buffer.getvalue()
    except Exception as exc:
        raise ValueError("Không đọc được ảnh. Hãy thử tệp JPG, PNG hoặc WebP hợp lệ.") from exc
    encoded = base64.b64encode(normalized).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def clean_text(text):
    return " ".join(str(text or "").split())


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)][:100]
    except Exception:
        return []


def save_history(item):
    """Write a bounded local history atomically to reduce corruption on interruption."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history = load_history()
    # Keep only JSON-compatible records and avoid unbounded text fields.
    safe_item = dict(item or {})
    safe_item.setdefault("id", uuid.uuid4().hex)
    for field in ("summary", "text", "mode", "confidence", "time"):
        if field in safe_item:
            safe_item[field] = str(safe_item[field] or "")[:12000]
    history.insert(0, safe_item)
    _write_history(history[:100])


def _write_history(history):
    payload = json.dumps(history[:100], ensure_ascii=False, indent=2)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=HISTORY_FILE.parent,
            prefix="history_", suffix=".tmp", delete=False
        ) as temp:
            temp.write(payload)
            temp.flush()
            os.fsync(temp.fileno())
            temp_path = Path(temp.name)
        temp_path.replace(HISTORY_FILE)
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def history_item_key(item):
    """Stable key for toggling favorites, including legacy history entries."""
    record_id = item.get("id")
    if record_id:
        return str(record_id)
    fields = ("time", "mode", "summary", "confidence")
    identity = "\0".join(str(item.get(field, "")) for field in fields)
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def set_history_favorite(item_key, favorite):
    history = load_history()
    for item in history:
        if history_item_key(item) == item_key:
            item["favorite"] = bool(favorite)
            _write_history(history)
            return
    raise ValueError("Không tìm thấy mục lịch sử cần cập nhật.")


def export_report(result, mode="Phân tích hình ảnh"):
    lines = [
        "TRỢ LÝ THỊ GIÁC AI - BÁO CÁO PHÂN TÍCH",
        f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Chế độ: {mode}",
        "",
        f"MÔ TẢ: {result.get('summary', '')}",
        f"ĐỘ TIN CẬY: {result.get('confidence', '')}",
        f"BỐI CẢNH: {result.get('scene', '')}",
        "",
        "VẬT THỂ:",
    ]
    for obj in result.get("objects", []):
        lines.append(f"- {obj.get('name', '')} | {obj.get('location', '')} | {obj.get('description', '')}")
    lines += ["", "CẢNH BÁO:"]
    for h in result.get("hazards", []):
        lines.append(f"- {h.get('name', '')} | {h.get('severity', '')} | {h.get('location', '')} | {h.get('description', '')}")
    lines += ["", "OCR:"]
    for item in result.get("text_detected", []):
        if isinstance(item, dict):
            lines.append(f"- {item.get('text', '')} | {item.get('location', 'Không xác định')} | {item.get('confidence', 'Không xác định')}")
        elif str(item).strip():
            lines.append(f"- {item}")
    money = result.get("money_detected", {})
    if money.get("detected"):
        lines.append(f"TIỀN: {money.get('denomination', '')} ({money.get('confidence', '')})")
    lines += ["", "HƯỚNG DẪN:"]
    for tip in result.get("accessibility_tips", []):
        lines.append(f"- {tip}")
    nav = result.get("navigation", {})
    if nav.get("instruction"):
        lines += ["", f"ĐIỀU HƯỚNG: {nav.get('instruction')}"]
    if result.get("warning"):
        lines += ["", f"LƯU Ý: {result['warning']}"]
    return "\n".join(lines)


def clear_history():
    """Delete locally stored analysis history."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text("[]", encoding="utf-8")
