import re

SECTION_PATTERNS: dict[str, list[str]] = {
    "summary":    ["summary", "objective", "profile", "about me", "about"],
    "experience": ["experience", "employment", "work history", "career history", "work experience"],
    "education":  ["education", "academic", "qualifications", "degrees", "academic background"],
    "projects":   ["projects", "personal projects", "key projects", "notable projects", "portfolio"],
    "skills":     ["skills", "technologies", "technical skills", "competencies", "core competencies"],
}


def _match_section(line: str) -> str | None:
    normalized = line.lower().strip()
    for section, keywords in SECTION_PATTERNS.items():
        for kw in keywords:
            if re.fullmatch(rf"[^a-z]*{re.escape(kw)}[^a-z]*", normalized):
                return section
    return None


def detect_sections(raw_text: str) -> dict[str, str]:
    lines = raw_text.splitlines()
    sections: dict[str, str] = {}
    current_section: str | None = None
    buffer: list[str] = []

    for line in lines:
        # Short lines only can be section headers
        if len(line.strip()) < 50:
            matched = _match_section(line)
            if matched:
                if current_section and buffer:
                    sections[current_section] = "\n".join(buffer).strip()
                current_section = matched
                buffer = []
                continue

        if current_section is not None:
            buffer.append(line)

    if current_section and buffer:
        sections[current_section] = "\n".join(buffer).strip()

    return sections
