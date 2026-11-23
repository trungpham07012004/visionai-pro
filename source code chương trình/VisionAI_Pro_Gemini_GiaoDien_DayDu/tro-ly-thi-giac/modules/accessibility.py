def build_spoken_result(result, mode=""):
    """Build a concise spoken version of the visual-analysis result."""
    parts = []

    if mode == "Hỗ trợ di chuyển":
        parts.append(
            "Lưu ý an toàn: đây chỉ là phân tích từ một ảnh tĩnh, không phải chỉ dẫn "
            "dẫn đường trực tiếp. Hãy tự kiểm tra lối đi và nghe ngóng môi trường xung quanh."
        )

    hazards = result.get("hazards", [])
    if hazards:
        parts.append("Cảnh báo an toàn.")
        for hazard in hazards:
            if not isinstance(hazard, dict):
                continue
            name = str(hazard.get("name", "Có nguy cơ")).strip()
            location = str(hazard.get("location", "")).strip()
            description = str(hazard.get("description", "")).strip()
            parts.append(" ".join(part for part in (name, location, description) if part))
    else:
        parts.append(
            "AI không phát hiện nguy cơ rõ ràng trong ảnh. Điều này không đảm bảo "
            "môi trường an toàn; hãy tự kiểm tra thực tế."
        )

    navigation = result.get("navigation", {})
    if isinstance(navigation, dict) and navigation.get("instruction"):
        direction = str(navigation.get("direction", "")).strip()
        distance = str(navigation.get("distance", "")).strip()
        instruction = str(navigation.get("instruction", "")).strip()
        parts.append(" ".join(part for part in (direction, distance, instruction) if part))

    summary = str(result.get("summary", "")).strip()
    if summary:
        parts.append(summary)

    text_items = result.get("text_detected", [])
    recognized_text = []
    if isinstance(text_items, list):
        for item in text_items:
            text = item.get("text", "") if isinstance(item, dict) else item
            text = str(text or "").strip()
            if text:
                recognized_text.append(text)
    if recognized_text:
        parts.append("Văn bản đọc được: " + ". ".join(recognized_text))

    tips = result.get("accessibility_tips", [])
    if isinstance(tips, list):
        parts.extend(str(tip).strip() for tip in tips if str(tip).strip())

    warning = str(result.get("warning", "")).strip()
    if warning:
        parts.append("Lưu ý: " + warning)

    return " ".join(parts)[:5000]


def build_ocr_spoken_text(items):
    """Prepare recognized OCR lines in their existing reading order."""
    lines = []
    for index, item in enumerate(items if isinstance(items, list) else [], start=1):
        text = item.get("text", "") if isinstance(item, dict) else item
        text = str(text or "").strip()
        if text:
            lines.append(f"Dòng {index}. {text}")
    return " ".join(lines)[:5000]
