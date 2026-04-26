import streamlit as st
import base64

from utils.document import DocumentLoader
from utils.llm import LLMHandler
from utils.bhashini_handler import speech_handler


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="LexBot",
    page_icon="⚖️",
    layout="wide"
)

# =========================
# SESSION INIT
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "vectorstore" not in st.session_state:
    loader = DocumentLoader()
    st.session_state.vectorstore = loader.load_from_folder()

if "llm" not in st.session_state:
    llm = LLMHandler()
    llm.set_vectorstore(st.session_state.vectorstore)
    st.session_state.llm = llm

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None


# =========================
# CSS (CHATGPT STYLE)
# =========================
st.markdown("""
<style>

.block-container {
    padding-bottom: 120px;
}

/* Chat bubbles */
.chat-user {
    background: #2563eb;
    color: white;
    padding: 10px 14px;
    border-radius: 14px;
    margin: 6px 0;
    max-width: 80%;
    margin-left: auto;
}

.chat-bot {
    background: #1f2937;
    color: white;
    padding: 10px 14px;
    border-radius: 14px;
    margin: 6px 0;
    max-width: 80%;
}

/* Bottom input */
.stChatInputContainer {
    position: fixed;
    bottom: 0;
    width: 100%;
    background: #0f172a;
    padding: 10px;
    border-top: 1px solid #333;
}

/* Mic small */
.mic-box {
    position: fixed;
    bottom: 70px;
    right: 20px;
}

</style>
""", unsafe_allow_html=True)


# =========================
# SHOW CHAT
# =========================
for msg in st.session_state.messages:

    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)

    else:
        st.markdown(f'<div class="chat-bot">{msg["content"]}</div>', unsafe_allow_html=True)

        # 🔊 AUDIO PLAY (FIXED)
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")


# =========================
# MIC INPUT (BOTTOM RIGHT)
# =========================
st.markdown('<div class="mic-box">', unsafe_allow_html=True)
audio_data = st.audio_input("")
st.markdown('</div>', unsafe_allow_html=True)

if audio_data:

    audio_bytes = audio_data.read()

    # prevent repeat
    if st.session_state.last_audio == audio_bytes:
        st.stop()

    st.session_state.last_audio = audio_bytes

    audio_b64 = base64.b64encode(audio_bytes).decode()

    text = speech_handler.speech_to_text(audio_b64)

    if text:
        st.session_state.messages.append({"role": "user", "content": text})
        st.rerun()


# =========================
# TEXT INPUT (CHATGPT STYLE)
# =========================
user_input = st.chat_input("Ask anything about law or your documents...")

if user_input:

    # show instantly
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("Thinking..."):
        answer = st.session_state.llm.answer(user_input)

        audio = speech_handler.text_to_speech(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "audio": audio
    })

    # st.rerun()