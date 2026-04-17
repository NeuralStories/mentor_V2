from core.ingestion.models import IngestionRecord, IngestionStatus
from core.ingestion.store import IngestionStore


def _make_rec(**overrides) -> IngestionRecord:
    base = dict(
        file_id="abc123def4567890",
        sha256="abc123def4567890" + "0" * 48,
        filename="doc.pdf",
        file_format="pdf",
        size_bytes=1234,
        collection="procedimientos",
        storage_path="/tmp/doc.pdf",
    )
    base.update(overrides)
    return IngestionRecord(**base)


def test_upsert_and_get(tmp_path):
    store = IngestionStore(tmp_path / "test.sqlite")
    record = _make_rec()
    store.upsert(record)
    assert store.get(record.file_id).file_id == record.file_id


def test_transition_updates_status(tmp_path):
    store = IngestionStore(tmp_path / "test.sqlite")
    store.upsert(_make_rec())
    store.transition("abc123def4567890", IngestionStatus.READY, chunks=3)
    result = store.get("abc123def4567890")
    assert result.status == IngestionStatus.READY
    assert result.chunks == 3
