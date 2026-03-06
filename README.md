# Retell Agent Pipeline

An automated pipeline to convert call transcripts into structured account memos and agent specs using regex + spaCy + an LLM, orchestrated by n8n and exposed via a FastAPI webhook.

---

## Table of Contents

* [What is this project?](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#what-is-this-project)
* [High-level architecture & data flow](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#high-level-architecture--data-flow)
* [Features](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#features)
* [Repository layout](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#repository-layout)
* [Prerequisites](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#prerequisites)
* [Quickstart — run locally (development)](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#quickstart--run-locally-development)
* [n8n orchestration (Docker)](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#n8n-orchestration-docker)
* [API endpoints (FastAPI)](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#api-endpoints-fastapi)
* [How the pipeline works — step-by-step](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#how-the-pipeline-works--step-by-step)
* [Configuration & environment variables](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#configuration--environment-variables)
* [CI (GitHub Actions) example](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#ci-github-actions-example)
* [Troubleshooting & tips](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#troubleshooting--tips)
* [Next improvements & roadmap](https://www.google.com/search?q=%23next-improvements--roadmap)
* [Screenshots](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#screenshots)
* [License & credits](https://github.com/Piku37/retell-agent-pipeline/tree/main?tab=readme-ov-file#contribution--development-notes)

---

## What is this project?

This project is an end-to-end automation pipeline that converts raw call transcripts into structured "account memos" and a generated agent spec. It uses:

* **Deterministic extraction** (regex + spaCy NER) to find emails, phones, names, services, etc.
* **Optional LLM validation layer** (token-efficient) to correct/normalize the regex output.
* **Versioning and diff-generation** for the memo and agent spec.
* **Orchestration layer** (n8n) that triggers the pipeline via webhooks.
* **FastAPI wrapper** that accepts uploaded transcript files, saves them, and triggers the pipeline.
* **Automation** via GitHub Actions for CI testing.

**The result:** Given a transcript file, the system will create an account folder with `memo.json`, `memo_validated.json`, `agent_spec.json`, and a change log.

---

## High-level architecture & data flow

1. **User uploads transcript** (via n8n webhook)
2. **n8n (Docker)** sends an HTTP POST to FastAPI `/upload-transcript`
3. **FastAPI** saves the file to `transcripts/` and calls:
`python scripts/run_pipeline.py <transcript_filename>`
4. **`scripts/run_pipeline.py`** executes the following sequence:
* Generates account ID
* `python scripts/save_memo.py <account_id> <transcript>`
* `python scripts/validate_with_llm.py <memo.json> <transcript>`
* `python scripts/generate_agent.py <account_id>`
* `python scripts/version_update.py <account_id>`
* `python scripts/generate_diff.py <account_id>`


5. **Output generated** at `outputs/accounts/account_XXX/v1|v2/...`

---

## Features

* **Deterministic information extraction** with regex + spaCy.
* **Token-efficient LLM validation** (hybrid approach) — only used when needed or when triggered.
* **Auto-generate** sequential `account_XXX` IDs.
* **Transcript upload webhook** (FastAPI) — push-to-run.
* **Orchestration with n8n** (Docker) — webhook + HTTP request nodes.
* **Local/Dev friendly** (Docker for n8n, local FastAPI server).
* **GitHub Actions-based CI** for pipeline smoke tests.
* **Minimal logs** and LLM call logging capability (easy to enable).

---

## Repository layout

```text
retell-agent-pipeline/
├── api_server.py             # FastAPI endpoints (upload + run)
├── README.md
├── requirements.txt
├── .gitignore
├── transcripts/              # input transcripts (uploaded or manual)
├── outputs/                  # runtime outputs (not committed)
├── logs/                     # optional logs (not committed)
├── scripts/
│   ├── run_pipeline.py       # orchestrates the run (call per transcript)
│   ├── save_memo.py          # run regex/spaCy extractor -> memo.json
│   ├── validate_with_llm.py  # LLM validator (OpenAI client)
│   ├── generate_agent.py     # generate agent spec from memo
│   ├── version_update.py     # do versioning (v1 -> v2)
│   ├── generate_diff.py      # compute change log / diff
│   ├── extract_memo.py       # extractor implementation
│   └── utils.py              # helper functions (generate_account_id, etc.)
└── .env                      # environment vars (not committed)

```

---

## Prerequisites

* Python 3.10+ (3.11 recommended)
* pip
* Docker (for n8n)
* An OpenAI API key (if you use LLM validation)
* *(Optional)* Git & GitHub account for CI

**Minimal `requirements.txt`:**

```text
fastapi
uvicorn
python-dotenv
spacy
openai

```

---

## Quickstart — run locally (development)

1. **Clone repo**
```bash
git clone https://github.com/YOUR_USERNAME/retell-agent-pipeline.git
cd retell-agent-pipeline

```


2. **Create `.env` in repo root:**
```env
OPEN_AI_KEY=sk-...

```


3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm

```


4. **Start the API server**
```bash
uvicorn api_server:app --reload --port 8000

```


*API will be available at http://localhost:8000.*
5. **Run the pipeline manually** (useful for quick testing)
```bash
python scripts/run_pipeline.py demo_call_1.txt

# or without argument to use default demo_call_1.txt
python scripts/run_pipeline.py

```


6. **Check outputs**
* `outputs/accounts/account_00X/v1/memo.json`
* `outputs/accounts/account_00X/v1/memo_validated.json`
* `outputs/accounts/account_00X/agent_spec.json`



---

## n8n orchestration (Docker)

We use n8n as a lightweight orchestration layer. Run it via Docker and mount the project folder.

**Run n8n (PowerShell on Windows):**

```powershell
docker run -it --rm -p 5678:5678 `
  -e N8N_ALLOW_EXECUTE_COMMAND=true `
  -v $env:USERPROFILE\.n8n:/home/node/.n8n `
  -v C:\path\to\retell-agent-pipeline:/project `
  n8nio/n8n

```

*(Replace `C:\path\to\retell-agent-pipeline` with your repo path).*

**n8n workflow (recommended):**

1. **Webhook node** (POST, path `upload-transcript`)
2. **HTTP Request node**:
* Method: POST
* URL: `http://host.docker.internal:8000/upload-transcript`
* Send Binary Data: TRUE
* Binary Property: `data`
* Flow: Webhook → HTTP Request → *(FastAPI handles saving + runs pipeline)*



**Testing from PowerShell:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook/upload-transcript" -Method Post -Form @{file = Get-Item "transcripts\demo_call_1.txt"}

```

*(Or use Postman / cURL inside WSL/Git Bash).*

---

## API endpoints (FastAPI)

### `POST /upload-transcript`

* **Body:** `file` (multipart binary upload)
* **Behavior:** Saves file to `transcripts/`, then calls `scripts/run_pipeline.py <filename>` and returns the pipeline output (stdout/stderr/return_code).

### `GET /run-pipeline?transcript=<filename>`

* **Example:** `http://localhost:8000/run-pipeline?transcript=demo_call_1.txt`
* **Behavior:** Triggers the pipeline via GET. Runs `scripts/run_pipeline.py <filename>` and returns output.

**Return JSON example:**

```json
{
  "filename": "demo_call_1.txt",
  "return_code": 0,
  "stdout": "Running save_memo.py ...",
  "stderr": ""
}

```

---

## How the pipeline works — step-by-step

1. **Upload / trigger:** n8n or user triggers upload of a transcript.
2. **FastAPI saves file:** Moved into `transcripts/` and invokes `scripts/run_pipeline.py <transcript>`.
3. **Account generation:** `run_pipeline.py` calls `utils.generate_account_id()` that creates a sequential `account_XXX` folder under `outputs/accounts`.
4. **Extraction:** `save_memo.py <account_id> <transcript_path>` loads the transcript, runs `extract_memo.extract_information()` (regex + spaCy), and writes `memo.json` to `outputs/accounts/<account_id>/v1/`.
5. **LLM validation:** `validate_with_llm.py <memo.json> <transcript>` loads the memo, extracts short transcript snippets, calls OpenAI with a compact prompt, parses returned JSON, and writes `memo_validated.json`.
* *Token-saving strategies:* only send relevant snippets, strict JSON-only response, temperature=0.


6. **Agent generation:** `generate_agent.py <account_id>` creates `agent_spec.json` from the memo.
7. **Versioning:** `version_update.py <account_id>` creates `v2` and handles diffs.
8. **Diff:** `generate_diff.py <account_id>` writes `changes.json`.

# Retell Agent Pipeline

An automated pipeline to convert call transcripts into structured account memos and agent specs using regex + spaCy + an LLM, orchestrated by n8n and exposed via a FastAPI webhook.

---

## Table of Contents

* [What is this project?](https://www.google.com/search?q=%23what-is-this-project)
* [High-level architecture & data flow](https://www.google.com/search?q=%23high-level-architecture--data-flow)
* [Features](https://www.google.com/search?q=%23features)
* [Repository layout](https://www.google.com/search?q=%23repository-layout)
* [Prerequisites](https://www.google.com/search?q=%23prerequisites)
* [Quickstart — run locally (development)](https://www.google.com/search?q=%23quickstart--run-locally-development)
* [n8n orchestration (Docker)](https://www.google.com/search?q=%23n8n-orchestration-docker)
* [API endpoints (FastAPI)](https://www.google.com/search?q=%23api-endpoints-fastapi)
* [How the pipeline works — step-by-step](https://www.google.com/search?q=%23how-the-pipeline-works--step-by-step)
* [Configuration & environment variables](https://www.google.com/search?q=%23configuration--environment-variables)
* [CI (GitHub Actions) example](https://www.google.com/search?q=%23ci-github-actions-example)
* [Troubleshooting & tips](https://www.google.com/search?q=%23troubleshooting--tips)
* [Next improvements & roadmap](https://www.google.com/search?q=%23next-improvements--roadmap)
* [Screenshots](https://www.google.com/search?q=%23screenshots)
* [License & credits](https://www.google.com/search?q=%23license--credits)

---

## What is this project?

This project is an end-to-end automation pipeline that converts raw call transcripts into structured "account memos" and a generated agent spec. It uses:

* **Deterministic extraction** (regex + spaCy NER) to find emails, phones, names, services, etc.
* **Optional LLM validation layer** (token-efficient) to correct/normalize the regex output.
* **Versioning and diff-generation** for the memo and agent spec.
* **Orchestration layer** (n8n) that triggers the pipeline via webhooks.
* **FastAPI wrapper** that accepts uploaded transcript files, saves them, and triggers the pipeline.
* **Automation** via GitHub Actions for CI testing.

**The result:** Given a transcript file, the system will create an account folder with `memo.json`, `memo_validated.json`, `agent_spec.json`, and a change log.

---

## High-level architecture & data flow

1. **User uploads transcript** (via n8n webhook)
2. **n8n (Docker)** sends an HTTP POST to FastAPI `/upload-transcript`
3. **FastAPI** saves the file to `transcripts/` and calls:
`python scripts/run_pipeline.py <transcript_filename>`
4. **`scripts/run_pipeline.py`** executes the following sequence:
* Generates account ID
* `python scripts/save_memo.py <account_id> <transcript>`
* `python scripts/validate_with_llm.py <memo.json> <transcript>`
* `python scripts/generate_agent.py <account_id>`
* `python scripts/version_update.py <account_id>`
* `python scripts/generate_diff.py <account_id>`


5. **Output generated** at `outputs/accounts/account_XXX/v1|v2/...`

---

## Features

* **Deterministic information extraction** with regex + spaCy.
* **Token-efficient LLM validation** (hybrid approach) — only used when needed or when triggered.
* **Auto-generate** sequential `account_XXX` IDs.
* **Transcript upload webhook** (FastAPI) — push-to-run.
* **Orchestration with n8n** (Docker) — webhook + HTTP request nodes.
* **Local/Dev friendly** (Docker for n8n, local FastAPI server).
* **GitHub Actions-based CI** for pipeline smoke tests.
* **Minimal logs** and LLM call logging capability (easy to enable).

---

## Repository layout

```text
retell-agent-pipeline/
├── api_server.py             # FastAPI endpoints (upload + run)
├── README.md
├── requirements.txt
├── .gitignore
├── transcripts/              # input transcripts (uploaded or manual)
├── outputs/                  # runtime outputs (not committed)
├── logs/                     # optional logs (not committed)
├── scripts/
│   ├── run_pipeline.py       # orchestrates the run (call per transcript)
│   ├── save_memo.py          # run regex/spaCy extractor -> memo.json
│   ├── validate_with_llm.py  # LLM validator (OpenAI client)
│   ├── generate_agent.py     # generate agent spec from memo
│   ├── version_update.py     # do versioning (v1 -> v2)
│   ├── generate_diff.py      # compute change log / diff
│   ├── extract_memo.py       # extractor implementation
│   └── utils.py              # helper functions (generate_account_id, etc.)
└── .env                      # environment vars (not committed)

```

---

## Prerequisites

* Python 3.10+ (3.11 recommended)
* pip
* Docker (for n8n)
* An OpenAI API key (if you use LLM validation)
* *(Optional)* Git & GitHub account for CI

**Minimal `requirements.txt`:**

```text
fastapi
uvicorn
python-dotenv
spacy
openai

```

---

## Quickstart — run locally (development)

1. **Clone repo**
```bash
git clone https://github.com/YOUR_USERNAME/retell-agent-pipeline.git
cd retell-agent-pipeline

```


2. **Create `.env` in repo root:**
```env
OPEN_AI_KEY=sk-...

```


3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm

```


4. **Start the API server**
```bash
uvicorn api_server:app --reload --port 8000

```


*API will be available at http://localhost:8000.*
5. **Run the pipeline manually** (useful for quick testing)
```bash
python scripts/run_pipeline.py demo_call_1.txt

# or without argument to use default demo_call_1.txt
python scripts/run_pipeline.py

```


6. **Check outputs**
* `outputs/accounts/account_00X/v1/memo.json`
* `outputs/accounts/account_00X/v1/memo_validated.json`
* `outputs/accounts/account_00X/agent_spec.json`



---

## n8n orchestration (Docker)

We use n8n as a lightweight orchestration layer. Run it via Docker and mount the project folder.

**Run n8n (PowerShell on Windows):**

```powershell
docker run -it --rm -p 5678:5678 `
  -e N8N_ALLOW_EXECUTE_COMMAND=true `
  -v $env:USERPROFILE\.n8n:/home/node/.n8n `
  -v C:\path\to\retell-agent-pipeline:/project `
  n8nio/n8n

```

*(Replace `C:\path\to\retell-agent-pipeline` with your repo path).*

**n8n workflow (recommended):**

1. **Webhook node** (POST, path `upload-transcript`)
2. **HTTP Request node**:
* Method: POST
* URL: `http://host.docker.internal:8000/upload-transcript`
* Send Binary Data: TRUE
* Binary Property: `data`
* Flow: Webhook → HTTP Request → *(FastAPI handles saving + runs pipeline)*



**Testing from PowerShell:**

```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook/upload-transcript" -Method Post -Form @{file = Get-Item "transcripts\demo_call_1.txt"}

```

*(Or use Postman / cURL inside WSL/Git Bash).*

---

## API endpoints (FastAPI)

### `POST /upload-transcript`

* **Body:** `file` (multipart binary upload)
* **Behavior:** Saves file to `transcripts/`, then calls `scripts/run_pipeline.py <filename>` and returns the pipeline output (stdout/stderr/return_code).

### `GET /run-pipeline?transcript=<filename>`

* **Example:** `http://localhost:8000/run-pipeline?transcript=demo_call_1.txt`
* **Behavior:** Triggers the pipeline via GET. Runs `scripts/run_pipeline.py <filename>` and returns output.

**Return JSON example:**

```json
{
  "filename": "demo_call_1.txt",
  "return_code": 0,
  "stdout": "Running save_memo.py ...",
  "stderr": ""
}

```

---

## How the pipeline works — step-by-step

1. **Upload / trigger:** n8n or user triggers upload of a transcript.
2. **FastAPI saves file:** Moved into `transcripts/` and invokes `scripts/run_pipeline.py <transcript>`.
3. **Account generation:** `run_pipeline.py` calls `utils.generate_account_id()` that creates a sequential `account_XXX` folder under `outputs/accounts`.
4. **Extraction:** `save_memo.py <account_id> <transcript_path>` loads the transcript, runs `extract_memo.extract_information()` (regex + spaCy), and writes `memo.json` to `outputs/accounts/<account_id>/v1/`.
5. **LLM validation:** `validate_with_llm.py <memo.json> <transcript>` loads the memo, extracts short transcript snippets, calls OpenAI with a compact prompt, parses returned JSON, and writes `memo_validated.json`.
* *Token-saving strategies:* only send relevant snippets, strict JSON-only response, temperature=0.


6. **Agent generation:** `generate_agent.py <account_id>` creates `agent_spec.json` from the memo.
7. **Versioning:** `version_update.py <account_id>` creates `v2` and handles diffs.
8. **Diff:** `generate_diff.py <account_id>` writes `changes.json`.

<img src="https://github.com/Piku37/retell-agent-pipeline/blob/b37e4f442cb2f85a073caad21a3a63b75540a40b/docs/flowchart/flow-chart.png" width="80%" alt="Workflow">

---

## Configuration & environment variables

Create a `.env` file **(DO NOT commit):**

```env
OPEN_AI_KEY=sk-...
# Optional:
LLM_MODEL=gpt-4o-mini

```

**Notes & best practices:**

* Never commit `.env` or API keys.
* For large-scale usage, put secrets into a secure vault (Azure Key Vault, AWS Secrets Manager, GitHub Secrets for Actions).

---

## CI (GitHub Actions) example

Place this file at `.github/workflows/pipeline.yml`:

```yaml
name: Pipeline CI

on:
  push:
    branches: [ main ]

jobs:
  run-pipeline-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with: python-version: '3.11'
      - name: Install deps
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_sm
      - name: Run pipeline smoke test
        run: |
          python scripts/run_pipeline.py demo_call_1.txt

```

*Note: For security, do not set `OPEN_AI_KEY` in CI for public repos; use a safe test mode or mock LLM calls.*

---

## Troubleshooting & tips

* **No OpenAI usage seen:** Make sure `.env` has `OPEN_AI_KEY` and the server process has the environment loaded. The `validate_with_llm.py` prints `OPENAI KEY LOADED: True` at startup—check that.
* **`openai.ChatCompletion` error:** If you see `openai.ChatCompletion not supported`, upgrade code to new SDK usage or pin `openai==0.28`. The repo uses `from openai import OpenAI` (v1+ client).
* **Windows encoding errors:** Replace Unicode arrows in prints (`→`) with ASCII (`->`) to avoid charmap errors in Windows console.
* **n8n cannot find Execute Command node:** Modern n8n may disable direct execution. Use HTTP → local API pattern (we implemented FastAPI).
* **Docker networking:** Inside n8n Docker container, call `host.docker.internal` to reach localhost of host.
* **Token cost:** LLM calls cost money. Use confidence scoring to skip LLM when regex output seems valid.
* **Duplicate transcripts:** Implement a simple check (hash the contents) and skip if identical to a previously processed file.

---

## Next improvements & roadmap

* [ ] Add confidence scoring to skip LLM for high-confidence regex results.
* [ ] Add LLM call logging (`logs/llm_calls.json`) with timestamp, tokens, and cost estimate.
* [ ] Add webhook auth/ACL for secure uploads.
* [ ] Deploy FastAPI behind a reverse proxy (nginx) and enable TLS.
* [ ] Add a small UI/dashboard to view `outputs/` and diffs.



---

## Contribution & development notes

* Follow the one-step-at-a-time rule: change one script, run tests, verify outputs.
* Add unit tests for extractors (`scripts/test_extractor.py`) before changing regex patterns.
* Use branches for feature work: `feature/confidence-scoring`, `feature/webhook-auth`.

---

---

## Configuration & environment variables

Create a `.env` file **(DO NOT commit):**

```env
OPEN_AI_KEY=sk-...
# Optional:
LLM_MODEL=gpt-4o-mini

```

**Notes & best practices:**

* Never commit `.env` or API keys.
* For large-scale usage, put secrets into a secure vault (Azure Key Vault, AWS Secrets Manager, GitHub Secrets for Actions).

---

## CI (GitHub Actions) example

Place this file at `.github/workflows/pipeline.yml`:

```yaml
name: Pipeline CI

on:
  push:
    branches: [ main ]

jobs:
  run-pipeline-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with: python-version: '3.11'
      - name: Install deps
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_sm
      - name: Run pipeline smoke test
        run: |
          python scripts/run_pipeline.py demo_call_1.txt

```

*Note: For security, do not set `OPEN_AI_KEY` in CI for public repos; use a safe test mode or mock LLM calls.*

---

## Troubleshooting & tips

* **No OpenAI usage seen:** Make sure `.env` has `OPEN_AI_KEY` and the server process has the environment loaded. The `validate_with_llm.py` prints `OPENAI KEY LOADED: True` at startup—check that.
* **`openai.ChatCompletion` error:** If you see `openai.ChatCompletion not supported`, upgrade code to new SDK usage or pin `openai==0.28`. The repo uses `from openai import OpenAI` (v1+ client).
* **Windows encoding errors:** Replace Unicode arrows in prints (`→`) with ASCII (`->`) to avoid charmap errors in Windows console.
* **n8n cannot find Execute Command node:** Modern n8n may disable direct execution. Use HTTP → local API pattern (we implemented FastAPI).
* **Docker networking:** Inside n8n Docker container, call `host.docker.internal` to reach localhost of host.
* **Token cost:** LLM calls cost money. Use confidence scoring to skip LLM when regex output seems valid.
* **Duplicate transcripts:** Implement a simple check (hash the contents) and skip if identical to a previously processed file.

---

## Next improvements & roadmap

* [ ] Add confidence scoring to skip LLM for high-confidence regex results.
* [ ] Add LLM call logging (`logs/llm_calls.json`) with timestamp, tokens, and cost estimate.
* [ ] Add webhook auth/ACL for secure uploads.
* [ ] Deploy FastAPI behind a reverse proxy (nginx) and enable TLS.
* [ ] Add a small UI/dashboard to view `outputs/` and diffs.

---
## Contribution & development notes

* Follow the one-step-at-a-time rule: change one script, run tests, verify outputs.
* Add unit tests for extractors (`scripts/test_extractor.py`) before changing regex patterns.
* Use branches for feature work: `feature/confidence-scoring`, `feature/webhook-auth`.

---

---

## Screenshots


*Final Memo*

<img src="https://github.com/Piku37/retell-agent-pipeline/blob/b37e4f442cb2f85a073caad21a3a63b75540a40b/docs/screenshots/memo-final.png" alt="final memo" width='50%'>

*Changes after Onboarding*

<img src="https://github.com/Piku37/retell-agent-pipeline/blob/b37e4f442cb2f85a073caad21a3a63b75540a40b/docs/screenshots/changes-onboarding.png" alt='onboarding changes' width='50%'>

*SwaggerUI of file upload*

<img src="https://github.com/Piku37/retell-agent-pipeline/blob/b37e4f442cb2f85a073caad21a3a63b75540a40b/docs/screenshots/swagger.png" alt="swaggerUI" width='50%'>

*n8n workflow*

<img src="https://github.com/Piku37/retell-agent-pipeline/blob/b37e4f442cb2f85a073caad21a3a63b75540a40b/docs/screenshots/n8n-upload.png" width='50%'>

*docker container running n8n*

<img src="https://github.com/Piku37/retell-agent-pipeline/blob/b37e4f442cb2f85a073caad21a3a63b75540a40b/docs/screenshots/docker-container.png" alt = 'docker conatiner running n8n' width='50%'>


