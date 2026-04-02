from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI(title="Logisk YouTube Transcriber")

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor v0.5 (Cookies activas 🍪)"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
