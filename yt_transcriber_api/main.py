import json
import html
import requests
import xml.etree.ElementTree as ET
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Logisk YT Transcriber")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

@app.get("/")
def read_root():
    return {"message": "Transcriptor v8 activo"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        # Usar sesion para mantener las cookies de YouTube entre requests
        session = requests.Session()
        session.headers.update(HEADERS)

        r = session.get(
            f"https://www.youtube.com/watch?v={video_id}",
            timeout=15
        )

        idx = r.text.find('"captionTracks":')
        if idx == -1:
            raise Exception("Este video no tiene subtitulos disponibles")

        arr_start = r.text.index('[', idx)

        try:
            tracks, _ = json.JSONDecoder().raw_decode(r.text, arr_start)
        except json.JSONDecodeError:
            raise Exception("Error al procesar los subtitulos")

        track_url = None
        for lang_try in [lang, "es", "en", "pt", "de"]:
            for track in tracks:
                if track.get("languageCode", "").startswith(lang_try):
                    track_url = track["baseUrl"]
                    break
            if track_url:
                break

        if not track_url and tracks:
            track_url = tracks[0]["baseUrl"]

        if not track_url:
            raise Exception("No se encontro URL de subtitulos")

        if not track_url.startswith("http"):
            track_url = "https://www.youtube.com" + track_url

        # La sesion reutiliza las cookies de la carga inicial
        tr = session.get(track_url, timeout=15)

        if not tr.text:
            raise Exception("Respuesta vacia - video sin acceso publico a subtitulos")

        root = ET.fromstring(tr.content)
        parts = []
        for text_elem in root.iter("text"):
            t = html.unescape(text_elem.text or "").strip()
            if t:
                parts.append(t)

        if not parts:
            raise Exception("Transcript vacio para este video")

        return {
            "success": True,
            "video_id": video_id,
            "transcript_text": " ".join(parts)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
