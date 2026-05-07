import io
import re

import pdfplumber
from docx import Document

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
MIN_TEXT_LENGTH = 50  # меньше — скорее всего scanned PDF


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Извлекает и нормализует текст из PDF или DOCX файла.

    Args:
        file_bytes: содержимое файла в байтах
        filename: имя файла (используется для определения формата)

    Returns:
        Нормализованный текст CV

    Raises:
        ValueError: если формат не поддерживается или файл нечитаем
    """
    ext = _get_extension(filename)

    if ext == ".pdf":
        text = _extract_from_pdf(file_bytes)
    elif ext == ".docx":
        text = _extract_from_docx(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file format '{ext}'. Please upload a PDF or DOCX file."
        )

    return _normalize(text)


def _get_extension(filename: str) -> str:
    lower = filename.lower()
    for ext in SUPPORTED_EXTENSIONS:
        if lower.endswith(ext):
            return ext
    # вернуть всё после последней точки
    parts = lower.rsplit(".", 1)
    return f".{parts[1]}" if len(parts) == 2 else ""


def _extract_from_pdf(file_bytes: bytes) -> str:
    text_parts: list[str] = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    text = "\n".join(text_parts)

    if len(text.strip()) < MIN_TEXT_LENGTH:
        raise ValueError(
            "CV appears to be a scanned image — please upload a text-based PDF."
        )

    return text


def _extract_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _normalize(text: str) -> str:
    """Убирает лишние пробелы и нормализует переносы строк."""
    # схлопнуть несколько пробелов в один
    text = re.sub(r" {2,}", " ", text)
    # схлопнуть более двух переносов подряд
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
