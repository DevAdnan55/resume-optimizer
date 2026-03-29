from __future__ import annotations

import os
import pathlib

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"

_WKHTMLTOPDF_PATHS = [
    r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
    r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
]

_PDFKIT_OPTIONS = {
    "page-size": "A4",
    "encoding": "UTF-8",
    "no-outline": None,
    "quiet": "",
}


def _get_pdfkit_config():
    try:
        import pdfkit as _pdfkit
    except ImportError:
        raise RuntimeError(
            "pdfkit is not installed. Run: pip install pdfkit"
        )
    if os.name == "nt":
        for path in _WKHTMLTOPDF_PATHS:
            if os.path.isfile(path):
                return _pdfkit.configuration(wkhtmltopdf=path), _pdfkit
        raise RuntimeError(
            "wkhtmltopdf not found. Download and install it from "
            "https://wkhtmltopdf.org/downloads.html\n"
            "Expected location: C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
        )
    return None, _pdfkit  # Linux/macOS: auto-detect via PATH


def _build_context(optimization_result: dict) -> dict:
    # Normalise contact — ensure it is always a dict with all expected keys
    raw_contact = optimization_result.get("contact") or {}
    contact = {
        "phone":    raw_contact.get("phone", "").strip(),
        "email":    raw_contact.get("email", "").strip(),
        "location": raw_contact.get("location", "").strip(),
        "linkedin": raw_contact.get("linkedin", "").strip(),
        "github":   raw_contact.get("github", "").strip(),
    }
    return {
        "name":           optimization_result.get("name", ""),
        "contact":        contact,
        "summary":        optimization_result.get("summary", ""),
        "experience":     optimization_result.get("experience", ""),
        "education":      optimization_result.get("education", ""),
        "projects":       optimization_result.get("projects", ""),
        "skills":         optimization_result.get("skills", ""),
        "keywords_added": optimization_result.get("keywords_added", []),
    }


def generate_pdf(optimization_result: dict) -> bytes:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("resume.html")
    html = template.render(**_build_context(optimization_result))

    try:
        config, pdfkit = _get_pdfkit_config()
    except RuntimeError:
        raise

    try:
        pdf_bytes = pdfkit.from_string(
            html,
            False,
            options=_PDFKIT_OPTIONS,
            configuration=config,
        )
    except OSError as exc:
        raise RuntimeError(
            f"pdfkit failed to generate PDF. "
            f"Ensure wkhtmltopdf is installed correctly. Detail: {exc}"
        ) from exc

    return pdf_bytes
