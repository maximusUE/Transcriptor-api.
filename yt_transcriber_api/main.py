from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
import subprocess, tempfile, os, json
from openai import OpenAI

app = FastAPI(title="Logisk YouTube Transcriber")

PREFERRED_LANGS = ["es", "es-MX", "es-ES", "es-419", "en", "en-US", "pt", "pt-BR", "fr", "de"]

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor Activo. Usa /transcript?video_id=ID"}

def get_video_title(video_id: str) -> str:
    """Obtiene el título del video con yt-dlp"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", "--quiet",
             f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout).get("title", f"Video {video_id}")
    except Exception:
        pass
    return f"Video {video_id}"

def transcribe_with_whisper(video_id: str) -> str:
    """Descarga audio y transcribe con OpenAI Whisper"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY no configurada en Easypanel")

    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.%(ext)s")
        result = subprocess.run([
            "yt-dlp", "-x",
            "--audio-format", "mp3",
            "--audio-quality", "5",
            "--max-filesize", "24m",
            "--output", audio_path,
            "--no-playlist", "--quiet", url
        ], capture_output=True, text=True, timeout=180)

        # Buscar el archivo de audio descargado
        audio_file = None
        for fname in os.listdir(tmpdir):
            if fname.endswith(('.mp3', '.m4a', '.opus', '.webm', '.ogg')):
                audio_file = os.path.join(tmpdir, fname)
                break

        if not audio_file:
            raise Exception(f"No se pudo descargar el audio. Error: {result.stderr[:200]}")

        client = OpenAI(api_key=api_key)
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="es",
                prompt="Contenido bíblico y cristiano en español"
            )

        return transcript.text

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    full_text = ""
    found_lang = None
    method_used = "youtube-transcript-api"
    raw_data = []

    # Obtenemos el título siempre
    video_title = get_video_title(video_id)

    # Método 1: youtube-transcript-api (rápido y gratis)
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
            all_t = list(transcript_list)
            if all_t:
                transcript = all_t[0]
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
            full_text = " ".join([d["text"] for d in raw_data if d.get("text")])

    except Exception:
        full_text = ""

    # Método 2: yt-dlp + OpenAI Whisper (si método 1 falla)
    if not full_text:
        try:
            method_used = "whisper"
            found_lang = "es (OpenAI Whisper)"
            full_text = transcribe_with_whisper(video_id)
            raw_data = [{"text": full_text, "start": 0, "duration": 0}]
        except Exception as e:
            raise HTTPException(status_code=404,
                detail=f"No se pudo transcribir '{video_id}': {str(e)}")

    if not full_text:
        raise HTTPException(status_code=404,
            detail=f"No se encontró transcripción para '{video_id}'.")

    return {
        "success": True,
        "video_id": video_id,
        "title": video_title,           # ← $json.title en tu n8n
        "transcriptionAsText": full_text, # ← $json.transcriptionAsText en tu n8n
        "transcript_text": full_text,
        "language_found": found_lang,
        "method": method_used,
        "raw_data": raw_data
    }
