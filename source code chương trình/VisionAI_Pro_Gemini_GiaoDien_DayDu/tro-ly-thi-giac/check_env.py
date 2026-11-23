from pathlib import Path
import importlib.util
import os
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

print("VisionAI Pro - kiem tra moi truong")
print("Python:", sys.version.split()[0])
print("File .env:", "CO" if (ROOT / ".env").is_file() else "CHUA CO")
print("GEMINI_API_KEY:", "DA CAU HINH" if os.getenv("GEMINI_API_KEY", "").strip() else "CHUA CAU HINH")
models = os.getenv("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite")
print("Gemini models:", ", ".join(x.strip() for x in models.split(",") if x.strip()))
for package, module in [("streamlit", "streamlit"), ("google-genai", "google.genai"), ("Pillow", "PIL"), ("edge-tts", "edge_tts"), ("SpeechRecognition", "speech_recognition"), ("pytesseract", "pytesseract")]:
    print(f"{package}:", "OK" if importlib.util.find_spec(module) else "CHUA CAI")
print("Luu y: kiem tra nay khong goi Gemini; vao Cai dat trong ung dung de thu ket noi API.")
