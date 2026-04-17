import pytest

from tests.conftest import tesseract_available, wait_for_terminal_status

pytestmark = pytest.mark.e2e


def _upload(client, filename: str, data: bytes, mime: str, collection="procedimientos", auto_process=True):
    return client.post(
        "/api/knowledge/upload",
        files={"file": (filename, data, mime)},
        data={"collection": collection, "auto_process": str(auto_process).lower()},
    )


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["supabase"] == "degraded"


def test_pdf_pipeline(client, pdf_native_bytes):
    response = _upload(client, "native.pdf", pdf_native_bytes, "application/pdf")
    assert response.status_code == 200
    record = wait_for_terminal_status(client, response.json()["file_id"])
    assert record["status"] == "ready"
    assert record["parser"] == "pymupdf"


def test_dedup(client, pdf_native_bytes):
    first = _upload(client, "a.pdf", pdf_native_bytes, "application/pdf")
    wait_for_terminal_status(client, first.json()["file_id"])
    second = _upload(client, "b.pdf", pdf_native_bytes, "application/pdf")
    assert second.json()["status"] == "duplicate"


def test_docx_pipeline(client, docx_bytes):
    response = _upload(
        client,
        "manual.docx",
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        collection="materiales",
    )
    record = wait_for_terminal_status(client, response.json()["file_id"])
    assert record["status"] == "ready"
    assert record["collection"] == "materiales"


@pytest.mark.requires_tesseract
@pytest.mark.skipif(not tesseract_available(), reason="tesseract no instalado")
def test_scanned_pdf_pipeline(client, pdf_scanned_bytes, monkeypatch):
    monkeypatch.setenv("OCR_ENABLED", "true")
    from core import config as cfg
    cfg.settings = cfg.Settings()

    response = _upload(client, "scan.pdf", pdf_scanned_bytes, "application/pdf")
    record = wait_for_terminal_status(client, response.json()["file_id"], timeout=90)
    assert record["status"] == "ready"
    assert record["ocr_used"] is True
