import React, { useEffect, useRef, useState } from "react";
import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";
import "./App.css";
import logo from "./og_mb_logo.png";
import { ReactComponent as DownloadIcon } from "./Icon.svg";
import { ReactComponent as RefineIcon } from "./Refine_Icon.svg";
import { ReactComponent as PlayIcon } from "./Play_Icon.svg";
import { ReactComponent as CopyIcon } from "./Copy_Paste_Icon.svg";
import { ReactComponent as UploadIcon } from "./Upload_Icon.svg";

const API_BASE = "http://localhost:8000";
const TTS_TEXT_LIMIT = 3000;

async function getApiErrorMessage(res: Response, fallback: string): Promise<string> {
  const text = await res.text();
  try {
    const json = JSON.parse(text);
    const detail = json.detail ?? json.message ?? text;
    return typeof detail === "string" ? detail : JSON.stringify(detail);
  } catch {
    return text || fallback;
  }
}

const TTS_VOICES: { id: string; label: string }[] = [
  { id: "Joanna", label: "English (Joanna)" },
  { id: "Matthew", label: "English (Matthew)" },
  { id: "Aditi", label: "Hindi (Aditi)" },
  { id: "Kajal", label: "Hindi (Kajal)" },
  { id: "Miguel", label: "Spanish (Miguel)" },
  { id: "Lupe", label: "Spanish (Lupe)" },
  { id: "Zeina", label: "Arabic (Zeina)" },
  { id: "Lea", label: "French (Lea)" },
];

type InputMethod = "file" | "gdoc" | "url" | "manual";

type Draft = { version: number; text: string; refinePrompt?: string };

type TranslationSession = {
  id: string;
  label: string;
  sourceText: string;
  baseInstructions: string;
  drafts: Draft[];
  selectedVersion: number | null;
  createdAt: number;
};

function generateSessionId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function getSessionLabel(instructions: string, sourceText: string): string {
  const fromInstructions = instructions.trim().slice(0, 36);
  const fromSource = sourceText.trim().slice(0, 30).replace(/\s+/g, " ");
  if (fromInstructions) return fromInstructions + (instructions.length > 36 ? "…" : "");
  if (fromSource) return fromSource + (sourceText.length > 30 ? "…" : "");
  return "Untitled translation";
}

const DEMO_SESSION: TranslationSession = {
  id: "demo-session",
  label: "Demo (no API)",
  sourceText:
    "This is sample original content. You can try the swap button, copy, PDF, and audio without calling the translation API.",
  baseInstructions: "Translate to Hindi, keep under 200 words.",
  drafts: [
    {
      version: 1,
      text: "This is a sample translated draft. Use the ⇄ button above to swap the Chat and Content Preview panels.",
    },
    {
      version: 2,
      text: "This is Draft v2—refined to be shorter. You can select different drafts in the chat to see them in the preview.",
      refinePrompt: "Make it shorter",
    },
  ],
  selectedVersion: 1,
  createdAt: Date.now(),
};

const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [view, setView] = useState<"input" | "result">("input");
  const [inputMethod, setInputMethod] = useState<InputMethod>("file");
  const [sourceText, setSourceText] = useState("");
  const [gdocUrl, setGdocUrl] = useState("");
  const [articleUrl, setArticleUrl] = useState("");
  const [instructions, setInstructions] = useState("");
  const [baseInstructions, setBaseInstructions] = useState("");
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [refinePrompt, setRefinePrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [extractLoading, setExtractLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [sessions, setSessions] = useState<TranslationSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioObjectUrl, setAudioObjectUrl] = useState<string | null>(null);
  const [selectedVoiceId, setSelectedVoiceId] = useState<string>("Joanna");
  const [swapResultsColumns, setSwapResultsColumns] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const activeSession = activeSessionId
    ? sessions.find((s) => s.id === activeSessionId) ?? null
    : null;

  const effectiveDrafts = view === "result" && activeSession ? activeSession.drafts : drafts;
  const effectiveSelectedVersion =
    view === "result" && activeSession ? activeSession.selectedVersion : selectedVersion;
  const effectiveSourceText =
    view === "result" && activeSession ? activeSession.sourceText : sourceText;
  const selectedDraft =
    effectiveSelectedVersion && effectiveSelectedVersion > 0
      ? effectiveDrafts.find((d) => d.version === effectiveSelectedVersion)
      : undefined;
  const currentDraftText =
    effectiveSelectedVersion === 0
      ? effectiveSourceText
      : selectedDraft?.text ?? effectiveDrafts[effectiveDrafts.length - 1]?.text ?? "";

  const effectiveBaseInstructions =
    view === "result" && activeSession ? activeSession.baseInstructions : baseInstructions;

  function updateActiveSession(updater: (s: TranslationSession) => TranslationSession) {
    if (!activeSessionId) return;
    setSessions((prev) =>
      prev.map((s) => (s.id === activeSessionId ? updater(s) : s))
    );
  }

  function handleCopyDraft() {
    if (!currentDraftText) return;
    navigator.clipboard.writeText(currentDraftText).then(
      () => {
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      },
      () => setError("Copy failed")
    );
  }

  async function handleDownloadPdf() {
    if (!currentDraftText) return;
    const A4_WIDTH_MM = 210;
    const A4_HEIGHT_MM = 297;
    const A4_WIDTH_PX = 595;
    const A4_HEIGHT_PX = 842;

    const container = document.createElement("div");
    container.style.position = "absolute";
    container.style.left = "-9999px";
    container.style.top = "0";
    container.style.width = `${A4_WIDTH_PX}px`;
    container.style.padding = "24px";
    container.style.fontFamily = "'Noto Sans Devanagari', 'Noto Sans Arabic', 'Noto Sans Bengali', 'Noto Sans Thai', 'Noto Sans', sans-serif";
    container.style.fontSize = "14px";
    container.style.lineHeight = "1.5";
    container.style.color = "#092f29";
    container.style.background = "#fff";
    container.style.whiteSpace = "pre-wrap";
    container.style.wordBreak = "break-word";
    container.style.boxSizing = "border-box";
    container.textContent = currentDraftText;
    document.body.appendChild(container);

    try {
      await document.fonts.ready;
      const canvas = await html2canvas(container, {
        scale: 1,
        useCORS: true,
        logging: false,
        width: A4_WIDTH_PX,
        windowWidth: A4_WIDTH_PX,
      });
      document.body.removeChild(container);

      const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
      const totalHeight = canvas.height;
      let sourceY = 0;

      while (sourceY < totalHeight) {
        const pageCanvas = document.createElement("canvas");
        pageCanvas.width = A4_WIDTH_PX;
        pageCanvas.height = Math.min(A4_HEIGHT_PX, totalHeight - sourceY);
        const ctx = pageCanvas.getContext("2d");
        if (ctx) {
          ctx.fillStyle = "#fff";
          ctx.fillRect(0, 0, pageCanvas.width, pageCanvas.height);
          ctx.drawImage(
            canvas,
            0, sourceY, A4_WIDTH_PX, pageCanvas.height,
            0, 0, A4_WIDTH_PX, pageCanvas.height
          );
        }
        const imgData = pageCanvas.toDataURL("image/png");
        doc.addImage(imgData, "PNG", 0, 0, A4_WIDTH_MM, A4_HEIGHT_MM);
        sourceY += A4_HEIGHT_PX;
        if (sourceY < totalHeight) doc.addPage();
      }

      doc.save(`translation-draft-v${effectiveSelectedVersion ?? 1}.pdf`);
    } catch (e) {
      if (container.parentNode) document.body.removeChild(container);
      setError("PDF generation failed. Try downloading as .txt for long or non-Latin text.");
    }
  }

  async function handleDownloadAudio() {
    if (!currentDraftText) return;
    setError(null);
    setAudioLoading(true);
    const text = currentDraftText.slice(0, TTS_TEXT_LIMIT);
    try {
      const res = await fetch(`${API_BASE}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voiceId: selectedVoiceId }),
      });
      if (!res.ok) throw new Error(await getApiErrorMessage(res, "TTS request failed"));
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `translation-draft-v${effectiveSelectedVersion ?? 1}.mp3`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message || "Audio download failed");
    } finally {
      setAudioLoading(false);
    }
  }

  async function handlePlayAudio() {
    if (!currentDraftText || !audioRef.current) return;
    setError(null);
    setAudioLoading(true);
    if (audioObjectUrl) {
      URL.revokeObjectURL(audioObjectUrl);
      setAudioObjectUrl(null);
    }
    const text = currentDraftText.slice(0, TTS_TEXT_LIMIT);
    const el = audioRef.current;
    try {
      const res = await fetch(`${API_BASE}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voiceId: selectedVoiceId }),
      });
      if (!res.ok) throw new Error(await getApiErrorMessage(res, "TTS request failed"));
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setAudioObjectUrl(url);

      el.src = url;
      const onCanPlay = () => {
        el.play().then(() => setAudioLoading(false)).catch(() => setAudioLoading(false));
      };
      const onEnded = () => setAudioLoading(false);
      const onError = () => setAudioLoading(false);
      el.addEventListener("canplay", onCanPlay, { once: true });
      el.addEventListener("ended", onEnded, { once: true });
      el.addEventListener("error", onError, { once: true });
      if (el.readyState >= 2) onCanPlay();
    } catch (e: any) {
      setError(e.message || "Audio playback failed");
      setAudioLoading(false);
    }
  }

  useEffect(() => {
    return () => {
      if (audioObjectUrl) URL.revokeObjectURL(audioObjectUrl);
    };
  }, [audioObjectUrl]);

  function handleNewTranslation() {
    setActiveSessionId(null);
    setView("input");
    setInputMethod("file");
    setSourceText("");
    setGdocUrl("");
    setArticleUrl("");
    setInstructions("");
    setBaseInstructions("");
    setDrafts([]);
    setSelectedVersion(null);
    setRefinePrompt("");
    setError(null);
  }

  function handleSelectSession(sessionId: string) {
    setActiveSessionId(sessionId);
    setView("result");
    setError(null);
  }

  function handleOpenDemo() {
    setSessions((prev) =>
      prev.some((s) => s.id === DEMO_SESSION.id) ? prev : [DEMO_SESSION, ...prev]
    );
    setActiveSessionId(DEMO_SESSION.id);
    setView("result");
    setError(null);
  }

  async function handleTranslate() {
    setError(null);

    if (!sourceText.trim()) {
      setError("Please provide some input text.");
      return;
    }
    if (!instructions.trim()) {
      setError("Please add translation instructions.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sourceText,
          instructions,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed with ${res.status}`);
      }

      const data = await res.json();
      const firstDraft = data.output ?? "";
      const newSession: TranslationSession = {
        id: generateSessionId(),
        label: getSessionLabel(instructions, sourceText),
        sourceText,
        baseInstructions: instructions,
        drafts: [{ version: 1, text: firstDraft }],
        selectedVersion: 1,
        createdAt: Date.now(),
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setView("result");
      setSourceText("");
      setInstructions("");
      setDrafts([]);
      setSelectedVersion(null);
    } catch (e: any) {
      setError(e.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleRefine() {
    if (!refinePrompt.trim() || !activeSession || effectiveDrafts.length === 0) return;
    setError(null);
    const currentDraft =
      effectiveDrafts.find((d) => d.version === effectiveSelectedVersion)?.text ??
      effectiveDrafts[effectiveDrafts.length - 1].text;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/translate/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sourceText: activeSession.sourceText,
          currentDraft,
          refinePrompt,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed with ${res.status}`);
      }

      const data = await res.json();
      const nextVersion = activeSession.drafts.length + 1;
      const newDraft: Draft = {
        version: nextVersion,
        text: data.output ?? "",
        refinePrompt,
      };
      updateActiveSession((s) => ({
        ...s,
        drafts: [...s.drafts, newDraft],
        selectedVersion: nextVersion,
      }));
      setRefinePrompt("");
    } catch (e: any) {
      setError(e.message || "Refine failed");
    } finally {
      setLoading(false);
    }
  }

  async function fetchArticleFromFile(selectedFile: File) {
    setError(null);

    try {
      const form = new FormData();
      form.append("file", selectedFile);

      const res = await fetch(`${API_BASE}/extract/file`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed with ${res.status}`);
      }

      const data = await res.json();
      setSourceText(data.text ?? "");
    } catch (e: any) {
      setError(e.message || "Failed to extract text from file");
    }
  }

  function handleSelectFileClick() {
    fileInputRef.current?.click();
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) {
      setUploadFile(null);
      return;
    }
    setUploadFile(file);
    fetchArticleFromFile(file);
  }
  
  async function fetchArticleFromUrl() {
    setError(null);

    if (!articleUrl.trim()) {
      setError("Please enter an article URL.");
      return;
    }

    setExtractLoading(true);
    try {
      const res = await fetch(`${API_BASE}/extract/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: articleUrl }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed with ${res.status}`);
      }

      const data = await res.json();
      setSourceText(data.text ?? "");
    } catch (e: any) {
      setError(e.message || "Failed to extract article from URL");
    } finally {
      setExtractLoading(false);
    }
  }

  async function fetchArticleFromGdoc() {
    setError(null);

    if (!gdocUrl.trim()) {
      setError("Please enter a Google Docs URL.");
      return;
    }

    setExtractLoading(true);
    try {
      const res = await fetch(`${API_BASE}/extract/gdoc`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: gdocUrl }),
      });

      if (!res.ok) {
        throw new Error(
          await getApiErrorMessage(res, "Failed to extract from Google Docs")
        );
      }

      const data = await res.json();
      setSourceText(data.text ?? "");
    } catch (e: any) {
      setError(e.message || "Failed to extract article from Google Docs");
    } finally {
      setExtractLoading(false);
    }
  }

  const disableTranslate =
    loading || !sourceText.trim() || !instructions.trim();

  return (
    <div className={`app-root ${sidebarOpen ? "" : "app-root--collapsed"}`}>
      <aside className={`sidebar ${sidebarOpen ? "" : "sidebar--collapsed"}`}>
        <div className="sidebar-top">
          <div className="sidebar-brand-row">
            <div className="sidebar-brand">
            <div className="brand-icon">
              <img
                src={logo}
                alt="Story Transformer logo"
                className="brand-logo-img"
              />
            </div>
            <div className="brand-text">
              <div>Story</div>
              <div>Transformer</div>
            </div>
          </div>
            <button
              className="sidebar-toggle"
              type="button"
              onClick={() => setSidebarOpen((open) => !open)}
              aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
              title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            >
              <span className="sidebar-toggle-icon" aria-hidden>
                {sidebarOpen ? (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </span>
            </button>
          </div>

          <button
            className="nav-button"
            type="button"
            onClick={handleNewTranslation}
          >
            <span className="nav-button-icon">＋</span>
            <span>New Translation</span>
          </button>

          {sessions.length > 0 && (
            <div className="sidebar-history">
              <div className="sidebar-history-label">History</div>
              <ul className="sidebar-history-list" role="list">
                {sessions.map((session) => (
                  <li key={session.id}>
                    <button
                      type="button"
                      className={`sidebar-history-item ${
                        activeSessionId === session.id
                          ? "sidebar-history-item--active"
                          : ""
                      }`}
                      onClick={() => handleSelectSession(session.id)}
                      title={session.label}
                    >
                      <span className="sidebar-history-item-label">
                        {session.label}
                      </span>
                      <span className="sidebar-history-item-meta">
                        {session.drafts.length} draft{session.drafts.length !== 1 ? "s" : ""}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar" />
            <div className="user-name">John Doe</div>
          </div>
          <button className="logout-button" type="button" aria-label="Log out">
            ⤤
          </button>
        </div>
      </aside>

      <main className="main">
        <h1 className="page-title">
          Upload articles in multiple formats and translate them using AI with
          custom formatting
        </h1>

        {view === "input" && (
          <section className="form-section">
            <div className="card card--no-border">
              <h2 className="section-title">Choose input method</h2>
              <div className="tabs">
                <button
                  className={
                    "tab" + (inputMethod === "file" ? " tab--active" : "")
                  }
                  type="button"
                  onClick={() => setInputMethod("file")}
                >
                  File Upload
                </button>
                <button
                  className={
                    "tab" + (inputMethod === "gdoc" ? " tab--active" : "")
                  }
                  type="button"
                  onClick={() => setInputMethod("gdoc")}
                >
                  Google Doc Link
                </button>
                <button
                  className={
                    "tab" + (inputMethod === "url" ? " tab--active" : "")
                  }
                  type="button"
                  onClick={() => setInputMethod("url")}
                >
                  Article URL
                </button>
                <button
                  className={
                    "tab" + (inputMethod === "manual" ? " tab--active" : "")
                  }
                  type="button"
                  onClick={() => setInputMethod("manual")}
                >
                  Manual Text
                </button>
              </div>
            </div>

            <section className="card upload-card">
              <div className="upload-panel">
                {inputMethod === "file" && (
                  <div className="upload-dropzone">
                    <UploadIcon className="upload-icon" aria-hidden />
                    <div className="upload-text">Drag and drop</div>
                    <div className="upload-subtext">
                      .pdf, .docx, .txt
                    </div>
                    <button
                      className="primary-chip-button"
                      type="button"
                      onClick={handleSelectFileClick}
                    >
                      Select File
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".docx,.pdf,.txt"
                      className="file-input-hidden"
                      onChange={handleFileChange}
                    />
                    {uploadFile && sourceText && (
                      <p className="helper-text upload-success">
                        Loaded content from <strong>{uploadFile.name}</strong>
                      </p>
                    )}
                  </div>
                )}

                {inputMethod === "gdoc" && (
                  <>
                    <div className="url-row">
                      <input
                        className="text-input"
                        placeholder="https://docs.google.com/document/d/..."
                        value={gdocUrl}
                        onChange={(e) => setGdocUrl(e.target.value)}
                      />
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={fetchArticleFromGdoc}
                        disabled={extractLoading}
                      >
                        {extractLoading ? (
                          <>
                            <span className="spinner" aria-hidden />
                            Fetching…
                          </>
                        ) : (
                          "Fetch article"
                        )}
                      </button>
                    </div>
                    <p className="helper-text">
                      Ensure the document is shared so that anyone with the link can view it (Share → General access).
                    </p>
                  </>
                )}

                {inputMethod === "url" && (
                  <div className="url-row">
                    <input
                      className="text-input"
                      placeholder="https://example.com/article"
                      value={articleUrl}
                      onChange={(e) => setArticleUrl(e.target.value)}
                    />
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={fetchArticleFromUrl}
                      disabled={extractLoading}
                    >
                      {extractLoading ? (
                        <>
                          <span className="spinner" aria-hidden />
                          Fetching…
                        </>
                      ) : (
                        "Fetch article"
                      )}
                    </button>
                  </div>
                )}

                {inputMethod === "manual" && (
                  <textarea
                    className="text-area"
                    placeholder="Paste or type your article here..."
                    value={sourceText}
                    onChange={(e) => setSourceText(e.target.value)}
                  />
                )}

                {sourceText.trim() && (
                  <p className="helper-text content-loaded-message">
                    ✓ Content loaded (
                    {sourceText.trim().split(/\s+/).filter(Boolean).length} words)
                  </p>
                )}
              </div>
            </section>

            <section className="card">
              <h2 className="section-title">Translation instructions</h2>
              <textarea
                className="text-area"
                placeholder={`e.g., "Translate from English to Hindi and summarize to under 500 words"`}
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
              />
              <p className="helper-text">
                Specify the source language, target language, word count, and
                any formatting preferences
              </p>
            </section>

            <button
              className="primary-button"
              type="button"
              onClick={handleTranslate}
              disabled={disableTranslate}
            >
              {loading ? "Translating..." : "✶ Translate Article"}
            </button>

            <button
              className="demo-button"
              type="button"
              onClick={handleOpenDemo}
              aria-label="Open results view with sample data (no API call)"
            >
              View results (demo)
            </button>

            {error && <div className="error">{error}</div>}
          </section>
        )}

        {view === "result" && (
          <section className="results-section">
            {error && <div className="error">{error}</div>}

            <div className={`results-header-row ${swapResultsColumns ? "results-header-row--swapped" : ""}`}>
              <h3 className="section-subtitle results-header-title" data-column="chat">
                Chat with Transformer
              </h3>
              <button
                type="button"
                className="results-swap-button"
                onClick={() => setSwapResultsColumns((s) => !s)}
                aria-label="Swap chat and preview panels"
                title="Swap panels"
              >
                ⇄
              </button>
              <h3 className="section-subtitle results-header-title" data-column="preview">
                Content Preview
              </h3>
            </div>

            <div className={`results-columns ${swapResultsColumns ? "results-columns--swapped" : ""}`}>
              <section className="results-column" data-column="chat">
                <div className="results-card">
                  <div className="chat-thread">
                    <div className="chat-row chat-row--bot">
                      <button
                        type="button"
                        className={`chat-bubble chat-bubble--original ${
                          effectiveSelectedVersion === 0
                            ? "chat-bubble--draft-selected"
                            : ""
                        }`}
                        onClick={() =>
                          updateActiveSession((s) => ({
                            ...s,
                            selectedVersion: 0,
                          }))
                        }
                      >
                        <div className="chat-label">Original</div>
                        <div className="chat-body chat-body--preview">
                          {effectiveSourceText.slice(0, 200)}
                          {effectiveSourceText.length > 200 ? "…" : ""}
                        </div>
                      </button>
                    </div>

                    <div className="chat-row chat-row--user">
                      <div className="chat-bubble chat-bubble--prompt">
                        <span className="chat-bubble-text">
                          {effectiveBaseInstructions || "Initial instructions"}
                        </span>
                      </div>
                    </div>

                    {effectiveDrafts.map((draft) => (
                      <React.Fragment key={draft.version}>
                        {draft.refinePrompt && (
                          <div className="chat-row chat-row--user">
                            <div className="chat-bubble chat-bubble--prompt">
                              <span className="chat-bubble-text">
                                {draft.refinePrompt}
                              </span>
                            </div>
                          </div>
                        )}
                        <div className="chat-row chat-row--bot">
                          <button
                            type="button"
                            className={`chat-bubble chat-bubble--draft ${
                              effectiveSelectedVersion === draft.version
                                ? "chat-bubble--draft-selected"
                                : ""
                            }`}
                            onClick={() =>
                              updateActiveSession((s) => ({
                                ...s,
                                selectedVersion: draft.version,
                              }))
                            }
                          >
                            <div className="chat-label">Draft v{draft.version}</div>
                            <div className="chat-body chat-body--muted">
                              {draft.text.slice(0, 120)}
                              {draft.text.length > 120 ? "…" : ""}
                            </div>
                          </button>
                        </div>
                      </React.Fragment>
                    ))}
                  </div>

                  <div className="results-footer">
                    <div className="results-footer-label">
                      Refine the translation
                    </div>
                    <div className="results-footer-input-row">
                      <textarea
                        className="text-area refine-textarea"
                        placeholder="e.g., Make it more formal, shorten to 300 words..."
                        rows={3}
                        value={refinePrompt}
                        onChange={(e) => setRefinePrompt(e.target.value)}
                      />
                      <button
                        type="button"
                        className="refine-action-button refine-action-button--submit"
                        onClick={handleRefine}
                        disabled={
                          loading ||
                          !refinePrompt.trim() ||
                          effectiveDrafts.length === 0 ||
                          !activeSession
                        }
                        aria-label="Refine translation"
                      >
                        {loading ? (
                          "…"
                        ) : (
                          <>
                            <RefineIcon className="refine-icon" aria-hidden />
                            Refine
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </section>

              <section className="results-column" data-column="preview">
                <div className="results-card">
                  <div className="results-draft-label">
                    {effectiveSelectedVersion === 0
                      ? "Original"
                      : effectiveSelectedVersion != null
                      ? `Draft v${effectiveSelectedVersion}`
                      : "Select a draft"}
                  </div>
                  <div className="results-preview">
                    <pre className="results-preview-text">
                      {currentDraftText ||
                        "[Translated Content]\n\nSelect a draft or refine to see content."}
                    </pre>
                  </div>
                  <div className="results-voice-row">
                    <label htmlFor="tts-voice" className="results-voice-label">
                      Voice for audio
                    </label>
                    <select
                      id="tts-voice"
                      className="results-voice-select"
                      value={selectedVoiceId}
                      onChange={(e) => setSelectedVoiceId(e.target.value)}
                      aria-label="Select voice for text-to-speech"
                    >
                      {TTS_VOICES.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="results-download-row">
                    <button
                      type="button"
                      className="results-download-button"
                      onClick={handleCopyDraft}
                      disabled={!currentDraftText}
                      title="Copy to clipboard"
                    >
                      <CopyIcon className="results-download-icon" aria-hidden />
                      <span>{copySuccess ? "Copied!" : "Copy"}</span>
                    </button>
                    <button
                      type="button"
                      className="results-download-button"
                      onClick={handleDownloadPdf}
                      disabled={!currentDraftText}
                      title="Download as PDF"
                    >
                      <DownloadIcon className="results-download-icon" aria-hidden />
                      <span>PDF</span>
                    </button>
                    <button
                      type="button"
                      className="results-download-button"
                      onClick={handleDownloadAudio}
                      disabled={!currentDraftText || audioLoading}
                      title="Download as audio (MP3)"
                    >
                      <DownloadIcon className="results-download-icon" aria-hidden />
                      <span>{audioLoading ? "…" : "Audio"}</span>
                    </button>
                    <button
                      type="button"
                      className="results-download-button"
                      onClick={handlePlayAudio}
                      disabled={!currentDraftText || audioLoading}
                      title="Play audio"
                    >
                      <PlayIcon className="results-download-icon" aria-hidden />
                      <span>{audioLoading ? "…" : "Play"}</span>
                    </button>
                  </div>
                  <audio
                    ref={audioRef}
                    src={audioObjectUrl ?? undefined}
                    style={{ display: "none" }}
                    aria-hidden
                  />
                </div>
              </section>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default App;