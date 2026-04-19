import base64
import io
from pydub import AudioSegment

# Split long text
def split_text_for_tts(text, max_chars=180):
    sentences = text.replace("\n", " ").split(".")
    chunks = []
    current = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue

        if len(current) + len(s) < max_chars:
            current += s + ". "
        else:
            chunks.append(current.strip())
            current = s + ". "

    if current:
        chunks.append(current.strip())

    return chunks


# Merge audio smoothly
def generate_smooth_audio(bhashini, text, lang, gender):
    chunks = split_text_for_tts(text)

    combined_audio = AudioSegment.empty()

    for chunk in chunks:
        audio_b64 = bhashini.text_to_speech(chunk, lang, gender)

        if not audio_b64:
            continue

        audio_bytes = base64.b64decode(audio_b64)

        try:
            segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
            combined_audio += segment
            combined_audio += AudioSegment.silent(duration=200)
        except:
            continue

    if len(combined_audio) == 0:
        return None

    output = io.BytesIO()
    combined_audio.export(output, format="wav")
    output.seek(0)

    return output