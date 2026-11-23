import asyncio
import os
import tempfile

# TTS miễn phí: ưu tiên Edge TTS (giọng tự nhiên, có tiếng Việt),
# nếu không dùng được thì fallback sang pyttsx3 (offline, dùng voice Windows).
EDGE_VOICE = os.getenv("EDGE_TTS_VOICE", "vi-VN-HoaiMyNeural")
EDGE_RATE = os.getenv("EDGE_TTS_RATE", "+0%")
EDGE_PITCH = os.getenv("EDGE_TTS_PITCH", "+0Hz")

# STT dùng SpeechRecognition/Google Web Speech để nhận dạng câu hỏi.
# STT miễn phí: SpeechRecognition + Google Web Speech endpoint.
# Không dùng OpenAI API nên không cần credit OpenAI cho nhận dạng giọng nói.
STT_LANGUAGE = os.getenv("STT_LANGUAGE", "vi-VN")


async def _edge_save(text, path, voice):
    import edge_tts
    communicate = edge_tts.Communicate(text=text[:5000], voice=voice, rate=EDGE_RATE, pitch=EDGE_PITCH)
    await communicate.save(path)


def _edge_tts(text, voice):
    path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    try:
        asyncio.run(_edge_save(text, path, voice))
        return path
    except Exception:
        try:
            os.remove(path)
        except OSError:
            pass
        raise


def _windows_tts(text, preferred_voice=None):
    import pyttsx3
    path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    engine = pyttsx3.init("sapi5")
    engine.setProperty("rate", 165)
    voices = engine.getProperty("voices") or []
    selected = None
    preferred = (preferred_voice or EDGE_VOICE or "").lower()
    # Match Vietnamese voices deliberately; the old substring "an" could
    # accidentally select an unrelated English voice.
    tokens = ["hoaimy", "hoai my"] if "hoaimy" in preferred else ["namminh", "nam minh"] if "namminh" in preferred else ["vietnam", "vietnamese", "vi-vn"]
    for voice in voices:
        name = str(getattr(voice, "name", "")).lower()
        voice_id = str(getattr(voice, "id", "")).lower()
        blob = f"{name} {voice_id}"
        if any(token in blob for token in tokens):
            selected = getattr(voice, "id", None)
            break
    if selected:
        engine.setProperty("voice", selected)
    engine.save_to_file(text[:5000], path)
    engine.runAndWait()
    engine.stop()
    return path


def text_to_speech(text, voice=None):
    """TTS miễn phí: Edge TTS, fallback Windows TTS. Không gọi OpenAI."""
    text = (text or "").strip()
    if not text:
        return None
    selected_voice = voice or EDGE_VOICE
    try:
        return _edge_tts(text, selected_voice)
    except Exception as edge_error:
        try:
            return _windows_tts(text, preferred_voice=selected_voice)
        except Exception as local_error:
            raise RuntimeError(
                "Không tạo được giọng nói miễn phí. "
                f"Edge TTS: {edge_error}; Windows TTS: {local_error}"
            ) from local_error


def transcribe_audio(audio_file):
    """STT miễn phí, không dùng OpenAI credit. Cần Internet."""
    if not audio_file:
        return ""

    import speech_recognition as sr

    suffix = ".wav"
    name = getattr(audio_file, "name", "")
    if "." in name:
        suffix = "." + name.rsplit(".", 1)[-1]

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        data = audio_file.getvalue() if hasattr(audio_file, "getvalue") else audio_file.read()
        if not data:
            raise RuntimeError("Bản ghi âm đang trống. Hãy ghi âm lại rồi thử lần nữa.")
        if len(data) > 15 * 1024 * 1024:
            raise RuntimeError("Bản ghi âm lớn hơn 15 MB. Hãy ghi câu hỏi ngắn hơn.")
        temp.write(data)
        temp.close()

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp.name) as source:
            audio = recognizer.record(source)

        try:
             return recognizer.recognize_google(audio, language=STT_LANGUAGE).strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            raise RuntimeError(f"Không kết nối được dịch vụ nhận dạng giọng nói miễn phí: {exc}")
    finally:
        try:
            os.remove(temp.name)
        except OSError:
            pass
