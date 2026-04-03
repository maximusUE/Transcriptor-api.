from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.formatters import TextFormatter

app = FastAPI(title="Logisk YouTube Transcriber")

PREFERRED_LANGS = ["es", "es-MX", "es-ES", "es-419", "en", "en-US", "pt", "pt-BR", "fr", "de"]

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor Activo. Usa /transcript?video_id=ID"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        transcript = None
        found_lang = None

        # 1. Buscar transcripción MANUAL primero
        for preferred in PREFERRED_LANGS:
            try:
                transcript = transcript_list.find_manually_created_transcript([preferred])
                found_lang = preferred + " (manual)"
                break
            except Exception:
                continue

        # 2. Si no hay manual, buscar AUTO-GENERADA
        if transcript is None:
            for preferred in PREFERRED_LANGS:
                try:
                    transcript = transcript_list.find_generated_transcript([preferred])
                    found_lang = preferred + " (auto-generated)"
                    break
                except Exception:
                    continue

        # 3. Si no hay nada, tomar CUALQUIER disponible
        if transcript is None:
            all_transcripts = list(transcript_list)
            if all_transcripts:
                transcript = all_transcripts[0]
                found_lang = transcript.language_code + " (first available)"

        if transcript is None:
            raise HTTPException(
                status_code=404,
                detail=f"No hay transcripciones disponibles para el video '{video_id}'."
            )

        # Traducir al español si no está en español
        if transcript.language_code not in ["es", "es-MX", "es-ES", "es-419"]:
            try:
                transcript = transcript.translate("es")
                found_lang = found_lang + " → traducido a es"
            except Exception:
                pass

        fetched = transcript.fetch()

        # Compatibilidad con distintas versiones
        raw_data = []
        for item in fetched:
            if hasattr(item, 'text'):
                raw_data.append({"text": item.text, "start": item.start, "duration": item.duration})
            else:
                raw_data.append(item)

        full_text = " ".join([d["text"] for d in raw_data if d.get("text")])

        return {
            "success": True,
            "video_id": video_id,
            "language_found": found_lang,
            "transcript_text": full_text,
            "raw_data": raw_data
        }

    except HTTPException:
        raise
    except TranscriptsDisabled:
        raise HTTPException(status_code=403, detail=f"Transcripciones deshabilitadas para '{video_id}'.")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail=f"No se encontró transcripción para '{video_id}'.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
