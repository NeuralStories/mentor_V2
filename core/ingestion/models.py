"""
Modelos de dominio de la ingestión.
"""
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class IngestionStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    OCR = "ocr"
    CHUNKING = "chunking"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


ParserName = Literal[
    "pymupdf",
    "pymupdf+ocr",
    "tesseract",
    "docx",
    "markdown",
    "txt",
]


class IngestionRecord(BaseModel):
    file_id: str
    sha256: str
    filename: str
    mime: str = ""
    file_format: str
    size_bytes: int
    storage_path: Optional[str] = None
    collection: str = "procedimientos"
    pages: Optional[int] = None
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    parser: Optional[ParserName] = None
    ocr_used: bool = False
    ocr_pages: Optional[int] = None
    chunks: Optional[int] = None
    status: IngestionStatus = IngestionStatus.UPLOADED
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
