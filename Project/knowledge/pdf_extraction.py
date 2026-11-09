"""Strict text extraction for the clearance policy PDFs."""
from pathlib import Path
import re

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency is declared by the project
    PdfReader = None


def extract_text_from_directory(directory):
    if PdfReader is None:
        raise ImportError("pypdf is required to extract policy documents")
    root = Path(directory)
    documents = []
    for path in sorted(root.iterdir(), key=lambda p: p.name):
        if path.suffix.lower() != ".pdf":
            continue
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            text = re.sub(r"[\x00-\x08\x0e-\x1f\x7f]", "", text).strip()
            if not text:
                raise ValueError(f"PDF page has no usable text: {path.name}")
            pages.append(text)
        if not pages:
            raise ValueError(f"PDF has no pages: {path.name}")
        documents.append({"document_name": path.name, "document_text": "\n".join(pages)})
    return documents