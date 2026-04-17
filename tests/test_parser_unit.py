import pytest

from core.tools.document_parser import DocumentParser
from tests.conftest import tesseract_available


def test_can_parse_supported():
    assert DocumentParser.can_parse("a.pdf")
    assert DocumentParser.can_parse("a.DOCX")


def test_parse_native_pdf(tmp_path, pdf_native_bytes):
    path = tmp_path / "native.pdf"
    path.write_bytes(pdf_native_bytes)
    content, metadata = DocumentParser.parse_file(path)
    assert metadata["parser"] == "pymupdf"
    assert metadata["ocr_used"] is False
    assert "tarima" in content.lower()


def test_parse_docx(tmp_path, docx_bytes):
    path = tmp_path / "manual.docx"
    path.write_bytes(docx_bytes)
    content, metadata = DocumentParser.parse_file(path)
    assert metadata["parser"] == "docx"
    assert "Tornillos 4x40" in content


@pytest.mark.requires_tesseract
@pytest.mark.skipif(not tesseract_available(), reason="tesseract no instalado")
def test_scanned_pdf_triggers_ocr(tmp_path, pdf_scanned_bytes, monkeypatch):
    monkeypatch.setenv("OCR_ENABLED", "true")
    from core import config as cfg
    cfg.settings = cfg.Settings()

    path = tmp_path / "scan.pdf"
    path.write_bytes(pdf_scanned_bytes)
    content, metadata = DocumentParser.parse_file(path)
    assert metadata["ocr_used"] is True
    assert metadata["parser"] in ("tesseract", "pymupdf+ocr")
    assert content
