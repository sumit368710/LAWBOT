import streamlit as st
import warnings
warnings.filterwarnings("ignore")

import os
import glob
import base64
from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
from utils.llm_handler import LLMHandler
from utils.bhashini_handler import BhashiniHandler

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LexBot – AI Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inline CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
* { box-sizing: border-box; }
body, .stApp { background:#0f1117 !important; color:#e8eaf0 !important;
               font-family:'Inter','Segoe UI',sans-serif; }
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#1a1d27 0%,#141720 100%) !important;
    border-right:1px solid #2a2d3e;
}
.sidebar-header { text-align:center; padding:1.5rem 0.5rem 1rem; }
.sidebar-header .logo { font-size:3rem; display:block; margin-bottom:0.3rem; }
.sidebar-header h1 {
    font-size:1.6rem; font-weight:800; margin:0;
    background:linear-gradient(135deg,#d4af37,#f5d060);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.sidebar-header p { color:#8b8fa8; font-size:0.78rem; margin:0.2rem 0 0; }
.status-badge {
    background:linear-gradient(135deg,#1a472a,#2d6a4f);
    border:1px solid #40916c; color:#b7e4c7;
    border-radius:20px; padding:0.4rem 1rem;
    text-align:center; font-size:0.8rem; font-weight:600; margin:0.5rem 0;
}
.status-error {
    background:linear-gradient(135deg,#3a1a1a,#5a2a2a);
    border:1px solid #a04040; color:#f0b0b0;
    border-radius:20px; padding:0.4rem 1rem;
    text-align:center; font-size:0.8rem; font-weight:600; margin:0.5rem 0;
}
.sidebar-footer { color:#555870; font-size:0.72rem; text-align:center; padding:0.5rem; }
.hero-banner {
    background:linear-gradient(135deg,#1c1f2e 0%,#242840 50%,#1c2035 100%);
    border:1px solid #2e3250; border-radius:16px;
    padding:2rem 2.5rem; margin-bottom:1.5rem; position:relative; overflow:hidden;
}
.hero-banner::before {
    content:''; position:absolute; top:0; left:0; right:0; bottom:0;
    background:radial-gradient(ellipse at top right,rgba(212,175,55,0.08) 0%,transparent 60%);
    pointer-events:none;
}
.hero-content h1 {
    font-size:2rem; font-weight:800; margin:0 0 0.4rem;
    background:linear-gradient(135deg,#d4af37,#f5d060,#e8c547);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.hero-content p { color:#8b8fa8; margin:0; font-size:1rem; }
.stat-card {
    background:#1a1d27; border:1px solid #2a2d3e; border-radius:12px;
    padding:1rem 1.2rem; display:flex; align-items:center; gap:0.8rem;
    transition:border-color 0.2s,transform 0.2s;
}
.stat-card:hover { border-color:#d4af37; transform:translateY(-2px); }
.stat-icon { font-size:1.8rem; }
.stat-card strong { color:#e8eaf0; font-size:0.9rem; }
.stat-card small  { color:#6b7080; font-size:0.75rem; }
.welcome-box {
    background:linear-gradient(135deg,#1a1d2e,#1e2138);
    border:1px solid #2e3250; border-left:4px solid #d4af37;
    border-radius:12px; padding:1.8rem 2rem; margin:1rem 0 1.5rem;
}
.welcome-box h3 { color:#d4af37; margin-top:0; font-size:1.2rem; }
.welcome-box p  { color:#9097b0; margin:0.3rem 0 0.8rem; }
.welcome-box ul { color:#9097b0; padding-left:1.4rem; margin:0; line-height:2; }
.chat-bubble {
    display:flex; align-items:flex-start; gap:0.8rem;
    padding:1rem 1.2rem; border-radius:12px; margin-bottom:0.8rem;
    animation:fadeIn 0.3s ease;
}
@keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
.user-message {
    background:linear-gradient(135deg,#1e2d4a,#1a2840);
    border:1px solid #2a4060; margin-left:3rem;
}
.bot-message {
    background:linear-gradient(135deg,#1e1e2e,#242438);
    border:1px solid #2e2e48; margin-right:3rem;
}
.role-icon { font-size:1.4rem; flex-shrink:0; margin-top:0.1rem; }
.message-content { color:#d8dae8; line-height:1.65; font-size:0.95rem; flex:1; }
.translation-box {
    background:linear-gradient(135deg,#1a2a1a,#1e2e1e);
    border:1px solid #2a5a2a; border-left:3px solid #40a040;
    border-radius:8px; padding:0.8rem 1rem; margin:0.4rem 0;
    color:#c8e8c8; font-size:0.9rem; line-height:1.6;
}
.copy-hint { color:#555870; font-size:0.75rem; padding:0.3rem 0; }
.stTextInput>div>div>input {
    background:#1a1d27 !important; border:1px solid #2e3250 !important;
    color:#e8eaf0 !important; border-radius:10px !important;
    padding:0.7rem 1rem !important; font-size:0.95rem !important;
}
.stTextInput>div>div>input:focus {
    border-color:#d4af37 !important;
    box-shadow:0 0 0 2px rgba(212,175,55,0.15) !important;
}
.stButton>button {
    background:linear-gradient(135deg,#1e2138,#252840) !important;
    border:1px solid #3a3d58 !important; color:#c8cae0 !important;
    border-radius:8px !important; font-size:0.82rem !important;
    transition:all 0.2s !important;
}
.stButton>button:hover {
    border-color:#d4af37 !important; color:#d4af37 !important;
    transform:translateY(-1px) !important;
}
[data-testid="stButton"]>button[kind="primary"] {
    background:linear-gradient(135deg,#b8960c,#d4af37) !important;
    border:none !important; color:#0f1117 !important; font-weight:700 !important;
}
[data-testid="stButton"]>button[kind="primary"]:hover {
    background:linear-gradient(135deg,#d4af37,#f5d060) !important; color:#0f1117 !important;
}
.stProgress>div>div>div { background:linear-gradient(90deg,#b8960c,#d4af37) !important; }
.footer {
    text-align:center; color:#444660; font-size:0.75rem;
    padding:1.5rem 0 0.5rem; border-top:1px solid #1e2030; margin-top:2rem;
}
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:#0f1117; }
::-webkit-scrollbar-thumb { background:#2a2d3e; border-radius:4px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "messages": [], "docs_loaded": False, "vectorstore": None,
    "selected_language": "en", "tts_gender": "female",
    "doc_count": 0, "chunk_count": 0, "load_error": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Cached handlers ───────────────────────────────────────────────────────────
@st.cache_resource
def get_llm_handler():
    return LLMHandler()

@st.cache_resource
def get_bhashini():
    return BhashiniHandler()

@st.cache_resource
def get_doc_loader():
    return DocumentLoader()

llm_handler = get_llm_handler()
bhashini    = get_bhashini()
doc_loader  = get_doc_loader()

# ── Auto-load documents from files/ at startup ────────────────────────────────
if not st.session_state.docs_loaded and st.session_state.load_error is None:
    with st.spinner("📚 Loading legal knowledge base from `files/` folder…"):
        try:
            progress = st.progress(0, text="Scanning documents…")
            vs, dc, cc = doc_loader.load_from_folder(DOCUMENTS_FOLDER, progress)
            st.session_state.update({
                "vectorstore": vs, "docs_loaded": True,
                "doc_count": dc,   "chunk_count": cc,
            })
            llm_handler.set_vectorstore(vs)
            progress.empty()
        except FileNotFoundError as e:
            st.session_state.load_error = str(e)
        except Exception as e:
            st.session_state.load_error = f"Unexpected error: {e}"

# ── Language map ──────────────────────────────────────────────────────────────
LANGUAGES = {
    "en": {"name": "English",   "script": "Latn", "flag": "🇺🇸"},
    "hi": {"name": "Hindi",     "script": "Deva", "flag": "🇮🇳"},
    "bn": {"name": "Bengali",   "script": "Beng", "flag": "🇧🇩"},
    "ta": {"name": "Tamil",     "script": "Taml", "flag": "🇮🇳"},
    "te": {"name": "Telugu",    "script": "Telu", "flag": "🇮🇳"},
    "mr": {"name": "Marathi",   "script": "Deva", "flag": "🇮🇳"},
    "gu": {"name": "Gujarati",  "script": "Gujr", "flag": "🇮🇳"},
    "kn": {"name": "Kannada",   "script": "Knda", "flag": "🇮🇳"},
    "ml": {"name": "Malayalam", "script": "Mlym", "flag": "🇮🇳"},
    "pa": {"name": "Punjabi",   "script": "Guru", "flag": "🇮🇳"},
    "ur": {"name": "Urdu",      "script": "Arab", "flag": "🇵🇰"},
}

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <span class="logo">⚖️</span>
        <h1>LexBot</h1>
        <p>AI-Powered Legal Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── API Configuration ──────────────────────────────────────────────────
    st.markdown("### 🔧 Configuration")
    with st.expander("API Settings", expanded=False):
        bhashini_api_key = st.text_input(
            "Bhashini API Key", type="password",
            value=os.getenv("BHASHINI_API_KEY", ""),
            help="Enter your Bhashini API key",
        )
        ollama_host = st.text_input(
            "Ollama Host",
            value=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )
        if st.button("💾 Save Config", use_container_width=True):
            os.environ["BHASHINI_API_KEY"] = bhashini_api_key
            os.environ["OLLAMA_HOST"]      = ollama_host
            st.success("Configuration saved!")
    st.markdown("---")

    # ── Knowledge Base Status ──────────────────────────────────────────────
    st.markdown("### 📂 Knowledge Base")
    if st.session_state.load_error:
        st.markdown('<div class="status-error">❌ Load Failed</div>', unsafe_allow_html=True)
        st.error(st.session_state.load_error)
        st.caption(f"📁 Add files to: `{DOCUMENTS_FOLDER}`")
        if st.button("🔄 Retry Loading", use_container_width=True, type="primary"):
            st.session_state.load_error = None
            st.rerun()
    elif st.session_state.docs_loaded:
        st.markdown('<div class="status-badge">📚 Knowledge Base Active</div>', unsafe_allow_html=True)
        st.caption(f"📄 **{st.session_state.doc_count}** files loaded")
        st.caption(f"🔖 **{st.session_state.chunk_count}** chunks indexed")
        with st.expander("📋 Loaded files", expanded=False):
            all_files = (
                glob.glob(os.path.join(DOCUMENTS_FOLDER, "**", "*.pdf"),  recursive=True) +
                glob.glob(os.path.join(DOCUMENTS_FOLDER, "**", "*.docx"), recursive=True) +
                glob.glob(os.path.join(DOCUMENTS_FOLDER, "**", "*.doc"),  recursive=True)
            )
            for f in all_files:
                st.caption(f"• {os.path.basename(f)}")
        if st.button("🔄 Reload Documents", use_container_width=True):
            st.session_state.docs_loaded = False
            st.session_state.load_error  = None
            st.cache_resource.clear()
            st.rerun()
    else:
        st.markdown('<div class="status-error">⏳ Loading…</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── Language & Voice ───────────────────────────────────────────────────
    st.markdown("### 🌐 Language & Voice")
    lang_options = {f"{v['flag']} {v['name']}": k for k, v in LANGUAGES.items()}
    selected_display = st.selectbox("Response Language", list(lang_options.keys()), index=0)
    st.session_state.selected_language = lang_options[selected_display]
    st.session_state.tts_gender = st.radio("Voice Gender", ["female", "male"], horizontal=True)
    st.markdown("---")

    # ── Quick Questions ────────────────────────────────────────────────────
    st.markdown("### 💡 Quick Questions")
    for q in [
        "What are fundamental rights?",
        "Explain Article 21",
        "What is bail procedure?",
        "Rights of an arrested person",
        "What is IPC Section 420?",
    ]:
        if st.button(q, use_container_width=True, key=f"qq_{q}"):
            st.session_state.pending_question = q

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="sidebar-footer">Powered by LLaMA 3.1 + Bhashini</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-banner">
  <div class="hero-content">
    <h1>⚖️ LexBot – AI Legal Assistant</h1>
    <p>Ask legal questions in natural language • Multi-language support • Voice output</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Stat cards ────────────────────────────────────────────────────────────────
for col, (icon, title, sub) in zip(
    st.columns(4),
    [
        ("📄", "Backend Docs",   f"{st.session_state.doc_count} files auto-loaded"),
        ("🌐", "11 Languages",   "Powered by Bhashini"),
        ("🔊", "Text-to-Speech", "Female & Male voices"),
        ("🤖", "LLaMA 3.1",      "Local AI inference"),
    ],
):
    col.markdown(
        f'<div class="stat-card"><span class="stat-icon">{icon}</span>'
        f'<div><strong>{title}</strong><br><small>{sub}</small></div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Load error banner ─────────────────────────────────────────────────────────
if st.session_state.load_error:
    st.error(
        f"**⚠️ Knowledge Base Not Loaded**\n\n"
        f"{st.session_state.load_error}\n\n"
        f"**Fix:** Place your PDF/DOCX files inside the `files/` folder next to `app.py`, "
        f"then click **Retry Loading** in the sidebar."
    )

# ── Welcome message ───────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-box">
        <h3>👋 Welcome to LexBot!</h3>
        <p>Your legal documents are auto-loaded from the <code>files/</code> folder.
           Ask me anything about Indian law.</p>
        <ul>
            <li>📜 Constitutional law &amp; fundamental rights</li>
            <li>⚖️ Criminal procedure (IPC, CrPC)</li>
            <li>🏛️ Civil matters &amp; contracts</li>
            <li>👨‍👩‍👧 Family law &amp; property disputes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    role_class = "user-message" if msg["role"] == "user" else "bot-message"
    role_icon  = "👤" if msg["role"] == "user" else "⚖️"
    st.markdown(
        f'<div class="chat-bubble {role_class}">'
        f'<span class="role-icon">{role_icon}</span>'
        f'<div class="message-content">{msg["content"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if msg["role"] == "assistant":
        a1, a2, a3, _, _ = st.columns([1, 1, 2, 3, 1])

        # Translate button
        with a1:
            lang = st.session_state.selected_language
            if lang != "en":
                lang_name = LANGUAGES[lang]["name"]
                if st.button(f"🌐 {lang_name}", key=f"tr_{i}"):
                    with st.spinner("Translating…"):
                        translated = bhashini.translate(
                            msg["content"], "en", lang,
                            LANGUAGES[lang]["script"],
                            os.getenv("BHASHINI_API_KEY", ""),
                        )
                    st.markdown(
                        f'<div class="translation-box">'
                        f'<strong>🌐 {lang_name}:</strong><br>{translated}</div>',
                        unsafe_allow_html=True,
                    )

        # TTS button
        with a2:
            if st.button("🔊 Listen", key=f"tts_{i}"):
                lang = st.session_state.selected_language
                with st.spinner("Generating audio…"):
                    audio_b64 = bhashini.text_to_speech(
                        msg["content"], lang,
                        LANGUAGES[lang]["script"],
                        st.session_state.tts_gender,
                        os.getenv("BHASHINI_API_KEY", ""),
                    )
                if audio_b64:
                    st.audio(base64.b64decode(audio_b64), format="audio/wav")
                else:
                    st.warning("TTS unavailable — check API key or language.")

        with a3:
            st.markdown(
                f'<div class="copy-hint">💬 {len(msg["content"].split())} words</div>',
                unsafe_allow_html=True,
            )

# ── Input bar ─────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
default_val  = st.session_state.pop("pending_question", "")
ic, bc       = st.columns([5, 1])

with ic:
    user_input = st.text_input(
        "Ask", value=default_val,
        placeholder="e.g. What are the rights of an accused under CrPC?",
        label_visibility="collapsed",
    )
with bc:
    send = st.button("Send ➤", type="primary", use_container_width=True)

# ── Process query ─────────────────────────────────────────────────────────────
if send and user_input.strip():
    q = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": q})
    with st.spinner("⚖️ Researching legal knowledge base…"):
        answer = (
            llm_handler.answer_with_docs(q)
            if st.session_state.docs_loaded
            else llm_handler.answer_general(q)
        )
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    ⚖️ LexBot is an AI assistant and does not constitute legal advice.
    Always consult a qualified legal professional for legal matters.
</div>
""", unsafe_allow_html=True)
