import subprocess
import json
import traceback
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Logisk YouTube Transcriber")

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor Tracker Activo."}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    debug_info = {"video_id": video_id}
    try:
        # Aquí ejecuta el comando
        comando = ["youtube_transcript_api", video_id, "--languages", lang, "es", "en", "pt", "de", "--format", "json"]
        debug_info["comando"] = comando
        
        result = subprocess.run(comando, capture_output=True, text=True)
        
        # Guardamos la evidencia de absolutamente todo lo que pasó en el servidor
        debug_info["returncode"] = result.returncode
        debug_info["stdout"] = result.stdout
        debug_info["stderr"] = result.stderr
        
        if result.returncode != 0:
            raise Exception("La consola arrojó un error (return code != 0)")
            
        if not result.stdout.strip():
            raise Exception("La consola devolvió un texto completamente en blanco.")
            
        data = json.loads(result.stdout)
        
        # Adaptación porque a veces el CLI devuelve un arreglo dentro de otro arreglo
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            data = data[0]
            
        # Armamos el texto gigante
        transcript_text = " ".join([item.get('text', '') for item in data if 'text' in item])
        
        return {
            "success": True,
            "video_id": video_id,
            "language_final": lang,
            "transcript_text": transcript_text.replace('\n', ' '),
            "debug": debug_info
        }

    except Exception as e:
        # ¡AQUÍ ESTÁ LA MAGIA! Si falla, mandamos TODA la evidencia en la respuesta del error
        error_msg = str(e)
        raise HTTPException(status_code=400, detail={
            "error_maestro": error_msg,
            "evidencia_forense": debug_info
        })
