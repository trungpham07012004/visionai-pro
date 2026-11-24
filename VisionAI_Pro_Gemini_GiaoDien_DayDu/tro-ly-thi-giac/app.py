import base64
import os
import html
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

from modules.ai_vision import (
    analyze_image,
    analyze_local_ocr,
    ask_about_image,
    ask_vision_assistant,
    get_gemini_models,
    is_api_ready,
    test_gemini_connection,
)
from modules.speech import text_to_speech, transcribe_audio
from modules.accessibility import build_spoken_result
from modules.accessibility import build_ocr_spoken_text
from modules.voice_commands import VOICE_COMMAND_HELP, parse_voice_command
from modules.robot_ui import render_dashboard_robot
from modules import utils
from modules.utils import image_to_data_url, save_history, load_history, export_report, clear_history

st.set_page_config(page_title="Trợ lý thị giác AI", page_icon="👁️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--va-accent:#6d7cff;--va-cyan:#38d9ff;--va-border:rgba(102,143,224,.22);--va-panel:rgba(5,20,48,.82)}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
h1,h2,h3{font-family:'Manrope','DM Sans',sans-serif;letter-spacing:-.035em}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 8% 0%,rgba(22,76,185,.22),transparent 36%),radial-gradient(ellipse at 95% 12%,rgba(4,156,208,.10),transparent 30%),#030b1d}
[data-testid="stHeader"]{background:rgba(3,11,29,.72)}
.block-container{max-width:1540px;padding-top:1.15rem;padding-bottom:3rem}
[data-testid="stSidebar"]{border-right:1px solid var(--va-border);background:linear-gradient(180deg,#06142f,#040d20)}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1{font-size:1.35rem}
[data-testid="stSidebar"] [data-testid="stRadio"] label{border-radius:11px;padding:.38rem .55rem;transition:background .2s ease,color .2s ease}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:rgba(57,106,210,.18);color:#85eaff}
.hero{position:relative;display:flex;align-items:center;justify-content:space-between;gap:1.5rem;overflow:hidden;padding:2.25rem 2.35rem;border-radius:28px;border:1px solid rgba(130,150,255,.3);margin-bottom:1.5rem;background:linear-gradient(120deg,rgba(67,78,190,.24),rgba(15,153,180,.13) 58%,rgba(255,255,255,.035));box-shadow:0 22px 70px rgba(25,35,85,.18);animation:rise-in .7s cubic-bezier(.2,.75,.25,1) both}
.hero:before{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 20%,rgba(255,255,255,.055) 48%,transparent 72%);transform:translateX(-100%);animation:hero-shimmer 8s ease-in-out infinite;pointer-events:none}
.hero-copy{position:relative;z-index:2;max-width:680px}
.hero h1{font-size:clamp(2rem,4vw,3.35rem);line-height:1.08;margin:.55rem 0 .65rem;font-weight:800}
.hero p{font-size:1.04rem;opacity:.86;margin:.3rem 0 0;line-height:1.65}
.hero-kicker{display:inline-flex;align-items:center;gap:.5rem;border:1px solid rgba(118,224,255,.27);background:rgba(25,190,220,.09);color:#83e9ff;border-radius:999px;padding:.38rem .72rem;font-size:.76rem;font-weight:800;letter-spacing:.11em}
.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#5cf2c2;box-shadow:0 0 0 4px rgba(92,242,194,.12);animation:pulse-dot 1.8s ease-in-out infinite}
.hero-tags{display:flex;flex-wrap:wrap;gap:.55rem;margin-top:1.2rem}
.hero-tag{font-size:.78rem;border:1px solid var(--va-border);background:rgba(255,255,255,.055);border-radius:10px;padding:.45rem .65rem;color:inherit}
.hero-art{position:relative;flex:0 0 300px;height:255px;display:grid;place-items:center;z-index:1}
.orbit{position:absolute;width:215px;height:215px;border:1px solid rgba(112,216,255,.26);border-radius:50%;animation:orbit-spin 18s linear infinite}
.orbit:before,.orbit:after{content:"";position:absolute;border:1px solid rgba(125,143,255,.22);border-radius:50%;inset:18px}
.orbit:after{inset:38px;border-style:dashed;animation:orbit-spin 22s linear infinite reverse}
.eye-glass{position:relative;width:145px;height:145px;border-radius:36px;display:grid;place-items:center;background:linear-gradient(145deg,rgba(98,117,255,.28),rgba(30,199,225,.13));border:1px solid rgba(153,220,255,.38);box-shadow:inset 0 0 35px rgba(110,180,255,.12),0 0 65px rgba(64,138,255,.18);backdrop-filter:blur(8px);animation:float-glow 5s ease-in-out infinite}
.eye-glass svg{width:94px;height:94px;filter:drop-shadow(0 0 12px rgba(81,221,255,.55))}
.scan-line{position:absolute;left:18%;right:18%;height:2px;top:32%;background:linear-gradient(90deg,transparent,#64e9ff,transparent);box-shadow:0 0 16px #49d9ff;animation:scan 3.4s ease-in-out infinite}
.robot-halo{position:absolute;width:174px;height:174px;border-radius:50%;background:radial-gradient(circle,rgba(56,217,255,.22),rgba(109,124,255,.08) 54%,transparent 72%);filter:blur(2px);animation:halo-breathe 4s ease-in-out infinite}
.robot-avatar{position:relative;width:158px;height:174px;display:flex;flex-direction:column;align-items:center;z-index:2;filter:drop-shadow(0 14px 28px rgba(38,128,255,.2));animation:robot-float 4.6s ease-in-out infinite}
.robot-antenna{position:relative;width:3px;height:19px;background:linear-gradient(#7cecff,#8d9bff);border-radius:9px;margin-bottom:-2px}
.robot-antenna span{position:absolute;top:-6px;left:-4px;width:11px;height:11px;border-radius:50%;background:#7ef3ff;box-shadow:0 0 15px #42dfff;animation:antenna-pulse 1.8s ease-in-out infinite}
.robot-ear{position:absolute;top:52px;width:14px;height:37px;border:2px solid #77eaff;background:linear-gradient(160deg,#4a6da5,#19264a);border-radius:8px;z-index:1}
.robot-ear.left{left:8px}.robot-ear.right{right:8px}
.robot-face{position:relative;width:126px;height:106px;border-radius:38px 38px 34px 34px;background:linear-gradient(145deg,#f3fbff 0%,#c5e8ff 36%,#819bd7 100%);border:2px solid rgba(185,244,255,.92);box-shadow:inset -9px -11px 22px rgba(48,70,132,.25),inset 5px 5px 16px rgba(255,255,255,.75),0 0 26px rgba(76,217,255,.23);display:flex;align-items:center;flex-direction:column;overflow:hidden}
.robot-face:before{content:"";position:absolute;top:8px;left:16px;right:16px;height:24px;border-radius:50%;background:rgba(255,255,255,.3);filter:blur(6px)}
.robot-eyes{display:flex;gap:30px;margin-top:36px;z-index:1}
.robot-eyes span{display:block;width:13px;height:19px;border-radius:50%;background:linear-gradient(#40eaff,#3672ff);box-shadow:0 0 13px rgba(35,185,255,.9);animation:robot-blink 5.2s infinite}
.robot-eyes span:nth-child(2){animation-delay:.08s}
.robot-cheeks{display:flex;gap:55px;margin-top:2px;opacity:.75}.robot-cheeks span{width:12px;height:5px;border-radius:50%;background:#79d9ff;filter:blur(1px)}
.robot-mouth{width:24px;height:8px;margin-top:5px;border-bottom:3px solid #3b70b7;border-radius:0 0 16px 16px;overflow:hidden}
.robot-mouth i{display:block;width:100%;height:100%;background:rgba(62,210,255,.12)}
.robot-neck{width:34px;height:12px;background:linear-gradient(90deg,#5b76bd,#d5f3ff,#5877bd);margin-top:-1px;border-radius:0 0 8px 8px}
.robot-shoulders{width:102px;height:30px;margin-top:-1px;border-radius:22px 22px 13px 13px;background:linear-gradient(110deg,#7d96d4,#e2f8ff 45%,#6e8bcb);border:1px solid #b1e8ff;box-shadow:inset 0 -7px 12px rgba(48,75,144,.22);display:grid;place-items:center;color:#315d9c;font-size:.7rem;font-weight:900;letter-spacing:.18em}
@keyframes robot-float{0%,100%{transform:translateY(0) rotate(-1deg)}50%{transform:translateY(-8px) rotate(1deg)}}
@keyframes halo-breathe{0%,100%{transform:scale(.9);opacity:.6}50%{transform:scale(1.12);opacity:1}}
@keyframes antenna-pulse{0%,100%{opacity:.7;box-shadow:0 0 9px #42dfff}50%{opacity:1;box-shadow:0 0 21px #42dfff}}
@keyframes robot-blink{0%,44%,48%,100%{transform:scaleY(1)}46%{transform:scaleY(.08)}}
@keyframes mouth-talk{0%,100%{height:5px;width:20px}50%{height:13px;width:16px}}
@keyframes mouth-inner{0%,100%{transform:scaleY(.15)}50%{transform:scaleY(1)}}
@media(prefers-reduced-motion:reduce){.robot-avatar,.robot-halo,.robot-antenna span,.robot-eyes span{animation:none!important}}

.float-chip{position:absolute;padding:.48rem .62rem;border-radius:11px;background:rgba(12,22,53,.72);border:1px solid rgba(139,194,255,.28);box-shadow:0 10px 25px rgba(0,0,0,.15);font-size:.73rem;backdrop-filter:blur(10px);animation:float-chip 5s ease-in-out infinite}
.chip-one{top:19px;right:0}.chip-two{bottom:18px;left:0;animation-delay:-2.2s}
@keyframes hero-shimmer{0%,65%,100%{transform:translateX(-100%)}82%{transform:translateX(100%)}}
@keyframes pulse-dot{0%,100%{opacity:1;box-shadow:0 0 0 4px rgba(92,242,194,.12)}50%{opacity:.65;box-shadow:0 0 0 7px rgba(92,242,194,.04)}}
@keyframes orbit-spin{to{transform:rotate(360deg)}}
@keyframes scan{0%,100%{top:30%;opacity:.25}50%{top:70%;opacity:1}}
@keyframes float-chip{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.card{padding:1.15rem 1.2rem;border-radius:19px;border:1px solid var(--va-border);margin:.6rem 0;background:linear-gradient(145deg,rgba(130,145,190,.09),rgba(130,145,190,.025));box-shadow:0 7px 22px rgba(15,25,60,.045);transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease;animation:rise-in .55s ease both}
.card:hover{transform:translateY(-3px);border-color:rgba(109,124,255,.48);box-shadow:0 12px 28px rgba(40,55,130,.11)}
.danger,.warning,.ok{padding:1rem 1.1rem;border-radius:17px;margin:.55rem 0;animation:rise-in .4s ease both}
.danger{border:1px solid rgba(239,68,68,.55);background:rgba(239,68,68,.07)}
.warning{border:1px solid rgba(245,158,11,.48);background:rgba(245,158,11,.07)}
.ok{border:1px solid var(--va-border);background:rgba(130,145,190,.045)}
.small{opacity:.72;font-size:.9rem}
.dashboard-title{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin:.25rem 0 1rem}
.dashboard-title h2{margin:0;font-size:1.3rem}
.dashboard-title p{margin:.25rem 0 0;color:rgba(219,232,255,.65);font-size:.88rem}
.dashboard-banner{position:relative;overflow:hidden;border:1px solid rgba(70,153,255,.42);border-radius:20px;margin:.45rem 0 1.15rem;background:#071a3a;box-shadow:0 18px 48px rgba(0,0,0,.24);animation:rise-in .65s cubic-bezier(.2,.75,.25,1) both}
.dashboard-banner:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(110deg,transparent 23%,rgba(255,255,255,.12) 48%,transparent 71%);transform:translateX(-110%);animation:hero-shimmer 9s ease-in-out infinite}
.dashboard-banner img{display:block;width:100%;height:auto;max-height:365px;object-fit:cover}
.dashboard-section-title{display:flex;align-items:center;justify-content:space-between;gap:.8rem;margin:1.15rem 0 .45rem}
.dashboard-section-title h3{margin:0;font-size:1rem}
.dashboard-panel{padding:1rem 1.05rem;border:1px solid rgba(66,130,220,.3);border-radius:17px;margin:0 0 .8rem;background:linear-gradient(145deg,rgba(8,29,65,.93),rgba(4,16,39,.94));box-shadow:0 12px 30px rgba(0,0,0,.14);animation:rise-in .55s ease both}
.dashboard-panel h3{font-size:.94rem;margin:0 0 .7rem}
.dashboard-status{display:flex;align-items:center;justify-content:space-between;gap:.6rem;font-size:.8rem}
.dashboard-status strong{color:#70edb0;font-weight:650}
.dashboard-status .live-dot{margin-right:.45rem}
.dashboard-activity{padding:.68rem 0;border-top:1px solid rgba(116,155,220,.12);font-size:.75rem;line-height:1.45}
.dashboard-activity:first-of-type{border-top:0}
.dashboard-activity span{display:block;color:rgba(217,230,255,.55);font-size:.68rem;margin-top:.18rem}
.dashboard-stat{display:flex;justify-content:space-between;gap:.7rem;padding:.44rem 0;font-size:.75rem;border-top:1px solid rgba(116,155,220,.1)}
.dashboard-stat:first-of-type{border-top:0}
.dashboard-stat b{color:#a7c7ff}
.feature-card{height:100%;padding:.88rem .82rem .55rem;border:1px solid rgba(86,134,222,.3);border-radius:16px;background:linear-gradient(145deg,rgba(10,48,105,.72),rgba(6,23,58,.92));transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease;animation:rise-in .55s ease both}
.feature-card:hover{transform:translateY(-4px);border-color:rgba(78,203,255,.65);box-shadow:0 12px 28px rgba(13,103,214,.18)}
.feature-icon{display:grid;place-items:center;width:42px;height:42px;border-radius:13px;margin-bottom:.62rem;background:linear-gradient(145deg,rgba(59,154,255,.35),rgba(72,73,239,.3));border:1px solid rgba(115,192,255,.35);font-size:1.3rem}
.feature-card h4{font-size:.84rem;margin:0 0 .35rem}
.feature-card p{min-height:2.5rem;margin:0;color:rgba(218,231,255,.63);font-size:.7rem;line-height:1.5}
.block-container [data-testid="column"]:has(.feature-card) [data-testid="stButton"]{margin-top:.45rem}
.block-container [data-testid="column"]:has(.feature-card) [data-testid="stButton"]>button{min-height:2.15rem;border-color:rgba(86,146,238,.32);background:rgba(23,61,125,.52);font-size:.73rem}
.welcome-card{padding:1rem 1.05rem;border:1px solid rgba(75,132,226,.27);border-radius:16px;background:linear-gradient(110deg,rgba(11,38,83,.78),rgba(6,21,49,.86));font-size:.82rem;line-height:1.65}
.dashboard-toolbar{display:flex;justify-content:flex-end;align-items:center;gap:.45rem;margin:-.35rem 0 .45rem}
.dashboard-hero-frame{height:100%;min-height:250px;overflow:hidden;border:1px solid rgba(40,147,255,.55);border-radius:12px;background:#061632;box-shadow:0 12px 32px rgba(0,0,0,.24)}
.feature-card{position:relative;min-height:163px;padding:.82rem .72rem .5rem;overflow:hidden;border:1px solid rgba(117,165,255,.38);border-radius:13px;background:linear-gradient(145deg,rgba(0,120,255,.72),rgba(7,40,114,.95));transition:transform .2s ease,border-color .2s ease,filter .2s ease}
.feature-card:after{content:"";position:absolute;inset:auto -12% -30% 25%;height:72px;background:radial-gradient(ellipse,rgba(83,190,255,.27),transparent 70%);pointer-events:none}
.feature-card:hover{transform:translateY(-4px);border-color:#69dfff;filter:brightness(1.12)}
.feature-card.purple{background:linear-gradient(145deg,rgba(105,37,240,.9),rgba(45,21,129,.98));border-color:rgba(175,106,255,.65)}
.feature-card.green{background:linear-gradient(145deg,rgba(0,153,95,.9),rgba(0,79,73,.98));border-color:rgba(71,231,173,.55)}
.feature-card.orange{background:linear-gradient(145deg,rgba(214,111,12,.94),rgba(126,56,11,.98));border-color:rgba(255,185,93,.6)}
.feature-card.pink{background:linear-gradient(145deg,rgba(210,24,112,.93),rgba(111,19,80,.98));border-color:rgba(255,107,185,.58)}
.feature-card .feature-icon{width:43px;height:43px;border:0;border-radius:11px;background:rgba(255,255,255,.15);font-size:1.35rem}
.feature-card h4{font-size:.82rem;margin:0 0 .34rem}
.feature-card p{min-height:2.4rem;margin:0;color:rgba(255,255,255,.8);font-size:.68rem;line-height:1.42}
.block-container [data-testid="column"]:has(.feature-card) [data-testid="stButton"]{margin-top:-2.95rem;position:relative;z-index:2}
.block-container [data-testid="column"]:has(.feature-card) [data-testid="stButton"]>button{width:34px;min-width:34px;height:34px;min-height:34px;margin-left:.05rem;padding:0;border:1px solid rgba(255,255,255,.23);border-radius:50%;background:rgba(255,255,255,.18);font-size:1rem}
.dashboard-chat{padding:.75rem .85rem .55rem;border:1px solid rgba(30,120,230,.38);border-radius:15px;background:linear-gradient(145deg,rgba(5,28,66,.96),rgba(3,17,43,.98));box-shadow:0 12px 30px rgba(0,0,0,.15)}
.dashboard-chat-heading{display:flex;align-items:center;gap:.6rem;margin-bottom:.6rem}
.dashboard-chat-avatar{display:grid;place-items:center;width:39px;height:39px;flex:0 0 39px;border:2px solid #65caff;border-radius:50%;background:radial-gradient(circle at 35% 25%,#182f6c,#050b23 70%);box-shadow:0 0 14px rgba(32,163,255,.38);font-size:1.25rem}
.dashboard-chat-title{font-size:.85rem;font-weight:700}
.dashboard-chat-online{display:inline-block;width:7px;height:7px;margin-left:.28rem;border-radius:50%;background:#20e96e;box-shadow:0 0 9px #20e96e}
.dashboard-chat-bubble{max-width:560px;margin:0 0 .6rem 44px;padding:.56rem .7rem;border:1px solid rgba(49,120,214,.22);border-radius:10px;background:rgba(13,44,91,.76);font-size:.69rem;line-height:1.45}
.dashboard-prompt-label{margin:.5rem 0 .25rem;color:rgba(203,223,255,.64);font-size:.67rem}
.dashboard-prompt-button [data-testid="stButton"]>button{min-height:1.85rem;padding:.2rem .48rem;border:1px solid rgba(50,121,221,.4);border-radius:999px;background:rgba(8,38,84,.72);font-size:.63rem}
.dashboard-chat-form [data-testid="stTextInput"] input{min-height:2.3rem;border:1px solid rgba(49,126,225,.58);border-radius:9px;background:rgba(9,34,76,.8);font-size:.72rem}
.dashboard-chat-form [data-testid="stFormSubmitButton"] button{min-height:2.3rem;border-radius:9px;background:linear-gradient(120deg,#1765e8,#6848f4)}
.sidebar-status{display:flex;align-items:center;gap:.55rem;padding:.62rem .7rem;border:1px solid rgba(27,217,109,.22);border-radius:10px;background:rgba(13,101,63,.18);color:#86eeb5;font-size:.74rem}
.sidebar-status i{width:8px;height:8px;border-radius:50%;background:#20df72;box-shadow:0 0 10px #20df72}
.sidebar-brand{padding:.8rem .35rem .3rem}
.sidebar-brand strong{display:block;font-family:'Manrope',sans-serif;font-size:1.12rem}
.sidebar-brand span{color:rgba(215,230,255,.65);font-size:.72rem}
[data-testid="stSidebar"] [data-testid="stRadio"] label{font-size:.82rem}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stRadioOption"]:has(input:checked){background:linear-gradient(100deg,rgba(0,153,255,.8),rgba(44,61,232,.88));box-shadow:0 5px 16px rgba(20,119,255,.22)}
[data-testid="stMetric"]{padding:1rem;border:1px solid var(--va-border);border-radius:17px;background:rgba(130,145,190,.055);transition:transform .2s ease}
[data-testid="stMetric"]:hover{transform:translateY(-2px)}
.stButton>button,.stDownloadButton>button{border-radius:13px;min-height:2.8rem;font-weight:650;transition:transform .18s ease,box-shadow .18s ease}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(90,105,240,.18)}
[data-testid="stFileUploader"]{border:1px dashed rgba(109,124,255,.55);border-radius:18px;padding:.35rem;background:rgba(109,124,255,.035)}
[data-testid="stImage"] img{border-radius:18px}
[data-testid="stExpander"]{border-radius:14px;border-color:var(--va-border)}
@keyframes rise-in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes float-glow{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-18px,18px) scale(1.08)}}
@media(max-width:760px){.hero{padding:1.5rem;}.hero-art{flex-basis:145px;height:150px;transform:scale(.72);transform-origin:center right;margin-left:-2rem}.hero h1{font-size:2rem}.hero p{font-size:.95rem}}
@media(max-width:540px){.hero-art{display:none}.hero{padding:1.35rem}.hero-tags{gap:.35rem}.hero-tag{font-size:.7rem}}
@media(max-width:1100px){
  [data-testid="stSidebar"]{width:16rem!important;min-width:16rem!important}
  .block-container [data-testid="stHorizontalBlock"]:has(.dashboard-section-title){flex-wrap:wrap}
  .block-container [data-testid="stHorizontalBlock"]:has(.dashboard-section-title)>[data-testid="stColumn"]{flex:1 1 100%!important;min-width:100%!important}
  .block-container [data-testid="stHorizontalBlock"]:has(.feature-card):not(:has(.dashboard-section-title)){flex-wrap:wrap;gap:.45rem}
  .block-container [data-testid="stHorizontalBlock"]:has(.feature-card):not(:has(.dashboard-section-title))>[data-testid="stColumn"]{flex:1 1 145px!important;min-width:145px!important}
}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
/* Keep the dark dashboard calm, legible, and responsive. */
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{font-size:.96rem;line-height:1.62}
[data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] p{font-size:.92rem}
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"] button{font-size:.91rem;min-height:2.9rem}
.feature-card h4{font-size:.94rem}
.feature-card p{font-size:.82rem;line-height:1.5}
.dashboard-chat-bubble,.dashboard-prompt-label,.dashboard-prompt-button [data-testid="stButton"]>button{font-size:.78rem}
.dashboard-chat-form [data-testid="stTextInput"] input{font-size:.9rem}
.sidebar-status{font-size:.84rem;line-height:1.55}
.card,.danger,.warning,.ok{line-height:1.65}
@media(max-width:700px){.block-container{padding-left:1rem;padding-right:1rem}.feature-card{min-height:145px}}
</style>
""", unsafe_allow_html=True)

DEFAULT_SETTINGS = {"voice": True, "detail": "Vừa", "mode": "Hỗ trợ người khiếm thị", "tts_voice": "vi-VN-HoaiMyNeural"}
for key, value in DEFAULT_SETTINGS.items():
    st.session_state.setdefault(key, value)
st.session_state.setdefault("accessible_mode", True)
st.session_state.setdefault("scene_style", "balanced")
st.session_state.setdefault("object_finder_question", "")
st.session_state.setdefault("object_finder_answer", "")
st.session_state.setdefault("object_finder_notice", "")
st.session_state.setdefault("last_history_id", None)
if st.session_state.accessible_mode:
    st.markdown(
        """
        <style>
        body:has(.va-accessibility-mode) [data-testid="stMarkdownContainer"] p,
        body:has(.va-accessibility-mode) [data-testid="stMarkdownContainer"] li {
          font-size: 1.08rem !important;
          line-height: 1.7 !important;
        }
        body:has(.va-accessibility-mode) [data-testid="stWidgetLabel"],
        body:has(.va-accessibility-mode) [data-testid="stWidgetLabel"] p,
        body:has(.va-accessibility-mode) [data-testid="stSidebar"] [data-testid="stRadio"] label {
          font-size: 1.02rem !important;
          line-height: 1.6 !important;
        }
        body:has(.va-accessibility-mode) .stButton > button,
        body:has(.va-accessibility-mode) .stDownloadButton > button,
        body:has(.va-accessibility-mode) [data-testid="stFormSubmitButton"] button {
          min-height: 3.2rem !important;
          font-size: 1rem !important;
        }
        body:has(.va-accessibility-mode) [data-testid="stTextInput"] input,
        body:has(.va-accessibility-mode) [data-testid="stTextArea"] textarea,
        body:has(.va-accessibility-mode) [data-testid="stSelectbox"] [role="combobox"] {
          min-height: 3rem !important;
          font-size: 1.05rem !important;
        }
        body:has(.va-accessibility-mode) :focus-visible {
          outline: 3px solid #ffe66d !important;
          outline-offset: 3px !important;
        }
        body:has(.va-accessibility-mode) .card,
        body:has(.va-accessibility-mode) .danger,
        body:has(.va-accessibility-mode) .warning,
        body:has(.va-accessibility-mode) .ok {
          font-size: 1.05rem !important;
          line-height: 1.75 !important;
          color: #fff !important;
        }
        </style>
        <div class="va-accessibility-mode" aria-hidden="true"></div>
        """,
        unsafe_allow_html=True,
    )
st.session_state.setdefault("last_result", None)
st.session_state.setdefault("last_data_url", None)
st.session_state.setdefault("last_image_bytes", None)
st.session_state.setdefault("last_mode", DEFAULT_SETTINGS["mode"])
st.session_state.setdefault("chat", [])
st.session_state.setdefault("analysis_mode", DEFAULT_SETTINGS["mode"])
st.session_state.setdefault("vision_chat", [])
st.session_state.setdefault("vision_pending_question", "")
st.session_state.setdefault("image_chat_pending", "")
st.session_state.setdefault("robot_status", "greeting")
st.session_state.setdefault("robot_message", "Xin chào! Mình là Vision, trợ lý thị giác của bạn.")
st.session_state.setdefault("robot_chat_open", False)
st.session_state.setdefault("robot_last_page", None)
st.session_state.setdefault("robot_error_detail", "")
st.session_state.setdefault("camera_source", "📁 Tải ảnh")
st.session_state.setdefault("gemini_connection_result", "")

pending_robot_page = st.session_state.pop("robot_pending_navigation", None)
if pending_robot_page:
    st.session_state["navigation_page"] = pending_robot_page

if st.query_params.get("vision_chat") == "open":
    st.session_state.robot_chat_open = True
    del st.query_params["vision_chat"]


def navigate_to(page_name, analysis_mode=None):
    st.session_state["navigation_page"] = page_name
    if analysis_mode:
        st.session_state["analysis_mode"] = analysis_mode
    st.session_state["robot_status"] = "helping"
    st.session_state["robot_message"] = robot_page_message(page_name, analysis_mode)


def toggle_vision_chat():
    st.session_state.robot_chat_open = not st.session_state.robot_chat_open
    if st.session_state.robot_chat_open:
        set_robot_state("helping", "Mình đang lắng nghe. Bạn có thể hỏi bằng tiếng Việt.")


def queue_vision_question(state_key):
    question = str(st.session_state.get(state_key, "")).strip()
    if question:
        st.session_state.vision_pending_question = question
        set_robot_state("thinking", "Mình đang suy nghĩ và gửi câu hỏi đến Gemini…")


def queue_image_question():
    question = str(st.session_state.get("image_chat_question", "")).strip()
    if question:
        st.session_state.image_chat_pending = question
        set_robot_state("thinking", "Mình đang xem lại ảnh và suy nghĩ câu trả lời…")


def robot_page_message(page_name, analysis_mode=None):
    if analysis_mode == "Đọc chữ trong ảnh (OCR)" or page_name == "🔤 OCR (Nhận diện văn bản)":
        return "Chọn ảnh có chữ rồi nhấn Nhận diện văn bản."
    messages = {
        "🏠 Trang chính": "Chọn một công cụ hoặc hỏi mình bằng giọng nói.",
        "📷 Phân tích hình ảnh": "Chọn ảnh hoặc chụp ảnh để mình phân tích.",
        "🧭 Hỗ trợ di chuyển": "Chụp ảnh phía trước. Hãy kiểm tra thực tế trước khi di chuyển.",
        "🔤 OCR (Nhận diện văn bản)": "Chọn ảnh có chữ để mình đọc.",
        "💬 Hỏi đáp AI": "Hỏi mình về ảnh gần nhất.",
        "🎙️ Trợ lý giọng nói": "Ghi âm câu hỏi hoặc nhập bằng bàn phím.",
        "📸 Camera": "Chụp ảnh khi bạn đã sẵn sàng.",
        "🕘 Lịch sử": "Xem lại kết quả đã lưu trên máy.",
        "📊 Thống kê": "Xem số liệu từ lịch sử phân tích.",
        "⚙️ Cài đặt": "Chọn giọng đọc hoặc kiểm tra kết nối Gemini.",
        "ℹ️ Hướng dẫn": "Xem cách dùng các công cụ.",
    }
    return messages.get(page_name, "Mình đang ở đây nếu bạn cần trợ giúp.")


def set_robot_state(status, message):
    allowed = {
        "idle", "greeting", "listening", "thinking", "speaking", "happy",
        "helping", "curious", "focused", "surprised", "confused", "concerned",
        "excited", "empathetic", "reassuring", "error",
    }
    st.session_state.robot_status = status if status in allowed else "idle"
    st.session_state.robot_message = str(message or "")
    if status != "error":
        st.session_state.robot_error_detail = ""


def show_robot_error_detail():
    if st.session_state.robot_status == "error" and st.session_state.robot_error_detail:
        with st.expander("Chi tiết kỹ thuật"):
            st.caption(st.session_state.robot_error_detail)


def friendly_error_message(error):
    detail = str(error)
    if "GEMINI_API_KEY" in detail or "Chưa có" in detail:
        return "Mình chưa thể kết nối Gemini. Hãy mở Cài đặt và kiểm tra file .env; không cần dán khóa vào trang."
    if "429" in detail or "quota" in detail.lower() or "resource_exhausted" in detail.lower():
        return "Gemini đang giới hạn lượt gọi. Ứng dụng đã thử các model Gemini dự phòng; hãy chờ hạn mức hồi phục hoặc kiểm tra quota trong Google AI Studio."
    if "503" in detail or "unavailable" in detail.lower():
        return "Gemini đang tạm thời quá tải. Ứng dụng đã thử lại và chuyển qua các model Gemini dự phòng; hãy thử lại sau."
    if "401" in detail or "403" in detail or "unauthorized" in detail.lower() or "permission" in detail.lower():
        return "Gemini chưa chấp nhận cấu hình hiện tại. Hãy kiểm tra API key và quyền truy cập model trong file .env."
    if "micro" in detail.lower() or "audio" in detail.lower() or "speech" in detail.lower():
        return "Mình chưa nhận được giọng nói. Hãy kiểm tra quyền micro, thiết bị ghi âm và thử nói lại."
    if "ảnh" in detail.lower() or "image" in detail.lower():
        return "Mình chưa đọc được ảnh này. Hãy chọn JPG, PNG hoặc WebP rõ nét, nhỏ hơn 15 MB."
    return "Mình gặp trục trặc khi xử lý yêu cầu. Hãy kiểm tra kết nối mạng/cấu hình rồi thử lại."


def render_vision_chat():
    if not st.session_state.robot_chat_open:
        return
    chat_heading, chat_close = st.columns([6, 2])
    with chat_heading:
        st.markdown("#### 💬 Trò chuyện với Vision")
    with chat_close:
        st.button(
            "Thu gọn",
            key="collapse_vision_chat",
            on_click=toggle_vision_chat,
            use_container_width=True,
        )
    for item in st.session_state.vision_chat[-8:]:
        with st.chat_message(item["role"], avatar="🤖" if item["role"] == "assistant" else "🙂"):
            st.markdown(item["content"])

    with st.form("vision_assistant_form", clear_on_submit=True):
        st.text_input(
            "Câu hỏi dành cho Vision",
            placeholder="Ví dụ: Làm sao đọc chữ trong một bức ảnh?",
            max_chars=2000,
            label_visibility="collapsed",
            key="vision_question",
        )
        st.form_submit_button(
            "Gửi cho Vision",
            type="primary",
            use_container_width=True,
            on_click=queue_vision_question,
            args=("vision_question",),
        )
    audio_question = st.audio_input(
        "🎙️ Hoặc ghi âm câu hỏi cho Vision",
        key="vision_chat_audio",
    )
    st.caption("Micro chỉ được dùng sau khi bạn bấm ghi âm. Nếu không có micro hoặc không cấp quyền, hãy nhập câu hỏi bằng bàn phím.")
    if audio_question and st.button(
        "📝 Nhận diện và gửi cho Vision",
        key="send_vision_audio_question",
        use_container_width=True,
    ):
        set_robot_state("thinking", "Mình đang nhận diện câu hỏi bằng giọng nói…")
        try:
            with st.spinner("Vision đang nghe lại câu hỏi…"):
                spoken_question = transcribe_audio(audio_question)
            if not spoken_question:
                set_robot_state(
                    "error",
                    "Mình chưa nghe rõ câu hỏi. Hãy kiểm tra micro, nói gần thiết bị và thử ghi âm lại.",
                )
                st.rerun()
            st.session_state.vision_pending_question = spoken_question
            st.rerun()
        except Exception as exc:
            set_robot_state("error", friendly_error_message(exc))
            st.session_state.robot_error_detail = str(exc)
            st.rerun()
    pending_question = st.session_state.vision_pending_question
    if pending_question:
        st.session_state.vision_pending_question = ""
        st.session_state.vision_chat.append({"role": "user", "content": pending_question})
        page_name = st.session_state.get("navigation_page", "🏠 Trang chính")
        context = robot_page_message(page_name, st.session_state.get("analysis_mode"))
        result = st.session_state.get("last_result")
        if result:
            context += "\nKết quả ảnh gần nhất: " + str(result.get("summary", ""))[:1200]
        set_robot_state("thinking", "Mình đang suy nghĩ và gửi câu hỏi đến Gemini…")
        try:
            with st.spinner("Vision đang trao đổi với Gemini…"):
                answer = ask_vision_assistant(
                    pending_question,
                    context,
                    st.session_state.vision_chat[:-1],
                    st.session_state.get("last_data_url"),
                )
            st.session_state.vision_chat.append({"role": "assistant", "content": answer})
            set_robot_state("happy", answer[:240])
        except Exception as exc:
            set_robot_state("error", friendly_error_message(exc))
            st.session_state.robot_error_detail = str(exc)
            st.rerun()
        st.rerun()

    if st.session_state.vision_chat and st.session_state.voice:
        last_reply = next(
            (item["content"] for item in reversed(st.session_state.vision_chat)
             if item["role"] == "assistant"),
            "",
        )
        if last_reply:
            speech_button(last_reply, "speak_vision_chat")


def render_speech_player(audio_path):
    extension = Path(audio_path).suffix.lower()
    mime_type = "audio/wav" if extension == ".wav" else "audio/mpeg"
    audio_data = base64.b64encode(Path(audio_path).read_bytes()).decode("ascii")
    player_html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}}html,body{{margin:0;background:transparent;font-family:Arial,sans-serif;color:#eaf6ff}}
.wrap{{display:flex;align-items:center;gap:12px;padding:8px 10px;border:1px solid rgba(59,139,255,.35);border-radius:13px;background:linear-gradient(120deg,#061a3a,#04132d)}}
.bot{{width:48px;height:48px;display:grid;place-items:center;flex:0 0 48px;border:2px solid #6beaff;border-radius:17px;background:#081735;box-shadow:0 0 14px rgba(32,191,255,.4);font-size:25px}}
.bot.speaking{{animation:speaking .34s ease-in-out infinite alternate;box-shadow:0 0 19px #3de5ff}}
.state{{font-size:11px;min-width:88px}}
audio{{width:100%;height:34px}}
.stop{{min-height:36px;padding:0 12px;border:1px solid rgba(255,130,151,.55);border-radius:9px;background:#35172b;color:#fff;font-weight:700;cursor:pointer}}
.stop:focus-visible{{outline:3px solid #ffe66d;outline-offset:3px}}
@keyframes speaking{{to{{transform:translateY(-2px) scale(1.05)}}}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style></head><body>
<div class="wrap"><div class="bot" id="bot" aria-label="Vision đang nói">🤖</div>
<div class="state" id="state">Bản đọc đã sẵn sàng</div>
<audio id="audio" controls autoplay aria-label="Bản đọc của Vision" src="data:{mime_type};base64,{audio_data}"></audio>
<button class="stop" id="stop" type="button" aria-label="Dừng đọc">Dừng</button></div>
<script>
const audio=document.getElementById("audio"),bot=document.getElementById("bot"),state=document.getElementById("state");
document.getElementById("stop").addEventListener("click",()=>{{audio.pause();audio.currentTime=0;state.textContent="Đã dừng đọc"}});
audio.addEventListener("play",()=>{{bot.classList.add("speaking");state.textContent="Vision đang đọc…"}});
audio.addEventListener("pause",()=>{{bot.classList.remove("speaking");state.textContent="Đã tạm dừng"}});
audio.addEventListener("ended",()=>{{bot.classList.remove("speaking");state.textContent="Vision đã đọc xong"}});
audio.addEventListener("error",()=>{{bot.classList.remove("speaking");state.textContent="Không phát được âm thanh"}});
</script></body></html>"""
    components.html(player_html, height=76, scrolling=False)


def render_dashboard_hero(image_path, status="greeting", message="Xin chào! Mình là Vision."):
    image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    safe_status = status if status in {
        "idle", "greeting", "listening", "thinking", "speaking", "happy",
        "helping", "curious", "focused", "surprised", "confused", "concerned",
        "excited", "empathetic", "reassuring", "error"
    } else "idle"
    safe_message = html.escape(str(message or "Mình sẵn sàng hỗ trợ bạn."))
    hero_html = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
html,body{{width:100%;height:100%;margin:0;overflow:hidden;background:#061632}}
.hero{{position:relative;width:100%;height:100%;min-height:160px;overflow:hidden;border:1px solid rgba(37,149,255,.55);border-radius:11px;background:#061632 url("data:image/png;base64,{image_data}") center/100% 100% no-repeat}}
.mask{{position:absolute;inset:0 0 0 53%;background:linear-gradient(90deg,rgba(4,17,46,0) 0%,rgba(4,17,46,.87) 18%,#061632 40%,#061632 100%)}}
.robot-link{{position:absolute;z-index:2;right:2%;top:1%;width:min(43%,320px);height:98%;display:block}}
.robot{{position:relative;width:100%;height:100%;overflow:visible;transform:translate(var(--shift-x,0),var(--shift-y,0)) rotate(var(--tilt,0));transform-origin:50% 64%;transition:transform .32s cubic-bezier(.2,.8,.2,1);filter:drop-shadow(0 13px 22px rgba(0,142,255,.3));animation:float 4.2s ease-in-out infinite}}
.halo{{position:absolute;inset:8% 2% 2%;border-radius:50%;background:radial-gradient(ellipse,rgba(0,199,255,.26),rgba(22,67,180,.1) 48%,transparent 73%);filter:blur(8px);animation:breathe 3.8s ease-in-out infinite}}
.orbit{{position:absolute;left:13%;top:13%;width:73%;height:68%;border:1px solid rgba(49,214,255,.36);border-radius:50%;transform:rotate(-18deg);box-shadow:0 0 17px rgba(17,183,255,.13)}}
.orbit:after{{content:"";position:absolute;inset:9%;border:1px dashed rgba(129,153,255,.42);border-radius:50%;transform:rotate(28deg)}}
.robot svg{{position:relative;width:100%;height:100%;overflow:visible}}
.eye-pupil{{transform-box:fill-box;transform-origin:center;animation:blink 5s infinite}}
.speech{{position:absolute;z-index:4;right:5%;top:5%;max-width:145px;padding:8px 10px;border:1px solid rgba(88,192,255,.55);border-radius:12px;background:rgba(4,17,45,.93);color:#eaf7ff;font:600 11px/1.35 Arial,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.24);pointer-events:none}}
.robot.greeting #arm-wave{{animation:wave .5s ease-in-out infinite alternate}}
.robot.thinking .halo{{background:radial-gradient(ellipse,rgba(146,101,255,.42),rgba(22,67,180,.1) 48%,transparent 73%)}}
.robot.thinking .orbit{{animation:spin 4s linear infinite}}
.robot.listening .screen{{filter:drop-shadow(0 0 11px #50eeff)}}
.robot.speaking #mouth{{animation:talk .25s ease-in-out infinite alternate;transform-origin:170px 173px}}
.robot.happy #mouth{{stroke:#70ffe2;stroke-width:11}}
.robot.error #eye-left path,.robot.error #eye-right path{{stroke:#ff8297}}
@keyframes wave{{from{{transform:rotate(0deg)}}to{{transform:rotate(17deg)}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes talk{{to{{transform:scaleY(1.7)}}}}
@keyframes float{{0%,100%{{translate:0 0}}50%{{translate:0 -6px}}}}
@keyframes breathe{{0%,100%{{opacity:.55;scale:.92}}50%{{opacity:1;scale:1.04}}}}
@keyframes blink{{0%,44%,48%,100%{{scale:1 1}}46%{{scale:1 .08}}}}
@media(prefers-reduced-motion:reduce){{*,*:before,*:after{{animation:none!important;transition:none!important}}}}
</style>
</head>
<body>
<div class="hero" id="vision-hero" aria-label="VisionAI Pro, trợ lý thị giác thông minh">
<div class="mask"></div>
<a class="robot-link" href="?vision_chat=open" target="_top" aria-label="Nhấn robot để trò chuyện với Vision">
<div class="robot {safe_status}" id="vision-robot" role="img" aria-label="Robot Vision chuyển động theo con trỏ chuột">
<div class="halo"></div><div class="orbit"></div>
<svg viewBox="0 0 340 350" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<defs>
<linearGradient id="shell" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff"/><stop offset=".23" stop-color="#a8d7ff"/><stop offset=".48" stop-color="#f8fdff"/><stop offset=".72" stop-color="#7295da"/><stop offset="1" stop-color="#d7f4ff"/></linearGradient>
<linearGradient id="shellSide" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#57dfff"/><stop offset=".45" stop-color="#3862c0"/><stop offset="1" stop-color="#e9fbff"/></linearGradient>
<linearGradient id="screen" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#07142e"/><stop offset=".55" stop-color="#020817"/><stop offset="1" stop-color="#0b2450"/></linearGradient>
<linearGradient id="body" x1="0" y1="0" x2=".9" y2="1"><stop stop-color="#a7eaff"/><stop offset=".38" stop-color="#f6fdff"/><stop offset=".7" stop-color="#6e91d4"/><stop offset="1" stop-color="#d7f7ff"/></linearGradient>
<radialGradient id="eyeGlow"><stop stop-color="#fff"/><stop offset=".35" stop-color="#52f5ff"/><stop offset="1" stop-color="#08aaff"/></radialGradient>
<filter id="glow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<path d="M170 8v29" stroke="#6deaff" stroke-width="5" stroke-linecap="round"/>
<circle cx="170" cy="24" r="15" fill="#061a42" stroke="#8df6ff" stroke-width="4" filter="url(#glow)"/>
<circle cx="170" cy="24" r="7" fill="#49dfff"/>
<path d="M170 37 170 57" stroke="#6ceaff" stroke-width="4"/>
<path d="M77 98 48 93v75l31-5M263 98l29-5v75l-31-5" fill="url(#shellSide)" stroke="#82eaff" stroke-width="4"/>
<rect x="61" y="61" width="218" height="174" rx="72" fill="url(#shell)" stroke="#bbf5ff" stroke-width="5"/>
<path d="M85 88q8-24 34-28h95q29 4 41 29" fill="none" stroke="#fff" stroke-opacity=".82" stroke-width="7" stroke-linecap="round"/>
<rect x="78" y="84" width="184" height="132" rx="52" fill="url(#screen)" stroke="#071a3f" stroke-width="5"/>
<path d="M91 96q51-25 107-17" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="5" stroke-linecap="round"/>
<g id="eyes" filter="url(#glow)">
<g class="eye-pupil" id="eye-left"><path d="M108 151q16-26 34 0" fill="none" stroke="url(#eyeGlow)" stroke-width="12" stroke-linecap="round"/></g>
<g class="eye-pupil" id="eye-right"><path d="M197 151q16-26 34 0" fill="none" stroke="url(#eyeGlow)" stroke-width="12" stroke-linecap="round"/></g>
<path d="M148 173q22 24 44 0" fill="none" stroke="#46eaff" stroke-width="8" stroke-linecap="round"/>
</g>
<circle cx="72" cy="147" r="19" fill="#183c78" stroke="#75f2ff" stroke-width="4"/>
<circle cx="268" cy="147" r="19" fill="#183c78" stroke="#75f2ff" stroke-width="4"/>
<path d="M147 235v19h46v-19" fill="url(#shellSide)" stroke="#bcefff" stroke-width="3"/>
<path d="M91 260q9-22 39-22h77q31 0 43 23l24 61H66z" fill="url(#body)" stroke="#9ceaff" stroke-width="4"/>
<path d="M116 251q53 25 108 0" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="5"/>
<circle cx="170" cy="284" r="30" fill="#102453" stroke="#55deff" stroke-width="5" filter="url(#glow)"/>
<path d="M149 284q21-21 42 0-21 21-42 0zm12 0a9 9 0 1 0 18 0 9 9 0 1 0-18 0" fill="none" stroke="#8ff8ff" stroke-width="4"/>
<path d="M84 267 56 283M256 267l24-27" stroke="#a9edff" stroke-width="18" stroke-linecap="round"/>
<g id="arm-wave" style="transform-box:fill-box;transform-origin:12% 100%"><path d="M280 242q-6-15 3-25l11 12 4-23q2-9 9-5l2 20 9-13q6-7 10 0l-7 18 8-7q8-5 9 2l-13 22q-9 14-27 9z" fill="url(#shell)" stroke="#77eaff" stroke-width="4" stroke-linejoin="round"/></g>
<path d="M65 314h210" stroke="#5fe4ff" stroke-width="3" stroke-linecap="round" opacity=".8"/>
</svg>
</div>
</a>
<div class="speech">{safe_message}</div>
</div>
<script>
(() => {{
  const hero = document.getElementById("vision-hero");
  const robot = document.getElementById("vision-robot");
  const leftEye = document.getElementById("eye-left");
  const rightEye = document.getElementById("eye-right");
  const follow = (event) => {{
    const bounds = hero.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width - .5;
    const y = (event.clientY - bounds.top) / bounds.height - .5;
    robot.style.setProperty("--shift-x", `${{(x * 12).toFixed(1)}}px`);
    robot.style.setProperty("--shift-y", `${{(y * 8).toFixed(1)}}px`);
    robot.style.setProperty("--tilt", `${{(x * 5).toFixed(1)}}deg`);
    const eyeX = (x * 4).toFixed(1);
    const eyeY = (y * 3).toFixed(1);
    leftEye.setAttribute("transform", `translate(${{eyeX}} ${{eyeY}})`);
    rightEye.setAttribute("transform", `translate(${{eyeX}} ${{eyeY}})`);
  }};
  hero.addEventListener("pointermove", follow);
  hero.addEventListener("pointerleave", () => {{
    robot.style.setProperty("--shift-x", "0px");
    robot.style.setProperty("--shift-y", "0px");
    robot.style.setProperty("--tilt", "0deg");
    leftEye.setAttribute("transform", "translate(0 0)");
    rightEye.setAttribute("transform", "translate(0 0)");
  }});
  const resizeHero = () => {{
    const height = Math.min(275, Math.max(160, Math.round(hero.clientWidth * .42)));
    hero.style.height = `${{height}}px`;
    if (window.frameElement) window.frameElement.style.height = `${{height + 4}}px`;
  }};
  new ResizeObserver(resizeHero).observe(hero.parentElement);
  resizeHero();
}})();
</script>
</body>
</html>"""
    components.html(hero_html, height=275, scrolling=False)


def speech_button(text, key, label="🔊 Đọc bằng giọng nói"):
    if not text or not st.session_state.voice:
        return
    if st.button(label, key=key, use_container_width=True):
        try:
            set_robot_state("speaking", "Mình đang chuẩn bị đọc câu trả lời thành tiếng.")
            with st.spinner("Đang tạo giọng nói miễn phí..."):
                path = text_to_speech(text, voice=st.session_state.get("tts_voice"))
            if path:
                render_speech_player(path)
                set_robot_state("happy", "Bản đọc đã sẵn sàng. Dùng trình phát để nghe lại hoặc dừng.")
            else:
                set_robot_state("happy", "Không có nội dung để đọc thành tiếng.")
        except Exception as exc:
            message = friendly_error_message(exc)
            set_robot_state("error", message)
            st.error(message)
            with st.expander("Chi tiết kỹ thuật"):
                st.caption(str(exc))


def run_voice_command(text):
    command = parse_voice_command(text)
    if not command:
        return False

    action = command["action"]
    if action == "help":
        st.info(VOICE_COMMAND_HELP)
        path = text_to_speech(VOICE_COMMAND_HELP, voice=st.session_state.get("tts_voice"))
        if path:
            render_speech_player(path)
        set_robot_state("helping", VOICE_COMMAND_HELP)
        return True

    if action == "navigate":
        st.session_state.robot_pending_navigation = command["page"]
        set_robot_state("helping", f"Mình đã mở mục {command['page']}.")
        return True

    if action == "replay":
        last_reply = next(
            (item["content"] for item in reversed(st.session_state.vision_chat)
             if item["role"] == "assistant"),
            "",
        )
        spoken_text = last_reply or (
            build_spoken_result(
                st.session_state.last_result,
                mode=st.session_state.get("last_mode", ""),
            )
            if st.session_state.last_result
            else ""
        )
        if not spoken_text:
            st.info("Chưa có kết quả để đọc lại.")
            return True
        path = text_to_speech(spoken_text, voice=st.session_state.get("tts_voice"))
        if not path:
            raise RuntimeError("Không tạo được nội dung đọc lại.")
        render_speech_player(path)
        set_robot_state("speaking", "Mình đang đọc lại kết quả gần nhất.")
        return True

    if action == "find_object":
        if not st.session_state.last_data_url:
            st.session_state.object_finder_notice = (
                f"Bạn vừa yêu cầu tìm “{command['target']}”. Hãy chọn và phân tích ảnh trước; "
                "sau đó có thể tìm vật trong ảnh gần nhất."
            )
            st.session_state.object_finder_question = command["target"]
            st.session_state.robot_pending_navigation = "📷 Phân tích hình ảnh"
            return True
        question = (
            f"Hãy tìm {command['target']} trong ảnh. Nếu nhìn thấy, mô tả vị trí tương đối "
            "trong khung hình và dấu hiệu giúp nhận ra. Nếu không chắc hoặc không thấy, hãy nói rõ; "
            "không suy đoán vật thể ngoài ảnh."
        )
        answer = ask_about_image(
            st.session_state.last_data_url,
            question,
            st.session_state.vision_chat,
        )
        st.session_state.vision_chat.extend([
            {"role": "user", "content": f"Tìm {command['target']}"},
            {"role": "assistant", "content": answer},
        ])
        st.success(answer)
        speech_button(answer, "speak_voice_object_finder")
        set_robot_state("happy", answer[:240])
        return True

    return False


def safety_text(result):
    hazards = result.get("hazards", [])
    parts = []
    for h in hazards:
        parts.append(f"{h.get('name','Có nguy cơ')} ở {h.get('location','phía trước')}. {h.get('description','')}")
    if result.get("navigation", {}).get("instruction"):
        parts.append(result["navigation"]["instruction"])
    if not parts:
        parts.append(result.get("summary", "Không có thông tin."))
    return "Cảnh báo an toàn. " + " ".join(parts)


def object_finder_section():
    if not st.session_state.last_data_url:
        return

    st.subheader("🔎 Tìm một vật trong ảnh")
    st.caption(
        "Nêu tên vật cần tìm. Vision chỉ trả lời theo ảnh hiện có, không tìm vật ngoài khung hình."
    )
    with st.form("object_finder_form"):
        target = st.text_input(
            "Vật cần tìm",
            placeholder="Ví dụ: chìa khóa, cốc nước, cửa ra vào",
            max_chars=120,
            key="object_finder_question",
        )
        submitted = st.form_submit_button("🔎 Tìm trong ảnh", type="primary")
    if submitted:
        if not target.strip():
            st.warning("Hãy nhập tên vật cần tìm.")
        else:
            question = (
                f"Hãy tìm {target.strip()} trong ảnh. Nếu nhìn thấy, mô tả vị trí tương đối "
                "trong khung hình và dấu hiệu giúp nhận ra. Nếu không chắc hoặc không thấy, "
                "hãy nói rõ; không suy đoán vật thể ngoài ảnh."
            )
            try:
                with st.spinner(f"Đang tìm {target.strip()} trong ảnh…"):
                    answer = ask_about_image(
                        st.session_state.last_data_url,
                        question,
                        st.session_state.chat,
                    )
                st.session_state.object_finder_answer = answer
                set_robot_state("happy", answer[:240])
            except Exception as exc:
                message = friendly_error_message(exc)
                set_robot_state("error", message)
                st.session_state.robot_error_detail = str(exc)
                st.error(message)
    if st.session_state.get("object_finder_answer"):
        st.info(st.session_state.object_finder_answer)
        speech_button(st.session_state.object_finder_answer, "speak_object_finder_answer")


def show_result(result):
    if not result:
        return
    st.subheader("🧠 Kết quả phân tích")
    full_speech = build_spoken_result(
        result,
        mode=st.session_state.get("last_mode", ""),
    )
    speech_button(full_speech, "speak_result", "🔊 Nghe toàn bộ kết quả")

    hazards = result.get("hazards", [])
    st.subheader("⚠️ An toàn")
    if hazards:
        for h in hazards:
            sev = h.get("severity", "Không xác định")
            cls = "danger" if sev == "Cao" else "warning" if sev == "Trung bình" else "ok"
            st.markdown(f"<div class='{cls}'><b>{html.escape(str(h.get('name','Nguy cơ')))}</b> — {html.escape(str(sev))}<br>📍 {html.escape(str(h.get('location','')))}<br>{html.escape(str(h.get('description','')))}</div>", unsafe_allow_html=True)
        speech_button(safety_text(result), "speak_safety", "🔊 Nghe cảnh báo")
    else:
        st.info("AI không phát hiện nguy cơ rõ ràng trong ảnh này. Điều đó không đảm bảo môi trường an toàn.")

    if result.get("model_used"):
        st.caption(f"Đã xử lý bằng: {result['model_used']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Độ tin cậy", result.get("confidence", "Không xác định"))
    c2.metric("Vật thể", len(result.get("objects", [])))
    c3.metric("Nguy cơ", len(result.get("hazards", [])))

    st.markdown(f"<div class='card'><b>📝 Mô tả</b><br>{html.escape(str(result.get('summary','')))}</div>", unsafe_allow_html=True)
    if result.get("scene"):
        st.markdown(f"<div class='card'><b>🏠 Bối cảnh</b><br>{html.escape(str(result['scene']))}</div>", unsafe_allow_html=True)

    nav = result.get("navigation", {})
    if nav.get("instruction"):
        st.subheader("🧭 Hỗ trợ di chuyển")
        st.warning(
            "Thông tin chỉ được suy ra từ một ảnh tĩnh, có thể thiếu hoặc sai. "
            "Không dùng thay cho gậy, chó dẫn đường, thiết bị hỗ trợ hoặc kiểm tra thực tế."
        )
        st.markdown(f"<div class='card'><b>{html.escape(str(nav.get('direction','')))}</b> {html.escape(str(nav.get('distance','')))}<br>{html.escape(str(nav.get('instruction','')))}</div>", unsafe_allow_html=True)

    objects = result.get("objects", [])
    if objects:
        st.subheader("👁️ Vật thể nhận diện")
        cols = st.columns(min(3, len(objects)))
        for i, obj in enumerate(objects):
            with cols[i % len(cols)]:
                st.markdown(f"**{obj.get('name','Vật thể')}**")
                st.caption(f"📍 {obj.get('location','Không rõ')}")
                st.write(obj.get("description", ""))

    money = result.get("money_detected", {})
    if money.get("detected"):
        st.subheader("💵 Tiền Việt Nam")
        st.success(f"Mệnh giá: **{money.get('denomination','Không xác định')}** · {money.get('confidence','')}")

    ocr_items = result.get("text_detected", [])
    if ocr_items:
        st.subheader("🔤 Văn bản OCR")
        st.caption(f"Đã nhận diện {len(ocr_items)} đoạn văn bản")
        for i, item in enumerate(ocr_items, 1):
            if isinstance(item, dict):
                st.markdown(
                    f"<div class='card'><b>🔹 {html.escape(str(item.get('text', '')))}</b><br>"
                    f"📍 {html.escape(str(item.get('location', 'Không xác định')))}<br>"
                    f"🎯 Độ tin cậy: {html.escape(str(item.get('confidence', 'Không xác định')))}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"🔹 {item}")
        with st.expander("Đọc từng dòng văn bản"):
            speech_button(build_ocr_spoken_text(ocr_items), "speak_all_ocr")
            for index, item in enumerate(ocr_items):
                line = item.get("text", "") if isinstance(item, dict) else str(item)
                if line.strip():
                    st.write(f"{index + 1}. {line}")
                    speech_button(
                        line,
                        f"speak_ocr_line_{index}",
                        f"🔊 Đọc dòng {index + 1}",
                    )

    tips = result.get("accessibility_tips", [])
    if tips:
        st.subheader("💡 Gợi ý cho người khiếm thị")
        for tip in tips:
            st.write(f"• {tip}")

    if result.get("warning"):
        st.warning(result["warning"])

    history_id = st.session_state.get("last_history_id")
    if history_id:
        history_record = next(
            (item for item in load_history() if utils.history_item_key(item) == history_id),
            None,
        )
        if history_record:
            is_favorite = bool(history_record.get("favorite"))
            if st.button(
                "★ Đã lưu yêu thích · bỏ lưu" if is_favorite else "☆ Lưu kết quả yêu thích",
                key=f"favorite_current_{history_id}",
            ):
                utils.set_history_favorite(history_id, not is_favorite)
                st.rerun()

    report = export_report(result, st.session_state.get("last_mode", "Phân tích hình ảnh"))
    st.download_button("📄 Xuất báo cáo TXT", report, file_name="bao-cao-tro-ly-thi-giac.txt", mime="text/plain", use_container_width=True)


with st.sidebar:
    st.markdown(
        "<div class='sidebar-brand'><strong>👁️ VisionAI Pro</strong>"
        "<span>Trợ lý thị giác thông minh</span></div>",
        unsafe_allow_html=True,
    )
    api_ready = is_api_ready()
    status_text = "Đã sẵn sàng" if api_ready else "Cần cấu hình Gemini"
    status_color = "#86eeb5" if api_ready else "#ffd08a"
    st.markdown(
        f"<div class='sidebar-status' style='color:{status_color}'>"
        f"<i></i> Trạng thái AI · {status_text}</div>",
        unsafe_allow_html=True,
    )
    page = st.radio("Điều hướng", [
        "🏠 Trang chính",
        "📷 Phân tích hình ảnh",
        "🔤 OCR (Nhận diện văn bản)",
        "🧭 Hỗ trợ di chuyển",
        "💬 Hỏi đáp AI",
        "🎙️ Trợ lý giọng nói",
        "📸 Camera",
        "🕘 Lịch sử",
        "📊 Thống kê",
        "⚙️ Cài đặt",
        "ℹ️ Hướng dẫn"
    ], key="navigation_page")
    st.button(
        "🤖 Trò chuyện với Vision",
        key="sidebar_vision_chat",
        use_container_width=True,
        on_click=toggle_vision_chat,
    )
    st.divider()
    st.session_state.voice = st.toggle("🔊 Bật giọng nói", value=st.session_state.voice)
    st.toggle(
        "🔎 Chế độ trợ năng",
        key="accessible_mode",
        help="Chữ và nút lớn hơn, viền bàn phím rõ hơn.",
    )
    if st.button("🗑️ Xóa phiên hiện tại", use_container_width=True):
        st.session_state.last_result = None
        st.session_state.last_data_url = None
        st.session_state.last_image_bytes = None
        st.session_state.chat = []
        st.rerun()

if st.session_state.robot_last_page != page:
    if st.session_state.robot_last_page is None and page == "🏠 Trang chính":
        set_robot_state("greeting", "Xin chào! Mình là Vision, trợ lý thị giác của bạn.")
    elif page in ("📷 Phân tích hình ảnh", "🔤 OCR (Nhận diện văn bản)", "🧭 Hỗ trợ di chuyển"):
        set_robot_state("curious", robot_page_message(page, st.session_state.analysis_mode))
    else:
        set_robot_state("helping", robot_page_message(page, st.session_state.analysis_mode))
    st.session_state.robot_last_page = page

if page != "🏠 Trang chính":
    render_dashboard_robot(st.session_state.robot_status, st.session_state.robot_message)
    show_robot_error_detail()
    if not st.session_state.robot_chat_open:
        st.button(
            "💬 Hỏi Vision",
            key="open_vision_chat",
            on_click=toggle_vision_chat,
        )
    render_vision_chat()

if page == "🏠 Trang chính":
    history = load_history()
    render_dashboard_robot(
        st.session_state.robot_status,
        st.session_state.robot_message,
    )
    show_robot_error_detail()
    render_vision_chat()
    main_column, side_column = st.columns([2.35, 1], gap="medium")
    with main_column:
        st.markdown(
            "<div class='dashboard-section-title'><h3>Công cụ</h3></div>",
            unsafe_allow_html=True,
        )
        features = [
            ("📷", "Phân tích ảnh", "Mô tả ảnh và cảnh báo nguy cơ.", "📷 Phân tích hình ảnh", None, ""),
            ("🔤", "Đọc văn bản", "Nhận diện chữ tiếng Việt.", "🔤 OCR (Nhận diện văn bản)", None, "purple"),
            ("💬", "Hỏi đáp ảnh", "Hỏi về ảnh gần nhất.", "💬 Hỏi đáp AI", None, "green"),
            ("🎙️", "Giọng nói", "Nói câu hỏi, nghe trả lời.", "🎙️ Trợ lý giọng nói", None, "orange"),
            ("📸", "Camera", "Chụp ảnh để phân tích.", "📸 Camera", None, "pink"),
        ]
        feature_columns = st.columns(len(features), gap="small")
        for index, (column, (icon, title, description, destination, analysis_mode, color)) in enumerate(
            zip(feature_columns, features)
        ):
            with column:
                st.markdown(
                    f"<div class='feature-card {color}' style='animation-delay:{index * 70}ms'>"
                    f"<div class='feature-icon'>{icon}</div><h4>{title}</h4>"
                    f"<p>{description}</p></div>",
                    unsafe_allow_html=True,
                )
                st.button(
                    f"Mở {title}",
                    key=f"dashboard_{index}",
                    use_container_width=True,
                    on_click=navigate_to,
                    args=(destination, analysis_mode),
                )

        st.markdown(
            "<div class='dashboard-section-title'><h3>Kết quả gần nhất</h3></div>",
            unsafe_allow_html=True,
        )
        if st.session_state.last_result:
            st.success("Có ảnh đã phân tích. Bạn có thể hỏi thêm hoặc nghe kết quả.")
            show_result(st.session_state.last_result)

    with side_column:
        st.button(
            "⚙️ Cấu hình Gemini",
            key="dashboard_settings",
            use_container_width=True,
            on_click=navigate_to,
            args=("⚙️ Cài đặt",),
            help="Mở cài đặt Gemini",
        )

        if history:
            activity_items = []
            for item in history[:4]:
                summary = html.escape(str(item.get("mode") or "Phân tích ảnh"))
                timestamp = html.escape(str(item.get("time") or ""))
                activity_items.append(
                    f"<div class='dashboard-activity'>✦ {summary}<span>{timestamp}</span></div>"
                )
            activity_html = "".join(activity_items)
        else:
            activity_html = "<div class='dashboard-activity'>Chưa có hoạt động.</div>"
        st.markdown(
            f"<div class='dashboard-panel'><h3>🕘 Hoạt động gần đây</h3>"
            f"{activity_html}</div>",
            unsafe_allow_html=True,
        )

elif page in (
    "📷 Phân tích hình ảnh",
    "🔤 OCR (Nhận diện văn bản)",
    "🧭 Hỗ trợ di chuyển",
    "📸 Camera",
):
    navigation_mode = page.startswith("🧭")
    camera_page = page == "📸 Camera"
    ocr_page = page == "🔤 OCR (Nhận diện văn bản)"
    page_title = (
        "📸 Camera · chụp và phân tích"
        if camera_page
        else "🔤 OCR · nhận diện văn bản"
        if ocr_page
        else "🧭 Phân tích hỗ trợ di chuyển"
        if navigation_mode
        else "📷 Phân tích hình ảnh"
    )
    st.subheader(page_title)
    if st.session_state.object_finder_notice:
        st.info(st.session_state.object_finder_notice)
        st.session_state.object_finder_notice = ""
    if navigation_mode:
        st.warning(
            "Ảnh chỉ ghi lại một thời điểm. AI có thể bỏ sót người, xe, bậc thềm hoặc vật cản đang di chuyển. "
            "Không dựa riêng vào ứng dụng để qua đường hoặc chọn lối đi; hãy dùng gậy/chó dẫn đường "
            "và xác nhận bằng các giác quan, thiết bị hỗ trợ của bạn."
        )
    if camera_page:
        st.info("Camera chỉ chụp khi bạn chủ động bấm nút và cấp quyền. Ứng dụng không phát trực tiếp hay gửi khung hình liên tục.")
        source = st.radio(
            "Nguồn ảnh",
            ["📸 Camera", "📁 Tải ảnh"],
            horizontal=True,
            key="camera_source",
        )
    else:
        source = st.radio("Nguồn ảnh", ["📁 Tải ảnh", "📸 Camera"], horizontal=True, key="source")
    uploaded = st.file_uploader("Chọn ảnh", type=["jpg", "jpeg", "png", "webp"], key="upload") if source == "📁 Tải ảnh" else st.camera_input("Chụp ảnh", key="camera")
    if navigation_mode:
        mode = "Hỗ trợ di chuyển"
        detail = "Cao"
        scene_style = "safety"
    elif ocr_page:
        mode = "Đọc chữ trong ảnh (OCR)"
        detail = st.session_state.detail
        scene_style = "balanced"
        st.caption("Mẹo của Vision: đặt văn bản đủ sáng, lấy nét rõ và chụp càng thẳng càng tốt.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            mode = st.selectbox("🧠 Chế độ", [
                "Mô tả toàn cảnh", "Nhận biết vật thể và vị trí", "Đọc chữ trong ảnh (OCR)",
                "Nhận diện tiền Việt", "Hỗ trợ người khiếm thị", "Hỗ trợ di chuyển"
            ], key="analysis_mode")
        with c2:
            detail = st.select_slider("🔍 Mức chi tiết", options=["Thấp", "Vừa", "Cao"], value=st.session_state.detail)
            st.session_state.detail = detail
        with c3:
            scene_style = st.selectbox(
                "🗣️ Cách mô tả",
                ["balanced", "brief", "detailed", "safety"],
                format_func={
                    "balanced": "Cân bằng",
                    "brief": "Ngắn gọn",
                    "detailed": "Chi tiết",
                    "safety": "Ưu tiên an toàn",
                }.get,
                key="scene_style",
            )
    if uploaded:
        if getattr(uploaded, "size", 0) > 15 * 1024 * 1024:
            message = friendly_error_message("Ảnh lớn hơn 15 MB.")
            set_robot_state("error", message)
            st.error(message)
            st.stop()
        try:
            image = Image.open(uploaded)
            image.verify()
            uploaded.seek(0)
            image = Image.open(uploaded)
            image.load()
        except Exception as exc:
            message = friendly_error_message(exc)
            set_robot_state("error", message)
            st.error(message)
            st.stop()
        st.image(image, caption="Ảnh đầu vào", use_container_width=True)
        if st.button(
            "🧠 Phân tích ngay",
            type="primary",
            use_container_width=True,
            on_click=set_robot_state,
            args=("focused", "Mình đang tập trung phân tích ảnh."),
        ):
            try:
                raw = uploaded.getvalue()
                mime = getattr(uploaded, "type", None) or "image/jpeg"
                data_url = image_to_data_url(raw, mime)
                set_robot_state("focused", "Mình đang tập trung phân tích ảnh.")
                if mode == "Đọc chữ trong ảnh (OCR)":
                    with st.spinner("🔤 OCR cục bộ đang đọc chữ..."):
                        result = analyze_local_ocr(raw)
                    st.info("🟢 OCR cục bộ: không tốn lượt gọi AI. Chất lượng phụ thuộc ảnh và dữ liệu ngôn ngữ Tesseract.")
                else:
                    with st.spinner("AI đang phân tích ảnh..."):
                        result = analyze_image(data_url, mode, detail, scene_style)
                    if not is_api_ready():
                        st.info("🟡 Chưa cấu hình API AI; ứng dụng dùng OCR cục bộ nếu có thể.")
                    elif "OCR cục bộ" in result.get("warning", "") or "OCR local" in result.get("warning", ""):
                        st.warning("🟡 AI trực tuyến không khả dụng. Ứng dụng đã chuyển sang OCR cục bộ.")
                st.session_state.last_result = result
                st.session_state.last_data_url = data_url
                st.session_state.last_image_bytes = raw
                st.session_state.last_mode = mode
                st.session_state.object_finder_answer = ""
                st.session_state.chat = []
                hazards = result.get("hazards", [])
                high_hazard = any(
                    isinstance(item, dict)
                    and str(item.get("severity", "")).casefold() == "cao"
                    for item in hazards
                )
                if high_hazard:
                    set_robot_state("concerned", "Mình phát hiện dấu hiệu nguy hiểm. Hãy kiểm tra thực tế trước khi hành động.")
                elif result.get("model_used") == "OCR local" and mode != "Đọc chữ trong ảnh (OCR)":
                    set_robot_state(
                        "error",
                        "Gemini chưa phản hồi; mình chỉ có thể cung cấp OCR cục bộ, chưa phân tích được cảnh vật.",
                    )
                elif result.get("money_detected", {}).get("detected"):
                    set_robot_state("surprised", "Mình nhận diện được dấu hiệu tiền. Hãy kiểm tra lại mệnh giá.")
                elif str(result.get("confidence", "")).casefold() in ("", "không xác định"):
                            set_robot_state("empathetic", "Ảnh chưa đủ rõ để mình chắc chắn. Bạn có thể chụp lại sáng và nét hơn.")
                else:
                            set_robot_state("excited", "Xử lý xong rồi! Bạn có thể nghe kết quả hoặc hỏi mình thêm.")
                try:
                    st.session_state.last_history_id = None
                    st.session_state.last_history_id = save_history({
                        "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "mode": mode, "summary": result.get("summary", ""),
                        "confidence": result.get("confidence", ""),
                        "money": result.get("money_detected", {}),
                        "hazards": hazards,
                        "navigation": result.get("navigation", {}),
                        "accessibility_tips": result.get("accessibility_tips", []),
                        "warning": result.get("warning", ""),
                        "scene": result.get("scene", ""),
                        "objects": result.get("objects", []),
                        "text_detected": result.get("text_detected", []),
                        "text": "\n".join(
                            str(x.get("text", "")) if isinstance(x, dict) else str(x)
                            for x in result.get("text_detected", [])
                        )
                    })
                except Exception:
                    st.warning("Phân tích đã hoàn tất nhưng không lưu được lịch sử. Kiểm tra quyền ghi thư mục data.")
                st.success("✅ Nhận diện văn bản hoàn tất" if mode == "Đọc chữ trong ảnh (OCR)" else "✅ Phân tích hoàn tất")
                st.rerun()
            except Exception as exc:
                message = friendly_error_message(exc)
                set_robot_state("error", message)
                st.session_state.robot_error_detail = str(exc)
                st.rerun()
    if st.session_state.last_result:
        show_result(st.session_state.last_result)
        object_finder_section()

elif page == "💬 Hỏi đáp AI":
    st.subheader("💬 Hỏi đáp với Vision")
    if st.session_state.last_image_bytes:
        st.image(st.session_state.last_image_bytes, caption="Ảnh đang dùng làm ngữ cảnh")
    else:
        chat_image = st.file_uploader(
            "Chọn ảnh để hỏi về nội dung",
            type=["jpg", "jpeg", "png", "webp"],
            key="image_chat_upload",
        )
        if chat_image:
            try:
                raw = chat_image.getvalue()
                st.session_state.last_data_url = image_to_data_url(
                    raw, getattr(chat_image, "type", None) or "image/jpeg"
                )
                st.session_state.last_image_bytes = raw
                st.image(raw, caption="Ảnh đã chọn cho cuộc trò chuyện")
            except Exception as exc:
                set_robot_state("error", friendly_error_message(exc))
                st.error(friendly_error_message(exc))
    for item in st.session_state.chat:
        with st.chat_message(item["role"], avatar="🤖" if item["role"] == "assistant" else "🙂"):
            st.markdown(item["content"])
    with st.form("image_chat_form", clear_on_submit=True):
        st.text_input(
            "Câu hỏi về ảnh",
            placeholder="Hỏi về ảnh hoặc cách sử dụng VisionAI…",
            max_chars=2000,
            key="image_chat_question",
        )
        st.form_submit_button(
            "Gửi câu hỏi →",
            type="primary",
            use_container_width=True,
            on_click=queue_image_question,
        )
    pending_question = st.session_state.image_chat_pending
    if pending_question:
        st.session_state.image_chat_pending = ""
        st.session_state.chat.append({"role": "user", "content": pending_question})
        try:
            with st.spinner("Vision đang trao đổi với Gemini…"):
                if st.session_state.last_data_url:
                    answer = ask_about_image(
                        st.session_state.last_data_url,
                        pending_question,
                        st.session_state.chat[:-1],
                    )
                else:
                    answer = ask_vision_assistant(
                        pending_question,
                        robot_page_message(page),
                        st.session_state.chat[:-1],
                    )
            st.session_state.chat.append({"role": "assistant", "content": answer})
            set_robot_state("happy", answer[:240])
            st.rerun()
        except Exception as exc:
            message = friendly_error_message(exc)
            set_robot_state("error", message)
            st.error(message)
            with st.expander("Chi tiết kỹ thuật"):
                st.caption(str(exc))
            st.rerun()
    if st.session_state.chat:
        last_reply = next(
            (item["content"] for item in reversed(st.session_state.chat)
             if item["role"] == "assistant"),
            "",
        )
        if last_reply:
            speech_button(last_reply, "speak_chat")

elif page == "🎙️ Trợ lý giọng nói":
    st.subheader("🎙️ Trò chuyện bằng giọng nói")
    st.caption(VOICE_COMMAND_HELP)
    with st.expander("Không ghi âm được hoặc không nhận ra giọng nói?"):
        st.markdown(
            """
            - **Bộ đếm không chạy hoặc trình duyệt báo lỗi micro:** mở quyền của trang cạnh thanh địa chỉ, đặt Microphone thành **Allow**, chọn đúng thiết bị ghi âm rồi tải lại trang. Kiểm tra thêm quyền Microphone trong Windows.
            - **Ghi âm xong nhưng không nhận ra chữ:** cần kết nối Internet để gửi bản ghi tới dịch vụ nhận dạng Google; thử nói ngắn, rõ, giảm tiếng ồn và ghi lại.
            - **Không muốn gửi giọng nói qua dịch vụ bên ngoài:** không dùng ghi âm; nhập câu hỏi bằng bàn phím. Âm thanh chỉ được xử lý sau khi bạn kết thúc ghi âm và chủ động bấm nhận diện.
            """
        )
    audio = st.audio_input("🎙️ Nhấn để ghi âm", key="voice_input")
    if audio:
        st.audio(audio)
        if st.button(
            "📝 Nhận diện và hỏi Vision",
            type="primary",
            use_container_width=True,
            on_click=set_robot_state,
            args=("thinking", "Mình đang nhận diện và chuẩn bị gửi câu hỏi cho Gemini…"),
        ):
            try:
                set_robot_state("listening", "Mình đang nghe lại bản ghi để nhận diện câu hỏi.")
                with st.spinner("Đang nhận dạng giọng nói..."):
                    text = transcribe_audio(audio)
                if not text:
                    set_robot_state(
                        "error",
                        "Mình chưa nghe rõ câu hỏi. Hãy kiểm tra micro, nói gần thiết bị và thử lại.",
                    )
                    st.warning(st.session_state.robot_message)
                    st.rerun()
                st.session_state.voice_question = text
                st.info(f"Bạn nói: {text}")
                command = parse_voice_command(text)
                if command:
                    run_voice_command(text)
                    if command["action"] == "navigate" or (
                        command["action"] == "find_object"
                        and not st.session_state.last_data_url
                    ):
                        st.rerun()
                else:
                    set_robot_state("thinking", "Mình đã nhận ra câu hỏi và đang gửi đến Gemini…")
                    context = robot_page_message(page)
                    if st.session_state.last_result:
                        context += "\nKết quả ảnh gần nhất: " + str(
                            st.session_state.last_result.get("summary", "")
                        )[:1000]
                    with st.spinner("Vision đang suy nghĩ…"):
                        answer = ask_vision_assistant(
                            text,
                            context,
                            st.session_state.vision_chat,
                            st.session_state.get("last_data_url"),
                        )
                    st.session_state.vision_chat.extend([
                        {"role": "user", "content": text},
                        {"role": "assistant", "content": answer},
                    ])
                    st.success(answer)
                    set_robot_state("happy", "Mình đã trả lời. Bạn có thể ghi âm câu hỏi tiếp theo.")
                    st.rerun()
            except Exception as exc:
                message = friendly_error_message(exc)
                set_robot_state("error", message)
                st.session_state.robot_error_detail = str(exc)
                st.rerun()
    for item in st.session_state.vision_chat[-6:]:
        with st.chat_message(item["role"], avatar="🤖" if item["role"] == "assistant" else "🙂"):
            st.markdown(item["content"])
    if st.session_state.vision_chat and st.session_state.voice:
        last_reply = next(
            (item["content"] for item in reversed(st.session_state.vision_chat)
             if item["role"] == "assistant"),
            "",
        )
        if last_reply:
            speech_button(last_reply, "speak_voice_answer")

elif page == "🕘 Lịch sử":
    st.subheader("🕘 Lịch sử phân tích")
    history = load_history()
    if not history:
        st.info("Chưa có lịch sử.")
    else:
        favorite_filter = st.selectbox(
            "Hiển thị",
            ["Tất cả", "Mục yêu thích"],
            key="history_favorite_filter",
        )
        visible_history = [
            item for item in history
            if favorite_filter == "Tất cả" or item.get("favorite")
        ]
        st.caption(f"Hiển thị {len(visible_history)} trên {len(history)} mục.")
        if not visible_history:
            st.info("Chưa có mục yêu thích. Mở một kết quả trong lịch sử và chọn Thêm vào yêu thích.")
        for i, item in enumerate(visible_history):
            item_key = utils.history_item_key(item)
            is_favorite = bool(item.get("favorite"))
            with st.expander(f"{'★ ' if is_favorite else ''}{item.get('time','')} — {item.get('mode','')}"):
                st.write(item.get("summary", ""))
                st.caption(f"Độ tin cậy: {item.get('confidence','')}")
                speech_button(
                    build_spoken_result(item, mode=item.get("mode", "")),
                    f"speak_history_{item_key}",
                )
                if st.button(
                    "★ Bỏ yêu thích" if is_favorite else "☆ Thêm vào yêu thích",
                    key=f"favorite_history_{item_key}",
                ):
                    utils.set_history_favorite(item_key, not is_favorite)
                    st.rerun()
                if item.get("hazards"):
                    st.warning(f"⚠️ Có {len(item['hazards'])} cảnh báo.")
                if item.get("money", {}).get("detected"):
                    st.write(f"💵 {item['money'].get('denomination','')}")
                if item.get("text"):
                    st.text(item["text"])
        st.divider()
        confirm_delete = st.checkbox("Tôi xác nhận muốn xóa toàn bộ lịch sử đã lưu trên máy", key="confirm_delete_history")
        if st.button("🗑️ Xóa toàn bộ lịch sử", disabled=not confirm_delete, type="secondary"):
            clear_history()
            st.success("Đã xóa lịch sử lưu cục bộ.")
            st.rerun()

elif page == "📊 Thống kê":
    st.subheader("📊 Thống kê sử dụng")
    history = load_history()
    total = len(history)
    hazards = sum(bool(x.get("hazards")) for x in history)
    money = sum(bool(x.get("money", {}).get("detected")) for x in history)
    ocr = sum(bool(x.get("text")) for x in history)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lần phân tích", total)
    c2.metric("Có cảnh báo", hazards)
    c3.metric("OCR", ocr)
    c4.metric("Nhận diện tiền", money)
    if history:
        modes = {}
        for x in history:
            modes[x.get("mode", "Khác")] = modes.get(x.get("mode", "Khác"), 0) + 1
        st.subheader("Phân bố chế độ")
        for mode_name, count in sorted(modes.items(), key=lambda x: -x[1]):
            st.write(f"**{mode_name}** — {count} lần")

elif page == "⚙️ Cài đặt":
    st.subheader("⚙️ Cài đặt")
    st.session_state.voice = st.toggle("🔊 Bật các nút đọc kết quả", value=st.session_state.voice)
    st.session_state.detail = st.selectbox("Mức chi tiết mặc định", ["Thấp", "Vừa", "Cao"], index=["Thấp", "Vừa", "Cao"].index(st.session_state.detail))
    voice_options = {"Nữ — Hoài My (tiếng Việt)": "vi-VN-HoaiMyNeural", "Nam — Nam Minh (tiếng Việt)": "vi-VN-NamMinhNeural"}
    current_voice = st.session_state.get("tts_voice", "vi-VN-HoaiMyNeural")
    current_label = next((label for label, value in voice_options.items() if value == current_voice), next(iter(voice_options)))
    selected_voice = st.selectbox("Giọng đọc trợ lý Vision", list(voice_options.keys()), index=list(voice_options.keys()).index(current_label))
    st.session_state.tts_voice = voice_options[selected_voice]
    st.info("Model Gemini thử theo thứ tự: " + " → ".join(get_gemini_models()))
    if st.session_state.gemini_connection_result:
        st.success(st.session_state.gemini_connection_result)
    if st.button(
        "🧪 Kiểm tra kết nối Gemini",
        type="primary",
        use_container_width=True,
        on_click=set_robot_state,
        args=("thinking", "Mình đang kiểm tra kết nối Gemini…"),
    ):
        if not is_api_ready():
            message = friendly_error_message("Chưa có GEMINI_API_KEY.")
            set_robot_state("error", message)
            st.session_state.robot_error_detail = "Chưa tìm thấy GEMINI_API_KEY trong file .env."
            st.rerun()
        else:
            try:
                st.session_state.last_history_id = None
                with st.spinner("Đang kiểm tra API key và quyền truy cập model…"):
                    check = test_gemini_connection()
                st.session_state.gemini_connection_result = (
                    f"Kết nối Gemini thành công · Model: {check['model']}"
                )
                set_robot_state("reassuring", "Gemini đã phản hồi. Mình sẵn sàng trò chuyện.")
                st.rerun()
            except Exception as exc:
                set_robot_state("error", friendly_error_message(exc))
                st.session_state.robot_error_detail = str(exc)
                st.rerun()
    st.info("🔤 OCR cục bộ: Tesseract + tiếng Việt — chạy trên máy nếu đã cài bộ dữ liệu ngôn ngữ.")
    st.caption("Vision phản hồi theo tác vụ trong ứng dụng và tôn trọng thiết lập giảm chuyển động của trình duyệt.")
    st.info(f"🔊 TTS: Edge TTS ({os.getenv('EDGE_TTS_VOICE', 'vi-VN-HoaiMyNeural')}) — không cần OpenAI API.")
    st.info("🎙️ STT: Nhận dạng tiếng Việt qua Google Speech Recognition; cần Internet và xử lý âm thanh qua dịch vụ bên ngoài.")
    st.warning("Không đưa API key vào ảnh chụp màn hình, GitHub hoặc file chia sẻ công khai.")

elif page == "ℹ️ Hướng dẫn":
    st.subheader("ℹ️ Hướng dẫn sử dụng")
    st.markdown("""
**1. Nhìn ảnh:** tải ảnh hoặc mở camera, chọn chế độ và bấm **Phân tích ngay**.

**2. Hỗ trợ di chuyển:** dùng ảnh phía trước để AI ưu tiên lối đi, vật cản, cầu thang và nguy cơ.

**3. Hỏi đáp:** sau khi có ảnh, đặt nhiều câu hỏi liên tiếp về cùng ảnh.

**4. Giọng nói:** ghi âm câu hỏi tiếng Việt → chuyển thành chữ → gửi cho AI → nghe câu trả lời.

**5. OCR / tiền:** chọn đúng chế độ để ưu tiên đọc chữ hoặc nhận diện mệnh giá.

**6. Lịch sử & thống kê:** theo dõi các lần phân tích đã thực hiện.

**7. Lệnh giọng nói:** trong mục Trợ lý giọng nói, nói “mở camera”, “mở OCR”, “mở lịch sử”, “tìm cái cốc”, “đọc lại kết quả” hoặc “trợ giúp”, rồi bấm nhận diện. Lệnh tìm vật cần có ảnh đã phân tích.

**8. Tìm vật trong ảnh:** sau khi phân tích ảnh, nhập tên vật cần tìm. Vision chỉ trả lời theo ảnh hiện có; kết quả không phải định vị chính xác.

**9. Mục yêu thích:** trong Lịch sử, đánh dấu kết quả bằng nút Thêm vào yêu thích rồi lọc danh sách theo mục đã lưu.

> ⚠️ Đây là công cụ hỗ trợ, không phải thiết bị dẫn đường hoặc phát hiện vật cản được chứng nhận. Không dựa riêng vào AI để qua đường hay di chuyển trong môi trường nguy hiểm.
""")
