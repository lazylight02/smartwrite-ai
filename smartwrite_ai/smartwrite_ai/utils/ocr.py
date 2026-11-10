"""
OCR utilities for SmartWrite AI.

Images  -> Tesseract OCR (via pytesseract)
PDFs    -> text layer read directly with PyMuPDF when present,
           otherwise each page is rendered to an image and OCR'd
           the same way as a photo (handles scanned/handwritten PDFs).
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pytesseract
from PIL import Image

try:
    import pymupdf as fitz  # PyMuPDF (new import name; falls back to legacy alias)
except ImportError:  # pragma: no cover
    try:
        import fitz
    except ImportError:
        fitz = None


@dataclass
class OCRResult:
    text: str
    confidence: float  # 0-100, average word confidence
    pages: int = 1


def _ocr_image(image: Image.Image) -> OCRResult:
    """Run Tesseract on a single PIL image and return text + confidence."""
    # Upscale small images a little — Tesseract does noticeably better
    # above ~300dpi-equivalent, which matters for phone photos of notes.
    if max(image.size) < 1200:
        scale = 1200 / max(image.size)
        image = image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.LANCZOS,
        )

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words = [w for w in data["text"] if w.strip()]
    confs = [float(c) for c, w in zip(data["conf"], data["text"]) if w.strip() and float(c) >= 0]

    text = " ".join(words)
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    return OCRResult(text=text, confidence=avg_conf, pages=1)


def extract_from_image(file_bytes: bytes) -> OCRResult:
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    return _ocr_image(image)


def extract_from_pdf(file_bytes: bytes, force_ocr: bool = False) -> OCRResult:
    """
    Extract text from a PDF. If the PDF already has a text layer (typed
    PDFs, most exported documents) we read it directly — instant and
    perfectly accurate. If it doesn't (scanned or handwritten pages),
    or force_ocr=True, we rasterize each page and OCR it like a photo.
    """
    if fitz is None:
        raise RuntimeError("PyMuPDF is not installed — add pymupdf to requirements.txt")

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = doc.page_count

    if not force_ocr:
        text_layer = "\n\n".join(page.get_text().strip() for page in doc)
        if len(text_layer.strip()) > 20:  # a real text layer exists
            return OCRResult(text=text_layer, confidence=100.0, pages=page_count)

    # No usable text layer -> OCR each page as an image
    texts, confs = [], []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        result = _ocr_image(img)
        texts.append(result.text)
        confs.append(result.confidence)

    return OCRResult(
        text="\n\n".join(texts),
        confidence=sum(confs) / len(confs) if confs else 0.0,
        pages=page_count,
    )


def extract(file_bytes: bytes, filename: str) -> OCRResult:
    """Dispatch to the right extractor based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return extract_from_pdf(file_bytes)
    if ext in {"png", "jpg", "jpeg", "bmp", "tiff", "webp"}:
        return extract_from_image(file_bytes)
    raise ValueError(f"Unsupported file type: .{ext}")
