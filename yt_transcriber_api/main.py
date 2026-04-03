from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import subprocess
import tempfile
import os
import re

app = FastAPI(title="Logisk YouTube Transcriber")

PREFERRED_LANGS = ["es", "es-MX", "es-ES", "es-419", "en", "en-US", "pt", "pt-BR", "fr", "de"]

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor Activo. Usa /transcript?video_id=ID"}

def parse_vtt(content: str) -> list:
    items = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '-->' in line:
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip():
                text_line = re.sub(r'<[^>]+>', '', lines[i].strip())
                if text_line:
                    text_lines.append(text_line)
                i += 1
            if text_lines:
                items.append({"text": " ".join(text_lines), "start": 0, "duration": 0})
        else:
            i += 1
    return items

def get_transcript_ytdlp(video_id: str) -> list:
    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory() as tmpdir:
        for lang_set in ["es,es-419,es-MX,es-ES", "en,en-US", ".*"]:
            cmd = [
                "yt-dlp", "--skip-download",
                "--write-subs", "--write-auto-subs",
                "--sub-langs", lang_set,
                "--convert-subs", "vtt",
                "--output", f"{tmpdir}/sub.%(ext)s",
                "--no-warnings", "--quiet", url
            ]
            try:
                subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                for fname in os.listdir(tmpdir):
                    if fname.endswith('.vtt'):
                        with open(os.path.join(tmpdir, fname), 'r', encoding='utf-8') as f:
                            content = f.read()
                        items = parse_vtt(content)
                        if items:
                            return items
            except Exception:
                continue
    return []

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    method_used = "youtube-transcript-api"
    raw_data = []
    found_lang = None

    # Método 1: youtube-transcript-api
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcript = None

        for preferred in PREFERRED_LANGS:
            try:
                transcript = transcript_list.find_manually_created_transcript([preferred])
                found_lang = preferred + " (manual)"
                break
            except Exception:
                continue

        if transcript is None:
            for preferred in PREFERRED_LANGS:
                try:
                    transcript = transcript_list.find_generated_transcript([preferred])
                    found_lang = preferred + " (auto-generated)"
                    break
                except Exception:
                    continue

        if transcript is None:
            all_transcripts = list(transcript_list)
            if all_transcripts:
                transcript = all_transcripts[0]
                found_lang = transcript.language_code + " (first available)"

        if transcript:
            if transcript.language_code not in ["es", "es-MX", "es-ES", "es-419"]:
                try:
                    transcript = transcript.translate("es")
                    found_lang = str(found_lang) + " → traducido a es"
                except Exception:
                    pass

            fetched = transcript.fetch()
            for item in fetched:
                if hasattr(item, 'text'):
                    raw_data.append({"text": item.text, "start": item.start, "duration": item.duration})
                else:
                    raw_data.append(item)

    except Exception:
        raw_data = []

    # Método 2: yt-dlp como respaldo
    if not raw_data:
        method_used = "yt-dlp"
        found_lang = "auto (yt-dlp)"
        raw_data = get_transcript_ytdlp(video_id)

    if not raw_data:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudo obtener transcripción para '{video_id}'. El video no tiene subtítulos accesibles."
        )

    full_text = " ".join([d["text"] for d in raw_data if d.get("text")])

    return {
        "success": True,
        "video_id": video_id,
        "language_found": found_lang,
        "method": method_used,
        "transcript_text": full_text,
        "raw_data": raw_data
    }
