# SmartWrite AI

A web workspace that turns handwritten notes, printed pages, or PDFs into
clean, editable text — then fixes spelling, translates, summarizes, and
exports it as a PDF. Built with Streamlit.

## Features

| Feature | How it works |
|---|---|
| OCR | Tesseract (`pytesseract`) for images; PyMuPDF reads a PDF's existing text layer directly, or rasterizes + OCRs pages that have none (scanned/handwritten PDFs) |
| Spell correction | `pyspellchecker` — offline, dictionary/edit-distance based |
| Summarization | Extractive TextRank (TF-IDF + PageRank over sentences via `scikit-learn` + `networkx`) — fully offline, no model download |
| Translation | `deep-translator`'s GoogleTranslator (free, no API key) — 9 languages |
| PDF export | `fpdf2`, styled to match the app |

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Needs a system Tesseract install for OCR:
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: install from the [UB-Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki), add it to PATH

Everything else installs via `pip`.

## Project structure

```
smartwrite_ai/
├── app.py              # Streamlit UI — hero, upload, tabs (Editor/Translate/Summarize/Export)
├── utils/
│   ├── ocr.py           # image + PDF text extraction
│   ├── corrector.py      # offline spell correction
│   ├── summarizer.py      # extractive TextRank summarization
│   ├── translator.py       # Google Translate wrapper + fallback handling
│   └── pdf_export.py        # styled PDF generation
├── assets/
│   └── style.css          # black + neon-green glassmorphism theme
└── requirements.txt
```

## A note on the translation feature

Live translation calls `translate.google.com`, so it needs normal outbound
internet access — it works fine on a laptop, a college wifi, or any
standard deployment (Streamlit Community Cloud, Render, etc.).

This project was built inside a sandboxed dev environment with a locked-down
network allowlist that blocks `translate.google.com` (and also blocks
`argos-net.com`, the model host for the offline alternative, `argos-translate`
— tested and confirmed during development). So the translation code path
couldn't be live-tested there. To keep that honest instead of hiding it,
`translator.py` catches any connection failure and raises a clear
`TranslationUnavailable` error, which the UI shows as a plain message rather
than silently failing. On a normal machine this fallback path simply never
triggers.

If you want translation to work fully offline (e.g. for a demo with no
wifi), swap in `argos-translate`: install it, download the language pair
once while you have internet (`argostranslate.package`), and it translates
with no network at all afterward.

## Possible extensions

- Swap extractive summarization for an abstractive transformer summarizer
  (`transformers.pipeline("summarization")`) if you have model-download
  access and want tighter, rephrased summaries.
- Add a grammar checker (`language_tool_python`) alongside spell correction
  for sentence-level fixes, not just word-level.
- Persist uploads/exports to a database for a "history" tab.
