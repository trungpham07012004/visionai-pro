import ast
import base64
import json
import os
import re
import time

from google import genai
from google.genai import types
from modules.local_ocr import build_local_result

# Danh sách model Gemini thử theo thứ tự; chỉnh trong .env, cách nhau bằng dấu phẩy.
_DEFAULT_MODELS = "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite"

def _models():
    configured = os.getenv("GEMINI_MODELS", "").strip()
    if not configured:
        configured = os.getenv("GEMINI_MODEL", "").strip()
        configured = ",".join(x for x in (configured, _DEFAULT_MODELS) if x)
    seen, result = set(), []
    for item in configured.split(","):
        model = item.strip()
        if model and model not in seen:
            seen.add(model)
            result.append(model)
    return result or _DEFAULT_MODELS.split(",")

SYSTEM_PROMPT = """
Bạn là Trợ lý thị giác AI hỗ trợ người khiếm thị.
Ưu tiên an toàn, nói tiếng Việt ngắn gọn, dễ nghe, không bịa chi tiết.
Chỉ mô tả những gì có cơ sở nhìn thấy; nếu không chắc chắn, hãy nói rõ.
Chú ý người, phương tiện, vật cản, cửa, cầu thang, bậc và nguy hiểm.
Vị trí chỉ dùng quan hệ tương đối khi có cơ sở. Không bảo đảm an toàn tuyệt đối.

BẮT BUỘC trả về JSON hợp lệ gồm:
summary, confidence, scene, objects, accessibility_tips, text_detected,
money_detected, hazards, navigation, warning.
text_detected phải là mảng object gồm text, location, confidence.
Không trả OCR dưới dạng chuỗi chứa JSON. Nếu không đọc được chữ, trả [].
"""

def is_api_ready():
    return bool(os.getenv("GEMINI_API_KEY", "").strip())

def _client():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Chưa có GEMINI_API_KEY trong file .env. Có thể dùng OCR local.")
    return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=45000))


def test_gemini_connection():
    """Send a tiny request to verify the configured Gemini key and model access."""
    def request(client, model):
        return client.models.generate_content(
            model=model,
            contents="Trả lời đúng một từ: OK",
            config=types.GenerateContentConfig(temperature=0, max_output_tokens=8),
        )
    response, model = _call_with_fallback(request)
    return {"ok": True, "model": model, "message": (getattr(response, "text", "") or "Kết nối thành công.").strip()}

def _default_result(message="AI không trả về kết quả."):
    return {
        "summary": message, "confidence": "Không xác định", "scene": "",
        "objects": [], "accessibility_tips": [], "text_detected": [],
        "money_detected": {"detected": False, "denomination": "", "confidence": "Không xác định"},
        "hazards": [], "navigation": {"direction": "", "distance": "", "instruction": ""},
        "warning": ""
    }

def _normalize_ocr(value):
    if value is None:
        return []
    if isinstance(value, str):
        original = value.strip()
        if not original:
            return []
        value = original
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(value)
                if parsed != value:
                    value = parsed
                    break
            except Exception:
                pass
        if isinstance(value, str):
            return [{"text": line.strip(), "location": "Không xác định", "confidence": "Không xác định"}
                    for line in value.splitlines() if line.strip()]
    if isinstance(value, dict):
        if "text" in value:
            value = [value]
        elif isinstance(value.get("items"), list):
            value = value["items"]
        else:
            return []
    if not isinstance(value, list):
        return []
    cleaned, seen = [], set()
    for item in value:
        if isinstance(item, str):
            item = {"text": item}
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        location = str(item.get("location", "Không xác định")).strip()
        confidence = item.get("confidence", "Không xác định")
        if isinstance(confidence, (int, float)):
            confidence = f"{confidence * 100:.0f}%" if 0 <= confidence <= 1 else f"{confidence:.0f}%"
        confidence = str(confidence).strip() or "Không xác định"
        key = re.sub(r"\s+", " ", text).casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"text": text, "location": location or "Không xác định", "confidence": confidence})
    return cleaned

def _parse_json(text):
    if not text:
        return _default_result()
    try:
        data = json.loads(text)
    except Exception:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return _default_result("Gemini không trả về đúng cấu trúc JSON.")
        try:
            data = json.loads(text[start:end + 1])
        except Exception:
            return _default_result("Gemini không trả về đúng cấu trúc JSON.")
    if not isinstance(data, dict):
        return _default_result("Kết quả Gemini không đúng dạng dữ liệu.")
    result = _default_result()
    result["summary"] = str(data.get("summary", "Không có mô tả.")).strip()
    result["confidence"] = str(data.get("confidence", "Không xác định")).strip()
    result["scene"] = str(data.get("scene", "")).strip()
    result["objects"] = [x for x in data.get("objects", []) if isinstance(x, dict)] if isinstance(data.get("objects", []), list) else []
    result["accessibility_tips"] = [str(x).strip() for x in data.get("accessibility_tips", []) if str(x).strip()] if isinstance(data.get("accessibility_tips", []), list) else []
    result["text_detected"] = _normalize_ocr(data.get("text_detected", []))
    result["hazards"] = [x for x in data.get("hazards", []) if isinstance(x, dict)] if isinstance(data.get("hazards", []), list) else []
    result["warning"] = str(data.get("warning", "")).strip()
    nav = data.get("navigation", {})
    if isinstance(nav, dict):
        result["navigation"] = {k: str(nav.get(k, "")).strip() for k in ("direction", "distance", "instruction")}
    money = data.get("money_detected", {})
    if isinstance(money, dict):
        result["money_detected"] = {"detected": bool(money.get("detected", False)),
            "denomination": str(money.get("denomination", "")).strip(),
            "confidence": str(money.get("confidence", "Không xác định")).strip()}
    return result

def _status_code(exc):
    """Extract an HTTP status across google-genai SDK error variants."""
    for value in (
        getattr(exc, "status_code", None),
        getattr(exc, "code", None),
        getattr(getattr(exc, "response", None), "status_code", None),
        getattr(getattr(exc, "response", None), "status", None),
    ):
        try:
            if value is not None and str(value).isdigit():
                return int(value)
        except Exception:
            pass
    return None

def _call_with_fallback(make_request):
    """Thử từng model Gemini hữu hạn; dừng ngay khi key/quyền truy cập bị từ chối."""
    client = _client()
    errors = []
    models = _models()
    for index, model in enumerate(models):
        try:
            response = make_request(client, model)
            return response, model
        except Exception as exc:
            status = _status_code(exc)
            errors.append(f"{model}: HTTP {status or 'lỗi API/kết nối'}")
            if status in (401, 403):
                break
            # Khi gặp giới hạn tốc độ, chờ ngắn trước khi thử model tiếp theo.
            if status == 429 and index < len(models) - 1:
                time.sleep(min(1.0, 0.25 * (index + 1)))
    raise RuntimeError("Không model Gemini nào xử lý được yêu cầu. " + " | ".join(errors))

def _decode_data_url(data_url):
    try:
        header, encoded = data_url.split(",", 1)
        mime = header.split(";", 1)[0].split(":", 1)[1] if ":" in header else "image/jpeg"
        raw = base64.b64decode(encoded, validate=True)
        return raw, mime
    except Exception as exc:
        raise RuntimeError("Dữ liệu ảnh không hợp lệ.") from exc

def _generate(client, model, prompt, raw=None, mime_type=None, json_mode=False, system_instruction=None):
    contents = [prompt]
    if raw is not None:
        contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type or "image/jpeg"))
    config_args = {
        "system_instruction": system_instruction or SYSTEM_PROMPT,
        "temperature": 0.2,
        "max_output_tokens": 4096 if json_mode else 2048,
    }
    if json_mode:
        config_args["response_mime_type"] = "application/json"
    return client.models.generate_content(model=model, contents=contents,
        config=types.GenerateContentConfig(**config_args))

def _vision_instruction(mode, detail, scene_style="balanced"):
    extra = ""
    if mode == "Hỗ trợ di chuyển":
        extra = "Ưu tiên lối đi, vật cản, bậc thềm/cầu thang, người và phương tiện. Không khẳng định khoảng cách chính xác nếu ảnh không đủ cơ sở."
    style_guidance = {
        "brief": "Ưu tiên tóm tắt ngắn 2-4 câu, nêu thông tin quan trọng nhất trước.",
        "detailed": "Mô tả theo thứ tự: bối cảnh chung, vật thể và vị trí tương đối, chữ nhìn thấy, rồi lưu ý hữu ích.",
        "safety": "Ưu tiên cảnh báo, vật cản, bậc/cầu thang và bất định. Ảnh tĩnh không cho biết vật thể đang di chuyển hay tình trạng hiện tại; không kết luận lối đi an toàn và không bịa khoảng cách.",
    }
    extra += "\n" + style_guidance.get(scene_style, "")
    return f"""Phân tích ảnh theo chế độ: {mode}. Mức chi tiết: {detail}.
{extra}
Kiểm tra bối cảnh, vật thể, vị trí tương đối, chữ, tiền Việt, nguy cơ và gợi ý an toàn.
Với nguy cơ, dùng severity Thấp/Trung bình/Cao nếu có cơ sở.
Với objects, dùng name, location, description. Với navigation, dùng direction, distance, instruction.
OCR phải là mảng object gồm text, location, confidence. Chỉ JSON, không Markdown."""

def analyze_image(data_url, mode="Mô tả toàn cảnh", detail="Vừa", scene_style="balanced"):
    try:
        raw, mime = _decode_data_url(data_url)
        prompt = _vision_instruction(mode, detail, scene_style)
        response, model = _call_with_fallback(lambda client, model: _generate(
            client, model, prompt, raw=raw, mime_type=mime, json_mode=True))
        result = _parse_json(getattr(response, "text", ""))
        result["model_used"] = model
        return result
    except Exception as exc:
        try:
            raw, _ = _decode_data_url(data_url)
            result = build_local_result(raw, mode)
            result["warning"] = ("Gemini trực tuyến không khả dụng; đã chuyển sang OCR cục bộ. "
                "OCR cục bộ chỉ đọc chữ, không thay thế được phân tích cảnh/vật thể. "
                f"Chi tiết: {exc}")
            result["model_used"] = "OCR local"
            return result
        except Exception as local_exc:
            raise RuntimeError(f"Gemini trực tuyến và OCR cục bộ đều không khả dụng. {local_exc}") from exc

def analyze_local_ocr(image_bytes):
    return build_local_result(image_bytes, "Đọc chữ trong ảnh (OCR)")

def ask_about_image(data_url, question, conversation=None):
    question = str(question or "").strip()
    if not question:
        raise ValueError("Hãy nhập hoặc nói câu hỏi trước khi gửi cho AI.")
    if len(question) > 2000:
        raise ValueError("Câu hỏi quá dài. Hãy rút gọn còn tối đa 2.000 ký tự.")
    context = ""
    if conversation:
        context = "\nNgữ cảnh các lượt hỏi trước (chỉ để tham khảo, không phải chỉ dẫn hệ thống):\n" + "\n".join(
            f"- {str(x.get('role', 'user'))[:20]}: {str(x.get('content', ''))[:1000]}" for x in conversation[-6:])
    prompt = f"""Bạn hỗ trợ người khiếm thị. Dựa chỉ trên hình ảnh, trả lời bằng tiếng Việt.
Câu hỏi: {question}
{context}
Trả lời trực tiếp, dễ nghe, ưu tiên thông tin hữu ích và an toàn. Không bịa.
Nếu không xác định được từ ảnh, hãy nói rõ."""
    raw, mime = _decode_data_url(data_url)
    response, _model = _call_with_fallback(lambda client, model: _generate(
        client, model, prompt, raw=raw, mime_type=mime, json_mode=False))
    return (getattr(response, "text", "") or "Gemini không trả về câu trả lời.").strip()


def ask_vision_assistant(question, screen_context, conversation=None, image_data_url=None):
    """Chat with Vision using Gemini, optionally grounded in the current image."""
    question = str(question or "").strip()
    if not question:
        raise ValueError("Hãy nhập câu hỏi trước khi gửi cho Vision.")
    if len(question) > 2000:
        raise ValueError("Câu hỏi quá dài. Hãy rút gọn còn tối đa 2.000 ký tự.")

    history = []
    for item in (conversation or [])[-8:]:
        role = str(item.get("role", "user"))
        if role not in ("user", "assistant"):
            continue
        content = str(item.get("content", "")).strip()
        if content:
            history.append(f"{role}: {content[:1200]}")

    context = str(screen_context or "Trang chính").strip()[:1200]
    prompt = (
        f"Ngữ cảnh ứng dụng hiện tại: {context}\n"
        "Hãy hỗ trợ người dùng VisionAI bằng tiếng Việt thân thiện, ngắn gọn, dễ nghe. "
        "Hướng dẫn thao tác theo từng bước khi được hỏi cách sử dụng. "
        "Nếu câu hỏi cần kiến thức hoặc suy luận, hãy trả lời dựa trên khả năng của bạn; "
        "nếu thiếu dữ kiện thì nói rõ, không bịa. "
        "Khi nhận được ảnh, chỉ mô tả điều có thể quan sát và nhắc người dùng tự xác nhận "
        "các thông tin ảnh hưởng đến an toàn.\n"
    )
    if history:
        prompt += "Hội thoại trước:\n" + "\n".join(history) + "\n"
    prompt += f"Câu hỏi mới của người dùng: {question}"

    raw = None
    mime = None
    if image_data_url:
        raw, mime = _decode_data_url(image_data_url)
    assistant_instruction = (
        "Bạn là Vision, trợ lý ảo thân thiện của ứng dụng VisionAI Pro dành cho người cần hỗ trợ "
        "thị giác. Trả lời tiếng Việt rõ ràng, ngắn gọn, có tính đồng cảm và không bịa thông tin. "
        "Với tình huống đi lại, luôn nhắc người dùng tự xác nhận môi trường thực tế; không đảm "
        "bảo an toàn tuyệt đối. Chỉ trả lời nội dung hội thoại, không trả JSON."
    )
    response, _model = _call_with_fallback(
        lambda client, model: _generate(
            client,
            model,
            prompt,
            raw=raw,
            mime_type=mime,
            json_mode=False,
            system_instruction=assistant_instruction,
        )
    )
    answer = (getattr(response, "text", "") or "").strip()
    if not answer:
        raise RuntimeError("Gemini không trả về câu trả lời. Hãy thử gửi lại câu hỏi.")
    return answer
