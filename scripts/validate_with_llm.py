# scripts/validate_with_llm.py
"""
Validate & clean regex-extracted memo using OpenAI (token-efficient).

Usage:
    python validate_with_llm.py <memo.json> <transcript.txt>

Outputs:
    <memo_parent>/<memo_stem>_validated.json
"""

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Optional

# -----------------------
# Config
# -----------------------
load_dotenv()  # reads .env in working dir
OPENAI_KEY = os.getenv("OPEN_AI_KEY") or os.getenv("OPEN_AI_KEY".lower()) or os.getenv("OPEN_AI_KEY".upper())
print("OPENAI KEY LOADED:", bool(OPENAI_KEY))
if not OPENAI_KEY:
    raise RuntimeError("OPEN_AI_KEY not found in environment (.env).")

# create client for openai >= 1.0.0
client = OpenAI(api_key=OPENAI_KEY)

# Model choice (change if you prefer another model in your account)
LLM_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.0
MAX_TOKENS = 600  # JSON output size allowance

# -----------------------
# Helpers
# -----------------------
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(obj, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def sentence_tokenize(text: str) -> List[str]:
    segs = re.split(r'(?<=[\.\?\!])\s+', text)
    return [s.strip() for s in segs if s.strip()]

def extract_relevant_snippets(transcript: str, memo: dict, window_chars=300) -> str:
    """
    Build a compact context: pick sentences that contain candidate values or
    likely keywords. Truncate each snippet to window_chars and join them.
    """
    sentences = sentence_tokenize(transcript)
    keywords = set()

    # add candidate values from memo
    for k in ("company_name", "contact_name", "contact_email", "contact_phone", "services_supported"):
        v = memo.get(k)
        if not v:
            continue
        if isinstance(v, list):
            for item in v:
                if item:
                    keywords.add(str(item).lower())
        else:
            keywords.add(str(v).lower())

    # always look for emergency & contact tokens
    keywords.update(["emergency", "urgent", "immediate", "burst", "fire", "no power", "contact", "phone", "email"])

    chosen = []
    email_re = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    phone_re = re.compile(r'\b(?:\+?1[\s\-\.]?)?\(?[2-9]\d{2}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}\b')

    for s in sentences:
        low = s.lower()
        if any(k in low for k in keywords):
            chosen.append(s)
            continue
        if email_re.search(s):
            chosen.append(s)
            continue
        if phone_re.search(s):
            chosen.append(s)
            continue

    # truncate and return
    trimmed = []
    for s in chosen:
        if len(s) > window_chars:
            trimmed.append(s[:window_chars].rsplit(' ', 1)[0] + " ...")
        else:
            trimmed.append(s)
    if not trimmed:
        # fallback to a short prefix of the transcript
        return (transcript[:min(len(transcript), 800)]) + (" ..." if len(transcript) > 800 else "")
    out = " ".join(trimmed)
    return out[:1500] + (" ..." if len(out) > 1500 else "")

def find_json_by_braces(text: str) -> Optional[str]:
    """
    Find the first balanced JSON object in `text`. Returns substring or None.
    Scans from first '{' and uses a stack to find matching '}'.
    """
    start = text.find("{")
    if start == -1:
        return None
    stack = []
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            stack.append("{")
        elif ch == "}":
            if not stack:
                # unmatched closing brace - ignore
                continue
            stack.pop()
            if not stack:
                return text[start:i+1]
    return None

def safe_parse_json_from_text(text: str):
    """
    Attempt to parse JSON robustly:
    1) direct json.loads
    2) find first balanced {...} and json.loads
    3) fallback: naive first-{ to last-}
    """
    if not isinstance(text, str):
        return None
    try:
        return json.loads(text)
    except Exception:
        pass

    # try balanced-brace extraction
    candidate = find_json_by_braces(text)
    if candidate:
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # last resort: find first { and last } and try
    s = text.find("{")
    e = text.rfind("}")
    if s != -1 and e != -1 and e > s:
        try:
            return json.loads(text[s:e+1])
        except Exception:
            pass

    return None

# -----------------------
# Build prompt
# -----------------------
VALIDATION_SCHEMA = {
    "company_name": "string or null",
    "contact_name": "string or null",
    "contact_email": "list of emails (may be empty)",
    "contact_phone": "list of phone-digit-strings (may be empty)",
    "services_supported": "list of literal service strings (may be empty)",
    "business_hours": "string or null",
    "emergency_definition": "string or null"
}

SYSTEM_INSTRUCTIONS = (
    "You are a strict JSON validator/cleaner. "
    "You will be given (A) a small transcript context and (B) a candidate JSON produced "
    "by a deterministic extractor. Your job is to CORRECT, NORMALIZE and RETURN ONLY a JSON object "
    "matching the exact schema below. Do NOT add any extra fields. "
    "If information is not present in the transcript, set it to null (or empty list for the lists). "
    "Keep values concise. For phone numbers, return digits only (country code optional). "
    "Return JSON ONLY (no explanation)."
)

def build_messages(memo: dict, transcript_snippets: str):
    prompt_body = (
        "Transcript context (compact):\n"
        f"{transcript_snippets}\n\n"
        "Candidate extracted fields (from deterministic extractor):\n"
        f"{json.dumps(memo, ensure_ascii=False)}\n\n"
        "Return a JSON object with these keys and corrected values only:\n"
        f"{json.dumps(VALIDATION_SCHEMA, indent=2)}\n"
    )
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": prompt_body}
    ]
    return messages

# -----------------------
# Main validator
# -----------------------
def validate_memo_with_llm(memo_path: str, transcript_path: str, out_path: str = None):
    memo_path = Path(memo_path)
    transcript_path = Path(transcript_path)

    if not memo_path.exists():
        raise FileNotFoundError(f"Memo file not found: {memo_path}")
    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript file not found: {transcript_path}")

    memo = load_json(str(memo_path))
    transcript = transcript_path.read_text(encoding="utf-8")

    snippets = extract_relevant_snippets(transcript, memo)
    messages = build_messages(memo, snippets)

    print("\nSending request to OpenAI...")
    print("Model:", LLM_MODEL)
    print("Snippet length (chars):", len(snippets))

    # Call OpenAI API (v1+ client)
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        # Pull content safely
        content = ""
        if getattr(response, "choices", None):
            # typical response structure: response.choices[0].message.content
            try:
                content = response.choices[0].message.content
            except Exception:
                # fallback to dict style
                resp_dict = json.loads(response.__dict__.get("_raw", "{}")) if hasattr(response, "_raw") else {}
                content = resp_dict.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            # fallback: stringify entire response
            content = str(response)

        print("\nLLM OUTPUT:")
        # print a shortened preview to avoid huge logs
        preview = content if len(content) < 2000 else content[:2000] + " ... (truncated)"
        print(preview)

    except Exception as e:
        print("OpenAI API error:", str(e))
        print("Falling back to original memo (no change).")
        if not out_path:
            out_path = str(memo_path.parent / (memo_path.stem + "_validated.json"))
        save_json(memo, out_path)
        return out_path

    # -----------------------
    # Parse JSON
    # -----------------------
    validated = safe_parse_json_from_text(content)

    if validated is None:
        print("Model did not return clean JSON. Attempting retry...")

        retry_messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS + " Return ONLY JSON."},
            {"role": "user", "content": "Fix this output to valid JSON:\n" + content}
        ]

        try:
            response2 = client.chat.completions.create(
                model=LLM_MODEL,
                messages=retry_messages,
                temperature=0,
                max_tokens=MAX_TOKENS
            )
            # extract content
            try:
                content2 = response2.choices[0].message.content
            except Exception:
                content2 = str(response2)
            validated = safe_parse_json_from_text(content2)
            if validated is not None:
                content = content2  # update for logging
        except Exception:
            validated = None

    if validated is None:
        print("ERROR: could not parse JSON from model response.")
        if not out_path:
            out_path = str(memo_path.parent / (memo_path.stem + "_validated.json"))
        save_json(memo, out_path)
        return out_path

    # -----------------------
    # Normalize schema
    # -----------------------
    final = {
        "company_name": validated.get("company_name"),
        "contact_name": validated.get("contact_name"),
        "contact_email": validated.get("contact_email") or [],
        "contact_phone": validated.get("contact_phone") or [],
        "services_supported": validated.get("services_supported") or [],
        "business_hours": validated.get("business_hours"),
        "emergency_definition": validated.get("emergency_definition")
    }

    if not out_path:
        out_path = str(memo_path.parent / (memo_path.stem + "_validated.json"))

    save_json(final, out_path)

    print("\nValidated memo saved to:", out_path)
    print("\nField changes (old -> validated):")
    for k in final:
        old = memo.get(k)
        new = final.get(k)
        if old != new:
            print(f" - {k}: {old} -> {new}")

    return out_path

# -----------------------
# CLI
# -----------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python validate_with_llm.py <memo.json> <transcript.txt>")
        sys.exit(1)

    memo_path = sys.argv[1]
    transcript_path = sys.argv[2]

    out = validate_memo_with_llm(memo_path, transcript_path)
    print("\nDone. Validated memo:", out)