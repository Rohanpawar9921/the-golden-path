import re
from config import config

def split_documents_into_sections(documents):
    sections = []
    heading = re.compile(config.SECTION_HEADING_PATTERN)
    header = re.compile(config.DOCUMENT_HEADER_PATTERN, re.I | re.S)
    for document in documents:
        text = re.sub(config.CONTROL_CHARACTER_PATTERN, "", document["document_text"])
        if not (header.search(text) and len(header.findall(text)) == 1):
            raise ValueError("missing or repeated document header")
        if not (heading.search(text) and heading.search(text).group(1) == "1"):
            raise ValueError("malformed document sections")
        cleaned = header.sub("", text)
        matches = list(heading.finditer(cleaned))
        if not matches or matches[0].group(1) != "1":
            raise ValueError("malformed document header")
        for i, match in enumerate(matches):
            part = cleaned[match.start():matches[i + 1].start() if i + 1 < len(matches) else None]
            part = re.sub(r"\s+", " ", part).strip()
            if part:
                sections.append({"document_name": document["document_name"],
                                 "section_number": int(match.group(1)), "section_text": part})
    return sections

def _chunks(text, size, overlap):
    if len(text) <= size: return [text]
    result, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = max(text.rfind(" ", start, end), text.rfind(". ", start, end))
            if boundary > start + size // 2: end = boundary + 1
        result.append(text[start:end].strip())
        if end >= len(text): break
        start = max(start + 1, end - overlap)
    return result

def build_chunk_records(sections):
    records = []
    for section in sections:
        for index, text in enumerate(_chunks(section["section_text"], config.CHUNK_SIZE_CHARACTERS,
                                              config.CHUNK_OVERLAP_CHARACTERS)):
            records.append({"chunk_id": f"{section['document_name']}-{section['section_number']}-{index}",
                            "chunk_text": text, "document_name": section["document_name"]})
    return records