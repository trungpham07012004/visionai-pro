import os
import re
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def _find_tesseract():
    try:
        import pytesseract
        found = pytesseract.pytesseract.tesseract_cmd
        if found and Path(found).exists():
            return found
    except Exception:
        pass
    candidates = [
        os.getenv("TESSERACT_CMD", ""),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for p in candidates:
        if p and Path(p).exists():
            return p
    return "tesseract"


def _prepare_variants(image):
    image = image.convert("RGB")
    scale = max(2, min(4, 1800 // max(1, max(image.size))))
    if scale > 1:
        image = image.resize((image.width * scale, image.height * scale))
    gray = ImageOps.grayscale(image)
    gray = ImageEnhance.Contrast(gray).enhance(1.8)
    gray = gray.filter(ImageFilter.SHARPEN)
    bw = gray.point(lambda p: 255 if p > 155 else 0)
    return [gray, bw]


def _clean_lines(text):
    lines = []
    for line in (text or "").splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) >= 2 and line not in lines:
            lines.append(line)
    return lines


def _confidence_text(value):
    try:
        v = float(value)
        return f"{max(0, min(100, v)):.0f}%"
    except Exception:
        return "Không xác định"



def local_ocr(image_or_bytes):
    """OCR cục bộ, giữ thứ tự dòng và trả kết quả ổn định."""
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("Chưa cài pytesseract. Chạy: python -m pip install -r requirements.txt") from exc

    pytesseract.pytesseract.tesseract_cmd = _find_tesseract()
    try:
        langs = pytesseract.get_languages(config="")
    except Exception as exc:
        raise RuntimeError(
            "Không tìm thấy Tesseract OCR. Hãy cài Tesseract và gói ngôn ngữ tiếng Việt, "
            "hoặc chạy setup_ocr.ps1."
        ) from exc

    available = []
    if "vie" in langs:
        available.append("vie")
    if "eng" in langs:
        available.append("eng")
    if not available:
        raise RuntimeError("Tesseract chưa có dữ liệu ngôn ngữ vie/eng. Chạy setup_ocr.ps1.")
    lang = "+".join(available)

    if isinstance(image_or_bytes, Image.Image):
        image = image_or_bytes.copy()
    else:
        import io
        try:
            image = Image.open(io.BytesIO(image_or_bytes))
            image.load()
        except Exception as exc:
            raise RuntimeError("Tệp ảnh không hợp lệ hoặc định dạng không được hỗ trợ.") from exc

    # EXIF transpose xử lý ảnh chụp điện thoại bị xoay; giới hạn kích thước để tránh quá tải RAM.
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((2600, 2600), Image.Resampling.LANCZOS)
    variants = _prepare_variants(image)
    candidates = []

    for variant in variants:
        for psm in (6, 11):
            try:
                data = pytesseract.image_to_data(
                    variant, lang=lang, config=f"--oem 3 --psm {psm}",
                    output_type=pytesseract.Output.DICT, timeout=25
                )
            except Exception:
                continue

            groups = {}
            texts = data.get("text", [])
            for i, raw_text in enumerate(texts):
                word = re.sub(r"\s+", " ", str(raw_text)).strip()
                try:
                    conf = float(data.get("conf", ["-1"])[i])
                except (ValueError, TypeError, IndexError):
                    conf = -1
                if not word or conf < 12:
                    continue
                key = tuple(data.get(k, [0] * len(texts))[i] for k in
                            ("page_num", "block_num", "par_num", "line_num"))
                group = groups.setdefault(key, {"words": [], "confs": []})
                group["words"].append(word)
                group["confs"].append(conf)

            lines = []
            for group in groups.values():
                line = " ".join(group["words"]).strip()
                if not line:
                    continue
                confidence = sum(group["confs"]) / len(group["confs"])
                lines.append({
                    "text": line,
                    "location": "trong ảnh",
                    "confidence": f"{max(0, min(100, confidence)):.0f}%"
                })
            score = sum(float(x["confidence"].rstrip("%")) for x in lines) / max(1, len(lines))
            candidates.append((len(" ".join(x["text"] for x in lines)), score, lines))

    if not candidates:
        return []
    # Chọn một bản nhận diện tốt nhất; không ghép các biến thể gây lặp chữ.
    candidates.sort(key=lambda c: (min(c[0], 5000) * (0.35 + c[1] / 100), c[1]), reverse=True)
    best = candidates[0][2]

    # Loại dòng trùng lặp nhưng giữ nguyên thứ tự đọc của ảnh.
    cleaned, seen = [], set()
    for item in best:
        normalized = re.sub(r"\W+", "", item["text"].lower(), flags=re.UNICODE)
        if len(normalized) < 2 or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(item)
    return cleaned


def build_local_result(image, mode="Đọc chữ trong ảnh (OCR)"):
    items = local_ocr(image)
    text = " ".join(x["text"] for x in items)
    money = {"detected": False, "denomination": "", "confidence": "Không xác định"}
    money_words = ["đồng", "vnd", "nghìn", "ngàn", "mệnh giá"]
    if any(w in text.lower() for w in money_words):
        money["detected"] = True
        money["denomination"] = text
        money["confidence"] = items[0]["confidence"] if items else "Không xác định"
    return {
        "summary": text if text else "Không đọc được chữ rõ ràng trong ảnh.",
        "confidence": items[0]["confidence"] if items else "Không xác định",
        "scene": "OCR cục bộ — không cần gọi API AI.",
        "objects": [],
        "accessibility_tips": ["Kết quả OCR là hỗ trợ đọc chữ, hãy kiểm tra lại các thông tin quan trọng."],
        "text_detected": items,
        "money_detected": money,
        "hazards": [],
        "navigation": {"direction": "", "distance": "", "instruction": ""},
        "warning": "OCR local không phân tích toàn cảnh/vật thể. Các chức năng thị giác nâng cao cần AI Vision hoặc mô hình local khác."
    }
