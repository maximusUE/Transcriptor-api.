from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI(title="Logisk YouTube Transcriber")

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor v2 (API nueva + Cookies 🍪)"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        # Nueva API v0.6+: se instancia la clase con las cookies
        ytt_api = YouTubeTranscriptApi(cookies="cookies.txt")
        
        # Obtener transcripción con idiomas preferidos
        fetched = ytt_api.fetch(video_id, languages=[lang, "es", "en", "pt", "de"])
        
        # Unir todos los textos en uno solo
        transcript_text = " ".join([item.text for item in fetched])
        
        return {
            "success": True,
            "video_id": video_id,
            "transcript_text": transcript_text.replace('\n', ' ')
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
