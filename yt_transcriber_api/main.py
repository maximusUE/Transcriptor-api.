from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

app = FastAPI(title="Logisk YouTube Transcriber")

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor Activo (Python + Cookies 🍪)"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        # Modo Python directo con cookies para pasar el bloqueo de IP
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=[lang, "es", "en", "pt", "de"],
            cookies="cookies.txt"
        )
        
        transcript_text = " ".join([item['text'] for item in transcript_list])
        
        return {
            "success": True,
            "video_id": video_id,
            "transcript_text": transcript_text.replace('\n', ' ')
        }

    except NoTranscriptFound:
        raise HTTPException(status_code=400, detail=f"No hay transcripción para el video {video_id}")
    except TranscriptsDisabled:
        raise HTTPException(status_code=400, detail=f"Las transcripciones están deshabilitadas para {video_id}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

