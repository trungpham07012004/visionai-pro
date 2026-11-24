import base64
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image
from modules import accessibility, ai_vision, speech, utils
from modules.ai_vision import _vision_instruction
from modules.voice_commands import parse_voice_command


class CoreTests(unittest.TestCase):
    def test_image_normalization_returns_jpeg_data_url(self):
        buf = BytesIO()
        Image.new("RGB", (32, 24), (20, 100, 180)).save(buf, format="PNG")
        url = utils.image_to_data_url(buf.getvalue(), "image/png")
        self.assertTrue(url.startswith("data:image/jpeg;base64,"))

    def test_invalid_image_is_rejected(self):
        with self.assertRaises(ValueError):
            utils.image_to_data_url(b"not an image")

    def test_empty_image_is_rejected(self):
        with self.assertRaises(ValueError):
            utils.image_to_data_url(b"")

    def test_history_is_bounded_and_valid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "history.json"
            with patch.object(utils, "HISTORY_FILE", target):
                for i in range(105):
                    utils.save_history({"summary": f"item-{i}"})
                data = json.loads(target.read_text(encoding="utf-8"))
                self.assertEqual(len(data), 100)
                self.assertEqual(data[0]["summary"], "item-104")

    def test_vision_assistant_sends_screen_context_and_conversation_to_gemini(self):
        captured = {}

        class FakeModels:
            def generate_content(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(text="Mình có thể hướng dẫn bạn.")

        fake_client = SimpleNamespace(models=FakeModels())

        def fake_fallback(make_request):
            return make_request(fake_client, "test-model"), "test-model"

        with patch.object(ai_vision, "_call_with_fallback", side_effect=fake_fallback):
            answer = ai_vision.ask_vision_assistant(
                "Làm sao đọc chữ?",
                "Đang ở màn hình OCR.",
                [{"role": "user", "content": "Xin chào"}],
            )

        self.assertEqual(answer, "Mình có thể hướng dẫn bạn.")
        prompt = captured["contents"][0]
        self.assertIn("Đang ở màn hình OCR", prompt)
        self.assertIn("Xin chào", prompt)
        self.assertIn("Làm sao đọc chữ?", prompt)
        self.assertIn("Vision", captured["config"].system_instruction)

    def test_vision_assistant_rejects_empty_question_before_gemini_call(self):
        with patch.object(ai_vision, "_call_with_fallback") as gemini:
            with self.assertRaisesRegex(ValueError, "nhập câu hỏi"):
                ai_vision.ask_vision_assistant("  ", "Trang chính")
        gemini.assert_not_called()

    def test_vision_assistant_uses_selected_image_as_gemini_input(self):
        captured = {}

        class FakeModels:
            def generate_content(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(text="Mình thấy một khung cảnh.")

        fake_client = SimpleNamespace(models=FakeModels())
        data_url = "data:image/png;base64," + base64.b64encode(b"image-bytes").decode("ascii")

        with patch.object(
            ai_vision,
            "_call_with_fallback",
            side_effect=lambda make_request: (make_request(fake_client, "test-model"), "test-model"),
        ):
            ai_vision.ask_vision_assistant(
                "Trong ảnh có gì?",
                "Đang hỏi đáp theo ảnh.",
                image_data_url=data_url,
            )

        self.assertEqual(len(captured["contents"]), 2)

    def test_image_answer_formats_all_objects_with_details(self):
        response = {
            "summary": "Tranh câu đố có nhiều đồ vật ẩn.",
            "objects": [
                {
                    "name": f"Vật {index}",
                    "location": "Phía trên bên trái",
                    "description": "Nằm khuất một phần sau chiếc khăn.",
                    "confidence": 0.8,
                }
                for index in range(1, 22)
            ],
        }

        answer = ai_vision._format_image_answer(json.dumps(response, ensure_ascii=False))

        numbered_items = [line for line in answer.splitlines() if line[:1].isdigit() and ". " in line]
        self.assertEqual(len(numbered_items), 21)
        self.assertIn("21. Vật 21", answer)
        self.assertIn("Vị trí tương đối: Phía trên bên trái", answer)
        self.assertIn("Dấu hiệu nhận biết: Nằm khuất một phần sau chiếc khăn.", answer)
        self.assertIn("Độ tin cậy: 80%", answer)
        self.assertNotIn('"objects"', answer)

    def test_image_question_requests_detailed_json_and_formats_it(self):
        captured = {}
        structured_answer = json.dumps(
            {
                "summary": "Có đồ vật ẩn trong tranh.",
                "objects": [
                    {
                        "name": "Chiếc ủng",
                        "location": "Góc dưới bên phải",
                        "description": "Nằm cạnh người tuyết đội mũ sọc.",
                        "confidence": "Cao",
                    }
                ],
            },
            ensure_ascii=False,
        )

        class FakeModels:
            def generate_content(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(text=structured_answer)

        fake_client = SimpleNamespace(models=FakeModels())

        def fake_fallback(make_request):
            return make_request(fake_client, "gemini-test"), "gemini-test"

        data_url = "data:image/png;base64," + base64.b64encode(b"image-bytes").decode("ascii")
        with patch.object(ai_vision, "_call_with_fallback", side_effect=fake_fallback):
            answer = ai_vision.ask_about_image(data_url, "Tìm 21 đồ vật ẩn và liệt kê")

        self.assertEqual(captured["config"].response_mime_type, "application/json")
        self.assertIn("rà lần lượt từ trên xuống dưới", captured["contents"][0])
        self.assertIn("Không lặp vật để đạt số lượng", captured["config"].system_instruction)
        self.assertIn("1. Chiếc ủng", answer)
        self.assertIn("Vị trí tương đối: Góc dưới bên phải", answer)
        self.assertIn("Dấu hiệu nhận biết: Nằm cạnh người tuyết đội mũ sọc.", answer)
        self.assertIn("Độ tin cậy: Cao", answer)

    def test_gemini_model_order_keeps_custom_priority_and_adds_defaults(self):
        with patch.dict("os.environ", {"GEMINI_MODELS": "gemini-3.6-flash"}):
            models = ai_vision.get_gemini_models()

        self.assertEqual(models[0], "gemini-3.6-flash")
        self.assertIn("gemini-3.1-flash-lite", models)
        self.assertEqual(len(models), len(set(models)))
        self.assertTrue(all(model.startswith("gemini-") for model in models))

    def test_gemini_model_order_rejects_non_gemini_provider(self):
        with patch.dict("os.environ", {"GEMINI_MODELS": "gpt-4o"}):
            with self.assertRaisesRegex(ValueError, "chỉ được chứa mã model Gemini"):
                ai_vision.get_gemini_models()

    def test_gemini_fallback_switches_models_on_rate_limit(self):
        class RateLimitError(Exception):
            status_code = 429

        attempted = []

        def request(_client, model):
            attempted.append(model)
            if model == "gemini-3.8-flash":
                raise RateLimitError()
            return "ok"

        with patch.object(ai_vision, "_client", return_value=object()), patch.object(
            ai_vision, "get_gemini_models",
            return_value=["gemini-3.8-flash", "gemini-3.6-flash"],
        ):
            response, model = ai_vision._call_with_fallback(request)

        self.assertEqual((response, model), ("ok", "gemini-3.6-flash"))
        self.assertEqual(attempted, ["gemini-3.8-flash", "gemini-3.6-flash"])

    def test_gemini_fallback_retries_server_error_once(self):
        class ServerError(Exception):
            status_code = 503
            response = SimpleNamespace(headers={"Retry-After": "0"})

        attempts = 0

        def request(_client, _model):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise ServerError()
            return "ok"

        with patch.object(ai_vision, "_client", return_value=object()), patch.object(
            ai_vision, "get_gemini_models", return_value=["gemini-3.8-flash"]
        ), patch.object(ai_vision.time, "sleep") as sleep:
            response, model = ai_vision._call_with_fallback(request)

        self.assertEqual((response, model), ("ok", "gemini-3.8-flash"))
        self.assertEqual(attempts, 2)
        sleep.assert_called_once_with(0.0)

    def test_spoken_mobility_result_includes_caution_and_navigation(self):
        speech = accessibility.build_spoken_result(
            {
                "summary": "Có lối đi phía trước.",
                "hazards": [],
                "navigation": {
                    "direction": "Phía trước",
                    "distance": "Gần",
                    "instruction": "Kiểm tra mặt đường trước khi bước.",
                },
            },
            mode="Hỗ trợ di chuyển",
        )

        self.assertIn("ảnh tĩnh", speech)
        self.assertIn("không đảm bảo môi trường an toàn", speech)
        self.assertIn("Kiểm tra mặt đường", speech)

    def test_spoken_result_includes_recognized_text_and_hazards(self):
        speech = accessibility.build_spoken_result(
            {
                "summary": "Có một lối đi.",
                "hazards": [
                    {"name": "Bậc thềm", "location": "Phía trước", "description": "Thấp."}
                ],
                "navigation": {},
                "text_detected": [{"text": "Lối ra", "location": "Cửa"}],
                "accessibility_tips": ["Đi chậm."],
                "warning": "Ảnh hơi tối.",
            }
        )

        self.assertIn("Bậc thềm Phía trước Thấp.", speech)
        self.assertIn("Văn bản đọc được: Lối ra", speech)
        self.assertIn("Đi chậm.", speech)
        self.assertIn("Ảnh hơi tối.", speech)

    def test_ocr_spoken_text_keeps_line_order_and_skips_blanks(self):
        answer = accessibility.build_ocr_spoken_text(
            [{"text": "Dòng đầu"}, {"text": " "}, "Dòng cuối"]
        )

        self.assertEqual(answer, "Dòng 1. Dòng đầu Dòng 3. Dòng cuối")

    def test_voice_commands_parse_navigation_search_and_replay(self):
        self.assertEqual(
            parse_voice_command("Mở hỗ trợ di chuyển"),
            {"action": "navigate", "page": "🧭 Hỗ trợ di chuyển"},
        )
        self.assertEqual(
            parse_voice_command("Tìm cái cốc màu xanh"),
            {"action": "find_object", "target": "cai coc mau xanh"},
        )
        self.assertEqual(parse_voice_command("Đọc lại kết quả"), {"action": "replay"})
        self.assertIsNone(parse_voice_command("Trong ảnh có phải cửa ra vào không?"))

    def test_scene_style_adds_requested_visual_description_guidance(self):
        prompt = _vision_instruction("Mô tả toàn cảnh", "Vừa", "safety")

        self.assertIn("Ưu tiên cảnh báo", prompt)
        self.assertIn("ảnh tĩnh", prompt.lower())
        self.assertIn("không kết luận lối đi an toàn", prompt)

    def test_favorite_update_persists_without_changing_history_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "history.json"
            with patch.object(utils, "HISTORY_FILE", target):
                item = {
                    "time": "03/11/2026 10:00:00",
                    "mode": "OCR",
                    "summary": "Lối ra",
                    "confidence": "90%",
                }
                utils.save_history(item)
                item_key = utils.history_item_key(utils.load_history()[0])
                utils.set_history_favorite(item_key, True)

                saved = utils.load_history()[0]
                self.assertTrue(saved["favorite"])
                self.assertEqual(utils.history_item_key(saved), item_key)
                utils.set_history_favorite(item_key, False)
                self.assertFalse(utils.load_history()[0]["favorite"])

    def test_transcribe_audio_uses_supported_google_recognition_arguments(self):
        class FakeAudioFile:
            def __init__(self, path):
                self.path = path

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class FakeRecognizer:
            def record(self, source):
                return "recorded audio"

            def recognize_google(self, audio, language):
                self.audio = audio
                self.language = language
                return "Xin chào Vision"

        recognizer = FakeRecognizer()
        fake_sr = SimpleNamespace(Recognizer=lambda: recognizer, AudioFile=FakeAudioFile)
        with patch.dict("sys.modules", {"speech_recognition": fake_sr}):
            answer = speech.transcribe_audio(BytesIO(b"wav audio"))

        self.assertEqual(answer, "Xin chào Vision")
        self.assertEqual(recognizer.language, speech.STT_LANGUAGE)


if __name__ == "__main__":
    unittest.main()
