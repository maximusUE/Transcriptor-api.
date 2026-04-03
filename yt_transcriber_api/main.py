from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

app = FastAPI(title="Logisk YT Transcriber API")

@app.get("/")
def read_root():
    return {"message": "Transcriptor v8 activo y listo para traducir"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    try:
        # 1. Obtener la lista de transcripciones disponibles para el video
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 2. Iterar para encontrar cualquier transcripción disponible (manual o generada)
        transcript = None
        for t in transcript_list:
            transcript = t
            break # Nos quedamos con la primera que encuentre
            
        if not transcript:
            raise HTTPException(status_code=404, detail="No se encontraron subtítulos para este video.")

        # 3. Si el idioma original no es español, lo traducimos al vuelo
        if transcript.language_code != lang:
            if transcript.is_translatable:
                transcript = transcript.translate(lang)
            else:
                raise HTTPException(status_code=400, detail="El video tiene subtítulos pero no permite traducción automática.")

        # 4. Extraer el diccionario de datos
        transcript_data = transcript.fetch()
        
        # 5. Formatear a texto plano (ideal para pasar a Claude o GPT después en n8n)
        formatter = TextFormatter()
        text_content = formatter.format_transcript(transcript_data)
        
        return {
            "success": True,
            "video_id": video_id,
            "language": lang,
            "is_translated": transcript.language_code != lang,
            "text": text_content,
            "raw_data": transcript_data # También enviamos el RAW con los timestamps por si los necesitas para shorts
        }

    except Exception as e:
        # Captura cualquier error de youtube_transcript_api (ej. subtítulos desactivados)
        raise HTTPException(status_code=400, detail=str(e))
