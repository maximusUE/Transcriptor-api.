from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

app = FastAPI(title="Logisk YouTube Transcriber")

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor Activo. Usa /transcript?video_id=ID"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        # Obtenemos la transcripción disponible (intenta varios idiomas)
        data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, 'es', 'en', 'pt', 'fr', 'de'])
        
        formatter = TextFormatter()
        text_formatted = formatter.format_transcript(data)

        return {
            "success": True,
            "video_id": video_id,
            "language_final": lang,
            "transcript_text": text_formatted.replace('\n', ' '),
            "raw_data": data 
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


