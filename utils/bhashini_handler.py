import os
import base64
import io
import tempfile
from groq import Groq
from gtts import gTTS
import speech_recognition as sr

GROQ_TTS_AVAILABLE = True

# =========================
# INIT GROQ CLIENT
# =========================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# =========================
# FALLBACK TTS
# =========================
def fallback_tts(text):

    if not text.strip():
        return None

    try:
        print("⚠️ Using fallback gTTS")

        tts = gTTS(text=text, lang="en")

        buf = io.BytesIO()
        tts.write_to_fp(buf)

        return buf.getvalue()

    except Exception as e:
        print("❌ FALLBACK TTS ERROR:", e)
        return None


# =========================
# TEXT CHUNKING
# =========================
def split_text(text, max_chars=190):
    words = text.split()
    chunks = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += " " + word
        else:
            chunks.append(current.strip())
            current = word

    if current:
        chunks.append(current.strip())

    return chunks


# =========================
# AUDIO → 16k WAV
# =========================
# def ensure_16k_wav_bytes(b64):

#     audio_bytes = base64.b64decode(b64)

#     audio = AudioSegment.from_file(io.BytesIO(audio_bytes))

#     audio = (
#         audio
#         .set_frame_rate(16000)
#         .set_channels(1)
#         .set_sample_width(2)
#     )

#     buf = io.BytesIO()
#     audio.export(buf, format="wav", codec="pcm_s16le")

#     return buf.getvalue()
def ensure_16k_wav_bytes(b64):
    if "," in b64:
        b64 = b64.split(",")[1]
    return base64.b64decode(b64)


# =========================
# 🎤 GROQ STT
# =========================
def groq_stt(audio_base64):

    if "," in audio_base64:
        audio_base64 = audio_base64.split(",")[1]

    temp_path = None

    try:
        wav_bytes = ensure_16k_wav_bytes(audio_base64)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(wav_bytes)
            temp_path = f.name

        with open(temp_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo",
                response_format="json",
                language=None,
                temperature=0.0
            )

        return transcription.text

    except Exception as e:
        print("❌ GROQ STT ERROR:", e)
        return ""

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# =========================
# 🎤 FALLBACK STT
# =========================
def fallback_stt(audio_base64):

    temp_path = None

    try:
        wav_bytes = ensure_16k_wav_bytes(audio_base64)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(wav_bytes)
            temp_path = f.name

        recognizer = sr.Recognizer()

        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)

        return recognizer.recognize_google(audio_data)

    except Exception as e:
        print("❌ FALLBACK STT ERROR:", e)
        return ""

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# =========================
# 🔊 GROQ TTS
# =========================
def groq_tts(text, voice="troy"):

    global GROQ_TTS_AVAILABLE

    if not text.strip():
        return None

    if not GROQ_TTS_AVAILABLE:
        return None

    try:
        chunks = split_text(text)
        audio_bytes = b""

        for chunk in chunks:
            response = client.audio.speech.create(
                model="canopylabs/orpheus-v1-english",
                voice=voice,
                input=chunk,
                response_format="wav"
            )
            audio_bytes += response.read()

        return audio_bytes

    except Exception as e:
        print("❌ GROQ TTS ERROR:", e)

        if "429" in str(e) or "rate_limit" in str(e):
            print("🚫 Disabling Groq TTS temporarily")
            GROQ_TTS_AVAILABLE = False

        return None


# =========================
# HANDLER CLASS
# =========================
class SpeechHandler:

    def __init__(self, debug=True):
        self.debug = debug

    def speech_to_text(self, audio_base64):

        text = groq_stt(audio_base64)

        if not text:
            print("⚠️ Switching to fallback STT...")
            text = fallback_stt(audio_base64)

        if self.debug:
            print("✅ FINAL STT:", text)

        return text


    def text_to_speech(self, text):

        audio = groq_tts(text)

        if not audio:
            print("⚠️ Switching to fallback TTS...")
            audio = fallback_tts(text)

        if self.debug:
            if audio:
                print("✅ FINAL TTS SUCCESS")
            else:
                print("❌ TTS FAILED")

        return audio


# =========================
# INSTANCE
# =========================
speech_handler = SpeechHandler()




# import os
# import base64
# import io
# import wave
# import requests
# from pydub import AudioSegment


# # =========================
# # CONFIG
# # =========================
# BHASHINI_URL = "https://anuvaad-backend.bhashini.co.in/v1/pipeline"


# def get_headers():
#     return {
#         "Authorization": f"Bearer {os.getenv('BHASHINI_URL')}",
#         "Content-Type": "application/json"
#     }


# # =========================
# # LANGUAGE MAP
# # =========================
# INDIC2_TO_BHASHINI = {
#     "eng_Latn": ("en", "Latn"),
#     "hin_Deva": ("hi", "Deva"),
#     "mar_Deva": ("mr", "Deva"),
#     "ben_Beng": ("bn", "Beng"),
#     "tam_Taml": ("ta", "Taml"),
#     "tel_Telu": ("te", "Telu"),
#     "guj_Gujr": ("gu", "Gujr"),
#     "kan_Knda": ("kn", "Knda"),
#     "mal_Mlym": ("ml", "Mlym"),
#     "pan_Guru": ("pa", "Guru"),
#     "urd_Arab": ("ur", "Arab"),
#     "ory_Orya": ("or", "Orya"),
#     "asm_Beng": ("as", "Beng"),
#     "npi_Deva": ("ne", "Deva"),
#     "san_Deva": ("sa", "Deva"),
#     "sat_Olck": ("sat", "Olck"),
#     "snd_Arab": ("sd", "Arab")
# }


# # =========================
# # TRANSLATION
# # =========================
# def bhashini_translate(text, src_lang, tgt_lang):

#     if not text.strip():
#         return ""

#     try:
#         src, src_script = INDIC2_TO_BHASHINI[src_lang]
#         tgt, tgt_script = INDIC2_TO_BHASHINI[tgt_lang]
#     except KeyError:
#         # print("❌ Language mapping error")
#         return ""

#     payload = {
#         "pipelineTasks": [
#             {
#                 "taskType": "translation",
#                 "config": {
#                     "language": {
#                         "sourceLanguage": src,
#                         "targetLanguage": tgt,
#                         "sourceScriptCode": src_script,
#                         "targetScriptCode": tgt_script
#                     },
#                     "serviceId": "ai4bharat/indictrans-v2-all-gpu--t4"
#                 }
#             }
#         ],
#         "inputData": {
#             "input": [{"source": text}]
#         }
#     }

#     r = requests.post(BHASHINI_URL, json=payload, headers=get_headers())

#     data = r.json()
#     # print("TRANSLATE RESPONSE:", data)

#     return (
#         data.get("pipelineResponse", [{}])[0]
#         .get("output", [{}])[0]
#         .get("target", "")
#     )


# def ensure_16k_wav_bytes(b64):

#     # print("\n--- AUDIO CONVERSION START ---")

#     audio_bytes = base64.b64decode(b64)
#     # print("Decoded audio size:", len(audio_bytes))

#     audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
#     # print("Original frame rate:", audio.frame_rate)

#     audio = (
#         audio
#         .set_frame_rate(16000)
#         .set_channels(1)
#         .set_sample_width(2)
#     )

#     buf = io.BytesIO()

#     audio.export(
#         buf,
#         format="wav",
#         codec="pcm_s16le"
#     )

#     wav_data = buf.getvalue()

#     # print("Converted WAV size:", len(wav_data))
#     # print("--- AUDIO CONVERSION END ---\n")

#     return wav_data


# # =========================
# # SPEECH TO TEXT (ASR)
# # =========================
# def bhashini_asr(audio_base64, src_lang="eng_Latn"):

#     # print("\n================= ASR START =================")

#     # =========================
#     # STEP 1: CLEAN BASE64
#     # =========================
#     if "," in audio_base64:
#         # print("Cleaning base64 header...")
#         audio_base64 = audio_base64.split(",")[1]

#     # print("Base64 length:", len(audio_base64))

#     # =========================
#     # STEP 2: CONVERT AUDIO → 16k WAV
#     # =========================
#     try:
#         # print("Converting to 16k WAV...")
#         wav_bytes = ensure_16k_wav_bytes(audio_base64)
#         # print("WAV size:", len(wav_bytes))
#     except Exception as e:
#         # print("❌ AUDIO CONVERSION FAILED:", str(e))
#         return ""

#     # =========================
#     # STEP 3: ENCODE AGAIN
#     # =========================
#     audio_b64 = base64.b64encode(wav_bytes).decode()
#     # print("Encoded WAV length:", len(audio_b64))

#     # =========================
#     # STEP 4: LANGUAGE FIX (CRITICAL)
#     # =========================
#     lang = INDIC2_TO_BHASHINI.get(src_lang, ("en", "Latn"))[0]

#     # print("Input src_lang:", src_lang)
#     # print("Converted ASR lang:", lang)
#     # print("Type check:", type(lang))   # must be str

#     # =========================
#     # STEP 5: PAYLOAD
#     # =========================
#     payload = {
#         "pipelineTasks": [
#             {
#                 "taskType": "asr",
#                 "config": {
#                     "language": {
#                         "sourceLanguage": lang   # MUST be "en", "hi"
#                     },
#                     # 🔥 IMPORTANT CHANGE
#                     "serviceId": "ai4bharat/whisper-medium-en--gpu--t4",  
#                     "audioFormat": "wav",
#                     "samplingRate": 16000,
#                     "preProcessors": ["vad", "denoiser"]
#                 }
#             }
#         ],
#         "inputData": {
#             "input": [{"source": ""}],
#             "audio": [{"audioContent": audio_b64}]
#         }
#     }

#     # print("Payload prepared")

#     # =========================
#     # STEP 6: API CALL
#     # =========================
#     try:
#         # print("Sending request to Bhashini...")

#         r = requests.post(
#             BHASHINI_URL,
#             json=payload,
#             headers=get_headers()
#         )

#         # print("Status Code:", r.status_code)
#         # print("Raw Response:", r.text[:500])

#     except Exception as e:
#         # print("❌ REQUEST FAILED:", str(e))
#         return ""

#     # =========================
#     # STEP 7: PARSE RESPONSE
#     # =========================
#     try:
#         data = r.json()
#     except Exception as e:
#         # print("❌ JSON PARSE ERROR:", str(e))
#         return ""

#     print("Parsed JSON:", data)

#     # =========================
#     # STEP 8: HANDLE ERROR RESPONSE
#     # =========================
#     if r.status_code != 200:
#         # print("❌ API ERROR:", data)
#         return ""

#     # =========================
#     # STEP 9: SAFE EXTRACTION
#     # =========================
#     result = (
#         data.get("pipelineResponse", [{}])[0]
#         .get("output", [{}])[0]
#         .get("source", "")
#     )

#     if not result:
#         print("❌ Empty transcription returned")

#     # print("Final Transcribed Text:", result)
#     # print("================= ASR END =================\n")

#     return result


# # =========================
# # TEXT TO SPEECH (TTS)
# # =========================
# def bhashini_tts(text, lang="eng_Latn", gender="female"):

#     print("\n================= TTS START =================")

#     # STEP 1: VALIDATE TEXT
#     if not text.strip():
#         # print("❌ Empty text")
#         return None

#     # print("Input text:", text[:100])
#     # print("Language:", lang)
#     # print("Gender:", gender)

#     # STEP 2: LANGUAGE MAPPING
#     try:
#         code, script = INDIC2_TO_BHASHINI[lang]
#     except KeyError:
#         # print("❌ Invalid language:", lang)
#         return None

#     print("Mapped language:", code, script)

#     # STEP 3: PAYLOAD
#     payload = {
#         "pipelineTasks": [
#             {
#                 "taskType": "tts",
#                 "config": {
#                     "language": {
#                         "sourceLanguage": code,
#                         "sourceScriptCode": script
#                     },
#                     "serviceId": "Bhashini/IITM/TTS",
#                     "gender": gender,
#                     "audioFormat": "wav",
#                     "samplingRate": 16000
#                 }
#             }
#         ],
#         "inputData": {
#             "input": [{"source": text}],
#             "audio": [{"audioContent": None}]
#         }
#     }

#     # print("Payload prepared")

#     # STEP 4: API CALL (NO HEADERS)
#     try:
#         # print("Sending request to Bhashini...")

#         r = requests.post(
#             BHASHINI_URL,
#             json=payload,
#             headers=get_headers()
#         )

#         # print("Status Code:", r.status_code)
#         # print("Raw Response:", r.text[:500])

#     except Exception as e:
#         # print("❌ REQUEST FAILED:", str(e))
#         return None

#     # STEP 5: PARSE JSON
#     try:
#         data = r.json()
#     except Exception as e:
#         # print("❌ JSON PARSE ERROR:", str(e))
#         return None

#     print("Parsed JSON:", data)

#     # STEP 6: HANDLE FAILURE
#     if r.status_code != 200:
#         # print("❌ API ERROR:", data)
#         return None

#     # STEP 7: EXTRACT AUDIO SAFELY
#     audio_b64 = (
#         data.get("pipelineResponse", [{}])[0]
#         .get("audio", [{}])[0]
#         .get("audioContent", None)
#     )

#     if not audio_b64:
#         # print("❌ No audio found in response")
#         return None

#     # print("✅ Audio generated successfully")
#     # print("Audio length:", len(audio_b64))

#     # print("================= TTS END =================\n")

#     return audio_b64

# # =========================
# # HANDLER CLASS
# # =========================
# class BhashiniHandler:

#     def __init__(self, debug=True):
#         self.debug = debug

#     # =========================
#     # TRANSLATION
#     # =========================
#     def translate(self, text, src, tgt):

#         if not text or not text.strip():
#             if self.debug:

#                 return ""

#         try:
#             result = bhashini_translate(text, src, tgt)

#             if self.debug:
#                 return result or ""

#         except Exception as e:
#             if self.debug:
#                 return ""

#     # =========================
#     # SPEECH TO TEXT
#     # =========================
#     def speech_to_text(self, audio, lang):

#         if not audio:
#             if self.debug:
                
#                 return ""

#         try:
#             result = bhashini_asr(audio, lang)

#             if self.debug:
                

#                 return result or ""

#         except Exception as e:
#             if self.debug:
                
#                 return ""

#     # =========================
#     # TEXT TO SPEECH
#     # =========================
#     def text_to_speech(self, text, lang, gender="female"):

#         if not text or not text.strip():
#             if self.debug:
                
#                 return None

#         try:
#             audio = bhashini_tts(text, lang, gender)

#             if not audio:
#                 if self.debug:
                    
#                     return None

#             if self.debug:
                

#                 return audio

#         except Exception as e:
#             if self.debug:
                
#                 return None