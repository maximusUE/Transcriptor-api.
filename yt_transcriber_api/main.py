import re, json, html, requests
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Logisk YT Transcriber - Directo")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor Directo iPhone"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        r = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers=HEADERS, timeout=15)
        match = re.search(r'"captionTracks":(\[.*?\])', r.text)
        if not match:
            raise Exception("Este video no tiene subtítulos disponibles")
        
        tracks = json.loads(match.group(1))
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
            raise Exception("No se encontró URL de subtítulos")
        
        tr = requests.get(track_url + "&fmt=json3", headers=HEADERS, timeout=15)
        data = tr.json()
        
        parts = []
        for event in data.get("events", []):
            for seg in event.get("segs", []):
                t = seg.get("utf8", "").strip()
                if t and t != "\n":
                    parts.append(html.unescape(t))
        
        return {"success": True, "video_id": video_id, "transcript_text": " ".join(parts)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
