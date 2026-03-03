import os
import sys
import io
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.bedrock_editor import refine_with_chat  # noqa: E402
from scripts.extract import extract_article  # noqa: E402
from scripts.file_extractor import extract_from_google_docs_url, extract_text_from_file  # noqa: E402


class TranslateRequest(BaseModel):
    sourceText: str
    instructions: str


class TranslateResponse(BaseModel):
    output: str


class UrlRequest(BaseModel):
    url: str


def _extract_text_from_pdf_bytes(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"PDF support requires pypdf. Import error: {e}")

    reader = PdfReader(io.BytesIO(raw))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts).strip()


app = FastAPI(title="Story Transformer API", version="0.1.0")

# Allow local React dev servers by default
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest) -> TranslateResponse:
    """
    Minimal endpoint for React:
    POST /translate { sourceText, instructions } -> { output }
    """
    source = (req.sourceText or "").strip()
    instructions = (req.instructions or "").strip()

    if not source:
        raise HTTPException(status_code=400, detail="sourceText cannot be empty")
    if not instructions:
        raise HTTPException(status_code=400, detail="instructions cannot be empty")

    result = refine_with_chat(
        original_text=source,
        current_text=source,
        user_request=instructions,
    )

    return TranslateResponse(output=result)


@app.post("/extract/url")
def extract_from_url(req: UrlRequest) -> dict:
    """
    Extract main article text from a URL using existing scraper logic.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="url cannot be empty")

    try:
        text = extract_article(req.url.strip())
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/gdoc")
def extract_from_gdoc(req: UrlRequest) -> dict:
    """
    Extract text from a Google Docs URL using existing helper.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="url cannot be empty")

    try:
        text = extract_from_google_docs_url(req.url.strip())
        if not text:
            raise RuntimeError("No text returned from Google Docs extraction")
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/file")
async def extract_from_uploaded_file(file: UploadFile = File(...)) -> dict:
    """
    Extract text from an uploaded file.

    Supported:
    - .txt
    - .docx (Word)
    - .pdf
    """
    filename = (file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="file is required")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    ext = os.path.splitext(filename.lower())[1]
    try:
        if ext == ".pdf":
            text = _extract_text_from_pdf_bytes(raw)
        elif ext in (".txt", ".docx"):
            # Reuse existing Streamlit-oriented extractor by providing a minimal file-like object
            class _UploadedLike:
                def __init__(self, name: str, data: bytes):
                    self.name = name
                    self._data = data

                def read(self) -> bytes:
                    return self._data

            text = extract_text_from_file(_UploadedLike(filename, raw))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload a .docx, .pdf, or .txt file.",
            )

        if not text or not text.strip():
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in the uploaded file.",
            )
        return {"text": text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

