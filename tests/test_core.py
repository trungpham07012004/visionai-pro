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
from modules.robot_ui import _ALLOWED_STATES
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

    def test_ocr_spoken_text_preserves_line_order_and_skips_empty_lines(self):
        self.assertEqual(
            accessibility.build_ocr_spoken_text(
                [{"text": "Dòng đầu"}, {"text": " "}, "Dòng cuối"]
            ),
            "Dòng 1. Dòng đầu Dòng 3. Dòng cuối",
        )

    def test_robot_supports_additional_accessible_emotions(self):
        self.assertTrue({"excited", "empathetic", "reassuring"}.issubset(_ALLOWED_STATES))

    def test_voice_commands_parse_navigation_search_and_replay(self):
        self.assertEqual(
            parse_voice_command("Mở hỗ trợ di chuyển"),
            {"action": "navigate", "page": "🧭 Hỗ trợ di chuyển"},
        )
        self.assertEqual(
            parse_voice_command("Tìm cái cốc màu xanh"),
            {"action": "find_object", "target": "cái cốc màu xanh"},
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

    def test_text_to_speech_uses_requested_edge_voice_without_mutating_default(self):
        default_voice = speech.EDGE_VOICE
        with patch.object(speech, "_edge_tts", return_value="audio.mp3") as edge_tts:
            path = speech.text_to_speech("Xin chào", voice="vi-VN-NamMinhNeural")

        self.assertEqual(path, "audio.mp3")
        edge_tts.assert_called_once_with("Xin chào", "vi-VN-NamMinhNeural")
        self.assertEqual(speech.EDGE_VOICE, default_voice)


if __name__ == "__main__":
    unittest.main()
