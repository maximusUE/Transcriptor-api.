from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

app = FastAPI(title="Logisk YT Transcriber API")

@app.get("/")
def read_root():
    return {"message": "Transcriptor v9 - Maneja videos sin subtítulos"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        # Intentar obtener transcripción directamente (método más simple)
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
        
        # Formatear texto plano
        formatter = TextFormatter()
        text_content = formatter.format_transcript(transcript_data)
        
        return {
            "success": True,
            "video_id": video_id,
            "has_subtitles": True,
            "text": text_content
        }
        
    except Exception as e:
        # Si falla por "TranscriptsDisabled" u otros errores comunes
        if "TranscriptsDisabled" in str(e) or "no subtitles" in str(e).lower():
            return {
                "success": False,
                "video_id": video_id,
                "has_subtitles": False,
                "error": "Este video no tiene subtítulos disponibles",
                "text": "",  # Campo vacío para que n8n pueda continuar
                "skip_reason": "No subtitles"
            }
        else:
            # Otros errores (video privado, etc.)
            raise HTTPException(status_code=400, detail=str(e))
