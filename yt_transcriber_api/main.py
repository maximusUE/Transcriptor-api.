from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

app = FastAPI(title="Logisk YouTube Transcriber", description="Extrae transcripciones de videos en milisegundos")

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor Activo en Easypanel. Usa el endpoint /transcript?video_id=ID_DEL_VIDEO"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    """
    Obtiene la transcripción de un video de YouTube.
    Si el video está originamente en otro idioma, intenta traducirlo al idioma solicitado (por defecto: español 'es').
    """
    try:
        # Obtenemos la lista de todas las transcripciones disponibles para este video
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Tratamos de buscar la transcripción en español o el idioma original
        try:
            # Primero intentamos sacar directamente los subtítulos manuales o generados
            video_transcript = transcript_list.find_transcript([lang, 'en', 'pt', 'fr', 'de'])
            
            # Si el idioma que encontró no es el español (lang="es"), le pedimos a YouTube que lo traduzca
            if video_transcript.language_code != lang and video_transcript.is_translatable:
                video_transcript = video_transcript.translate(lang)
                
            # Extraemos la data final (diccionarios con texto y tiempo)
            data = video_transcript.fetch()
            
        except Exception:
            # Si falla la búsqueda, tomamos CUALQUIERA de las disponibles (fallback) y la traducimos
            video_transcript = next(iter(transcript_list))
            if video_transcript.language_code != lang and video_transcript.is_translatable:
                video_transcript = video_transcript.translate(lang)
            
            data = video_transcript.fetch()

        # Usamos el formateador para tener un texto limpio (como un guion)
        formatter = TextFormatter()
        text_formatted = formatter.format_transcript(data)

        # Regresamos la respuesta elegante
        return {
            "success": True,
            "video_id": video_id,
            "language_final": lang,
            "transcript_text": text_formatted.replace('\n', ' '), # Quitamos saltos de línea molestos
            "raw_data": data # Por si en el futuro queremos saber los tiempos (timestamps)
        }

    except Exception as e:
        # Si de verdad no tiene ningún tipo de subtítulo o el video no existe
        raise HTTPException(status_code=400, detail=str(e))
