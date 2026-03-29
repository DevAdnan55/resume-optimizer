from typing import TypedDict

from .pdf_extractor import extract_text_from_pdf
from .docx_extractor import extract_text_from_docx
from .section_detector import detect_sections


class ResumeData(TypedDict):
    raw_text: str
    file_type: str          # "pdf", "docx", or "text"
    sections: dict[str, str]


def parse_resume(file_bytes: bytes, file_type: str) -> ResumeData:
    ft = file_type.lower().lstrip(".")

    if ft == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ft in ("docx", "doc"):
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type: '{ft}'. Please upload a PDF or DOCX file."
        )

    return ResumeData(
        raw_text=raw_text,
        file_type=ft,
        sections=detect_sections(raw_text),
    )


def parse_job_description(text: str) -> ResumeData:
    raw_text = text.strip()
    return ResumeData(
        raw_text=raw_text,
        file_type="text",
        sections=detect_sections(raw_text),
    )
