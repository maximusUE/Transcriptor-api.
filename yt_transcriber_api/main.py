import subprocess
import json
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Logisk YouTube Transcriber")

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor VIP Activo."}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        # BYPASS: En vez de un Import que hace conflicto, le tiramos el comando directo al sistema linux de tu servidor
        comando = ["youtube_transcript_api", video_id, "--languages", lang, "es", "en", "pt", "de", "fr", "--format", "json"]
        
        result = subprocess.run(comando, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception("Error interno CLI: " + result.stderr.strip())
            
        # Leemos el resultado crudo en JSON
        data = json.loads(result.stdout)
        
        # Pegamos todo el texto 
        transcript_text = " ".join([item.get('text', '') for item in data])
        
        return {
            "success": True,
            "video_id": video_id,
            "language_final": lang,
            "transcript_text": transcript_text.replace('\n', ' ')
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



