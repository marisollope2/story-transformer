# [DSS x Mongabay] Story Transformer Technical Reference Guide

## Project Overview

This project extracts, summarizes, and translates Mongabay articles.

⸻

## Features
- **Article extraction**: Pulls clean text from Mongabay URLs, Google Docs links, and uploaded `.docx` / `.pdf` / `.txt` files.
- **Editing, translation, and summarization**: Uses a single Bedrock‑backed editor (`bedrock_editor`) that can translate, summarize, or refine copy based on your instructions.
- **FastAPI backend**: Exposes a small, focused API (`/translate`, `/translate/refine`, `/extract/*`, `/tts`) used by the React frontend.
- **React frontend**: Modern web UI for extracting, translating, revising drafts, and downloading results.
- **Text‑to‑speech (AWS Polly)**: Converts the current draft to MP3 audio via the `/tts` endpoint.
- **Safe demo mode**: Optional React demo flow that uses mocked responses so the UX can be tested without live Bedrock/OpenAI credentials.

⸻

## Opening the Project

### If you're new to this project

1. **Clone the repository**

```bash
git clone [url]
cd story-transformer
```

2. **Open the folder in your editor**

- In **editor**: `File → Open Folder…` and select the `story-transformer` folder you just cloned.

3. **Create and activate a virtual environment (Python backend)**

- **Windows (Git Bash)**:

```bash
python -m venv venv
source venv/Scripts/activate
```

- **Windows (Command Prompt / PowerShell)**:

```bash
python -m venv venv
venv\Scripts\activate
```

- **Mac/Linux**:

```bash
python3 -m venv venv
source venv/bin/activate
```

4. **Install backend dependencies**

```bash
pip install -r requirements.txt
```

5. **Add API / Bedrock credentials**

Create a `.env` file in the project root with the keys you use (OpenAI, AWS Bedrock, etc.), for example:

```bash
echo OPENAI_API_KEY="your_api_key_here" > .env
```

If you also use AWS Bedrock, configure your AWS credentials (e.g. via `aws configure`) so the providers in `providers/` can authenticate.

---

### If you’ve worked on this project before

1. **Pull the latest changes**

From the project root:

```bash
git pull origin main   # or your active branch
```

2. **Re-open / focus the folder in your editor**

- In **editor**, open the existing `story-transformer` folder (or switch to that workspace if it’s already open).

3. **Reactivate your virtual environment**

If you already created `venv` previously, just activate it again:

- **Windows (Git Bash)**:

```bash
source venv/Scripts/activate
```

- **Windows (Command Prompt / PowerShell)**:

```bash
venv\Scripts\activate
```

- **Mac/Linux**:

```bash
source venv/bin/activate
```

4. **Install any new dependencies**

If `requirements.txt` changed since your last pull:

```bash
pip install -r requirements.txt
```


⸻

## Running Instructions

1. Activate Your Virtual Environment

Before each session:

Windows (Git Bash):

```
source venv/Scripts/activate
```

Windows (Command Prompt):

```
venv\Scripts\activate
```

Mac/Linux:

```
source venv/bin/activate
```

2. Launch the backend

From the project root (with your virtual environment active):

```bash
uvicorn api.backend:app --reload --port 8000
```

Then open `http://localhost:8000/docs` to explore the API.

> Note: A React frontend (in `frontend/`) can call this FastAPI backend. If you’re using that UI, follow the frontend README or `package.json` scripts there to start the React dev server, usually on `http://localhost:3000`.

3. Launch the frontend

In a separate terminal window, cd into story-transformer/frontend and run:

```bash
npm install # if this is your first time running the frontend, if not then ignore
npm start
```

⸻

## AWS Polly (Text‑to‑Speech)

The backend includes a `/tts` endpoint that uses **Amazon Polly** to synthesize MP3 audio from the current draft.

- **Infrastructure:** The code and IAM permissions are wired up to call `polly:SynthesizeSpeech` via `boto3`.
- **Still required in AWS Console:** You must:
  - Configure AWS credentials on your machine (e.g. `aws configure`) with access to Polly.
  - Ensure the default region (or `AWS_DEFAULT_REGION` env var) supports the voices you plan to use.
- The backend defaults to the `Joanna` voice; the frontend can send a different `voiceId` (for example, a Spanish or Hindi voice) in the `/tts` request body.

⸻

## Notes

- **Backend vs frontend**
  - `api/backend.py` is the FastAPI app used by the React frontend.
  - Old Streamlit code (`api/app.py` and related assets) is legacy and can be removed if you only care about the React UI.
- **React demo mode**
  - The React app includes a demo version that can run with mocked/stubbed responses instead of calling the live FastAPI/Bedrock stack.
  - This exists so designers and contributors can try the UX without AWS/OpenAI credentials and so UI changes can be developed safely without touching production infrastructure.
- **LLM behavior**
  - `providers/bedrock_editor.py` is the single entry point for translate/summarize/refine; it uses a generic prompt and infers the task from `user_request`.
  - `providers/text_normalization.py` normalizes and lightly cleans model outputs before they reach the UI.
- **Extraction**
  - URL, Google Docs, and file extraction are handled by `scripts/extract.py` and `scripts/file_extractor.py`, wrapped by `/extract/*` endpoints.
- **AWS / Bedrock**
  - Bedrock/model settings live in `providers/bedrock_config.py`; check this if you change models or regions.
  - Make sure AWS credentials are correctly scoped; IAM policies should include both the Bedrock models you use and Polly if you rely on `/tts`.
- **Housekeeping**
  - `examples/` and legacy Streamlit files are safe to delete if unused.
  - Before removing any `providers/` or `scripts/` modules, run the tests in `tests/` and a quick manual pass through the main flows (extract → translate → refine → TTS).
