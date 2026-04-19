import os
import requests

PIPELINE_URL = "https://anuvaad-backend.bhashini.co.in/v1/pipeline"

TRANSLATION_SERVICE = "ai4bharat/indictrans-v2-all-gpu--t4"
TTS_SERVICE_INDIC = "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4"
TTS_SERVICE_EN = "Bhashini/IITM/TTS"

# ✅ FULL LANGUAGE MAP (CDAC FORMAT)
LANGUAGE_MAP = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "mr": "mar_Deva",
    "bn": "ben_Beng",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "gu": "guj_Gujr",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "pa": "pan_Guru",
    "ur": "urd_Arab"
}

SCRIPT_MAP = {
    "eng_Latn": "Latn",
    "hin_Deva": "Deva",
    "mar_Deva": "Deva",
    "ben_Beng": "Beng",
    "tam_Taml": "Taml",
    "tel_Telu": "Telu",
    "guj_Gujr": "Gujr",
    "kan_Knda": "Knda",
    "mal_Mlym": "Mlym",
    "pan_Guru": "Guru",
    "urd_Arab": "Arab"
}


class BhashiniHandler:

    def __init__(self):
        self.api_key = os.getenv("BHASHINI_API_KEY", "")
        print("API KEY:", self.api_key)

    def _headers(self):
        return {
            "Authorization": self.api_key,  # ✅ FIXED
            "Content-Type": "application/json",
        }

    def is_ready(self):
        return bool(self.api_key)

    # ───────── TRANSLATION ─────────
    def translate(self, text, source_lang, target_lang):

        if not self.is_ready():
            print("❌ API Key missing")
            return text

        src = LANGUAGE_MAP.get(source_lang)
        tgt = LANGUAGE_MAP.get(target_lang)

        if not src or not tgt or src == tgt:
            return text

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": src,
                            "targetLanguage": tgt,
                            "sourceScriptCode": SCRIPT_MAP[src],
                            "targetScriptCode": SCRIPT_MAP[tgt],
                        },
                        "serviceId": TRANSLATION_SERVICE,
                    },
                }
            ],
            "inputData": {
                "input": [
                    {"source": text}
                ]
            }
        }

        try:
            resp = requests.post(
                PIPELINE_URL,
                json=payload,
                headers=self._headers(),
                timeout=30
            )
            resp.raise_for_status()

            data = resp.json()

            return (
                data.get("pipelineResponse", [{}])[0]
                .get("output", [{}])[0]
                .get("target", text)
            )

        except Exception as e:
            print("❌ Translation error:", e)
            return text

    # ───────── TEXT TO SPEECH ─────────
    def text_to_speech(self, text, lang, gender="female"):

        if not self.is_ready():
            print("❌ API Key missing")
            return None

        lang_code = LANGUAGE_MAP.get(lang)

        if not lang_code:
            print("❌ Invalid language")
            return None

        service_id = TTS_SERVICE_EN if lang == "en" else TTS_SERVICE_INDIC

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {
                            "sourceLanguage": lang_code,
                            "sourceScriptCode": SCRIPT_MAP[lang_code]
                        },
                        "serviceId": service_id,
                        "gender": gender
                    }
                }
            ],
            "inputData": {
                "input": [
                    {
                        "text": text[:250]  # ✅ FIXED
                    }
                ]
            }
        }

        try:
            resp = requests.post(
                PIPELINE_URL,
                json=payload,
                headers=self._headers(),
                timeout=40
            )
            resp.raise_for_status()

            data = resp.json()

            return (
                data.get("pipelineResponse", [{}])[0]
                .get("audio", [{}])[0]
                .get("audioContent")
            )

        except Exception as e:
            print("❌ TTS error:", e)
            return None


# class BhashiniHandler:
#     def __init__(self):
#         # ✅ API key comes ONLY from Streamlit Secrets / env — never from UI
#         self.api_key = os.getenv("BHASHINI_API_KEY", "")

#     @property
#     def _ready(self) -> bool:
#         return bool(self.api_key)

#     # ── Translation ───────────────────────────────────────────────────────────
#     def translate(
#         self,
#         text: str,
#         source_lang: str,
#         target_lang: str,
#         target_script: str,
#     ) -> str:
#         if not self._ready:
#             return "⚠️ Bhashini API key not configured in Streamlit Secrets."
#         if source_lang == target_lang:
#             return text

#         payload = {
#             "pipelineTasks": [{
#                 "taskType": "translation",
#                 "config": {
#                     "language": {
#                         "sourceLanguage":   source_lang,
#                         "targetLanguage":   target_lang,
#                         "sourceScriptCode": SCRIPT_MAP.get(source_lang, "Latn"),
#                         "targetScriptCode": target_script,
#                     },
#                     "postProcessors": ["glossary"],
#                     "serviceId": TRANSLATION_SERVICE,
#                 },
#             }],
#             "inputData": {
#                 "input": [{"source": text}],
#                 "audio": [{"audioContent": None}],
#             },
#         }

#         try:
#             resp = requests.post(
#                 PIPELINE_URL,
#                 json=payload,
#                 headers={
#                     "Authorization": self.api_key,
#                     "Content-Type":  "application/json",
#                 },
#                 timeout=30,
#             )
#             resp.raise_for_status()
#             return (
#                 resp.json()
#                     .get("pipelineResponse", [{}])[0]
#                     .get("output", [{}])[0]
#                     .get("target", "Translation not available")
#             )
#         except requests.exceptions.HTTPError as e:
#             return f"⚠️ Bhashini API error ({e.response.status_code}). Check BHASHINI_API_KEY."
#         except requests.exceptions.ConnectionError:
#             return "⚠️ Could not reach Bhashini API. Check internet connection."
#         except Exception as e:
#             return f"⚠️ Translation failed: {e}"

#     # ── Text-to-Speech ────────────────────────────────────────────────────────
#     def text_to_speech(
#         self,
#         text: str,
#         source_lang: str,
#         source_script: str,
#         gender: str,
#     ):

#         if not self._ready:
#             return None

#         # 🔥 STRICT SERVICE MAPPING
#         if source_lang == "en":
#             service_id = "Bhashini/IITM/TTS"
#         elif source_lang in ["hi", "mr"]:
#             service_id = "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4"
#         else:
#             print(f"⚠️ TTS not supported for {source_lang}")
#             return None

#         payload = {
#             "pipelineTasks": [
#                 {
#                     "taskType": "tts",
#                     "config": {
#                         "language": {
#                             "sourceLanguage": source_lang,
#                             "sourceScriptCode": source_script
#                         },
#                         "serviceId": service_id,
#                         "gender": gender,
#                         "preProcessors": [],
#                         "postProcessors": []
#                     }
#                 }
#             ],
#             "inputData": {
#                 "input": [
#                     {
#                         "source": text[:300]   # 🔥 keep it short
#                     }
#                 ],
#                 "audio": [
#                     {
#                         "audioContent": None   # 🔥 MUST BE PRESENT
#                     }
#                 ]
#             }
#         }

#         try:
#             resp = requests.post(
#                 PIPELINE_URL,
#                 json=payload,
#                 headers={
#                     "Authorization": self.api_key,
#                     "Content-Type": "application/json",
#                 },
#                 timeout=40,
#             )

#             resp.raise_for_status()
#             data = resp.json()

#             audio = (
#                 data.get("pipelineResponse", [{}])[0]
#                     .get("audio", [{}])[0]
#                     .get("audioContent")
#             )

#             if not audio:
#                 print("⚠️ No audio returned from API")
#                 return None

#             return audio

#         except Exception as e:
#             print(f"❌ TTS error: {e}")
#             return None
