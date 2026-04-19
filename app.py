import os
import base64
import streamlit as st

from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
from utils.llm_handler import LLMHandler
from utils.bhashini_handler import BhashiniHandler


# PAGE CONFIG
st.set_page_config(page_title="LexBot", page_icon="⚖️", layout="wide")


# CSS (RESPONSIVE)
st.markdown("""
<style>
body, .stApp {
    background: #0f1117;
    color: #e8eaf0;
}

.block-container {
    max-width: 900px;
    margin: auto;
    padding-bottom: 6rem;
}

[data-testid="stChatInput"] {
    position: fixed;
    bottom: 0;
    left: 300px;
    right: 20px;
    padding: 10px;
}

@media (max-width: 768px) {
    [data-testid="stChatInput"] {
        left: 10px !important;
        right: 10px !important;
    }
}
</style>
""", unsafe_allow_html=True)


# SECRETS
# for key in ["BHASHINI_API_KEY"]:
#     if key in st.secrets:
#         os.environ[key] = st.secrets[key]

os.environ["BHASHINI_API_KEY"] = st.secrets.get("BHASHINI_API_KEY", "")

# SESSION STATE
if "messages" not in st.session_state:
    st.session_state.messages = []

if "lang" not in st.session_state:
    st.session_state.lang = "en"

if "gender" not in st.session_state:
    st.session_state.gender = "female"


# LANGUAGE MAP
LANGUAGES = {
    "en": {"name": "English", "script": "Latn", "flag": "🇺🇸"},
    "hi": {"name": "Hindi", "script": "Deva", "flag": "🇮🇳"},
    "mr": {"name": "Marathi", "script": "Deva", "flag": "🇮🇳"},
    "ta": {"name": "Tamil", "script": "Taml", "flag": "🇮🇳"},
    "te": {"name": "Telugu", "script": "Telu", "flag": "🇮🇳"},
    "bn": {"name": "Bengali", "script": "Beng", "flag": "🇧🇩"},
    "gu": {"name": "Gujarati", "script": "Gujr", "flag": "🇮🇳"},
    "kn": {"name": "Kannada", "script": "Knda", "flag": "🇮🇳"},
    "ml": {"name": "Malayalam", "script": "Mlym", "flag": "🇮🇳"},
    "pa": {"name": "Punjabi", "script": "Guru", "flag": "🇮🇳"},
    "ur": {"name": "Urdu", "script": "Arab", "flag": "🇵🇰"},
}


# LOAD HANDLERS
@st.cache_resource
def load_all():
    llm = LLMHandler()
    bhashini = BhashiniHandler()
    loader = DocumentLoader()

    # 🔥 LOAD DOCUMENTS + VECTOR DB
    vs, doc_count, chunk_count = loader.load_from_folder(DOCUMENTS_FOLDER)

    # 🔥 CONNECT VECTORSTORE TO LLM
    llm.set_vectorstore(vs)

    return llm, bhashini, doc_count, chunk_count


llm, bhashini, doc_count, chunk_count = load_all()


# SIDEBAR
with st.sidebar:
    st.title("⚖️ LexBot")
    st.sidebar.success(f"📄 {doc_count} files loaded")

    keys = list(LANGUAGES.keys())
    display = [f"{v['flag']} {v['name']} ({k})" for k, v in LANGUAGES.items()]

    selected = st.selectbox("Language", display)
    st.session_state.lang = keys[display.index(selected)]

    st.session_state.gender = st.radio("Voice", ["female", "male"])

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()


# HEADER
st.markdown("### ⚖️ Ask Legal Questions")


# CHAT DISPLAY
for i, msg in enumerate(st.session_state.messages):

    with st.chat_message(msg["role"]):
        st.write(msg["content"])

        if msg["role"] == "assistant":

            if st.button("🌐 Translate", key=f"tr_{i}"):

                lang = st.session_state.lang
                script = LANGUAGES[lang]["script"]

                result = bhashini.translate(
                    msg["content"],
                    "en",
                    lang
                )

                st.success(result)

            if st.button("🔊 Audio", key=f"tts_{i}"):

                lang = st.session_state.lang
                script = LANGUAGES[lang]["script"]

                audio = bhashini.text_to_speech(
                    msg["content"],
                    lang,
                    st.session_state.gender
                )

                if audio:
                    st.audio(base64.b64decode(audio))


# INPUT
user_input = st.chat_input("Ask your legal question...")

if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    answer = llm.answer_with_docs(user_input)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.rerun()





# import os
# import base64
# import streamlit as st

# from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
# from utils.llm_handler import LLMHandler
# from utils.bhashini_handler import BhashiniHandler


# # ─────────────────────────────────────────────
# # PAGE CONFIG
# # ─────────────────────────────────────────────
# st.set_page_config(
#     page_title="LexBot",
#     page_icon="⚖️",
#     layout="wide"
# )


# # ─────────────────────────────────────────────
# # RESPONSIVE CSS
# # ─────────────────────────────────────────────
# st.markdown("""
# <style>

# /* GLOBAL */
# body, .stApp {
#     background: #0f1117;
#     color: #e8eaf0;
#     font-family: 'Inter', sans-serif;
# }

# /* CENTER CHAT */
# .block-container {
#     max-width: 900px;
#     margin: auto;
#     padding-top: 1rem;
#     padding-bottom: 6rem;
# }

# /* SIDEBAR */
# [data-testid="stSidebar"] {
#     background: #141720;
# }

# /* TOP TEXT */
# .top-text {
#     font-size: 0.9rem;
#     color: #8b8fa8;
#     margin-bottom: 1rem;
# }

# /* CHAT INPUT DESKTOP */
# [data-testid="stChatInput"] {
#     position: fixed;
#     bottom: 0;
#     left: 300px;
#     right: 20px;
#     background: #0f1117;
#     padding: 10px;
#     z-index: 100;
# }

# /* MOBILE FIX */
# @media (max-width: 768px) {

#     .block-container {
#         padding-left: 10px;
#         padding-right: 10px;
#     }

#     [data-testid="stChatInput"] {
#         left: 10px !important;
#         right: 10px !important;
#     }

#     [data-testid="stSidebar"] {
#         width: 80% !important;
#     }
# }

# </style>
# """, unsafe_allow_html=True)


# # ─────────────────────────────────────────────
# # LOAD SECRETS
# # ─────────────────────────────────────────────
# for key in ["HF_TOKEN", "GROQ_API_KEY", "BHASHINI_API_KEY"]:
#     if key in st.secrets:
#         os.environ[key] = st.secrets[key]


# # ─────────────────────────────────────────────
# # SESSION STATE
# # ─────────────────────────────────────────────
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# if "docs_loaded" not in st.session_state:
#     st.session_state.docs_loaded = False

# if "lang" not in st.session_state:
#     st.session_state.lang = "en"

# if "gender" not in st.session_state:
#     st.session_state.gender = "female"


# # ─────────────────────────────────────────────
# # LANGUAGE MAP (UPDATED)
# # ─────────────────────────────────────────────
# LANGUAGES = {
#     "en": {"name": "English",   "script": "Latn", "flag": "🇺🇸"},
#     "hi": {"name": "Hindi",     "script": "Deva", "flag": "🇮🇳"},
#     "bn": {"name": "Bengali",   "script": "Beng", "flag": "🇧🇩"},
#     "ta": {"name": "Tamil",     "script": "Taml", "flag": "🇮🇳"},
#     "te": {"name": "Telugu",    "script": "Telu", "flag": "🇮🇳"},
#     "mr": {"name": "Marathi",   "script": "Deva", "flag": "🇮🇳"},
#     "gu": {"name": "Gujarati",  "script": "Gujr", "flag": "🇮🇳"},
#     "kn": {"name": "Kannada",   "script": "Knda", "flag": "🇮🇳"},
#     "ml": {"name": "Malayalam", "script": "Mlym", "flag": "🇮🇳"},
#     "pa": {"name": "Punjabi",   "script": "Guru", "flag": "🇮🇳"},
#     "ur": {"name": "Urdu",      "script": "Arab", "flag": "🇵🇰"},
# }


# # ─────────────────────────────────────────────
# # LOAD MODELS
# # ─────────────────────────────────────────────
# @st.cache_resource
# def load_all():
#     return LLMHandler(), BhashiniHandler(), DocumentLoader()

# llm, bhashini, loader = load_all()


# # ─────────────────────────────────────────────
# # LOAD DOCUMENTS
# # ─────────────────────────────────────────────
# if not st.session_state.docs_loaded:
#     try:
#         vs, dc, cc = loader.load_from_folder(DOCUMENTS_FOLDER)
#         llm.set_vectorstore(vs)

#         st.session_state.docs_loaded = True
#         st.session_state.doc_count = dc
#         st.session_state.chunk_count = cc
#     except:
#         st.session_state.docs_loaded = False


# # ─────────────────────────────────────────────
# # SIDEBAR
# # ─────────────────────────────────────────────
# with st.sidebar:
#     st.title("⚖️ LexBot")

#     # KNOWLEDGE BASE
#     with st.expander("📂 Knowledge Base", expanded=True):
#         if st.session_state.docs_loaded:
#             st.success("Loaded")
#             st.caption(f"{st.session_state.doc_count} files")
#         else:
#             st.warning("Not Loaded")

#     # LANGUAGE SELECTOR (UPDATED)
#     with st.expander("🌐 Language & Voice"):

#         language_keys = list(LANGUAGES.keys())

#         language_display = [
#             f"{v['flag']} {v['name']} ({k})"
#             for k, v in LANGUAGES.items()
#         ]

#         selected_index = language_keys.index(st.session_state.lang)

#         selected_lang_display = st.selectbox(
#             "Language",
#             options=language_display,
#             index=selected_index
#         )

#         st.session_state.lang = language_keys[
#             language_display.index(selected_lang_display)
#         ]

#         st.session_state.gender = st.radio(
#             "Voice",
#             ["female", "male"],
#             index=0 if st.session_state.gender == "female" else 1
#         )

#     # QUICK QUESTIONS
#     with st.expander("💡 Quick Questions"):
#         questions = [
#             "What are fundamental rights?",
#             "Explain Article 21",
#             "What is bail procedure?"
#         ]

#         for q in questions:
#             if st.button(q):
#                 st.session_state.messages.append({
#                     "role": "user",
#                     "content": q
#                 })

#     # CLEAR CHAT
#     if st.button("🗑 Clear Chat"):
#         st.session_state.messages = []
#         st.rerun()


# # ─────────────────────────────────────────────
# # HEADER
# # ─────────────────────────────────────────────
# st.markdown(
#     '<div class="top-text">Welcome to LexBot ⚖️ — Ask your legal questions</div>',
#     unsafe_allow_html=True
# )


# # ─────────────────────────────────────────────
# # CHAT DISPLAY
# # ─────────────────────────────────────────────
# for i, msg in enumerate(st.session_state.messages):

#     with st.chat_message(msg["role"]):
#         st.write(msg["content"])

#         if msg["role"] == "assistant":

#             with st.expander("🔧 Options"):

#                 # TRANSLATE
#                 if st.button("🌐 Translate", key=f"tr_{i}"):

#                     target_lang = st.session_state.lang
#                     target_script = LANGUAGES[target_lang]["script"]

#                     translated = bhashini.translate(
#                         msg["content"],
#                         "en",
#                         target_lang,
#                         target_script
#                     )

#                     st.success(translated)

#                 # TTS
#                 if st.button("🔊 Play Audio", key=f"tts_{i}"):

#                     target_lang = st.session_state.lang
#                     target_script = LANGUAGES[target_lang]["script"]

#                     audio = bhashini.text_to_speech(
#                         msg["content"],
#                         target_lang,
#                         target_script,
#                         st.session_state.gender
#                     )

#                     if audio:
#                         st.audio(base64.b64decode(audio))
#                     else:
#                         st.warning("Audio unavailable")


# # ─────────────────────────────────────────────
# # CHAT INPUT
# # ─────────────────────────────────────────────
# user_input = st.chat_input("Ask your legal question...")

# if user_input:

#     st.session_state.messages.append({
#         "role": "user",
#         "content": user_input
#     })

#     with st.spinner("Thinking..."):

#         if st.session_state.docs_loaded:
#             answer = llm.answer_with_docs(user_input)
#         else:
#             answer = llm.answer_general(user_input)

#     st.session_state.messages.append({
#         "role": "assistant",
#         "content": answer
#     })

#     st.rerun()




# # import os
# # import glob
# # import base64
# # import streamlit as st

# # from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
# # from utils.llm_handler import LLMHandler
# # from utils.bhashini_handler import BhashiniHandler

# # # ─────────────────────────────────────────────────────────────
# # # PAGE CONFIG
# # # ─────────────────────────────────────────────────────────────
# # st.set_page_config(
# #     page_title="LexBot",
# #     page_icon="⚖️",
# #     layout="wide"
# # )

# # # ─────────────────────────────────────────────────────────────
# # # CSS (CLEAN MODERN UI)
# # # ─────────────────────────────────────────────────────────────
# # st.markdown("""
# # <style>
# # body, .stApp {
# #     background:#0f1117;
# #     color:#e8eaf0;
# #     font-family: 'Inter', sans-serif;
# # }

# # /* Chat spacing */
# # .block-container {
# #     padding-top: 1rem;
# #     padding-bottom: 5rem;
# # }

# # /* Sidebar */
# # [data-testid="stSidebar"] {
# #     background:#141720;
# # }

# # /* Small top text */
# # .top-text {
# #     font-size: 0.9rem;
# #     color:#8b8fa8;
# #     margin-bottom: 1rem;
# # }

# # /* Buttons */
# # .stButton>button {
# #     border-radius: 8px;
# # }

# # /* Chat input */
# # [data-testid="stChatInput"] {
# #     position: fixed;
# #     bottom: 10px;
# #     left: 300px;
# #     right: 20px;
# # }
# # </style>
# # """, unsafe_allow_html=True)

# # # ─────────────────────────────────────────────────────────────
# # # LOAD SECRETS
# # # ─────────────────────────────────────────────────────────────
# # for key in ["HF_TOKEN", "GROQ_API_KEY", "BHASHINI_API_KEY"]:
# #     if key in st.secrets:
# #         os.environ[key] = st.secrets[key]

# # # ─────────────────────────────────────────────────────────────
# # # SESSION STATE
# # # ─────────────────────────────────────────────────────────────
# # if "messages" not in st.session_state:
# #     st.session_state.messages = []

# # if "docs_loaded" not in st.session_state:
# #     st.session_state.docs_loaded = False

# # # ─────────────────────────────────────────────────────────────
# # # LOAD HANDLERS
# # # ─────────────────────────────────────────────────────────────
# # @st.cache_resource
# # def load_all():
# #     return LLMHandler(), BhashiniHandler(), DocumentLoader()

# # llm, bhashini, loader = load_all()

# # # ─────────────────────────────────────────────────────────────
# # # LOAD DOCUMENTS
# # # ─────────────────────────────────────────────────────────────
# # if not st.session_state.docs_loaded:
# #     try:
# #         vs, dc, cc = loader.load_from_folder(DOCUMENTS_FOLDER)
# #         llm.set_vectorstore(vs)

# #         st.session_state.docs_loaded = True
# #         st.session_state.doc_count = dc
# #         st.session_state.chunk_count = cc
# #     except:
# #         st.session_state.docs_loaded = False

# # # ─────────────────────────────────────────────────────────────
# # # LANGUAGE MAP
# # # ─────────────────────────────────────────────────────────────
# # LANGUAGES = {
# #     "en": "English",
# #     "hi": "Hindi",
# #     "mr": "Marathi"
# # }

# # # ─────────────────────────────────────────────────────────────
# # # SIDEBAR (CLEAN)
# # # ─────────────────────────────────────────────────────────────
# # with st.sidebar:
# #     st.title("⚖️ LexBot")

# #     with st.expander("📂 Knowledge Base", expanded=True):
# #         if st.session_state.docs_loaded:
# #             st.success("Loaded")
# #             st.caption(f"{st.session_state.doc_count} files")
# #         else:
# #             st.warning("Not Loaded")

# #     with st.expander("🌐 Language & Voice"):
# #         st.session_state.lang = st.selectbox(
# #             "Language",
# #             list(LANGUAGES.keys())
# #         )
# #         st.session_state.gender = st.radio("Voice", ["female", "male"])

# #     with st.expander("💡 Quick Questions"):
# #         for q in [
# #             "What are fundamental rights?",
# #             "Explain Article 21",
# #             "What is bail procedure?"
# #         ]:
# #             if st.button(q):
# #                 st.session_state.messages.append({"role": "user", "content": q})

# #     if st.button("🗑 Clear Chat"):
# #         st.session_state.messages = []
# #         st.rerun()

# # # ─────────────────────────────────────────────────────────────
# # # MAIN UI
# # # ─────────────────────────────────────────────────────────────

# # # 🔹 Small welcome text
# # st.markdown(
# #     '<div class="top-text">Hello Nidhi, welcome to LexBot. How can I help you?</div>',
# #     unsafe_allow_html=True
# # )

# # # ─────────────────────────────────────────────────────────────
# # # CHAT DISPLAY
# # # ─────────────────────────────────────────────────────────────
# # for i, msg in enumerate(st.session_state.messages):
# #     if msg["role"] == "user":
# #         st.chat_message("user").write(msg["content"])
# #     else:
# #         with st.chat_message("assistant"):
# #             st.write(msg["content"])

# #             # Actions inside expander
# #             with st.expander("🔧 Options"):
# #                 lang = st.session_state.lang

# #                 if st.button("🌐 Translate", key=f"tr_{i}"):
# #                     result = bhashini.translate(msg["content"], "en", lang)
# #                     st.success(result)

# #                 if st.button("🔊 Play Audio", key=f"tts_{i}"):
# #                     audio = bhashini.text_to_speech(
# #                         msg["content"],
# #                         lang,
# #                         st.session_state.gender
# #                     )
# #                     if audio:
# #                         st.audio(base64.b64decode(audio))
# #                     else:
# #                         st.warning("Audio unavailable")

# # # ─────────────────────────────────────────────────────────────
# # # CHAT INPUT (BOTTOM)
# # # ─────────────────────────────────────────────────────────────
# # user_input = st.chat_input("Ask your legal question...")

# # if user_input:
# #     st.session_state.messages.append({"role": "user", "content": user_input})

# #     with st.spinner("Thinking..."):
# #         answer = (
# #             llm.answer_with_docs(user_input)
# #             if st.session_state.docs_loaded
# #             else llm.answer_general(user_input)
# #         )

# #     st.session_state.messages.append({"role": "assistant", "content": answer})
# #     st.rerun()





# # # """
# # # LexBot – AI Legal Assistant
# # # Stack : Groq (LLaMA3) + HuggingFace Embeddings + FAISS + Bhashini
# # # Deploy: Streamlit Cloud — all secrets in st.secrets, no local server needed
# # # """

# # # import os
# # # import glob
# # # import base64
# # # import streamlit as st
# # # from utils.bhashini_handler import BhashiniHandler
# # # import base64
# # # bhashini = BhashiniHandler()
# # # # ── Load secrets into env BEFORE importing handlers ──────────────────────────
# # # try:
# # #     for _k in ["HF_TOKEN", "GROQ_API_KEY", "BHASHINI_API_KEY"]:
# # #         if _k in st.secrets and not os.getenv(_k):
# # #             os.environ[_k] = st.secrets[_k]
# # # except Exception:
# # #     pass

# # # from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
# # # from utils.llm_handler import LLMHandler
# # # from utils.bhashini_handler import BhashiniHandler

# # # # ── Page config ───────────────────────────────────────────────────────────────
# # # st.set_page_config(
# # #     page_title="LexBot – AI Legal Assistant",
# # #     page_icon="⚖️",
# # #     layout="wide",
# # #     initial_sidebar_state="expanded",
# # # )

# # # # ── CSS ───────────────────────────────────────────────────────────────────────
# # # st.markdown("""
# # # <style>
# # # * { box-sizing:border-box; }
# # # body,.stApp { background:#0f1117!important; color:#e8eaf0!important;
# # #               font-family:'Inter','Segoe UI',sans-serif; }

# # # /* Sidebar */
# # # [data-testid="stSidebar"] {
# # #     background:linear-gradient(180deg,#1a1d27 0%,#141720 100%)!important;
# # #     border-right:1px solid #2a2d3e;
# # # }
# # # .sidebar-header { text-align:center; padding:1.5rem 0.5rem 1rem; }
# # # .sidebar-header .logo { font-size:3rem; display:block; margin-bottom:.3rem; }
# # # .sidebar-header h1 {
# # #     font-size:1.6rem; font-weight:800; margin:0;
# # #     background:linear-gradient(135deg,#d4af37,#f5d060);
# # #     -webkit-background-clip:text; -webkit-text-fill-color:transparent;
# # # }
# # # .sidebar-header p { color:#8b8fa8; font-size:.78rem; margin:.2rem 0 0; }

# # # .badge-ok {
# # #     background:linear-gradient(135deg,#1a472a,#2d6a4f);
# # #     border:1px solid #40916c; color:#b7e4c7;
# # #     border-radius:20px; padding:.4rem 1rem;
# # #     text-align:center; font-size:.8rem; font-weight:600; margin:.5rem 0;
# # # }
# # # .badge-err {
# # #     background:linear-gradient(135deg,#3a1a1a,#5a2a2a);
# # #     border:1px solid #a04040; color:#f0b0b0;
# # #     border-radius:20px; padding:.4rem 1rem;
# # #     text-align:center; font-size:.8rem; font-weight:600; margin:.5rem 0;
# # # }
# # # .sidebar-footer { color:#555870; font-size:.72rem; text-align:center; padding:.5rem; }

# # # /* Hero */
# # # .hero {
# # #     background:linear-gradient(135deg,#1c1f2e,#242840,#1c2035);
# # #     border:1px solid #2e3250; border-radius:16px;
# # #     padding:2rem 2.5rem; margin-bottom:1.5rem; position:relative; overflow:hidden;
# # # }
# # # .hero::before {
# # #     content:''; position:absolute; inset:0;
# # #     background:radial-gradient(ellipse at top right,rgba(212,175,55,.08),transparent 60%);
# # #     pointer-events:none;
# # # }
# # # .hero h1 {
# # #     font-size:2rem; font-weight:800; margin:0 0 .4rem;
# # #     background:linear-gradient(135deg,#d4af37,#f5d060,#e8c547);
# # #     -webkit-background-clip:text; -webkit-text-fill-color:transparent;
# # # }
# # # .hero p { color:#8b8fa8; margin:0; font-size:1rem; }

# # # /* Stat cards */
# # # .card {
# # #     background:#1a1d27; border:1px solid #2a2d3e; border-radius:12px;
# # #     padding:1rem 1.2rem; display:flex; align-items:center; gap:.8rem;
# # #     transition:border-color .2s,transform .2s;
# # # }
# # # .card:hover { border-color:#d4af37; transform:translateY(-2px); }
# # # .card-icon { font-size:1.8rem; }
# # # .card strong { color:#e8eaf0; font-size:.9rem; }
# # # .card small  { color:#6b7080; font-size:.75rem; }

# # # /* Welcome */
# # # .welcome {
# # #     background:linear-gradient(135deg,#1a1d2e,#1e2138);
# # #     border:1px solid #2e3250; border-left:4px solid #d4af37;
# # #     border-radius:12px; padding:1.8rem 2rem; margin:1rem 0 1.5rem;
# # # }
# # # .welcome h3 { color:#d4af37; margin-top:0; font-size:1.2rem; }
# # # .welcome p  { color:#9097b0; margin:.3rem 0 .8rem; }
# # # .welcome ul { color:#9097b0; padding-left:1.4rem; margin:0; line-height:2; }

# # # /* Chat bubbles */
# # # .bubble {
# # #     display:flex; align-items:flex-start; gap:.8rem;
# # #     padding:1rem 1.2rem; border-radius:12px; margin-bottom:.8rem;
# # #     animation:fadeIn .3s ease;
# # # }
# # # @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
# # # .user-msg { background:linear-gradient(135deg,#1e2d4a,#1a2840); border:1px solid #2a4060; margin-left:3rem; }
# # # .bot-msg  { background:linear-gradient(135deg,#1e1e2e,#242438); border:1px solid #2e2e48; margin-right:3rem; }
# # # .bubble-icon { font-size:1.4rem; flex-shrink:0; margin-top:.1rem; }
# # # .bubble-text { color:#d8dae8; line-height:1.65; font-size:.95rem; flex:1; }

# # # /* Translation box */
# # # .trans-box {
# # #     background:linear-gradient(135deg,#1a2a1a,#1e2e1e);
# # #     border:1px solid #2a5a2a; border-left:3px solid #40a040;
# # #     border-radius:8px; padding:.8rem 1rem; margin:.4rem 0;
# # #     color:#c8e8c8; font-size:.9rem; line-height:1.6;
# # # }
# # # .word-count { color:#555870; font-size:.75rem; padding:.3rem 0; }

# # # /* Input */
# # # .stTextInput>div>div>input {
# # #     background:#1a1d27!important; border:1px solid #2e3250!important;
# # #     color:#e8eaf0!important; border-radius:10px!important;
# # #     padding:.7rem 1rem!important; font-size:.95rem!important;
# # # }
# # # .stTextInput>div>div>input:focus {
# # #     border-color:#d4af37!important;
# # #     box-shadow:0 0 0 2px rgba(212,175,55,.15)!important;
# # # }

# # # /* Buttons */
# # # .stButton>button {
# # #     background:linear-gradient(135deg,#1e2138,#252840)!important;
# # #     border:1px solid #3a3d58!important; color:#c8cae0!important;
# # #     border-radius:8px!important; font-size:.82rem!important; transition:all .2s!important;
# # # }
# # # .stButton>button:hover {
# # #     border-color:#d4af37!important; color:#d4af37!important; transform:translateY(-1px)!important;
# # # }
# # # [data-testid="stButton"]>button[kind="primary"] {
# # #     background:linear-gradient(135deg,#b8960c,#d4af37)!important;
# # #     border:none!important; color:#0f1117!important; font-weight:700!important;
# # # }
# # # [data-testid="stButton"]>button[kind="primary"]:hover {
# # #     background:linear-gradient(135deg,#d4af37,#f5d060)!important;
# # # }

# # # /* Progress */
# # # .stProgress>div>div>div { background:linear-gradient(90deg,#b8960c,#d4af37)!important; }

# # # /* Footer */
# # # .footer {
# # #     text-align:center; color:#444660; font-size:.75rem;
# # #     padding:1.5rem 0 .5rem; border-top:1px solid #1e2030; margin-top:2rem;
# # # }

# # # /* Scrollbar */
# # # ::-webkit-scrollbar { width:5px; }
# # # ::-webkit-scrollbar-track { background:#0f1117; }
# # # ::-webkit-scrollbar-thumb { background:#2a2d3e; border-radius:4px; }
# # # </style>
# # # """, unsafe_allow_html=True)

# # # # ── Session state ─────────────────────────────────────────────────────────────
# # # for k, v in {
# # #     "messages":          [],
# # #     "docs_loaded":       False,
# # #     "vectorstore":       None,
# # #     "lang":              "en",
# # #     "tts_gender":        "female",
# # #     "doc_count":         0,
# # #     "chunk_count":       0,
# # #     "load_error":        None,
# # # }.items():
# # #     if k not in st.session_state:
# # #         st.session_state[k] = v

# # # # ── Cached handlers ───────────────────────────────────────────────────────────
# # # @st.cache_resource(show_spinner=False)
# # # def get_llm():
# # #     return LLMHandler()

# # # @st.cache_resource(show_spinner=False)
# # # def get_bhashini():
# # #     return BhashiniHandler()

# # # @st.cache_resource(show_spinner=False)
# # # def get_loader():
# # #     return DocumentLoader()

# # # llm      = get_llm()
# # # bhashini = get_bhashini()
# # # loader   = get_loader()

# # # # ── Auto-load documents at startup ───────────────────────────────────────────
# # # if not st.session_state.docs_loaded and st.session_state.load_error is None:
# # #     with st.spinner("📚 Loading legal knowledge base…"):
# # #         try:
# # #             bar = st.progress(0, text="Scanning files…")
# # #             vs, dc, cc = loader.load_from_folder(DOCUMENTS_FOLDER)
# # #             st.session_state.update({
# # #                 "vectorstore": vs,
# # #                 "docs_loaded": True,
# # #                 "doc_count":   dc,
# # #                 "chunk_count": cc,
# # #             })
# # #             llm.set_vectorstore(vs)
# # #             bar.empty()
# # #         except Exception as e:
# # #             st.session_state.load_error = str(e)

# # # # ── Language map ──────────────────────────────────────────────────────────────
# # # LANGUAGES = {
# # #     "en": {"name": "English",   "script": "Latn", "flag": "🇺🇸"},
# # #     "hi": {"name": "Hindi",     "script": "Deva", "flag": "🇮🇳"},
# # #     "bn": {"name": "Bengali",   "script": "Beng", "flag": "🇧🇩"},
# # #     "ta": {"name": "Tamil",     "script": "Taml", "flag": "🇮🇳"},
# # #     "te": {"name": "Telugu",    "script": "Telu", "flag": "🇮🇳"},
# # #     "mr": {"name": "Marathi",   "script": "Deva", "flag": "🇮🇳"},
# # #     "gu": {"name": "Gujarati",  "script": "Gujr", "flag": "🇮🇳"},
# # #     "kn": {"name": "Kannada",   "script": "Knda", "flag": "🇮🇳"},
# # #     "ml": {"name": "Malayalam", "script": "Mlym", "flag": "🇮🇳"},
# # #     "pa": {"name": "Punjabi",   "script": "Guru", "flag": "🇮🇳"},
# # #     "ur": {"name": "Urdu",      "script": "Arab", "flag": "🇵🇰"},
# # # }

# # # # ══════════════════════════════════════════════════════════════════════════════
# # # #  SIDEBAR
# # # # ══════════════════════════════════════════════════════════════════════════════
# # # with st.sidebar:
# # #     st.markdown("""
# # #     <div class="sidebar-header">
# # #         <span class="logo">⚖️</span>
# # #         <h1>LexBot</h1>
# # #         <p>AI-Powered Legal Assistant</p>
# # #     </div>
# # #     """, unsafe_allow_html=True)
# # #     st.markdown("---")

# # #     # ── Knowledge Base Status ──────────────────────────────────────────────
# # #     st.markdown("### 📂 Knowledge Base")
# # #     if st.session_state.load_error:
# # #         st.markdown('<div class="badge-err">❌ Load Failed</div>', unsafe_allow_html=True)
# # #         st.error(st.session_state.load_error)
# # #         st.caption(f"📁 Add files to: `{DOCUMENTS_FOLDER}`")
# # #         if st.button("🔄 Retry", use_container_width=True, type="primary"):
# # #             st.session_state.load_error = None
# # #             st.cache_resource.clear()
# # #             st.rerun()

# # #     elif st.session_state.docs_loaded:
# # #         st.markdown('<div class="badge-ok">📚 Knowledge Base Active</div>', unsafe_allow_html=True)
# # #         st.caption(f"📄 **{st.session_state.doc_count}** files  |  🔖 **{st.session_state.chunk_count}** chunks")
# # #         with st.expander("📋 Loaded files"):
# # #             for f in (
# # #                 glob.glob(os.path.join(DOCUMENTS_FOLDER, "**", "*.pdf"),  recursive=True) +
# # #                 glob.glob(os.path.join(DOCUMENTS_FOLDER, "**", "*.docx"), recursive=True)
# # #             ):
# # #                 st.caption(f"• {os.path.basename(f)}")
# # #         if st.button("🔄 Reload Docs", use_container_width=True):
# # #             st.session_state.docs_loaded = False
# # #             st.session_state.load_error  = None
# # #             st.cache_resource.clear()
# # #             st.rerun()
# # #     else:
# # #         st.markdown('<div class="badge-err">⏳ Loading…</div>', unsafe_allow_html=True)

# # #     st.markdown("---")

# # #     # ── Language & Voice ───────────────────────────────────────────────────
# # #     st.markdown("### 🌐 Language & Voice")
# # #     lang_map = {f"{v['flag']} {v['name']}": k for k, v in LANGUAGES.items()}
# # #     sel      = st.selectbox("Output Language", list(lang_map.keys()), index=0)
# # #     st.session_state.lang       = lang_map[sel]
# # #     st.session_state.tts_gender = st.radio("Voice", ["female", "male"], horizontal=True)

# # #     # Show Bhashini status (no key input — static backend)
# # #     if bhashini._ready:
# # #         st.caption("🔊 Translation & TTS: ✅ Active")
# # #     else:
# # #         st.caption("🔊 Translation & TTS: ⚠️ BHASHINI_API_KEY not set in Secrets")

# # #     st.markdown("---")

# # #     # ── Quick Questions ────────────────────────────────────────────────────
# # #     st.markdown("### 💡 Quick Questions")
# # #     for q in [
# # #         "What are fundamental rights?",
# # #         "Explain Article 21",
# # #         "What is bail procedure?",
# # #         "Rights of an arrested person",
# # #         "What is IPC Section 420?",
# # #         "Explain right to free legal aid",
# # #     ]:
# # #         if st.button(q, use_container_width=True, key=f"qq_{q}"):
# # #             st.session_state.pending_q = q

# # #     st.markdown("---")
# # #     if st.button("🗑️ Clear Chat", use_container_width=True):
# # #         st.session_state.messages = []
# # #         st.rerun()

# # #     st.markdown('<div class="sidebar-footer">Groq · HuggingFace · Bhashini</div>', unsafe_allow_html=True)

# # # # ══════════════════════════════════════════════════════════════════════════════
# # # #  MAIN
# # # # ══════════════════════════════════════════════════════════════════════════════
# # # st.markdown("""
# # # <div class="hero">
# # #   <h1>⚖️ LexBot – AI Legal Assistant</h1>
# # #   <p>Ask legal questions in natural language &nbsp;•&nbsp; 11 Indian languages &nbsp;•&nbsp; Voice output</p>
# # # </div>
# # # """, unsafe_allow_html=True)

# # # # Stat cards
# # # for col, (icon, title, sub) in zip(
# # #     st.columns(4),
# # #     [
# # #         ("📄", "Auto-Loaded Docs",  f"{st.session_state.doc_count} files from files/"),
# # #         ("⚡", "Groq LLaMA3",       "Fast cloud inference"),
# # #         ("🌐", "11 Languages",      "Bhashini translation"),
# # #         ("🔊", "Text-to-Speech",    "Female & Male voices"),
# # #     ],
# # # ):
# # #     col.markdown(
# # #         f'<div class="card"><span class="card-icon">{icon}</span>'
# # #         f'<div><strong>{title}</strong><br><small>{sub}</small></div></div>',
# # #         unsafe_allow_html=True,
# # #     )

# # # st.markdown("<br>", unsafe_allow_html=True)

# # # # Load error banner
# # # if st.session_state.load_error:
# # #     st.error(
# # #         f"**⚠️ Knowledge Base Not Loaded**\n\n"
# # #         f"{st.session_state.load_error}\n\n"
# # #         f"Place your PDF/DOCX files inside the `files/` folder, then click **Retry** in the sidebar."
# # #     )

# # # # Welcome message
# # # if not st.session_state.messages:
# # #     st.markdown("""
# # #     <div class="welcome">
# # #         <h3>👋 Welcome to LexBot!</h3>
# # #         <p>Your legal documents are auto-loaded from the <code>files/</code> folder.
# # #            Ask me anything about Indian law.</p>
# # #         <ul>
# # #             <li>📜 Constitutional law &amp; fundamental rights</li>
# # #             <li>⚖️ Criminal procedure — IPC, CrPC</li>
# # #             <li>🏛️ Civil matters &amp; contracts</li>
# # #             <li>👨‍👩‍👧 Family law &amp; property disputes</li>
# # #         </ul>
# # #     </div>
# # #     """, unsafe_allow_html=True)

# # # # Chat history
# # # for i, msg in enumerate(st.session_state.messages):
# # #     cls  = "user-msg" if msg["role"] == "user" else "bot-msg"
# # #     icon = "👤" if msg["role"] == "user" else "⚖️"
# # #     st.markdown(
# # #         f'<div class="bubble {cls}">'
# # #         f'<span class="bubble-icon">{icon}</span>'
# # #         f'<div class="bubble-text">{msg["content"]}</div>'
# # #         f'</div>',
# # #         unsafe_allow_html=True,
# # #     )

# # #     if msg["role"] == "assistant":
# # #         c1, c2, c3, _, _ = st.columns([1, 1, 2, 2, 2])
# # #         lang        = st.session_state.lang
# # #         lang_info   = LANGUAGES[lang]

# # #         # Translate button
# # #         with c1:
# # #             if lang != "en" and bhashini._ready:
# # #                 if st.button(f"🌐 {lang_info['name']}", key=f"tr_{i}"):
# # #                     with st.spinner("Translating…"):
# # #                         result = bhashini.translate(
# # #                             msg["content"], "en", lang, lang_info["script"]
# # #                         )
# # #                     st.markdown(
# # #                         f'<div class="trans-box"><strong>🌐 {lang_info["name"]}:</strong>'
# # #                         f'<br>{result}</div>',
# # #                         unsafe_allow_html=True,
# # #                     )
# # #             elif lang != "en":
# # #                 st.caption("⚠️ TTS key not set")

# # #         # TTS button
# # #         with c2:
# # #             if bhashini._ready:
# # #                 if st.button("🔊 Listen", key=f"tts_{i}"):
# # #                     with st.spinner("Generating audio…"):
# # #                         audio_b64 = bhashini.text_to_speech(
# # #                             msg["content"], lang,
# # #                             # lang_info["script"],
# # #                             st.session_state.tts_gender,
# # #                         )
# # #                     if audio_b64:
# # #                         st.audio(base64.b64decode(audio_b64), format="audio/wav")
# # #                     else:
# # #                         st.warning("Audio unavailable for this language.")

# # #         # Word count
# # #         with c3:
# # #             st.markdown(
# # #                 f'<div class="word-count">💬 {len(msg["content"].split())} words</div>',
# # #                 unsafe_allow_html=True,
# # #             )

# # # # ── Input ─────────────────────────────────────────────────────────────────────
# # # st.markdown("<br>", unsafe_allow_html=True)
# # # default = st.session_state.pop("pending_q", "")
# # # ic, bc  = st.columns([5, 1])

# # # with ic:
# # #     user_input = st.text_input(
# # #         "q", value=default,
# # #         placeholder="e.g. What are the rights of an accused under CrPC?",
# # #         label_visibility="collapsed",
# # #     )
# # # with bc:
# # #     send = st.button("Send ➤", type="primary", use_container_width=True)

# # # # Process
# # # if send and user_input.strip():
# # #     q = user_input.strip()
# # #     st.session_state.messages.append({"role": "user", "content": q})
# # #     with st.spinner("⚖️ Thinking…"):
# # #         answer = (
# # #             llm.answer_with_docs(q)
# # #             if st.session_state.docs_loaded
# # #             else llm.answer_general(q)
# # #         )
# # #     st.session_state.messages.append({"role": "assistant", "content": answer})
# # #     st.rerun()

# # # st.markdown("""
# # # <div class="footer">
# # #     ⚖️ LexBot provides general legal information only.
# # #     Always consult a qualified legal professional for specific legal matters.
# # # </div>
# # # """, unsafe_allow_html=True)
