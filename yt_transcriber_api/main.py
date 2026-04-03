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
        # Intentamos obtener la lista de transcripciones (usando el método correcto de la instancia)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Le decimos que prefiera español, y si no, que busque en inglés u otros idiomas
        transcript = transcript_list.find_transcript(['es', 'en'])
        
        # Si la transcripción que encontró no está en español, la traducimos
        if transcript.language_code != lang:
            if transcript.is_translatable:
                transcript = transcript.translate(lang)
            else:
                raise HTTPException(status_code=400, detail="El video tiene subtítulos pero no se pueden traducir.")
                
        # Obtenemos los datos ya traducidos
        transcript_data = transcript.fetch()
        
        # Formateamos a texto plano
        formatter = TextFormatter()
        text_content = formatter.format_transcript(transcript_data)
        
        return {
            "success": True,
            "video_id": video_id,
            "language": lang,
            "is_translated": transcript.language_code != lang,
            "text": text_content
        }

    except Exception as e:
        # Si falla el método de lista, usamos el método directo de fallback
        try:
            # Fallback: intenta obtener cualquier idioma directamente
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
            
            # Formateamos a texto plano (nota: el fallback no traduce automáticamente si está en inglés)
            formatter = TextFormatter()
            text_content = formatter.format_transcript(transcript_data)
            
            return {
                "success": True,
                "video_id": video_id,
                "text": text_content,
                "note": "Usado método fallback directo"
            }
        except Exception as fallback_error:
            raise HTTPException(status_code=400, detail=f"Error principal: {str(e)} | Error fallback: {str(fallback_error)}")
