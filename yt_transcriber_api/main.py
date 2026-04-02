import subprocess, re, glob, os, tempfile
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Logisk YT Transcriber - yt-dlp")

@app.get("/")
def read_root():
    return {"message": "✅ Transcriptor con yt-dlp activo"}

@app.get("/transcript")
def get_transcript(video_id: str, lang: str = "es"):
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            result = subprocess.run([
                "yt-dlp",
                "--skip-download",
                "--write-auto-sub",
                "--sub-langs", f"{lang},es,en",
                "--sub-format", "vtt",
                "--cookies", "cookies.txt",
                "--"--js-runtimes", "node:/usr/local/bin/node",
                "-o", f"{tmpdir}/sub",
                url
            ], capture_output=True, text=True, timeout=60)

            vtt_files = glob.glob(f"{tmpdir}/*.vtt")
            if not vtt_files:
                raise Exception(f"Sin subtítulos. Error: {result.stderr[:400]}")

            with open(vtt_files[0], 'r', encoding='utf-8') as f:
                content = f.read()

            lines = []
            for line in content.split('\n'):
                line = line.strip()
                if line and '-->' not in line and not line.startswith('WEBVTT') and not re.match(r'^\d+$', line):
                    clean = re.sub(r'<[^>]+>', '', line)
                    if clean:
                        lines.append(clean)

            text = ' '.join(lines)
            text = re.sub(r'(.{20,}?)\1+', r'\1', text)

            return {"success": True, "video_id": video_id, "transcript_text": text}

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
