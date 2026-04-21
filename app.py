import os
import base64
import streamlit as st

from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
from utils.llm_handler import LLMHandler
from utils.bhashini_handler import BhashiniHandler


# =========================
# CONFIG
# =========================
st.set_page_config(page_title="LexBot", page_icon="⚖️", layout="centered")

os.environ["BHASHINI_API_KEY"] = st.secrets.get("BHASHINI_API_KEY", "")


# =========================
# CSS
# =========================
st.markdown("""
<style>
.block-container {
    max-width: 850px;
    margin: auto;
    padding-bottom: 120px;
}
.bottom-container {
    position: sticky;
    bottom: 0;
    background: #0f1117;
    padding: 10px 0;
    border-top: 1px solid #2a2a2a;
}
</style>
""", unsafe_allow_html=True)


# =========================
# LANGUAGE MAP
# =========================
LANG_MAP = {
    "English": "eng_Latn",
    "Hindi": "hin_Deva",
    "Marathi": "mar_Deva",
    "Tamil": "tam_Taml",
    "Telugu": "tel_Telu",
}


# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "lang" not in st.session_state:
    st.session_state.lang = "English"

if "gender" not in st.session_state:
    st.session_state.gender = "female"

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None


# =========================
# LOAD
# =========================
@st.cache_resource
def load_all():
    llm = LLMHandler()
    bhashini = BhashiniHandler()
    loader = DocumentLoader()

    vs, _, _ = loader.load_from_folder(DOCUMENTS_FOLDER)
    llm.set_vectorstore(vs)

    return llm, bhashini


llm, bhashini = load_all()


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.title("⚖️ LexBot")

    st.session_state.lang = st.selectbox("Language", list(LANG_MAP.keys()))
    st.session_state.gender = st.radio("Voice", ["female", "male"])

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_audio = None
        st.rerun()


# =========================
# CHAT DISPLAY
# =========================
for i, msg in enumerate(st.session_state.messages):

    with st.chat_message(msg["role"]):
        st.write(msg["content"])

        if msg["role"] == "assistant":

            col1, col2 = st.columns([1,1])

            # TRANSLATE
            with col1:
                if st.button("🌐 Translate", key=f"tr_{i}"):

                    tgt = LANG_MAP[st.session_state.lang]

                    translated = bhashini.translate(
                        msg["content"], "eng_Latn", tgt
                    )

                    st.session_state.messages[i]["translated"] = translated
                    st.rerun()

            # AUDIO
            with col2:
                if st.button("🔊 Audio", key=f"tts_{i}"):

                    tgt = LANG_MAP[st.session_state.lang]

                    audio = bhashini.text_to_speech(
                        msg["content"], tgt, st.session_state.gender
                    )

                    st.session_state.messages[i]["audio"] = audio
                    st.rerun()

            # SHOW OUTPUT
            if msg.get("translated"):
                st.success(msg["translated"])

            if msg.get("audio"):
                st.audio(base64.b64decode(msg["audio"]))


# =========================
# INPUT (BOTTOM)
# =========================
st.markdown('<div class="bottom-container">', unsafe_allow_html=True)

user_input = st.chat_input("Ask your question...")

st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 🎤 SPEECH INPUT (FIXED)
# =========================
audio_data = st.audio_input("🎤 Speak", label_visibility="collapsed")

if audio_data:

    audio_bytes = audio_data.read()

    # Prevent duplicate processing
    if st.session_state.last_audio == audio_bytes:
        st.stop()

    st.session_state.last_audio = audio_bytes

    audio_b64 = base64.b64encode(audio_bytes).decode()
    src_lang = LANG_MAP[st.session_state.lang]

    text = bhashini.speech_to_text(audio_b64, src_lang)

    if text and text.strip():

        text = text.strip()

        # ADD USER MESSAGE
        st.session_state.messages.append({
            "role": "user",
            "content": text
        })

        # GENERATE RESPONSE
        answer = llm.answer_with_docs(text)

        tgt = LANG_MAP[st.session_state.lang]

        if tgt != "eng_Latn":
            answer = bhashini.translate(answer, "eng_Latn", tgt)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "translated": None,
            "audio": None
        })

        st.rerun()


# =========================
# TEXT INPUT
# =========================
if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    answer = llm.answer_with_docs(user_input)

    tgt = LANG_MAP[st.session_state.lang]

    if tgt != "eng_Latn":
        answer = bhashini.translate(answer, "eng_Latn", tgt)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "translated": None,
        "audio": None
    })

    st.rerun()





# import os
# import base64
# import streamlit as st

# from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
# from utils.llm_handler import LLMHandler
# from utils.bhashini_handler import BhashiniHandler


# # =========================
# # CONFIG
# # =========================
# st.set_page_config(page_title="LexBot", page_icon="⚖️")

# os.environ["BHASHINI_API_KEY"] = st.secrets.get("BHASHINI_API_KEY", "")


# # =========================
# # CSS (CHATGPT STYLE)
# # =========================
# st.markdown("""
# <style>
# .block-container {
#     max-width: 900px;
#     padding-bottom: 120px;
# }
# .bottom-bar {
#     position: fixed;
#     bottom: 0;
#     left: 0;
#     right: 0;
#     background: #0f1117;
#     padding: 12px;
#     border-top: 1px solid #2a2a2a;
#     z-index: 9999;
# }
# .bottom-inner {
#     max-width: 900px;
#     margin: auto;
# }
# @media (max-width: 768px) {
#     .block-container {
#         max-width: 100% !important;
#         padding: 10px !important;
#     }
# }
# </style>
# """, unsafe_allow_html=True)


# # =========================
# # LANGUAGE MAP
# # =========================
# LANG_MAP = {
#     "English": "eng_Latn",
#     "Hindi": "hin_Deva",
#     "Marathi": "mar_Deva",
#     "Tamil": "tam_Taml",
#     "Telugu": "tel_Telu",
#     "Bengali": "ben_Beng",
#     "Gujarati": "guj_Gujr",
#     "Kannada": "kan_Knda",
#     "Malayalam": "mal_Mlym",
#     "Punjabi": "pan_Guru",
#     "Urdu": "urd_Arab"
# }


# # =========================
# # SESSION STATE
# # =========================
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# if "lang" not in st.session_state:
#     st.session_state.lang = "English"

# if "gender" not in st.session_state:
#     st.session_state.gender = "female"

# if "last_audio" not in st.session_state:
#     st.session_state.last_audio = None


# # =========================
# # LOAD MODELS
# # =========================
# @st.cache_resource
# def load_all():
#     llm = LLMHandler()
#     bhashini = BhashiniHandler()
#     loader = DocumentLoader()

#     vs, doc_count, _ = loader.load_from_folder(DOCUMENTS_FOLDER)
#     llm.set_vectorstore(vs)

#     return llm, bhashini, doc_count


# llm, bhashini, doc_count = load_all()


# # =========================
# # SIDEBAR
# # =========================
# with st.sidebar:
#     st.title("⚖️ LexBot")
#     st.success(f"📄 {doc_count} docs loaded")

#     st.session_state.lang = st.selectbox("🌍 Language", list(LANG_MAP.keys()))
#     st.session_state.gender = st.radio("🔊 Voice", ["female", "male"])

#     if st.button("🧹 Clear Chat"):
#         st.session_state.messages = []
#         st.session_state.last_audio = None
#         st.rerun()


# # =========================
# # HEADER
# # =========================
# st.title("⚖️ Legal AI Assistant")


# # =========================
# # CHAT DISPLAY + ACTIONS
# # =========================
# for i, msg in enumerate(st.session_state.messages):

#     with st.chat_message(msg["role"]):
#         st.write(msg["content"])

#         # 🔥 ACTION BUTTONS FOR ASSISTANT
#         if msg["role"] == "assistant":

#             col1, col2 = st.columns(2)

#             # 🌐 TRANSLATE
#             with col1:
#                 if st.button("🌐 Translate", key=f"tr_{i}"):

#                     tgt_lang = LANG_MAP[st.session_state.lang]

#                     if tgt_lang != "eng_Latn":
#                         translated = bhashini.translate(
#                             msg["content"],
#                             "eng_Latn",
#                             tgt_lang
#                         )
#                     else:
#                         translated = msg["content"]

#                     st.success(translated)

#             # 🔊 AUDIO (TTS)
#             with col2:
#                 if st.button("🔊 Audio", key=f"tts_{i}"):

#                     tgt_lang = LANG_MAP[st.session_state.lang]

#                     # Ensure text language matches TTS language
#                     if tgt_lang != "eng_Latn":
#                         tts_text = bhashini.translate(
#                             msg["content"],
#                             "eng_Latn",
#                             tgt_lang
#                         )
#                     else:
#                         tts_text = msg["content"]

#                     audio_b64 = bhashini.text_to_speech(
#                         tts_text,
#                         tgt_lang,
#                         st.session_state.gender
#                     )

#                     if audio_b64:
#                         st.audio(base64.b64decode(audio_b64), format="audio/wav")


# # =========================
# # INPUT BAR (BOTTOM)
# # =========================
# st.markdown('<div class="bottom-bar"><div class="bottom-inner">', unsafe_allow_html=True)

# col1, col2 = st.columns([10, 1])

# with col1:
#     user_input = st.chat_input("Ask your legal question...")

# # with col2:
#     # mic_clicked = st.button("🎤", key="mic_btn")

# st.markdown('</div></div>', unsafe_allow_html=True)


# # =========================
# # HIDDEN AUDIO INPUT
# # =========================
# audio_data = st.audio_input("hidden", label_visibility="collapsed")


# # =========================
# # SPEECH INPUT
# # =========================
# if audio_data:

#     audio_bytes = audio_data.read()

#     if st.session_state.last_audio == audio_bytes:
#         st.stop()

#     st.session_state.last_audio = audio_bytes

#     audio_b64 = base64.b64encode(audio_bytes).decode()
#     src_lang = LANG_MAP[st.session_state.lang]

#     text = bhashini.speech_to_text(audio_b64, src_lang)

#     if text:
#         st.session_state.messages.append({"role": "user", "content": text})

#         with st.chat_message("user"):
#             st.write(text)

#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 answer = llm.answer_with_docs(text)

#                 tgt_lang = LANG_MAP[st.session_state.lang]
#                 if tgt_lang != "eng_Latn":
#                     answer = bhashini.translate(answer, "eng_Latn", tgt_lang)

#                 st.write(answer)

#         st.session_state.messages.append({"role": "assistant", "content": answer})


# # =========================
# # TEXT INPUT
# # =========================
# if user_input:

#     st.session_state.messages.append({
#         "role": "user",
#         "content": user_input
#     })

#     with st.chat_message("user"):
#         st.write(user_input)

#     # ASSISTANT RESPONSE
#     with st.chat_message("assistant"):

#         with st.spinner("Thinking..."):
#             answer = llm.answer_with_docs(user_input)

#             tgt_lang = LANG_MAP[st.session_state.lang]

#             if tgt_lang != "eng_Latn":
#                 answer = bhashini.translate(answer, "eng_Latn", tgt_lang)

#             st.write(answer)

#         # 🔥 ADD BUTTONS HERE
#         col1, col2 = st.columns(2)

#         with col1:
#             if st.button("🌐 Translate", key=f"tr_new_{len(st.session_state.messages)}"):

#                 translated = bhashini.translate(
#                     answer,
#                     "eng_Latn",
#                     tgt_lang
#                 )
#                 st.success(translated)

#         with col2:
#             if st.button("🔊 Audio", key=f"tts_new_{len(st.session_state.messages)}"):

#                 audio_b64 = bhashini.text_to_speech(
#                     answer,
#                     tgt_lang,
#                     st.session_state.gender
#                 )

#                 if audio_b64:
#                     st.audio(base64.b64decode(audio_b64), format="audio/wav")

#     # SAVE MESSAGE
#     st.session_state.messages.append({
#         "role": "assistant",
#         "content": answer
#     })



# # import os
# # import base64
# # import streamlit as st

# # from utils.document_loader import DocumentLoader, DOCUMENTS_FOLDER
# # from utils.llm_handler import LLMHandler
# # from utils.bhashini_handler import BhashiniHandler


# # # =========================
# # # CONFIG
# # # =========================
# # st.set_page_config(page_title="LexBot", page_icon="⚖️")

# # os.environ["BHASHINI_API_KEY"] = st.secrets.get("BHASHINI_API_KEY", "")


# # # =========================
# # # CSS (CHATGPT STYLE)
# # # =========================
# # st.markdown("""
# # <style>
# # .block-container {
# #     max-width: 900px;
# #     padding-bottom: 120px;
# # }
# # .bottom-bar {
# #     position: fixed;
# #     bottom: 0;
# #     left: 0;
# #     right: 0;
# #     background: #0f1117;
# #     padding: 12px;
# #     border-top: 1px solid #2a2a2a;
# #     z-index: 9999;
# # }
# # .bottom-inner {
# #     max-width: 900px;
# #     margin: auto;
# # }
# # @media (max-width: 768px) {
# #     .block-container {
# #         max-width: 100% !important;
# #         padding: 10px !important;
# #     }
# # }
# # </style>
# # """, unsafe_allow_html=True)


# # # =========================
# # # LANGUAGE MAP
# # # =========================
# # LANG_MAP = {
# #     "English": "eng_Latn",
# #     "Hindi": "hin_Deva",
# #     "Marathi": "mar_Deva",
# #     "Tamil": "tam_Taml",
# #     "Telugu": "tel_Telu",
# #     "Bengali": "ben_Beng",
# #     "Gujarati": "guj_Gujr",
# #     "Kannada": "kan_Knda",
# #     "Malayalam": "mal_Mlym",
# #     "Punjabi": "pan_Guru",
# #     "Urdu": "urd_Arab"
# # }


# # # =========================
# # # SESSION STATE
# # # =========================
# # if "messages" not in st.session_state:
# #     st.session_state.messages = []

# # if "lang" not in st.session_state:
# #     st.session_state.lang = "English"

# # if "gender" not in st.session_state:
# #     st.session_state.gender = "female"

# # if "last_audio" not in st.session_state:
# #     st.session_state.last_audio = None


# # # =========================
# # # LOAD MODELS
# # # =========================
# # @st.cache_resource
# # def load_all():
# #     llm = LLMHandler()
# #     bhashini = BhashiniHandler()
# #     loader = DocumentLoader()

# #     vs, doc_count, _ = loader.load_from_folder(DOCUMENTS_FOLDER)
# #     llm.set_vectorstore(vs)

# #     return llm, bhashini, doc_count


# # llm, bhashini, doc_count = load_all()


# # # =========================
# # # SIDEBAR
# # # =========================
# # with st.sidebar:
# #     st.title("⚖️ LexBot")
# #     st.success(f"📄 {doc_count} docs loaded")

# #     st.session_state.lang = st.selectbox("🌍 Language", list(LANG_MAP.keys()))
# #     st.session_state.gender = st.radio("🔊 Voice", ["female", "male"])

# #     if st.button("🧹 Clear Chat"):
# #         st.session_state.messages = []
# #         st.session_state.last_audio = None
# #         st.rerun()


# # # =========================
# # # HEADER
# # # =========================
# # st.title("⚖️ Legal AI Assistant")


# # # =========================
# # # CHAT DISPLAY + ACTIONS
# # # =========================
# # for i, msg in enumerate(st.session_state.messages):

# #     with st.chat_message(msg["role"]):
# #         st.write(msg["content"])

# #         # 🔥 ACTION BUTTONS FOR ASSISTANT
# #         if msg["role"] == "assistant":

# #             col1, col2 = st.columns(2)

# #             # 🌐 TRANSLATE
# #             with col1:
# #                 if st.button("🌐 Translate", key=f"tr_{i}"):

# #                     tgt_lang = LANG_MAP[st.session_state.lang]

# #                     if tgt_lang != "eng_Latn":
# #                         translated = bhashini.translate(
# #                             msg["content"],
# #                             "eng_Latn",
# #                             tgt_lang
# #                         )
# #                     else:
# #                         translated = msg["content"]

# #                     st.success(translated)

# #             # 🔊 AUDIO (TTS)
# #             with col2:
# #                 if st.button("🔊 Audio", key=f"tts_{i}"):

# #                     tgt_lang = LANG_MAP[st.session_state.lang]

# #                     # Ensure text language matches TTS language
# #                     if tgt_lang != "eng_Latn":
# #                         tts_text = bhashini.translate(
# #                             msg["content"],
# #                             "eng_Latn",
# #                             tgt_lang
# #                         )
# #                     else:
# #                         tts_text = msg["content"]

# #                     audio_b64 = bhashini.text_to_speech(
# #                         tts_text,
# #                         tgt_lang,
# #                         st.session_state.gender
# #                     )

# #                     if audio_b64:
# #                         st.audio(base64.b64decode(audio_b64), format="audio/wav")


# # # =========================
# # # INPUT BAR (BOTTOM)
# # # =========================
# # st.markdown('<div class="bottom-bar"><div class="bottom-inner">', unsafe_allow_html=True)

# # col1, col2 = st.columns([10, 1])

# # with col1:
# #     user_input = st.chat_input("Ask your legal question...")

# # with col2:
# #     mic_clicked = st.button("🎤", key="mic_btn")

# # st.markdown('</div></div>', unsafe_allow_html=True)


# # # =========================
# # # HIDDEN AUDIO INPUT
# # # =========================
# # audio_data = st.audio_input("hidden", label_visibility="collapsed")


# # # =========================
# # # SPEECH INPUT
# # # =========================
# # if audio_data:

# #     audio_bytes = audio_data.read()

# #     if st.session_state.last_audio == audio_bytes:
# #         st.stop()

# #     st.session_state.last_audio = audio_bytes

# #     audio_b64 = base64.b64encode(audio_bytes).decode()
# #     src_lang = LANG_MAP[st.session_state.lang]

# #     text = bhashini.speech_to_text(audio_b64, src_lang)

# #     if text:
# #         st.session_state.messages.append({"role": "user", "content": text})

# #         with st.chat_message("user"):
# #             st.write(text)

# #         with st.chat_message("assistant"):
# #             with st.spinner("Thinking..."):
# #                 answer = llm.answer_with_docs(text)

# #                 tgt_lang = LANG_MAP[st.session_state.lang]
# #                 if tgt_lang != "eng_Latn":
# #                     answer = bhashini.translate(answer, "eng_Latn", tgt_lang)

# #                 st.write(answer)

# #         st.session_state.messages.append({"role": "assistant", "content": answer})


# # # =========================
# # # TEXT INPUT
# # # =========================
# # if user_input:

# #     st.session_state.messages.append({"role": "user", "content": user_input})

# #     with st.chat_message("user"):
# #         st.write(user_input)

# #     with st.chat_message("assistant"):
# #         with st.spinner("Thinking..."):
# #             answer = llm.answer_with_docs(user_input)

# #             tgt_lang = LANG_MAP[st.session_state.lang]
# #             if tgt_lang != "eng_Latn":
# #                 answer = bhashini.translate(answer, "eng_Latn", tgt_lang)

# #             st.write(answer)

# #     st.session_state.messages.append({"role": "assistant", "content": answer})