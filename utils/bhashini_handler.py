"""
Bhashini API Handler – FINAL PRODUCTION VERSION
Supports:
✔ Translation
✔ TTS (English + Indic)
✔ Automatic fallback if Bhashini fails
"""

import requests
import base64
from typing import Optional

PIPELINE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

TRANSLATION_SERVICE = "ai4bharat/indictrans-v2-all-gpu--t4"

SCRIPT_MAP = {
    "hi": "Deva", "mr": "Deva", "bn": "Beng", "ta": "Taml",
    "te": "Telu", "gu": "Gujr", "kn": "Knda", "ml": "Mlym",
    "pa": "Guru", "ur": "Arab", "en": "Latn"
}


class BhashiniHandler:

    # ───────────────────────────────────────────────
    # TRANSLATION
    # ───────────────────────────────────────────────
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        target_script: str,
        api_key: str,
    ) -> str:

        if not api_key:
            return "⚠️ API key missing"

        if source_lang == target_lang:
            return text

        payload = {
            "pipelineTasks": [{
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": source_lang,
                        "targetLanguage": target_lang,
                        "sourceScriptCode": SCRIPT_MAP.get(source_lang, "Latn"),
                        "targetScriptCode": target_script,
                    },
                    "serviceId": TRANSLATION_SERVICE,
                },
            }],
            "inputData": {
                "input": [{"source": text}],
            },
        }

        try:
            r = requests.post(
                PIPELINE_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            r.raise_for_status()

            return (
                r.json()
                .get("pipelineResponse", [{}])[0]
                .get("output", [{}])[0]
                .get("target", text)
            )

        except Exception as e:
            print("Translation error:", e)
            return text

    # ───────────────────────────────────────────────
    # TEXT TO SPEECH (SMART)
    # ───────────────────────────────────────────────
    def text_to_speech(
        self,
        text: str,
        source_lang: str,
        source_script: str,
        gender: str,
        api_key: str,
    ) -> Optional[str]:

        if not api_key:
            return None

        # Fix script
        source_script = SCRIPT_MAP.get(source_lang, "Latn")

        # 🔥 TRY BHASHINI FIRST (ENGLISH + INDIC)
        payload = {
            "pipelineTasks": [{
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": source_lang,
                        "sourceScriptCode": source_script,
                    },
                    # 👇 Try English service first
                    "serviceId": "Bhashini/IITM/TTS" if source_lang == "en"
                                 else "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4",
                    "gender": gender,
                },
            }],
            "inputData": {
                "input": [{"source": text[:500]}],
                "audio": [{"audioContent": None}]
            },
        }

        try:
            r = requests.post(
                PIPELINE_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=40,
            )

            r.raise_for_status()
            data = r.json()

            print("🔍 TTS RESPONSE:", data)

            audio = (
                data.get("pipelineResponse", [{}])[0]
                .get("audio", [{}])[0]
                .get("audioContent", None)
            )

            # ✅ SUCCESS
            if audio:
                return audio

            # ❌ FALLBACK (only if needed)
            print("⚠️ Bhashini failed → fallback to gTTS")

            return self._fallback_tts(text, source_lang)

        except Exception as e:
            print("TTS error:", e)
            return self._fallback_tts(text, source_lang)

    # ───────────────────────────────────────────────
    # FALLBACK TTS (gTTS)
    # ───────────────────────────────────────────────
    def _fallback_tts(self, text: str, lang: str) -> Optional[str]:
        try:
            from gtts import gTTS
            import io

            tts = gTTS(text=text, lang=lang if lang != "ur" else "hi")

            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)

            return base64.b64encode(audio_bytes.read()).decode("utf-8")

        except Exception as e:
            print("Fallback TTS failed:", e)
            return None