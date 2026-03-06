# This script loads transcript files and cleans speaker labels and timestamps

import os
import re

TRANSCRIPT_FOLDER = "../transcripts"

def clean_transcript(text):
    # remove speaker labels and timestamps
    cleaned = re.sub(r"Speaker \d+:\s*\d+:\d+\s*", "", text)
    return cleaned

def load_transcripts():
    transcripts = []

    for file in os.listdir(TRANSCRIPT_FOLDER):
        if file.endswith(".txt"):
            path = os.path.join(TRANSCRIPT_FOLDER, file)

            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()

            cleaned_text = clean_transcript(raw_text)

            transcripts.append({
                "file_name": file,
                "transcript": cleaned_text
            })

    return transcripts


if __name__ == "__main__":
    transcripts = load_transcripts()

    for t in transcripts:
        print("\n--- Transcript Loaded ---")
        print("File:", t["file_name"])
        print("Content:\n")
        print(t["transcript"])