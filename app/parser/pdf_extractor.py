import re
import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()

    raw = "\n\n".join(pages)
    # Collapse 3+ consecutive newlines to 2
    cleaned = re.sub(r"\n{3,}", "\n\n", raw).strip()

    if not cleaned:
        raise ValueError(
            "This PDF appears to be scanned or image-based. "
            "Text extraction requires a text-based PDF."
        )

    return cleaned
