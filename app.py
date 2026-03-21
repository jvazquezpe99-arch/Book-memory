import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
import uuid
import json

from database import init_db, cargar_desde_csv, get_all_books, update_book, add_book, delete_book
from google_books import buscar_libros, buscar_novedades, buscar_por_autor
from recommender import recomendar_libros, libros_pendientes_saga

import os as _os
import requests as _requests

try:
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", _os.environ.get("GROQ_API_KEY", ""))
except:
    GROQ_API_KEY = _os.environ.get("GROQ_API_KEY", "")
GROQ_OK = bool(GROQ_API_KEY)

def _groq_chat(prompt, max_tokens=1500):
    """Llama al API de Groq (gratis) con llama-3."""
    resp = _requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        },
        timeout=45,
    )
    if not resp.ok:
        raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"].strip()

PHOTO_B64 = "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"

# Favicon — square PNG pre-generado a 64x64
from PIL import Image
import base64 as _b64, io as _io
FAVICON_B64 = "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"
_fav_img = Image.open(_io.BytesIO(_b64.b64decode(FAVICON_B64))).convert("RGBA")

st.set_page_config(page_title="Book Memory", page_icon=_fav_img, layout="wide", initial_sidebar_state="expanded")

# ── Session state ──────────────────────────────────────────
for k, v in [("nav_pagina","🏠 Inicio"),("timer_activo",False),
             ("timer_inicio",None),("timer_libro_id",None),
             ("db_loaded",False),("meta_anual",30),
             ("editing_id",""),("bib_page",0),
             ("f_bus",""),("f_gen","Todos"),("f_est","Todos"),("f_sag","Todas")]:
    if k not in st.session_state:
        st.session_state[k] = v

def ir_a(p):
    st.session_state["nav_pagina"] = p
    st.query_params.clear()
    st.rerun()

# ── Query params bridge ──────────────────────────────────────
_qp = st.query_params
_action = _qp.get("action","")
if _action == "edit":
    st.session_state["editing_id"] = _qp.get("id","")
    st.session_state["nav_pagina"] = "📖 Mi Biblioteca"
    st.query_params.clear(); st.rerun()
if _action == "delete":
    _did = _qp.get("id","")
    if _did: delete_book(_did)
    st.query_params.clear(); st.rerun()

# ══════════════════════════════════════════════════════════════
#  ESTILOS GLOBALES
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Nunito:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Nunito', sans-serif; background: #F7F3EE; }
h1,h2,h3 { font-family: 'Playfair Display', serif; color: #3D2B1F; }

.stSidebar { background: #130C04 !important; }
.stSidebar * { color: #DDD3C8 !important; }
.stSidebar .stButton > button {
    background: transparent !important; border: none !important;
    box-shadow: none !important; color: #7A6A5E !important;
    text-align: left !important; padding: 9px 20px !important;
    font-size: 0.72rem !important; font-weight: 700 !important;
    border-radius: 0 !important; margin: 0 !important;
    transition: all 0.12s !important; width: 100% !important;
    letter-spacing: 1.8px !important; text-transform: uppercase !important;
    border-left: 2px solid transparent !important;
}
.stSidebar .stButton > button:hover {
    background: rgba(196,120,58,0.07) !important;
    color: #D4A976 !important; transform: none !important;
    box-shadow: none !important;
    border-left: 2px solid rgba(196,120,58,0.35) !important;
    padding-left: 24px !important;
}
.stSidebar [data-testid="stButton"] { margin: 0 !important; padding: 0 !important; }
.section-title {
    font-family: 'Playfair Display', serif; font-size: 2rem;
    color: #3D2B1F; border-bottom: 3px solid #C4783A;
    padding-bottom: 10px; margin-bottom: 24px;
}
.stButton > button {
    background: linear-gradient(135deg, #C4783A, #A0622E) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    font-family: 'Nunito', sans-serif !important;
    box-shadow: 0 3px 10px rgba(196,120,58,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(196,120,58,0.45) !important;
}
div[data-testid="metric-container"] {
    background: white; border-radius: 14px; padding: 16px;
    box-shadow: 0 4px 14px rgba(61,43,31,0.08);
    border-bottom: 3px solid #C4783A;
}
.stTabs [data-baseweb="tab"] { font-weight: 700 !important; font-family: 'Nunito', sans-serif !important; border-radius: 10px 10px 0 0 !important; }
.stTabs [aria-selected="true"] { background: #C4783A !important; color: white !important; }
.stTextInput input, .stTextArea textarea {
    border-radius: 10px !important; border: 2px solid #E8DDD4 !important;
    background: #FEFCF9 !important; font-family: 'Nunito', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #C4783A !important;
    box-shadow: 0 0 0 3px rgba(196,120,58,0.12) !important;
}
.badge { display:inline-block; padding:3px 11px; border-radius:20px; font-size:11px; font-weight:800; margin:2px; }
.badge-fantasia   { background:#EDE0FF; color:#5B2D8E; }
.badge-romantasy  { background:#FFE0EE; color:#C2185B; }
.badge-romance    { background:#FCE4EC; color:#AD1457; }
.badge-thriller   { background:#FFF3E0; color:#E65100; }
.badge-historica  { background:#E0F2F1; color:#00695C; }
.badge-ficcion    { background:#E8EAF6; color:#283593; }
.badge-juvenil    { background:#FFF9C4; color:#F57F17; }
.badge-clasico    { background:#EFEBE9; color:#4E342E; }
.badge-paranormal { background:#F3E5F5; color:#6A1B9A; }
.badge-distopia   { background:#E3F2FD; color:#1565C0; }
.badge-terror     { background:#FCE4EC; color:#B71C1C; }
.badge-darkrom    { background:#EDE0FF; color:#4A148C; }
.badge-misterio   { background:#E0F2F1; color:#004D40; }
.badge-comics     { background:#FBE9E7; color:#BF360C; }
.badge-leido      { background:#E8F5E9; color:#2E7D32; }
.badge-leyendo    { background:#E3F2FD; color:#1565C0; }
.badge-pendiente  { background:#FFFDE7; color:#F57F17; }
.badge-pausado    { background:#F3E5F5; color:#6A1B9A; }
.badge-abandonado { background:#F5F5F5; color:#757575; }
.badge-especial   { background:linear-gradient(135deg,#FFD700,#FFA000); color:#3E2723; }
.hero-banner {
    background: linear-gradient(135deg, #1C1008 0%, #4A2810 50%, #C4783A 100%);
    border-radius: 24px; padding: 36px 42px; color: white; margin-bottom: 28px;
    box-shadow: 0 12px 40px rgba(28,16,8,0.3);
}
.hero-title { font-family:'Playfair Display',serif; font-size:2.6rem; margin:0; color:white !important; font-style:italic; }
.hero-sub { color:#F5D0A9; font-size:1.05rem; margin-top:8px; font-weight:600; }
.streak-card {
    background: linear-gradient(135deg, #C4783A, #E8A87C);
    border-radius: 20px; padding: 20px; color:white; text-align:center;
    box-shadow: 0 8px 24px rgba(196,120,58,0.4);
}
.streak-num { font-family:'Playfair Display',serif; font-size:3.2rem; font-weight:700; line-height:1; }
.streak-lbl { font-size:0.75rem; font-weight:800; opacity:0.9; text-transform:uppercase; letter-spacing:1.2px; margin-top:4px; }
.prog-wrap { background:#F0E8E0; border-radius:20px; height:8px; overflow:hidden; margin:4px 0; }
.prog-fill { background:linear-gradient(90deg,#C4783A,#F4A460); height:100%; border-radius:20px; }
.book-card-v2 {
    background:white; border-radius:16px; padding:16px; margin:6px 0;
    box-shadow:0 4px 16px rgba(61,43,31,0.09); border-left:4px solid #C4783A;
    transition:all 0.2s;
}
.book-card-v2:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(61,43,31,0.16); }
.star-rating { color:#F4B942; font-size:1rem; }
.cal-table { width:100%; border-collapse:separate; border-spacing:3px; }
.cal-h { text-align:center; padding:8px 2px; color:#C4783A; font-weight:800; font-size:0.78rem; text-transform:uppercase; letter-spacing:1px; }
.timer-box {
    background:linear-gradient(135deg,#1C1008,#3D2B1F);
    border-radius:16px; padding:18px; color:white; text-align:center;
}
.timer-display { font-family:'Playfair Display',serif; font-size:3rem; color:white; letter-spacing:4px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  INIT DB
# ══════════════════════════════════════════════════════════════
init_db()
if not st.session_state["db_loaded"]:
    cargar_desde_csv("biblioteca_personal.csv")
    st.session_state["db_loaded"] = True

# ══════════════════════════════════════════════════════════════
#  CONSTANTS & HELPERS
# ══════════════════════════════════════════════════════════════
ESTADOS = ["Leído","Leyendo","Quiero leer","Pausado","Abandonado"]
TODOS_GENEROS = ["Fantasía","Romantasy","Romance","Juvenil","Thriller","Histórica",
                 "Ficción","Clásico","Paranormal","Distopía","Ciencia Ficción",
                 "Misterio","Terror","Dark Romance","Cómics","Autoayuda","Ensayo","Otro"]
MESES_ES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

BADGE_MAP = {
    "Fantasía":"fantasia","Romantasy":"romantasy","Romance":"romance","Juvenil":"juvenil",
    "Thriller":"thriller","Histórica":"historica","Ficción":"ficcion","Clásico":"clasico",
    "Paranormal":"paranormal","Distopía":"distopia","Ciencia Ficción":"ficcion",
    "Misterio":"misterio","Terror":"terror","Dark Romance":"darkrom","Cómics":"comics",
    "Autoayuda":"ficcion","Ensayo":"ficcion",
}
ESTADO_MAP = {"Leído":"leido","Leyendo":"leyendo","Quiero leer":"pendiente",
              "Pausado":"pausado","Abandonado":"abandonado"}

def safe_str(v):
    if v is None or str(v) in ["nan","None",""]: return ""
    return str(v)

def safe_int(v, d=0):
    if v is None or str(v) in ["","nan","None"]: return d
    try: return int(float(v))
    except: return d

def safe_float(v, d=0.0):
    if v is None or str(v) in ["","nan","None"]: return d
    try: return max(0.0, min(5.0, float(v)))
    except: return d

def get_stars(r):
    if not r or str(r) in ["nan","None",""]: return "☆☆☆☆☆"
    try:
        r=float(r); f=int(r); h=1 if r-f>=0.5 else 0
        return "★"*f+("½" if h else "")+"☆"*(5-f-h)
    except: return "☆☆☆☆☆"

def badge_g(genero):
    g=str(genero).split(",")[0].strip()
    cls=BADGE_MAP.get(g,"ficcion")
    return f'<span class="badge badge-{cls}">{g}</span>'

def badge_e(estado):
    cls=ESTADO_MAP.get(estado,"pendiente")
    return f'<span class="badge badge-{cls}">{estado}</span>'

def cover_url(url):
    u = safe_str(url)
    if u: return u.replace("zoom=1","zoom=0").replace("http://","https://")
    return ""

def cover_img(url, w=65, h=93):
    u = cover_url(url)
    if u: return f'<img src="{u}" style="width:{w}px;height:{h}px;object-fit:cover;border-radius:10px;box-shadow:2px 4px 10px rgba(0,0,0,0.18);flex-shrink:0">'
    return f'<div style="width:{w}px;height:{h}px;background:linear-gradient(135deg,#F5D0A9,#C4783A);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:{w//3}px;flex-shrink:0">📖</div>'

def clean_saga(s):
    v = safe_str(s)
    return "" if v.lower() in ["no","nan","none",""] else v

def calcular_racha(df):
    if df.empty: return 0
    dias = set()
    for _, row in df.iterrows():
        for col in ["fecha_fin","fecha_inicio"]:
            fs = safe_str(row.get(col,""))
            if fs:
                try: dias.add(datetime.strptime(fs[:10],"%Y-%m-%d").date())
                except: pass
    racha=0; d=date.today()
    while d in dias: racha+=1; d-=timedelta(days=1)
    return racha

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_portada(titulo, autor):
    """Busca portada en Google Books directamente."""
    import requests as _req
    for query in [f"{titulo} {autor}", titulo]:
        try:
            r = _req.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": query, "maxResults": 3},
                timeout=8
            )
            for item in r.json().get("items", []):
                links = item.get("volumeInfo", {}).get("imageLinks", {})
                img = (links.get("thumbnail") or links.get("smallThumbnail", ""))
                if img:
                    return img.replace("zoom=1","zoom=0").replace("http://","https://")
        except: pass
    return ""

def get_cover(row):
    """URL guardada primero; si no hay, busca en Google Books y GUARDA en BD."""
    u = cover_url(row.get("imagen_portada_url",""))
    if not u:
        u = fetch_portada(safe_str(row.get("titulo","")), safe_str(row.get("autor","")))
        if u:
            try: update_book(row["id"], {"imagen_portada_url": u})
            except: pass
    return u

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    # Sidebar header luxury
    _sb_photo = f'data:image/png;base64,{PHOTO_B64}'
    st.markdown(f"""
    <div style="padding:20px 12px 16px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
            <img src="{_sb_photo}" style="width:42px;height:42px;border-radius:50%;object-fit:cover;
                border:1.5px solid rgba(196,120,58,0.5);flex-shrink:0;opacity:0.92">
            <div>
                <div style="font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;
                    color:#E8DDD3;letter-spacing:0.3px;line-height:1.1">Book Memory</div>
                <div style="font-size:0.6rem;color:rgba(196,120,58,0.7);font-weight:600;
                    letter-spacing:2px;text-transform:uppercase;margin-top:3px">Biblioteca Personal</div>
            </div>
        </div>
        <div style="height:1px;background:linear-gradient(90deg,rgba(196,120,58,0.5),transparent)"></div>
    </div>
    """, unsafe_allow_html=True)

    pagina_act = st.session_state["nav_pagina"]
    nav_items = [
        ("Inicio","🏠 Inicio"),
        ("Mi Biblioteca","📖 Mi Biblioteca"),
        ("Buscar Libros","🔍 Buscar Libro"),
        ("Estadísticas","📊 Estadísticas"),
        ("Para ti","✨ Recomendaciones"),
        ("Novedades","🆕 Novedades"),
        ("Calendario","📅 Calendario"),
        ("Mis Metas","🎯 Mis Metas"),
    ]
    # Render: active = styled div, inactive = button
    # This always works, no JS needed
    for label, key in nav_items:
        if key == pagina_act:
            st.markdown(f'''<div style="
                padding:10px 20px;font-size:0.72rem;font-weight:800;
                letter-spacing:1.8px;text-transform:uppercase;
                color:#D4A976;border-left:2px solid #C4783A;
                background:rgba(196,120,58,0.12);margin:1px 0;
                font-family:Nunito,sans-serif">{label}</div>''', unsafe_allow_html=True)
        else:
            if st.button(label, key=f"sb_{key}", use_container_width=True):
                ir_a(key)

    st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:10px 0">', unsafe_allow_html=True)
    df_all = get_all_books()
    if not df_all.empty:
        leidos_s = len(df_all[df_all["estado"]=="Leído"])
        leyendo_s = len(df_all[df_all["estado"]=="Leyendo"])
        total_s = len(df_all)
        racha_s = calcular_racha(df_all)
        st.markdown(f"""
        <div style="margin:8px;background:rgba(196,120,58,0.1);border-radius:10px;
            padding:12px;text-align:center;border:1px solid rgba(196,120,58,0.2)">
            <div style="font-size:0.55rem;color:rgba(196,120,58,0.7);text-transform:uppercase;
                letter-spacing:2px;font-weight:700;margin-bottom:4px">Racha</div>
            <div style="font-size:1.8rem;font-weight:700;color:#E8C9A0;
                font-family:'Playfair Display',serif;line-height:1">{racha_s}</div>
            <div style="font-size:0.55rem;color:#5A4A3E;letter-spacing:1px;margin-top:3px">días consecutivos</div>
        </div>
        """, unsafe_allow_html=True)
        _esp_s = len(df_all[df_all["edicion_especial"]==1])
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:0 8px 8px">
            <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:10px 8px;
                text-align:center;border:1px solid rgba(255,255,255,0.06)">
                <div style="font-size:1.4rem;font-weight:700;color:#E8C9A0;
                    font-family:'Playfair Display',serif;line-height:1">{total_s}</div>
                <div style="font-size:0.55rem;color:#5A4A3E;text-transform:uppercase;
                    letter-spacing:1.5px;margin-top:3px;font-weight:700">Total</div>
            </div>
            <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:10px 8px;
                text-align:center;border:1px solid rgba(255,255,255,0.06)">
                <div style="font-size:1.4rem;font-weight:700;color:#A8D5B5;
                    font-family:'Playfair Display',serif;line-height:1">{leidos_s}</div>
                <div style="font-size:0.55rem;color:#5A4A3E;text-transform:uppercase;
                    letter-spacing:1.5px;margin-top:3px;font-weight:700">Leídos</div>
            </div>
            <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:10px 8px;
                text-align:center;border:1px solid rgba(255,255,255,0.06)">
                <div style="font-size:1.4rem;font-weight:700;color:#A0BFDE;
                    font-family:'Playfair Display',serif;line-height:1">{leyendo_s}</div>
                <div style="font-size:0.55rem;color:#5A4A3E;text-transform:uppercase;
                    letter-spacing:1.5px;margin-top:3px;font-weight:700">Leyendo</div>
            </div>
            <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:10px 8px;
                text-align:center;border:1px solid rgba(255,255,255,0.06)">
                <div style="font-size:1.4rem;font-weight:700;color:#F4D87A;
                    font-family:'Playfair Display',serif;line-height:1">{_esp_s}</div>
                <div style="font-size:0.55rem;color:#5A4A3E;text-transform:uppercase;
                    letter-spacing:1.5px;margin-top:3px;font-weight:700">Especiales</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

pagina = st.session_state["nav_pagina"]

# ══════════════════════════════════════════════════════════════
#  INICIO
# ══════════════════════════════════════════════════════════════
if pagina == "🏠 Inicio":
    hoy = date.today()
    df = get_all_books()
    df["valoracion_personal"] = pd.to_numeric(df.get("valoracion_personal", pd.Series(dtype=float)), errors="coerce")
    racha = calcular_racha(df) if not df.empty else 0
    leidos_count = len(df[df["estado"]=="Leído"]) if not df.empty else 0

    _hoy_str = hoy.strftime("%A, %d de %B de %Y").capitalize()
    _hero_html = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Nunito:wght@400;600;700;800&display=swap');
    *{{box-sizing:border-box;margin:0;padding:0;font-family:'Nunito',sans-serif}}
    .hero{{
        background:linear-gradient(145deg,#1C1008 0%,#3D2008 40%,#7A3C18 75%,#C4783A 100%);
        border-radius:20px;padding:28px 36px;color:white;
        box-shadow:0 12px 40px rgba(28,16,8,0.35);
        display:flex;justify-content:space-between;align-items:center;
        flex-wrap:wrap;gap:16px;
    }}
    .hero-left{{display:flex;align-items:center;gap:16px}}
    .hero-avatar{{width:64px;height:64px;border-radius:50%;object-fit:cover;
        border:2.5px solid rgba(255,255,255,0.3);
        box-shadow:0 4px 16px rgba(0,0,0,0.4);flex-shrink:0}}
    .hero-title{{font-family:'Playfair Display',serif;font-size:1.9rem;
        font-weight:700;color:white;line-height:1.1;margin-bottom:4px}}
    .hero-sub{{font-size:0.8rem;color:#F5D0A9;font-weight:600;opacity:0.9}}
    .hero-stats{{display:flex;gap:20px;align-items:center}}
    .hero-stat{{text-align:center}}
    .hero-stat-n{{font-family:'Playfair Display',serif;font-size:2rem;
        font-weight:700;line-height:1}}
    .hero-stat-l{{font-size:0.6rem;text-transform:uppercase;letter-spacing:1.5px;
        opacity:0.75;margin-top:3px;font-weight:700}}
    .divider{{width:1px;height:40px;background:rgba(255,255,255,0.15)}}
    </style>
    <div class="hero">
        <div class="hero-left">
            <img class="hero-avatar" src="data:image/png;base64,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">
            <div>
                <div class="hero-title">Book Memory</div>
                <div class="hero-sub">{_hoy_str}</div>
            </div>
        </div>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-n" style="color:#FFD700">{len(df)}</div>
                <div class="hero-stat-l">Libros</div>
            </div>
            <div class="divider"></div>
            <div class="hero-stat">
                <div class="hero-stat-n" style="color:#B8F5C8">{leidos_count}</div>
                <div class="hero-stat-l">Leídos</div>
            </div>
            <div class="divider"></div>
            <div class="hero-stat">
                <div class="hero-stat-n" style="color:#F4B942">{racha}</div>
                <div class="hero-stat-l">Días racha</div>
            </div>
        </div>
    </div>
    """
    components.html(_hero_html, height=130, scrolling=False)

    # Nav rápida con botones funcionales
    nav_rapida = [
        ("📖","Biblioteca","📖 Mi Biblioteca"),
        ("🔍","Buscar","🔍 Buscar Libro"),
        ("✨","Para ti","✨ Recomendaciones"),
        ("🆕","Novedades","🆕 Novedades"),
        ("📅","Calendario","📅 Calendario"),
        ("📊","Estadísticas","📊 Estadísticas"),
    ]
    # Nav rápida — un solo st.button con CSS que lo hace parecer card visual
    st.markdown("""
    <style>
    div[data-testid="column"] .stButton > button[kind="secondary"],
    div[data-testid="column"] .stButton > button {
        background: white !important;
        color: #3D2B1F !important;
        border: 2px solid transparent !important;
        border-radius: 18px !important;
        padding: 18px 8px !important;
        font-size: 0.82rem !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 16px rgba(61,43,31,0.08) !important;
        min-height: 85px !important;
        transition: all 0.2s !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        border-color: #C4783A !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 24px rgba(196,120,58,0.2) !important;
        background: #FDF6EE !important;
    }
    </style>
    """, unsafe_allow_html=True)
    cols6 = st.columns(6)
    for i,(ico,lab,dest) in enumerate(nav_rapida):
        with cols6[i]:
            if st.button(f"{ico}\n\n{lab}", key=f"ir_{dest}", use_container_width=True):
                ir_a(dest)

    st.markdown("")
    if not df.empty:
        col_cal, col_mid, col_right = st.columns([1.1, 1, 1])

        with col_cal:
            st.markdown(f"### 📅 {MESES_ES[hoy.month]} {hoy.year}")
            libros_mes = {}
            for _, row in df.iterrows():
                fs = safe_str(row.get("fecha_fin",""))
                if fs:
                    try:
                        fd = datetime.strptime(fs[:10],"%Y-%m-%d").date()
                        if fd.month==hoy.month and fd.year==hoy.year:
                            libros_mes.setdefault(fd.day,[]).append(safe_str(row.get("titulo",""))[:12])
                    except: pass
            dias = ["L","M","X","J","V","S","D"]
            hdr = "".join([f'<th class="cal-h">{d}</th>' for d in dias])
            rows_c = ""
            for week in calendar.monthcalendar(hoy.year, hoy.month):
                rows_c += "<tr>"
                for d in week:
                    if d==0: rows_c += "<td></td>"
                    else:
                        bg = "background:#FFF3E0;border:2px solid #C4783A;" if d==hoy.day else "background:white;"
                        bs = "".join([f'<div style="background:#E8F5E9;color:#2E7D32;border-radius:5px;padding:1px 4px;font-size:0.6rem;font-weight:700;margin-top:1px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">✅ {b}</div>' for b in libros_mes.get(d,[])])
                        rows_c += f'<td style="padding:3px;vertical-align:top"><div style="{bg}border-radius:8px;padding:5px;border:1px solid #EDE0D0;min-height:56px"><b style="font-size:0.8rem;color:#3D2B1F">{d}</b>{bs}</div></td>'
                rows_c += "</tr>"
            st.markdown(f'<table class="cal-table"><thead><tr>{hdr}</tr></thead><tbody>{rows_c}</tbody></table>', unsafe_allow_html=True)
            st.markdown("")

            # Temporizador
            st.markdown("### ⏱️ Temporizador")
            libros_act = df[df["estado"]=="Leyendo"]["titulo"].tolist() if not df.empty else []
            if libros_act:
                libro_t = st.selectbox("", libros_act, key="sel_timer", label_visibility="collapsed")
                lid = df[df["titulo"]==libro_t].iloc[0]["id"] if libro_t else None
                if st.session_state["timer_activo"] and st.session_state["timer_inicio"]:
                    elapsed = datetime.now() - st.session_state["timer_inicio"]
                    m = int(elapsed.total_seconds()//60); s = int(elapsed.total_seconds()%60)
                    st.markdown(f'<div class="timer-box"><div style="font-size:0.72rem;color:#F5D0A9;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">⏱️ Leyendo</div><div class="timer-display">{m:02d}:{s:02d}</div></div>', unsafe_allow_html=True)
                    if st.button("⏹ Parar y guardar", use_container_width=True, key="btn_stop"):
                        em = int(elapsed.total_seconds()//60)
                        if st.session_state["timer_libro_id"]:
                            r_t = df[df["id"]==st.session_state["timer_libro_id"]]
                            if not r_t.empty:
                                old = safe_int(r_t.iloc[0].get("tiempo_lectura_min",0))
                                update_book(st.session_state["timer_libro_id"], {"tiempo_lectura_min": old+em})
                        st.session_state.update({"timer_activo":False,"timer_inicio":None,"timer_libro_id":None})
                        st.success(f"✅ {em} min guardados")
                        st.rerun()
                else:
                    if st.button("▶️ Iniciar sesión de lectura", use_container_width=True, key="btn_start"):
                        st.session_state.update({"timer_activo":True,"timer_inicio":datetime.now(),"timer_libro_id":lid})
                        st.rerun()
            else:
                st.caption("Marca un libro como 'Leyendo' para usar el temporizador")

        with col_mid:
            st.markdown("### 🌟 Mejor valorados")
            top = df[df["valoracion_personal"].notna()].sort_values("valoracion_personal",ascending=False).head(5)
            for _, row in top.iterrows():
                u = get_cover(row)
                img = cover_img(u, 44, 62)
                title_html = f'<b style="font-size:0.88rem;color:#3D2B1F;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_str(row["titulo"])}</b>'
                st.markdown('<div class="book-card-v2" style="padding:10px;display:flex;gap:10px;align-items:center">' +
                    img + '<div style="min-width:0;flex:1">' + title_html +
                    f'<small style="color:#9E8F84">{safe_str(row["autor"])}</small><br>' +
                    f'<span class="star-rating">{get_stars(row["valoracion_personal"])}</span>' +
                    '</div></div>', unsafe_allow_html=True)

        with col_right:
            st.markdown("### 📖 Leyendo ahora")
            leyendo_df = df[df["estado"]=="Leyendo"]
            if leyendo_df.empty:
                st.info("No estás leyendo nada ahora.")
            else:
                for _, row in leyendo_df.iterrows():
                    tp = safe_int(row.get("paginas_total",0))
                    lp = safe_int(row.get("paginas_leidas",0))
                    pct = int(lp/tp*100) if tp>0 else 0
                    u = get_cover(row)
                    img = cover_img(u, 50, 72)
                    tm = safe_int(row.get("tiempo_lectura_min",0))
                    st.markdown(
                        '<div class="book-card-v2" style="padding:12px">' +
                        '<div style="display:flex;gap:12px;align-items:flex-start">' + img +
                        f'<div style="flex:1;min-width:0"><b style="color:#3D2B1F;font-size:0.92rem;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_str(row["titulo"])}</b>' +
                        f'<small style="color:#9E8F84">{safe_str(row["autor"])}</small>' +
                        f'<div class="prog-wrap" style="margin:6px 0"><div class="prog-fill" style="width:{pct}%"></div></div>' +
                        f'<small style="color:#C4783A;font-weight:700">{pct}% · {lp}/{tp} pág.</small>' +
                        (f'<br><small style="color:#9E8F84">⏱️ {tm//60}h {tm%60}min leídos</small>' if tm>0 else "") +
                        '</div></div></div>', unsafe_allow_html=True)

        # Géneros pills
        st.markdown("---")
        st.markdown("### 🎨 Tus géneros")
        gc = df.groupby("genero").size().reset_index(name="n").sort_values("n",ascending=False).head(10)
        def _pill(r):
            g_p=safe_str(r["genero"]); cls_p=BADGE_MAP.get(g_p,"ficcion")
            return f'<span class="badge badge-{cls_p}" style="font-size:0.9rem;padding:6px 16px;margin:3px;cursor:default">{g_p} <b>{int(r["n"])}</b></span>'
        pills="".join([_pill(r) for _,r in gc.iterrows()])
        st.markdown(f'<div style="margin-bottom:4px;line-height:2.2">{pills}</div>', unsafe_allow_html=True)

        # Sagas grid
        st.markdown("---")
        sagas_df = df[df["saga"].notna() & (df["saga"]!="") & (df["saga"].str.strip()!="")].copy()
        if not sagas_df.empty:
            col_h1, col_h2 = st.columns([4,1])
            with col_h1: st.markdown("### 📚 Tus sagas")
            with col_h2:
                if st.button("Ver todas →", key="ver_sagas"): ir_a("📖 Mi Biblioteca")
            def _furl(series):
                for v in series:
                    if v and str(v).strip() and str(v) not in ["nan","None",""]: return str(v)
                return ""
            sagas_res = sagas_df.groupby("saga").agg(
                total=("id","count"), leidos=("estado", lambda x:(x=="Leído").sum()),
                autor=("autor","first"), portada=("imagen_portada_url", _furl),
            ).reset_index().sort_values("total",ascending=False).head(8)
            cols4 = st.columns(4)
            for i,(_, saga) in enumerate(sagas_res.iterrows()):
                with cols4[i%4]:
                    u = cover_url(saga.get("portada",""))
                    if not u:
                        primer_lib = sagas_df[sagas_df["saga"]==saga["saga"]].iloc[0]
                        u = fetch_portada(safe_str(primer_lib.get("titulo","")), safe_str(primer_lib.get("autor","")))
                    img_s = f'<img src="{u}" style="width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:12px 12px 0 0">' if u else '<div style="width:100%;aspect-ratio:2/3;background:linear-gradient(135deg,#F5D0A9,#C4783A);border-radius:12px 12px 0 0;display:flex;align-items:center;justify-content:center;font-size:2.5rem">📚</div>'
                    l_s = int(saga["leidos"]); t_s = int(saga["total"])
                    p_s = int(l_s/t_s*100) if t_s>0 else 0
                    st.markdown(
                        '<div style="background:white;border-radius:14px;overflow:hidden;box-shadow:0 4px 16px rgba(61,43,31,0.09);margin-bottom:8px">' +
                        img_s + f'<div style="padding:10px"><b style="font-size:0.82rem;color:#3D2B1F;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_str(saga["saga"])}</b>' +
                        f'<small style="color:#9E8F84">{safe_str(saga["autor"])}</small>' +
                        f'<div class="prog-wrap" style="margin:5px 0"><div class="prog-fill" style="width:{p_s}%"></div></div>' +
                        f'<small style="color:#C4783A;font-weight:700">{l_s}/{t_s} · {p_s}%</small></div></div>',
                        unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  MI BIBLIOTECA — Portadas visuales + Alpine filtros instantáneos
# ══════════════════════════════════════════════════════════════
elif pagina == "📖 Mi Biblioteca":
    st.markdown('<p class="section-title">📖 Mi Biblioteca</p>', unsafe_allow_html=True)
    df = get_all_books()

    # ── Panel edición (cuando se abre desde el expander) ──────
    if st.session_state["editing_id"]:
        book_id = st.session_state["editing_id"]
        row_e_df = df[df["id"] == book_id]
        if not row_e_df.empty:
            row_e = row_e_df.iloc[0]
            u_e = cover_url(row_e.get("imagen_portada_url",""))
            img_e = f'<img src="{u_e}" style="width:80px;height:115px;object-fit:cover;border-radius:10px;box-shadow:2px 4px 12px rgba(0,0,0,0.2)">' if u_e else '<div style="width:80px;height:115px;background:linear-gradient(135deg,#F5D0A9,#C4783A);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:2rem">📖</div>'
            st.markdown(f"""
            <div style="background:white;border-radius:20px;padding:20px 24px;
                box-shadow:0 8px 32px rgba(61,43,31,0.12);border-top:4px solid #C4783A;margin-bottom:20px">
                <div style="display:flex;gap:16px;align-items:center">
                    {img_e}
                    <div>
                        <h3 style="font-family:'Playfair Display',serif;color:#3D2B1F;margin:0 0 4px">{safe_str(row_e['titulo'])}</h3>
                        <p style="color:#9E8F84;margin:0;font-size:0.9rem;font-style:italic">{safe_str(row_e['autor'])}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            ec1, ec2 = st.columns(2)
            with ec1:
                nuevo_estado = st.selectbox("Estado", ESTADOS,
                    index=ESTADOS.index(row_e["estado"]) if row_e["estado"] in ESTADOS else 0,
                    key="edit_estado")
                val_e = safe_float(row_e.get("valoracion_personal"))
                nueva_val = st.slider("⭐ Valoración", 0.0, 5.0, val_e, 0.5, key="edit_val")
                resena = st.text_area("📝 Reseña", value=safe_str(row_e.get("resena_personal","")), height=90, key="edit_res")
                cita = st.text_area("✍️ Cita favorita", value=safe_str(row_e.get("cita_favorita","")), height=70, key="edit_cita")
            with ec2:
                ep1,ep2 = st.columns(2)
                pag_t = ep1.number_input("Pág. totales", value=safe_int(row_e.get("paginas_total")), min_value=0, key="edit_pt")
                pag_l = ep2.number_input("Leídas", value=safe_int(row_e.get("paginas_leidas")), min_value=0, key="edit_pl")
                tm_e = st.number_input("⏱️ Minutos leídos", value=safe_int(row_e.get("tiempo_lectura_min",0)), min_value=0, key="edit_tm")
                fi_v=None; ff_v=None
                fi_s=safe_str(row_e.get("fecha_inicio","")); ff_s=safe_str(row_e.get("fecha_fin",""))
                if fi_s:
                    try: fi_v=datetime.strptime(fi_s[:10],"%Y-%m-%d").date()
                    except: pass
                if ff_s:
                    try: ff_v=datetime.strptime(ff_s[:10],"%Y-%m-%d").date()
                    except: pass
                ef1,ef2 = st.columns(2)
                fi_e = ef1.date_input("📅 Inicio", value=fi_v, key="edit_fi")
                ff_e = ef2.date_input("📅 Fin", value=ff_v, key="edit_ff")
                # Cover URL editable
                new_cover = st.text_input("🖼️ URL portada", value=cover_url(row_e.get("imagen_portada_url","")), key="edit_cover")

            ce1,ce2,ce3 = st.columns(3)
            if ce1.button("💾 Guardar cambios", use_container_width=True, key="btn_save_edit"):
                update_book(book_id, {
                    "estado":nuevo_estado,"valoracion_personal":nueva_val,
                    "resena_personal":resena,"cita_favorita":cita,
                    "paginas_total":pag_t,"paginas_leidas":pag_l,"tiempo_lectura_min":tm_e,
                    "fecha_inicio":str(fi_e) if fi_e else "","fecha_fin":str(ff_e) if ff_e else "",
                    "imagen_portada_url":new_cover
                })
                st.session_state["editing_id"] = ""
                st.success("✅ Guardado correctamente")
                st.rerun()
            if ce2.button("🗑️ Eliminar libro", use_container_width=True, key="btn_del_edit"):
                delete_book(book_id)
                st.session_state["editing_id"] = ""
                st.warning("Libro eliminado"); st.rerun()
            if ce3.button("✖ Cancelar", use_container_width=True, key="btn_cancel_edit"):
                st.session_state["editing_id"] = ""; st.rerun()
            st.markdown("---")

    if df.empty:
        st.info("Tu biblioteca está vacía. ¡Busca tu primer libro!")
    else:
        df["valoracion_personal"] = pd.to_numeric(df["valoracion_personal"], errors="coerce")
        df["_ord_num"] = pd.to_numeric(df["orden_saga"], errors="coerce").fillna(0)

        # ── Alpine.js barra de búsqueda y filtros INSTANTÁNEA ──
        generos_opts_j = json.dumps(["Todos"]+sorted(df["genero"].dropna().unique().tolist()))
        estados_opts_j = json.dumps(["Todos"]+ESTADOS)
        sagas_opts_j = json.dumps(["Todas"]+sorted([s for s in df["saga"].dropna().unique()
                        if s and str(s).strip() and str(s).lower() not in ["no","nan",""]]))

        components.html(f"""
<script src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js" defer></script>
<style>
* {{ box-sizing:border-box; margin:0; padding:0; font-family:'Nunito','Segoe UI',sans-serif; }}
.filters {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; padding:4px 0; }}
.filters input,.filters select {{
    border:2px solid #E8DDD4; border-radius:10px; padding:8px 12px;
    font-size:13px; background:white; color:#3D2B1F; outline:none;
    transition:border-color .2s; font-family:inherit;
}}
.filters input:focus,.filters select:focus {{ border-color:#C4783A; }}
.filters input.srch {{ flex:1; min-width:200px; }}
.filters select {{ min-width:130px; }}
.chip {{
    background:#FDF6EE; border:2px solid #E8DDD4; color:#9E8F84;
    border-radius:10px; padding:8px 14px; font-size:12px; font-weight:700;
    cursor:pointer; font-family:inherit; transition:all .2s; white-space:nowrap;
}}
.chip.on {{ background:#C4783A; border-color:#C4783A; color:white; }}
.stats {{ font-size:12px; color:#9E8F84; padding:6px 2px; }}
.stats b {{ color:#3D2B1F; }}
</style>
<div x-data="filt()">
  <div class="filters">
    <input class="srch" type="text" x-model="b" @input="send()" placeholder="🔍 Buscar título o autor...">
    <select x-model="g" @change="send()">
      <template x-for="o in {generos_opts_j}"><option :value="o" x-text="o"></option></template>
    </select>
    <select x-model="e" @change="send()">
      <template x-for="o in {estados_opts_j}"><option :value="o" x-text="o"></option></template>
    </select>
    <select x-model="s" @change="send()">
      <template x-for="o in {sagas_opts_j}"><option :value="o" x-text="o"></option></template>
    </select>
    <select x-model="ord" @change="send()">
      <option value="az">A-Z Título</option>
      <option value="autor">Autor</option>
      <option value="val">⭐ Valoración</option>
      <option value="saga">Saga</option>
    </select>
    <button class="chip" :class="{{on:esp}}" @click="esp=!esp; send()">✨ Especiales</button>
  </div>
</div>
<script>
function filt(){{
  return {{
    b:"",g:"Todos",e:"Todos",s:"Todas",ord:"az",esp:false,
    send(){{
      const params=new URLSearchParams({{
        action:"filter",b:this.b,g:this.g,e:this.e,s:this.s,ord:this.ord,esp:this.esp?1:0
      }});
      window.parent.history.replaceState(null,"","?"+params.toString());
      // Trigger Streamlit rerun via postMessage
      window.parent.postMessage({{type:"streamlit:setComponentValue",value:{{b:this.b,g:this.g,e:this.e,s:this.s,ord:this.ord,esp:this.esp}}}}, "*");
    }}
  }}
}}
</script>
""", height=80, scrolling=False)

        # ── Leer filtros de session_state (persistentes) ──────
        c1f,c2f,c3f,c4f = st.columns(4)
        with c1f: busqueda = st.text_input("🔎 Buscar", value=st.session_state["f_bus"], placeholder="Título o autor...", key="fi_b", label_visibility="collapsed")
        with c2f:
            gens = ["Todos"]+sorted(df["genero"].dropna().unique().tolist())
            ig = gens.index(st.session_state["f_gen"]) if st.session_state["f_gen"] in gens else 0
            fg = st.selectbox("Género",gens,index=ig,key="fi_g",label_visibility="collapsed")
        with c3f:
            ef_opts = ["Todos"]+ESTADOS
            ie = ef_opts.index(st.session_state["f_est"]) if st.session_state["f_est"] in ef_opts else 0
            fe = st.selectbox("Estado",ef_opts,index=ie,key="fi_e",label_visibility="collapsed")
        with c4f:
            sag_l = ["Todas"]+sorted([s for s in df["saga"].dropna().unique()
                     if s and str(s).strip() and str(s).lower() not in ["no","nan",""]])
            is_idx = sag_l.index(st.session_state["f_sag"]) if st.session_state["f_sag"] in sag_l else 0
            fs = st.selectbox("Saga",sag_l,index=is_idx,key="fi_s",label_visibility="collapsed")

        c5f,c6f = st.columns([2,1])
        with c5f: orden = st.selectbox("Ordenar",["Título A-Z","Autor","Valoración ↓","Saga"],key="fi_ord",label_visibility="collapsed")
        with c6f: solo_esp = st.checkbox("✨ Solo especiales", key="fi_esp")

        # Persist filters
        st.session_state.update({"f_bus":busqueda,"f_gen":fg,"f_est":fe,"f_sag":fs})

        # Apply filters
        df_f = df.copy()
        if busqueda:
            m = df_f["titulo"].str.contains(busqueda,case=False,na=False)|df_f["autor"].str.contains(busqueda,case=False,na=False)
            df_f = df_f[m]
        if fg!="Todos": df_f = df_f[df_f["genero"]==fg]
        if fe!="Todos": df_f = df_f[df_f["estado"]==fe]
        if fs!="Todas": df_f = df_f[df_f["saga"]==fs]
        if solo_esp: df_f = df_f[df_f["edicion_especial"]==1]
        if orden=="Título A-Z": df_f=df_f.sort_values("titulo")
        elif orden=="Autor": df_f=df_f.sort_values("autor")
        elif orden=="Valoración ↓": df_f=df_f.sort_values("valoracion_personal",ascending=False)
        elif orden=="Saga": df_f=df_f.sort_values(["saga","_ord_num"])

        leidos_f = len(df_f[df_f["estado"]=="Leído"])
        leyendo_f = len(df_f[df_f["estado"]=="Leyendo"])
        st.markdown(f'<p style="color:#9E8F84;font-size:0.88rem;margin:4px 0 14px"><b style="color:#3D2B1F">{len(df_f)}</b> libros · <b style="color:#2E7D32">{leidos_f}</b> leídos · <b style="color:#1565C0">{leyendo_f}</b> leyendo</p>', unsafe_allow_html=True)

        st.markdown('### 📖 Mis libros')

        # Botón carga masiva de portadas
        sin_portada = df[df["imagen_portada_url"].isna() | (df["imagen_portada_url"] == "")]
        if len(sin_portada) > 0:
            col_carga, _ = st.columns([2,3])
            with col_carga:
                if st.button(f"🖼️ Cargar {len(sin_portada)} portadas que faltan", key="btn_cargar_portadas"):
                    progreso = st.progress(0, text="Cargando portadas...")
                    for idx_p, (_, row_p) in enumerate(sin_portada.iterrows()):
                        u_p = fetch_portada(safe_str(row_p.get("titulo","")), safe_str(row_p.get("autor","")))
                        if u_p:
                            try: update_book(row_p["id"], {"imagen_portada_url": u_p})
                            except: pass
                        progreso.progress((idx_p+1)/len(sin_portada), text=f"Portada {idx_p+1}/{len(sin_portada)}: {safe_str(row_p.get('titulo',''))[:30]}")
                    progreso.empty()
                    st.success("✅ ¡Portadas cargadas! Recargando...")
                    st.rerun()

        # ── Paginación ─────────────────────────────────────────
        PAGE_SIZE = 24
        n_pag = max(1,(len(df_f)+PAGE_SIZE-1)//PAGE_SIZE)
        if st.session_state["bib_page"] >= n_pag: st.session_state["bib_page"] = 0
        pg = st.session_state["bib_page"]
        df_page = df_f.iloc[pg*PAGE_SIZE:(pg+1)*PAGE_SIZE]

        if n_pag > 1:
            pn1,pn2,pn3 = st.columns([1,3,1])
            with pn1:
                if pg>0 and st.button("← Anterior",key="pg_p"): st.session_state["bib_page"]-=1; st.rerun()
            with pn2:
                st.markdown(f'<p style="text-align:center;color:#9E8F84;font-size:0.85rem;margin:8px 0">Página {pg+1} de {n_pag}</p>', unsafe_allow_html=True)
            with pn3:
                if pg<n_pag-1 and st.button("Siguiente →",key="pg_n"): st.session_state["bib_page"]+=1; st.rerun()

        # ── Grid de portadas 4 columnas ────────────────────────
        COLS = 4
        cols_grid = st.columns(COLS)
        for i,(_, row) in enumerate(df_page.iterrows()):
            with cols_grid[i % COLS]:
                u = get_cover(row)
                saga_s = clean_saga(row.get("saga",""))
                stars = get_stars(row.get("valoracion_personal"))
                bg = badge_g(safe_str(row.get("genero","")))
                be = badge_e(safe_str(row.get("estado","")))
                especial = row.get("edicion_especial",0) == 1

                # Portada grande
                if u:
                    cover_section = f'<img src="{u}" style="width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:14px 14px 0 0;display:block">'
                else:
                    cover_section = '<div style="width:100%;aspect-ratio:2/3;background:linear-gradient(135deg,#F5D0A9 0%,#C4783A 100%);border-radius:14px 14px 0 0;display:flex;align-items:center;justify-content:center;font-size:3.5rem">📖</div>'

                especial_pin = '<div style="position:absolute;top:8px;right:8px;background:linear-gradient(135deg,#FFD700,#FFA000);color:#3E2723;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;box-shadow:0 2px 6px rgba(0,0,0,0.2)">✨</div>' if especial else ""

                card_html = (
                    '<div style="background:white;border-radius:16px;overflow:hidden;'
                    'box-shadow:0 4px 20px rgba(61,43,31,0.10);position:relative;'
                    'transition:transform .2s,box-shadow .2s;margin-bottom:6px">' +
                    cover_section + especial_pin +
                    '<div style="padding:10px 12px 12px">' +
                    f'<div style="font-weight:800;font-size:0.82rem;color:#3D2B1F;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px">{safe_str(row["titulo"])}</div>' +
                    f'<div style="font-size:0.72rem;color:#9E8F84;font-style:italic;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:5px">{safe_str(row["autor"])}</div>' +
                    (f'<div style="font-size:0.68rem;color:#C4783A;font-weight:700;margin-bottom:4px">📚 {saga_s}</div>' if saga_s else "") +
                    '<div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:5px">' + bg + " " + be + '</div>' +
                    f'<div style="color:#F4B942;font-size:0.75rem">{stars}</div>' +
                    '</div></div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                # Edit button — sets session state, renders edit panel at TOP
                if st.button("✏️ Editar", key=f"edit_btn_{row['id']}", use_container_width=True):
                    st.session_state["editing_id"] = row["id"]
                    st.rerun()

        # ── Sagas ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📚 Mis sagas")
        sagas_bib = df[df["saga"].notna()&(df["saga"]!="")&(df["saga"].str.strip()!="")&(df["saga"].str.lower()!="nan")].copy()
        if not sagas_bib.empty:
            def _fus(series):
                for v in series:
                    if v and str(v).strip() and str(v) not in ["nan","None",""]: return str(v)
                return ""
            sr2 = sagas_bib.groupby("saga").agg(
                total=("id","count"), leidos=("estado", lambda x:(x=="Leído").sum()),
                autor=("autor","first"), portada=("imagen_portada_url", _fus),
            ).reset_index().sort_values("total",ascending=False)
            cols_s2 = st.columns(6)
            for i_s2,(_, sg2) in enumerate(sr2.iterrows()):
                with cols_s2[i_s2%6]:
                    u_s2 = cover_url(sg2.get("portada",""))
                    if not u_s2:
                        pr2 = sagas_bib[sagas_bib["saga"]==sg2["saga"]].iloc[0]
                        u_s2 = fetch_portada(safe_str(pr2.get("titulo","")), safe_str(pr2.get("autor","")))
                    ls2=int(sg2["leidos"]); ts2=int(sg2["total"])
                    ps2=int(ls2/ts2*100) if ts2>0 else 0
                    img_sg2 = f'<img src="{u_s2}" style="width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:10px 10px 0 0;display:block">' if u_s2 else '<div style="width:100%;aspect-ratio:2/3;background:linear-gradient(135deg,#F5D0A9,#C4783A);border-radius:10px 10px 0 0;display:flex;align-items:center;justify-content:center;font-size:2rem">📚</div>'
                    st.markdown(
                        '<div style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 14px rgba(61,43,31,0.09);margin-bottom:10px">' +
                        img_sg2 +
                        '<div style="padding:8px 10px">' +
                        f'<div style="font-weight:800;font-size:0.75rem;color:#3D2B1F;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_str(sg2["saga"])}</div>' +
                        f'<div style="font-size:0.65rem;color:#9E8F84;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_str(sg2["autor"])}</div>' +
                        f'<div class="prog-wrap" style="margin:4px 0"><div class="prog-fill" style="width:{ps2}%"></div></div>' +
                        f'<div style="font-size:0.65rem;color:#C4783A;font-weight:700">{ls2}/{ts2} · {ps2}%</div>' +
                        '</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  BUSCAR LIBRO
# ══════════════════════════════════════════════════════════════
elif pagina == "🔍 Buscar Libro":
    st.markdown('<p class="section-title">🔍 Buscar Libros</p>', unsafe_allow_html=True)
    tab1,tab2 = st.tabs(["🌐 Google Books","✍️ Añadir manual"])
    with tab1:
        st.markdown("*Busca cualquier libro del mundo y añádelo a tu biblioteca*")
        query = st.text_input("", placeholder="Título, autor o ISBN...", label_visibility="collapsed")
        if query and len(query)>=3:
            with st.spinner("Buscando..."):
                resultados = buscar_libros(query, max_results=10)
            if resultados:
                st.markdown(f"**{len(resultados)} resultados**")
                for idx_r,libro in enumerate(resultados):
                    c1,c2 = st.columns([1,5])
                    with c1:
                        u_l = cover_url(libro.get("imagen_portada_url",""))
                        if u_l: st.image(u_l, width=85)
                        else: st.markdown('<div style="width:85px;height:120px;background:linear-gradient(135deg,#EDD5B3,#C4783A);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:2rem">📖</div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"**{libro['titulo']}** · *{libro['autor']}* · {libro['anio']}")
                        st.markdown(f"<small>🏷️ {libro['genero']} · {libro['editorial']} · {libro['paginas_total']} pág.</small>", unsafe_allow_html=True)
                        if libro.get("descripcion") and libro["descripcion"] != "Sin descripción disponible.":
                            st.markdown(f"<small style='color:#9E8F84'>{libro['descripcion'][:200]}…</small>", unsafe_allow_html=True)
                        key_b = f"add_{idx_r}_{libro['isbn'][:6]}"
                        if st.button("➕ Añadir a mi biblioteca", key=key_b):
                            new_id = f"USR{str(uuid.uuid4())[:6].upper()}"
                            add_book({"id":new_id,"titulo":libro["titulo"],"autor":libro["autor"],
                                "saga":"","orden_saga":"","genero":libro["genero"],"editorial":libro["editorial"],
                                "formato":"Tapa Blanda","edicion_especial":0,"detalles_edicion":"",
                                "imagen_portada_url":cover_url(libro["imagen_portada_url"]),
                                "valoracion_personal":"","resena_personal":"","estado":"Quiero leer",
                                "paginas_total":libro["paginas_total"],"paginas_leidas":0,
                                "fecha_inicio":"","fecha_fin":"","tiempo_lectura_min":0,"cita_favorita":"","etiquetas":""})
                            st.success(f"✅ '{libro['titulo']}' añadido")
                    st.markdown('<hr style="border:none;border-top:1px solid #EDE0D0;margin:6px 0">', unsafe_allow_html=True)
            else:
                st.warning("Sin resultados. Prueba otro término.")
        elif query: st.caption("Escribe al menos 3 caracteres...")

    with tab2:
        with st.form("form_manual"):
            c1,c2 = st.columns(2)
            with c1:
                titulo=st.text_input("Título *"); autor=st.text_input("Autor *")
                saga=st.text_input("Saga"); orden=st.text_input("Nº en saga")
            with c2:
                genero=st.selectbox("Género",TODOS_GENEROS)
                editorial=st.text_input("Editorial")
                formato=st.selectbox("Formato",["Tapa Blanda","Tapa Dura","Ebook","Audiolibro","Bolsillo"])
                estado=st.selectbox("Estado",ESTADOS)
            edicion_esp=st.checkbox("✨ Edición especial"); detalles=st.text_input("Detalles")
            paginas=st.number_input("Páginas",min_value=0,value=300)
            if st.form_submit_button("➕ Añadir libro") and titulo and autor:
                add_book({"id":f"USR{str(uuid.uuid4())[:6].upper()}","titulo":titulo,"autor":autor,
                    "saga":saga,"orden_saga":orden,"genero":genero,"editorial":editorial,"formato":formato,
                    "edicion_especial":int(edicion_esp),"detalles_edicion":detalles,"imagen_portada_url":"",
                    "valoracion_personal":"","resena_personal":"","estado":estado,"paginas_total":paginas,
                    "paginas_leidas":0,"fecha_inicio":"","fecha_fin":"","tiempo_lectura_min":0,"cita_favorita":"","etiquetas":""})
                st.success(f"✅ '{titulo}' añadido")

# ══════════════════════════════════════════════════════════════
#  ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════
elif pagina == "📊 Estadísticas":
    st.markdown('<p class="section-title">📊 Mis Estadísticas</p>', unsafe_allow_html=True)
    df = get_all_books()
    if df.empty: st.info("Añade libros para ver estadísticas.")
    else:
        df["valoracion_personal"] = pd.to_numeric(df["valoracion_personal"],errors="coerce")
        leidos_df = df[df["estado"]=="Leído"].copy()
        n_leidos = len(leidos_df)
        media_val = leidos_df["valoracion_personal"].mean() if not leidos_df.empty and leidos_df["valoracion_personal"].notna().any() else 0
        n_sagas = df[df["saga"].notna()&(df["saga"]!="")&(df["saga"].str.lower()!="nan")]["saga"].nunique()
        n_autoras = df["autor"].nunique()
        pags = leidos_df["paginas_total"].apply(safe_int).sum()

        # ── KPIs principales ──────────────────────────────────
        k1,k2,k3,k4,k5 = st.columns(5)
        def _kpi(col, num, label, color="#C4783A"):
            col.markdown(f'''<div style="background:white;border-radius:14px;padding:18px 14px;
                text-align:center;box-shadow:0 4px 14px rgba(61,43,31,0.08);
                border-bottom:3px solid {color}">
                <div style="font-family:'Playfair Display',serif;font-size:2rem;font-weight:700;color:#3D2B1F;line-height:1">{num}</div>
                <div style="font-size:0.7rem;color:#9E8F84;text-transform:uppercase;letter-spacing:1px;margin-top:5px;font-weight:700">{label}</div>
            </div>''', unsafe_allow_html=True)
        _kpi(k1, n_leidos, "Libros leídos")
        _kpi(k2, f"{media_val:.1f} ★", "Valoración media", "#F4B942")
        _kpi(k3, n_sagas, "Sagas", "#5B2D8E")
        _kpi(k4, n_autoras, "Autoras distintas", "#00695C")
        _kpi(k5, f"{pags:,}".replace(",","."), "Páginas leídas", "#1565C0")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Fila 1: Géneros (barras horizontales) + Valoraciones ──
        col_g, col_v = st.columns(2)

        with col_g:
            st.markdown("#### 🎨 Tus géneros favoritos")
            gc = df.groupby("genero").size().reset_index(name="n").sort_values("n",ascending=True).tail(10)
            colores_gen = ["#EDE0FF","#FFE0EE","#FCE4EC","#FFF3E0","#E0F2F1","#E8EAF6","#FFF9C4","#EFEBE9","#F3E5F5","#E3F2FD"]
            texto_gen =  ["#5B2D8E","#C2185B","#AD1457","#E65100","#00695C","#283593","#F57F17","#4E342E","#6A1B9A","#1565C0"]
            fig_g = go.Figure()
            for i_g, (_, row_g) in enumerate(gc.iterrows()):
                c_idx = i_g % len(colores_gen)
                fig_g.add_trace(go.Bar(
                    x=[row_g["n"]], y=[row_g["genero"]], orientation="h",
                    text=[f" {row_g['n']} libros"], textposition="outside",
                    marker_color=colores_gen[c_idx], marker_line_color=texto_gen[c_idx],
                    marker_line_width=1.5, name=row_g["genero"],
                    hovertemplate=f"{row_g['genero']}: {row_g['n']} libros<extra></extra>",
                    textfont=dict(color="#3D2B1F", size=12)
                ))
            fig_g.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, height=360, font=dict(family="Nunito"),
                margin=dict(t=10,b=10,l=5,r=80),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(tickfont=dict(size=12, color="#3D2B1F")),
            )
            st.plotly_chart(fig_g, use_container_width=True)

        with col_v:
            st.markdown("#### ⭐ Distribución de valoraciones")
            df_val = leidos_df[leidos_df["valoracion_personal"].notna()].copy()
            if not df_val.empty:
                df_val["stars"] = df_val["valoracion_personal"].apply(
                    lambda v: f"{'★'*int(v)}{'½' if v-int(v)>=0.5 else ''} ({v})")
                vc = df_val["valoracion_personal"].value_counts().sort_index()
                labels_v = [f"{'★'*int(v)}{'½' if v-int(v)>=0.5 else ''}" for v in vc.index]
                cols_v = ["#F5F5F5","#FFE0B2","#FFB74D","#FF9800","#F57C00","#E65100","#BF360C","#C4783A","#8D4E1A","#3D2B1F"]
                fig_v = go.Figure(go.Bar(
                    x=labels_v, y=vc.values,
                    marker_color=[cols_v[min(int(v*2)-1,len(cols_v)-1)] for v in vc.index],
                    text=vc.values, textposition="outside",
                    textfont=dict(size=13, color="#3D2B1F"),
                    hovertemplate="%{x}: %{y} libros<extra></extra>",
                ))
                fig_v.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, height=360, font=dict(family="Nunito"),
                    margin=dict(t=10,b=10,l=5,r=10),
                    xaxis=dict(tickfont=dict(size=14), gridcolor="rgba(0,0,0,0.05)"),
                    yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                )
                # Línea media
                fig_v.add_vline(x=f"{'★'*int(media_val)}{'½' if media_val-int(media_val)>=0.5 else ''}",
                    line_dash="dot", line_color="#C4783A",
                    annotation_text=f"Media: {media_val:.1f}★",
                    annotation_position="top")
                st.plotly_chart(fig_v, use_container_width=True)
            else:
                st.info("Valora tus libros para ver esta gráfica.")

        # ── Fila 2: Top autoras + Libros por año ──────────────
        col_a, col_t = st.columns(2)

        with col_a:
            st.markdown("#### 👤 Tus autoras más leídas")
            ta = leidos_df.groupby("autor").agg(
                n=("id","count"),
                media=("valoracion_personal","mean")
            ).reset_index().sort_values("n",ascending=False).head(10)
            ta["media"] = ta["media"].fillna(0).round(1)
            ta_sorted = ta.sort_values("n", ascending=True)
            fig_a = go.Figure()
            fig_a.add_trace(go.Bar(
                y=ta_sorted["autor"], x=ta_sorted["n"],
                orientation="h", name="Libros",
                marker_color="#C4783A", marker_line_width=0,
                text=[f" {int(n)} libros · {m:.1f}★" for n,m in zip(ta_sorted["n"],ta_sorted["media"])],
                textposition="outside",
                textfont=dict(size=11, color="#3D2B1F"),
                hovertemplate="%{y}: %{x} libros<extra></extra>",
            ))
            fig_a.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, height=380, font=dict(family="Nunito"),
                margin=dict(t=10,b=10,l=5,r=140),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(tickfont=dict(size=11, color="#3D2B1F")),
            )
            st.plotly_chart(fig_a, use_container_width=True)

        with col_t:
            st.markdown("#### 📅 Libros terminados por año")
            df_ff = leidos_df[leidos_df["fecha_fin"].notna() & (leidos_df["fecha_fin"]!="")].copy()
            if not df_ff.empty:
                df_ff["anio"] = df_ff["fecha_fin"].apply(lambda x: safe_str(x)[:4])
                df_ff = df_ff[df_ff["anio"].str.match(r"\d{4}")]
                by_year = df_ff.groupby("anio").size().reset_index(name="n").sort_values("anio")
                fig_t = go.Figure(go.Bar(
                    x=by_year["anio"], y=by_year["n"],
                    marker_color="#C4783A",
                    text=by_year["n"], textposition="outside",
                    textfont=dict(size=13, color="#3D2B1F"),
                    hovertemplate="%{x}: %{y} libros<extra></extra>",
                ))
                fig_t.add_trace(go.Scatter(
                    x=by_year["anio"], y=by_year["n"],
                    mode="lines+markers",
                    line=dict(color="#F4B942", width=2.5),
                    marker=dict(color="#F4B942", size=8),
                    showlegend=False, hoverinfo="skip",
                ))
                fig_t.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, height=380, font=dict(family="Nunito"),
                    margin=dict(t=20,b=10,l=5,r=10),
                    xaxis=dict(tickfont=dict(size=12, color="#3D2B1F"), gridcolor="rgba(0,0,0,0.05)"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False,
                               tickfont=dict(color="#9E8F84")),
                    bargap=0.35,
                )
                st.plotly_chart(fig_t, use_container_width=True)
            else:
                st.info("Registra fechas de fin en tus libros para ver este gráfico.")

        # ── Fila 3: Top 10 mejor valorados con portadas ───────
        st.markdown("---")
        st.markdown("#### 🏆 Tus 10 libros favoritos")
        top10 = leidos_df[leidos_df["valoracion_personal"].notna()].sort_values("valoracion_personal",ascending=False).head(10)
        if not top10.empty:
            cols_top = st.columns(5)
            for i_t,(_, row_t) in enumerate(top10.head(10).iterrows()):
                with cols_top[i_t%5]:
                    u_t = cover_url(row_t.get("imagen_portada_url",""))
                    if u_t:
                        img_t = f'<img src="{u_t}" style="width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:10px;box-shadow:0 4px 12px rgba(0,0,0,0.15);margin-bottom:6px">'
                    else:
                        img_t = '<div style="width:100%;aspect-ratio:2/3;background:linear-gradient(135deg,#F5D0A9,#C4783A);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:2rem;margin-bottom:6px">📖</div>'
                    medal = ["🥇","🥈","🥉","4º","5º","6º","7º","8º","9º","10º"][i_t]
                    st.markdown(
                        f'<div style="text-align:center">' + img_t +
                        f'<div style="font-size:1.1rem">{medal}</div>' +
                        f'<div style="font-size:0.72rem;font-weight:800;color:#3D2B1F;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_str(row_t["titulo"])}</div>' +
                        f'<div style="font-size:0.65rem;color:#9E8F84;font-style:italic">{safe_str(row_t["autor"])}</div>' +
                        f'<div style="color:#F4B942;font-size:0.85rem">{get_stars(row_t["valoracion_personal"])}</div>' +
                        '</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  RECOMENDACIONES
# ══════════════════════════════════════════════════════════════
elif pagina == "✨ Recomendaciones":
    st.markdown('<p class="section-title">✨ Para ti</p>', unsafe_allow_html=True)
    df = get_all_books()
    tab1, tab2 = st.tabs(["🤖 IA","📊 Por similitud"])

    with tab1:
        df_l = df[df["estado"]=="Leído"].copy() if not df.empty else pd.DataFrame()
        df_l["valoracion_personal"] = pd.to_numeric(df_l.get("valoracion_personal", pd.Series(dtype=float)), errors="coerce").fillna(0)

        gf = df_l["genero"].value_counts().head(5).index.tolist() if not df_l.empty else ["Romantasy"]
        af = df_l["autor"].value_counts().head(5).index.tolist() if not df_l.empty else []
        sagas_ok = df_l[df_l["saga"].notna()&(df_l["saga"]!="")]["saga"].value_counts().head(6).index.tolist() if not df_l.empty else []

        # Perfil
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown("**🎨 Géneros**")
            for g in gf[:5]:
                cls = BADGE_MAP.get(g,"ficcion")
                st.markdown(f'<span class="badge badge-{cls}">{g}</span>', unsafe_allow_html=True)
        with c2:
            st.markdown("**✍️ Autoras**")
            for a in af[:5]: st.markdown(f"• {a}")
        with c3:
            st.markdown("**📚 Sagas**")
            for s in sagas_ok[:4]: st.markdown(f"• {s}")

        st.markdown("---")

        if not GROQ_API_KEY:
            st.error("⚠️ Falta la API key. Ejecuta: bash setup_key.sh gsk_...")
        else:
            if st.button("✨ Generar recomendaciones con IA", key="btn_ia", use_container_width=False):
                with st.spinner("🤖 Analizando tu biblioteca..."):
                    try:
                        # Contexto inteligente
                        top5 = df_l[df_l["valoracion_personal"]==5.0]["titulo"].tolist()[:12]
                        top4 = df_l[df_l["valoracion_personal"]>=4.0]["titulo"].tolist()[:15]
                        gen_counts = df_l.groupby("genero").size().sort_values(ascending=False).head(6)
                        txt_gen = ", ".join([f"{g}({n})" for g,n in gen_counts.items()])
                        aut_stats = df_l.groupby("autor").agg(n=("id","count"), m=("valoracion_personal","mean")).sort_values("n",ascending=False).head(6)
                        txt_aut = ", ".join([f"{a}({int(r['n'])} libros, {r['m']:.1f}★)" for a,r in aut_stats.iterrows()])
                        todos = df["titulo"].tolist()

                        prompt = f"""Eres una experta en literatura. Recomienda 8 libros a esta lectora.

SUS 5 ESTRELLAS (lo que más ama): {", ".join(top5) if top5 else "Sin datos"}
SUS 4+ ESTRELLAS: {", ".join(top4) if top4 else "Sin datos"}
GÉNEROS (volumen): {txt_gen}
AUTORAS FAVORITAS: {txt_aut}
SAGAS QUE SIGUE: {", ".join(sagas_ok) if sagas_ok else "variadas"}
LIBROS QUE YA TIENE (no repetir): {", ".join(todos)}

Recomiéndale 8 libros que aún no tenga. Analiza sus 5★ para entender qué le apasiona.
El motivo debe mencionar un libro suyo específico que justifique la recomendación.

Devuelve SOLO este JSON sin texto extra:
[{{"titulo":"título exacto","autor":"autor completo","genero":"género","motivo":"basado en X libro tuyo, max 12 palabras"}}]"""

                        resp = _groq_chat(prompt, max_tokens=1800)
                        t = resp.strip()
                        if "```" in t:
                            for p in t.split("```"):
                                if "[" in p and "{" in p:
                                    t = p.strip()
                                    if t.startswith("json"): t = t[4:].strip()
                                    break
                        s_idx = t.find("["); e_idx = t.rfind("]")+1
                        if s_idx >= 0 and e_idx > s_idx:
                            t = t[s_idx:e_idx]
                        st.session_state["recs_ia"] = json.loads(" ".join(t.split()))
                    except Exception as e:
                        err = str(e)
                        if "401" in err: st.error("❌ API key inválida. Actualiza .streamlit/secrets.toml")
                        elif "429" in err: st.error("❌ Límite alcanzado. Espera 30 segundos.")
                        else: st.error(f"❌ Error: {err}")
                        st.session_state["recs_ia"] = []

            # ── Mostrar resultados ──────────────────────────────
            if st.session_state.get("recs_ia"):
                recs = st.session_state["recs_ia"]
                st.markdown(f"### ✨ {len(recs)} recomendaciones para ti")
                cols_r = st.columns(4)
                for i_r, rec in enumerate(recs):
                    with cols_r[i_r % 4]:
                        pu = fetch_portada(safe_str(rec.get("titulo","")), safe_str(rec.get("autor","")))
                        img_r = f'<img src="{pu}" style="width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:14px 14px 0 0">' if pu else '<div style="width:100%;aspect-ratio:2/3;background:linear-gradient(135deg,#F5D0A9,#C4783A);border-radius:14px 14px 0 0;display:flex;align-items:center;justify-content:center;font-size:3rem">📖</div>'
                        gn = safe_str(rec.get("genero",""))
                        cls_r = BADGE_MAP.get(gn,"ficcion")
                        st.markdown(
                            '<div style="background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(61,43,31,0.10);margin-bottom:8px">' +
                            img_r + '<div style="padding:10px 12px 12px">' +
                            f'<div style="font-weight:800;font-size:0.82rem;color:#3D2B1F;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_str(rec.get("titulo",""))}</div>' +
                            f'<div style="font-size:0.72rem;color:#9E8F84;font-style:italic;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_str(rec.get("autor",""))}</div>' +
                            f'<span class="badge badge-{cls_r}">{gn}</span><br>' +
                            f'<div style="font-size:0.72rem;color:#C4783A;font-style:italic;margin-top:5px">✨ {safe_str(rec.get("motivo",""))}</div>' +
                            '</div></div>', unsafe_allow_html=True)
                        if st.button("➕ Añadir", key=f"add_ia_{i_r}", use_container_width=True):
                            add_book({"id":f"IA{str(uuid.uuid4())[:6].upper()}",
                                "titulo":rec.get("titulo",""),"autor":rec.get("autor",""),
                                "saga":"","orden_saga":"","genero":rec.get("genero",""),
                                "editorial":"","formato":"Tapa Blanda","edicion_especial":0,
                                "detalles_edicion":"","imagen_portada_url":pu,
                                "valoracion_personal":"","resena_personal":"","estado":"Quiero leer",
                                "paginas_total":0,"paginas_leidas":0,"fecha_inicio":"","fecha_fin":"",
                                "tiempo_lectura_min":0,"cita_favorita":"","etiquetas":""})
                            st.success(f"✅ Añadido"); st.rerun()
                if st.button("🔄 Regenerar", key="regen_ia"):
                    del st.session_state["recs_ia"]; st.rerun()
            elif GROQ_API_KEY:
                st.markdown('''<div style="background:white;border-radius:20px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(61,43,31,0.08)">
                    <div style="font-size:3rem;margin-bottom:12px">✨</div>
                    <h3 style="font-family:Playfair Display,serif;color:#3D2B1F;margin-bottom:8px">Recomendaciones personalizadas</h3>
                    <p style="color:#9E8F84;max-width:400px;margin:0 auto;line-height:1.7">
                        La IA analizará tus libros favoritos, géneros y autoras para encontrar libros que te van a encantar.
                    </p>
                </div>''', unsafe_allow_html=True)

    with tab2:
        st.markdown("*Por similitud con tus libros mejor valorados*")
        recs_s = recomendar_libros(df)
        if recs_s.empty:
            st.info("Valora tus libros con 4-5 ⭐ para recibir recomendaciones.")
        else:
            cols3 = st.columns(3)
            for i_s,(_, row) in enumerate(recs_s.iterrows()):
                with cols3[i_s%3]:
                    u_s = get_cover(row)
                    img_s2 = cover_img(u_s, 60, 86)
                    bg_s = badge_g(safe_str(row.get("genero","")))
                    st.markdown(
                        '<div class="book-card-v2"><div style="display:flex;gap:10px">' + img_s2 +
                        f'<div><b>{safe_str(row["titulo"])}</b><br><small style="color:#9E8F84">{safe_str(row["autor"])}</small><br>'+bg_s+
                        (f'<br><small style="color:#C4783A">📚 {safe_str(row["saga"])}</small>' if clean_saga(row.get("saga","")) else "")+
                        '</div></div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  NOVEDADES
# ══════════════════════════════════════════════════════════════
elif pagina == "🆕 Novedades":
    st.markdown('<p class="section-title">🆕 Novedades</p>', unsafe_allow_html=True)
    GENEROS_B = ["Romantasy","Fantasy","Romance","Young Adult","Thriller","Historical Fiction","Science Fiction","Dystopia","Horror","Mystery","Poetry"]
    c1,c2 = st.columns(2)
    with c1: gs = st.selectbox("Género", GENEROS_B)
    with c2: ai = st.text_input("O buscar por autora", placeholder="Ej: Rebecca Yarros...")
    if st.button("🔍 Buscar novedades",use_container_width=False):
        with st.spinner("Buscando..."):
            res = buscar_por_autor(ai.strip(),9) if ai.strip() else buscar_novedades(gs,9)
        if res:
            cols3 = st.columns(3)
            for i_n,libro in enumerate(res):
                with cols3[i_n%3]:
                    u_n = cover_url(libro.get("imagen_portada_url",""))
                    if u_n: st.image(u_n,width=120)
                    else: st.markdown('<div style="width:120px;height:170px;background:linear-gradient(135deg,#EDD5B3,#C4783A);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:2.5rem">📖</div>',unsafe_allow_html=True)
                    st.markdown(f"**{libro['titulo']}**")
                    st.markdown(f"<small>*{libro['autor']}* · {libro['anio']}</small>",unsafe_allow_html=True)
                    if st.button("➕ Añadir",key=f"nov_{i_n}_{libro['isbn'][:5]}"):
                        add_book({"id":f"NOV{str(uuid.uuid4())[:6].upper()}","titulo":libro["titulo"],"autor":libro["autor"],
                            "saga":"","orden_saga":"","genero":libro["genero"],"editorial":libro["editorial"],
                            "formato":"Tapa Blanda","edicion_especial":0,"detalles_edicion":"",
                            "imagen_portada_url":u_n,"valoracion_personal":"","resena_personal":"","estado":"Quiero leer",
                            "paginas_total":libro["paginas_total"],"paginas_leidas":0,"fecha_inicio":"","fecha_fin":"",
                            "tiempo_lectura_min":0,"cita_favorita":"","etiquetas":""})
                        st.success("✅ Añadido a 'Quiero leer'")
        else: st.warning("Sin resultados. Comprueba tu conexión.")

# ══════════════════════════════════════════════════════════════
#  CALENDARIO
# ══════════════════════════════════════════════════════════════
elif pagina == "📅 Calendario":
    st.markdown('<p class="section-title">📅 Calendario</p>', unsafe_allow_html=True)
    df = get_all_books(); hoy = date.today()
    tab_v,tab_r = st.tabs(["📆 Vista mensual","✏️ Registrar fechas"])

    with tab_v:
        c1,c2 = st.columns(2)
        with c1: anio_s = st.selectbox("Año",list(range(2020,hoy.year+1))[::-1],index=0)
        with c2: mes_s = st.selectbox("Mes",list(range(1,13)),format_func=lambda m:MESES_ES[m],index=hoy.month-1)

        libros_fin_c={}; libros_ini_c={}
        if not df.empty:
            for _,row in df.iterrows():
                t=safe_str(row.get("titulo",""))[:20]
                for col_c,dct_c in [("fecha_fin",libros_fin_c),("fecha_inicio",libros_ini_c)]:
                    fs=safe_str(row.get(col_c,""))
                    if fs:
                        try:
                            dc=datetime.strptime(fs[:10],"%Y-%m-%d").date()
                            if dc.month==mes_s and dc.year==anio_s: dct_c.setdefault(dc.day,[]).append(t)
                        except: pass

        dias_c=["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        th_c="".join([f'<th class="cal-h" style="padding:10px 4px">{d}</th>' for d in dias_c])
        rows_c=""
        for week in calendar.monthcalendar(anio_s,mes_s):
            rows_c+="<tr>"
            for d in week:
                if d==0: rows_c+='<td style="padding:4px;min-width:80px"></td>'
                else:
                    is_t=d==hoy.day and mes_s==hoy.month and anio_s==hoy.year
                    bg_d="background:#FFF3E0;border:2px solid #C4783A;" if is_t else "background:white;"
                    fin_e="".join([f'<div style="background:#E8F5E9;color:#2E7D32;border-radius:5px;padding:1px 5px;font-size:0.62rem;font-weight:700;margin-top:2px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">✅ {b}</div>' for b in libros_fin_c.get(d,[])])
                    ini_e="".join([f'<div style="background:#E3F2FD;color:#1565C0;border-radius:5px;padding:1px 5px;font-size:0.62rem;font-weight:700;margin-top:2px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">▶️ {b}</div>' for b in libros_ini_c.get(d,[])])
                    rows_c+=f'<td style="padding:4px;vertical-align:top;min-width:80px"><div style="{bg_d}border-radius:10px;padding:6px;border:1.5px solid #EDE0D0;min-height:72px"><b style="font-size:0.85rem;color:#3D2B1F">{d}</b>{ini_e}{fin_e}</div></td>'
            rows_c+="</tr>"

        st.markdown(f'''<div style="background:white;border-radius:20px;padding:20px;box-shadow:0 4px 20px rgba(61,43,31,0.08)">
            <h3 style="font-family:Playfair Display,serif;color:#3D2B1F;text-align:center;margin:0 0 16px">{MESES_ES[mes_s]} {anio_s}</h3>
            <table style="width:100%;border-collapse:separate;border-spacing:3px"><thead><tr>{th_c}</tr></thead><tbody>{rows_c}</tbody></table>
            <div style="margin-top:12px;display:flex;gap:16px;font-size:0.78rem">
                <span style="color:#2E7D32;font-weight:700">✅ Terminado</span>
                <span style="color:#1565C0;font-weight:700">▶️ Empezado</span>
            </div>
        </div>''', unsafe_allow_html=True)

        total_f=sum(len(v) for v in libros_fin_c.values())
        if total_f:
            st.markdown(f"---\n**{total_f} libro(s) terminado(s) en {MESES_ES[mes_s]} {anio_s}:**")
            for dia_c,tits_c in sorted(libros_fin_c.items()):
                for t_c in tits_c: st.markdown(f"- ✅ Día {dia_c}: *{t_c}*")
        else: st.info(f"Sin libros terminados en {MESES_ES[mes_s]} {anio_s}. Registra fechas en '✏️ Registrar fechas'.")

    with tab_r:
        if df.empty: st.info("Añade libros primero.")
        else:
            busq_c=st.text_input("🔍 Buscar libro",placeholder="Escribe el título...")
            df_c=df[df["titulo"].str.contains(busq_c,case=False,na=False)] if busq_c else df
            if not df_c.empty:
                ls=st.selectbox("Selecciona un libro",df_c["titulo"].tolist(),key="sel_cal")
                rs=df_c[df_c["titulo"]==ls].iloc[0]
                fi_v=None; ff_v=None
                fi_s=safe_str(rs.get("fecha_inicio","")); ff_s=safe_str(rs.get("fecha_fin",""))
                if fi_s:
                    try: fi_v=datetime.strptime(fi_s[:10],"%Y-%m-%d").date()
                    except: pass
                if ff_s:
                    try: ff_v=datetime.strptime(ff_s[:10],"%Y-%m-%d").date()
                    except: pass
                be_c=badge_e(rs["estado"])
                st.markdown(
                    '<div class="book-card-v2" style="margin-bottom:16px">' +
                    f'<b style="font-size:1rem;color:#3D2B1F">{safe_str(rs["titulo"])}</b><br>' +
                    f'<small style="color:#9E8F84">{safe_str(rs["autor"])}</small> ' + be_c +
                    (f'<br><small style="color:#9E8F84">📅 Inicio: {fi_s[:10]}</small>' if fi_s else "") +
                    (f'<small style="color:#9E8F84"> · Fin: {ff_s[:10]}</small>' if ff_s else "") +
                    '</div>', unsafe_allow_html=True)
                cc1,cc2=st.columns(2)
                nfi=cc1.date_input("📅 Inicio",value=fi_v,key="fi_cal")
                nff=cc2.date_input("📅 Fin",value=ff_v,key="ff_cal")
                if nfi and nff:
                    dias_r=(nff-nfi).days
                    if dias_r>=0:
                        pgs=safe_int(rs.get("paginas_total",0))
                        ci1,ci2,ci3=st.columns(3)
                        ci1.metric("⏱️ Días",dias_r); ci2.metric("📄 Páginas",pgs)
                        ci3.metric("📃 Pág/día",f"{pgs/dias_r:.0f}" if dias_r>0 else "—")
                    else: st.error("⚠️ La fecha fin no puede ser anterior al inicio.")
                if st.button("💾 Guardar fechas",use_container_width=True,key="btn_save_cal"):
                    update_book(rs["id"],{"fecha_inicio":str(nfi) if nfi else "","fecha_fin":str(nff) if nff else ""})
                    st.success("✅ Fechas guardadas"); st.rerun()

# ══════════════════════════════════════════════════════════════
#  MIS METAS
# ══════════════════════════════════════════════════════════════
elif pagina == "🎯 Mis Metas":
    st.markdown('<p class="section-title">🎯 Mis Metas</p>', unsafe_allow_html=True)
    df = get_all_books()
    leidos_n = len(df[df["estado"]=="Leído"]) if not df.empty else 0

    c1,c2 = st.columns([2,1])
    with c2:
        meta = st.number_input("🎯 Meta anual de libros",min_value=1,max_value=500,value=st.session_state["meta_anual"])
        st.session_state["meta_anual"] = meta
    with c1:
        prog = min(leidos_n/meta,1.0)
        pct_m = int(prog*100)
        st.markdown(f"### {leidos_n} de {meta} libros leídos")
        st.markdown(f'<div style="background:#F0E8E0;border-radius:20px;height:16px;overflow:hidden;margin:8px 0"><div style="background:linear-gradient(90deg,#C4783A,#F4A460);height:100%;border-radius:20px;width:{pct_m}%;transition:width 0.5s"></div></div>', unsafe_allow_html=True)
        rest = max(meta-leidos_n,0)
        if rest==0: st.success("🎉 ¡Has superado tu meta anual! Increíble lectora.")
        else:
            hoy=date.today(); dias_r=365-hoy.timetuple().tm_yday
            ritmo=rest/dias_r if dias_r>0 else 0
            st.info(f"📖 Te quedan **{rest} libros** · necesitas **{ritmo:.2f} libros/día**")

    st.markdown("---")
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number+delta",value=leidos_n,delta={"reference":meta},
        gauge={"axis":{"range":[0,meta]},"bar":{"color":"#C4783A"},
               "steps":[{"range":[0,meta*0.33],"color":"#FFF3E0"},
                        {"range":[meta*0.33,meta*0.66],"color":"#FFE0B2"},
                        {"range":[meta*0.66,meta],"color":"#FFCC80"}],
               "threshold":{"line":{"color":"#3D2B1F","width":4},"value":meta}},
        title={"text":"Libros leídos este año","font":{"family":"Playfair Display"}}))
    fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)",height=300,font=dict(family="Nunito"))
    st.plotly_chart(fig_g,use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🏆 Logros")
    logros = [("🥉 Primer libro",leidos_n>=1),("📗 5 libros",leidos_n>=5),
              ("📘 10 libros",leidos_n>=10),("📙 25 libros",leidos_n>=25),
              ("📕 50 libros",leidos_n>=50),("💯 100 libros",leidos_n>=100),
              ("🏅 150 libros",leidos_n>=150),("👑 Meta alcanzada",leidos_n>=meta)]
    cols_l = st.columns(4)
    for i,(nom,ok) in enumerate(logros):
        with cols_l[i%4]:
            if ok: st.success(f"✅ {nom}")
            else: st.markdown(f"<div style='background:white;border-radius:12px;padding:12px;text-align:center;color:#9E8F84;box-shadow:0 2px 8px rgba(61,43,31,0.06)'>🔒<br><small>{nom}</small></div>",unsafe_allow_html=True)
