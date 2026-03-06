# Extract structured information from transcript using regex + spaCy

import re
import json
import spacy

nlp = spacy.load("en_core_web_sm")

# -------------------------------
# Regex Patterns
# -------------------------------

EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')

PHONE_RE = re.compile(
    r'\b(?:\+?1[\s\-\.]?)?\(?[2-9]\d{2}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}\b'
)

BUSINESS_HOURS_RE = re.compile(
    r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday).*?(am|pm)',
    re.IGNORECASE
)

# phrases that should NEVER be company names
INVALID_COMPANY_PHRASES = [
    "have a great day",
    "thanks for calling",
    "thank you",
    "speaker"
]

# service keywords
SERVICE_KEYWORDS = [
    "electrician",
    "electrical",
    "plumbing",
    "repair",
    "installation",
    "maintenance",
    "ev charger",
    "panel change",
    "hot tub",
]

# emergency indicators
EMERGENCY_KEYWORDS = [
    "emergency",
    "urgent",
    "sparking",
    "no power",
    "burst pipe"
]


# -------------------------------
# Extraction Function
# -------------------------------

def extract_information(text):

    doc = nlp(text)

    memo = {
        "company_name": None,
        "contact_name": None,
        "contact_email": [],
        "contact_phone": [],
        "services_supported": [],
        "business_hours": None,
        "emergency_definition": None,
        "routing_rules": {},
        "questions_or_unknowns": []
    }

    # -------------------------------
    # Email Extraction
    # -------------------------------

    emails = re.findall(EMAIL_RE, text)
    memo["contact_email"] = list(set(emails))

    # -------------------------------
    # Phone Extraction
    # -------------------------------

    phones = re.findall(PHONE_RE, text)

    clean_phones = []
    for p in phones:
        digits = re.sub(r"\D", "", p)
        if len(digits) == 10:
            clean_phones.append(digits)

    memo["contact_phone"] = list(set(clean_phones))

    # -------------------------------
    # Contact Name via spaCy
    # -------------------------------

    for ent in doc.ents:
        if ent.label_ == "PERSON":

            name = ent.text.strip()

            # avoid picking names like "Nick", "Bharat" from Clara team
            if len(name.split()) <= 2:
                memo["contact_name"] = name
                break

    # -------------------------------
    # Company Name Detection
    # -------------------------------

    company_patterns = [
        r"thanks for calling ([A-Za-z &]+)",
        r"this is ([A-Za-z &]+)",
        r"welcome to ([A-Za-z &]+)"
    ]

    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            candidate = match.group(1).strip()

            if candidate.lower() not in INVALID_COMPANY_PHRASES:
                memo["company_name"] = candidate
                break

    # -------------------------------
    # Services Detection
    # -------------------------------

    services_found = []

    for service in SERVICE_KEYWORDS:
        if service.lower() in text.lower():
            services_found.append(service)

    memo["services_supported"] = list(set(services_found))

    # -------------------------------
    # Business Hours Detection
    # -------------------------------

    hours_match = re.search(BUSINESS_HOURS_RE, text)

    if hours_match:
        memo["business_hours"] = hours_match.group(0)

    # -------------------------------
    # Emergency Definition
    # -------------------------------

    sentences = text.split(".")

    for sentence in sentences:
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in sentence.lower():
                memo["emergency_definition"] = sentence.strip()
                memo["routing_rules"]["emergency"] = "transfer_to_human"
                break

    # -------------------------------
    # Unknown Fields
    # -------------------------------

    for key in ["company_name", "services_supported", "business_hours", "emergency_definition"]:

        val = memo[key]

        if val is None or val == []:
            memo["questions_or_unknowns"].append(f"{key} not found")

    return memo


# -------------------------------
# Test
# -------------------------------

if __name__ == "__main__":

    with open("../transcripts/demo_call_1.txt", "r", encoding="utf-8") as f:
        transcript = f.read()

    result = extract_information(transcript)

    print("\n--- Extracted Account Memo ---\n")
    print(json.dumps(result, indent=4))