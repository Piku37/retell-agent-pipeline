from fastapi import FastAPI, UploadFile, File
import subprocess
import os
import shutil

app = FastAPI()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_DIR = os.path.join(PROJECT_ROOT, "transcripts")


@app.post("/upload-transcript")
async def upload_transcript(file: UploadFile = File(...)):

    # ensure transcripts folder exists
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

    transcript_path = os.path.join(TRANSCRIPTS_DIR, file.filename)

    # save uploaded file
    with open(transcript_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # run pipeline
    result = subprocess.run(
        ["python", "scripts/run_pipeline.py", file.filename],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    return {
        "filename": file.filename,
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }