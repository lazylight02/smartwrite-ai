"""
SmartWrite AI — handwriting/document OCR, correction, translation and
summarization in one workspace.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils import corrector, ocr, pdf_export, summarizer, translator

# ----------------------------------------------------------------- setup
st.set_page_config(
    page_title="SmartWrite AI",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS_PATH = Path(__file__).parent / "assets" / "style.css"
st.markdown(f"<style>{CSS_PATH.read_text()}</style>", unsafe_allow_html=True)

for key, default in {
    "working_text": "",
    "original_text": "",
    "source_filename": "",
    "ocr_confidence": None,
    "last_action": None,
}.items():
    st.session_state.setdefault(key, default)


# ----------------------------------------------------------------- hero
st.markdown(
    """
    <div class="sw-hero">
      <div class="sw-hero-eyebrow"><span class="dot"></span>Handwriting & document workspace</div>
      <h1>Turn handwriting and scans into clean, usable text.</h1>
      <p>Upload a photo of notes or a PDF, and SmartWrite AI pulls out the text, fixes
      spelling, translates it, and condenses it to a summary — ready to export.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

FEATURES = [
    ("📝", "OCR extraction", "Reads handwriting, printed notes, and scanned or typed PDFs."),
    ("🩹", "Spell correction", "Offline, dictionary-based cleanup — works without internet."),
    ("🌐", "Translation", "Carries your text into 9 languages via Google Translate."),
    ("📄", "PDF export", "Download the finished text as a formatted PDF."),
]
st.markdown(
    '<div class="sw-feature-grid">'
    + "".join(
        f'<div class="sw-card"><span class="icon">{icon}</span>'
        f'<div class="title">{title}</div><div class="desc">{desc}</div></div>'
        for icon, title, desc in FEATURES
    )
    + "</div>",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- upload
st.markdown('<div class="sw-panel">', unsafe_allow_html=True)
uploaded = st.file_uploader(
    "Upload a photo of handwritten/printed notes, or a PDF",
    type=["png", "jpg", "jpeg", "bmp", "tiff", "webp", "pdf"],
)

if uploaded is not None and uploaded.name != st.session_state["source_filename"]:
    with st.spinner("Reading your document..."):
        try:
            result = ocr.extract(uploaded.getvalue(), uploaded.name)
            st.session_state["working_text"] = result.text
            st.session_state["original_text"] = result.text
            st.session_state["source_filename"] = uploaded.name
            st.session_state["ocr_confidence"] = result.confidence
        except Exception as e:
            st.error(f"Couldn't read that file: {e}")

if st.session_state["ocr_confidence"] is not None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Source", st.session_state["source_filename"] or "—")
    c2.metric("OCR confidence", f"{st.session_state['ocr_confidence']:.0f}%")
    c3.metric("Words extracted", len(st.session_state["original_text"].split()))
st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------- workspace
if not st.session_state["working_text"]:
    st.info("Upload a file above to get started — or paste text directly in the Editor tab below.")

tab_editor, tab_translate, tab_summarize, tab_export = st.tabs(
    ["✏️ Editor", "🌐 Translate", "🧠 Summarize", "⬇️ Export"]
)

with tab_editor:
    st.markdown('<div class="sw-panel">', unsafe_allow_html=True)
    text = st.text_area(
        "Working text", value=st.session_state["working_text"], height=320, label_visibility="collapsed"
    )
    st.session_state["working_text"] = text

    col_fix, col_reset, _ = st.columns([1, 1, 3])
    if col_fix.button("Fix spelling", use_container_width=True):
        with st.spinner("Checking spelling..."):
            res = corrector.correct_text(st.session_state["working_text"])
        st.session_state["working_text"] = res.corrected_text
        if res.count:
            st.success(f"Fixed {res.count} word(s). " + ", ".join(f"{c.original}→{c.suggestion}" for c in res.corrections[:8]))
        else:
            st.success("No spelling issues found.")
        st.rerun()

    if col_reset.button("Reset to original", use_container_width=True):
        st.session_state["working_text"] = st.session_state["original_text"]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with tab_translate:
    st.markdown('<div class="sw-panel">', unsafe_allow_html=True)
    col_lang, col_btn = st.columns([2, 1])
    target_lang_name = col_lang.selectbox("Translate to", list(translator.LANGUAGES.keys()), index=1)
    col_btn.write("")
    col_btn.write("")
    go = col_btn.button("Translate", use_container_width=True)

    if go:
        with st.spinner(f"Translating to {target_lang_name}..."):
            try:
                result = translator.translate_text(
                    st.session_state["working_text"], translator.LANGUAGES[target_lang_name]
                )
                st.session_state["translated_text"] = result.translated_text
            except translator.TranslationUnavailable as e:
                st.session_state["translated_text"] = None
                st.warning(
                    "Translation needs outbound internet access to Google Translate, "
                    f"which this environment doesn't have right now.\n\n`{e}`"
                )

    if st.session_state.get("translated_text"):
        st.text_area("Translated text", value=st.session_state["translated_text"], height=240)
        if st.button("Use translation as working text"):
            st.session_state["working_text"] = st.session_state["translated_text"]
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with tab_summarize:
    st.markdown('<div class="sw-panel">', unsafe_allow_html=True)
    ratio = st.slider("Summary length (share of original sentences)", 0.1, 0.7, 0.3, 0.05)
    if st.button("Summarize"):
        with st.spinner("Summarizing..."):
            res = summarizer.summarize(st.session_state["working_text"], ratio=ratio)
        st.session_state["summary_text"] = res.summary
        st.caption(f"{res.sentence_count} of {res.original_sentence_count} sentences kept.")

    if st.session_state.get("summary_text"):
        st.text_area("Summary", value=st.session_state["summary_text"], height=200)
        if st.button("Use summary as working text"):
            st.session_state["working_text"] = st.session_state["summary_text"]
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with tab_export:
    st.markdown('<div class="sw-panel">', unsafe_allow_html=True)
    st.text_area("Final text", value=st.session_state["working_text"], height=240, disabled=True)

    col_pdf, col_txt = st.columns(2)
    if st.session_state["working_text"]:
        pdf_bytes = pdf_export.export_to_pdf(
            st.session_state["working_text"],
            title=f"SmartWrite AI — {st.session_state['source_filename'] or 'Document'}",
        )
        col_pdf.download_button(
            "Download PDF", data=pdf_bytes, file_name="smartwrite_export.pdf", mime="application/pdf", use_container_width=True
        )
        col_txt.download_button(
            "Download .txt",
            data=st.session_state["working_text"],
            file_name="smartwrite_export.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.caption("Nothing to export yet.")
    st.markdown("</div>", unsafe_allow_html=True)
