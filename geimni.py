import os
import base64
import streamlit as st

# Custom Handlers
from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
from utils.llm_handler import LLMHandler
from utils.bhashini_handler import BhashiniHandler

# ==========================================
# 1. INITIALIZATION & CONFIG
# ==========================================
st.set_page_config(page_title="LexBot", page_icon="⚖️", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# 2. SHARP MOBILE-FIRST CSS
# ==========================================
st.markdown("""
<style>
    /* Prevent blur on mobile by using standard backgrounds */
    .stApp { background-color: #0E1117; color: #E3E3E3; }
    
    /* STICKY TOP HEADER */
    .header-box {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background-color: #000000;
        padding: 10px;
        text-align: center;
        z-index: 1000;
        border-bottom: 1px solid #333;
    }

    /* PADDING ADJUSTMENT (Crucial for Cloud Deployment) */
    .main .block-container { 
        padding-top: 60px !important; 
        padding-bottom: 150px !important;
        max-width: 800px;
    }

    /* CHAT BUBBLES */
    .stChatMessage { 
        background-color: #1E1F20; 
        border-radius: 18px; 
        border: 1px solid #333;
        margin-bottom: 10px;
    }

    /* THE MIC BUTTON: Positioned just above the chat input */
    [data-testid="stAudioInput"] {
        position: fixed;
        bottom: 85px; /* Sits directly above the chat input */
        right: 20px;
        z-index: 1001;
        width: 50px !important;
        height: 50px !important;
        overflow: hidden;
        border-radius: 50% !important;
        background-color: #262730;
        border: 1px solid #444;
        transition: 0.2s;
    }

    /* ACTION BUTTONS */
    .stButton > button { 
        border-radius: 20px !important; 
        background-color: #333 !important; 
        color: white !important; 
        border: 1px solid #444 !important;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #000000 !important; }
</style>

<div class="header-box">
    <h3 style="margin:0; color: white; font-family: sans-serif;">⚖️ Legal AI Assistant</h3>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 3. LOAD MODELS
# ==========================================
@st.cache_resource
def load_all():
    llm, bhashini, loader = LLMHandler(), BhashiniHandler(), DocumentLoader()
    vs, doc_count, _ = loader.load_from_folder(DOCUMENTS_FOLDER)
    llm.set_vectorstore(vs)
    return llm, bhashini, doc_count

llm, bhashini, doc_count = load_all()

LANG_MAP = {
    "English": "eng_Latn", "Hindi": "hin_Deva", "Marathi": "mar_Deva",
    "Tamil": "tam_Taml", "Telugu": "tel_Telu", "Bengali": "ben_Beng"
}

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.title("Settings")
    st.info(f"📄 {doc_count} Docs Loaded")
    st.session_state.lang = st.selectbox("🌍 Language", list(LANG_MAP.keys()))
    st.session_state.gender = st.radio("🔊 Voice", ["female", "male"], horizontal=True)
    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 5. DISPLAY MESSAGES
# ==========================================
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            c1, c2, _ = st.columns([0.3, 0.3, 0.4])
            with c1:
                if st.button("🌐 Translate", key=f"tr_{i}"):
                    tgt = LANG_MAP[st.session_state.lang]
                    res = bhashini.translate(msg["content"], "eng_Latn", tgt) if tgt != "eng_Latn" else msg["content"]
                    st.info(res)
            with c2:
                if st.button("🔊 Audio", key=f"tts_{i}"):
                    tgt = LANG_MAP[st.session_state.lang]
                    audio = bhashini.text_to_speech(msg["content"], tgt, st.session_state.gender)
                    if audio:
                        st.audio(base64.b64decode(audio), format="audio/wav", autoplay=True)

# ==========================================
# 6. FIXED INPUTS (MIC + TEXT)
# ==========================================
# The Mic button is styled via CSS to float just above the chat bar
audio_data = st.audio_input("Mic", label_visibility="collapsed")
user_input = st.chat_input("Ask your legal question...")

# ==========================================
# 7. PROCESSING LOGIC
# ==========================================
input_text = None

if user_input:
    input_text = user_input
elif audio_data:
    with st.spinner("🎙️ Listening..."):
        audio_b64 = base64.b64encode(audio_data.read()).decode()
        input_text = bhashini.speech_to_text(audio_b64, LANG_MAP[st.session_state.lang])

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    with st.chat_message("assistant"):
        with st.spinner("Consulting documents..."):
            raw_answer = llm.answer_with_docs(input_text)
            tgt_lang = LANG_MAP[st.session_state.lang]
            display_answer = bhashini.translate(raw_answer, "eng_Latn", tgt_lang) if tgt_lang != "eng_Latn" else raw_answer
            st.session_state.messages.append({"role": "assistant", "content": display_answer})
            
    # st.rerun()







# import os
# import base64
# import streamlit as st

# from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
# from utils.llm_handler import LLMHandler
# from utils.bhashini_handler import BhashiniHandler

# # =========================
# # CONFIG & PREMIUM UI
# # =========================
# st.set_page_config(page_title="LexBot", page_icon="⚖️", layout="centered")

# st.markdown("""
# <style>
#     .stApp { background-color: #0E1117; color: #E3E3E3; }
#     [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #333; }
#     [data-testid="stSidebar"] * { color: #FFFFFF !important; }
#     .stChatMessage { background-color: #1E1F20; border-radius: 15px; border: 1px solid #333; }
#     .stButton > button { border-radius: 20px !important; background-color: #262730 !important; color: white !important; height: 32px !important; }
#     /* Fixes the gap at the bottom */
#     .block-container { padding-bottom: 150px; }
# </style>
# """, unsafe_allow_html=True)

# # =========================
# # INITIALIZATION
# # =========================
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# @st.cache_resource
# def load_all():
#     llm, bhashini, loader = LLMHandler(), BhashiniHandler(), DocumentLoader()
#     vs, doc_count, _ = loader.load_from_folder(DOCUMENTS_FOLDER)
#     llm.set_vectorstore(vs)
#     return llm, bhashini, doc_count

# llm, bhashini, doc_count = load_all()

# LANG_MAP = {
#     "English": "eng_Latn", "Hindi": "hin_Deva", "Marathi": "mar_Deva",
#     "Tamil": "tam_Taml", "Telugu": "tel_Telu", "Bengali": "ben_Beng"
# }

# # =========================
# # SIDEBAR
# # =========================
# with st.sidebar:
#     st.title("⚖️ LexBot Settings")
#     st.success(f"📄 {doc_count} Docs Loaded")
#     st.session_state.lang = st.selectbox("🌍 Language", list(LANG_MAP.keys()))
#     st.session_state.gender = st.radio("🔊 Voice", ["female", "male"], horizontal=True)
#     if st.button("🧹 Clear Chat", use_container_width=True):
#         st.session_state.messages = []
#         st.rerun()

# # =========================
# # LOGIC SECTION (MOVED UP)
# # =========================
# # We process inputs BEFORE displaying the chat history
# with st.container():
#     audio_data = st.audio_input("Voice Input", label_visibility="collapsed")
#     user_input = st.chat_input("Ask your legal question...")

# input_text = None
# if user_input:
#     input_text = user_input
# elif audio_data:
#     with st.spinner("Processing Voice..."):
#         audio_b64 = base64.b64encode(audio_data.read()).decode()
#         input_text = bhashini.speech_to_text(audio_b64, LANG_MAP[st.session_state.lang])

# if input_text:
#     # Add User Message
#     st.session_state.messages.append({"role": "user", "content": input_text})
    
#     # Generate Assistant Answer immediately
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             raw_answer = llm.answer_with_docs(input_text)
#             tgt_lang = LANG_MAP[st.session_state.lang]
#             display_answer = bhashini.translate(raw_answer, "eng_Latn", tgt_lang) if tgt_lang != "eng_Latn" else raw_answer
            
#             # Save to history
#             st.session_state.messages.append({"role": "assistant", "content": display_answer})
#             # Force a rerun so the loop below sees the new messages and draws buttons
#             st.rerun()

# # =========================
# # CHAT DISPLAY (AFTER LOGIC)
# # =========================
# # st.title("⚖️ Legal AI Assistant")

# # Use a container for the chat history
# for i, msg in enumerate(st.session_state.messages):
#     with st.chat_message(msg["role"]):
#         st.write(msg["content"])

#         if msg["role"] == "assistant":
#             col1, col2, _ = st.columns([0.25, 0.25, 0.5])
#             with col1:
#                 if st.button("🌐 Translate", key=f"tr_{i}"):
#                     tgt = LANG_MAP[st.session_state.lang]
#                     res = bhashini.translate(msg["content"], "eng_Latn", tgt) if tgt != "eng_Latn" else msg["content"]
#                     st.info(res)
#             with col2:
#                 if st.button("🔊 Audio", key=f"tts_{i}"):
#                     tgt = LANG_MAP[st.session_state.lang]
#                     audio = bhashini.text_to_speech(msg["content"], tgt, st.session_state.gender)
#                     if audio:
#                         st.audio(base64.b64decode(audio), format="audio/wav", autoplay=True)