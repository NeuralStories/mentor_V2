"""
Almacén persistente de registros de ingestión.
"""
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import IngestionRecord, IngestionStatus


class IngestionStore:
    def __init__(self, db_path: str | Path, supabase=None):
        self.db_path = Path(db_path)
        self.supabase = supabase
        self._lock = threading.RLock()
        self._init()

    def _init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ingestion (
                    file_id TEXT PRIMARY KEY,
                    sha256 TEXT NOT NULL,
                    status TEXT NOT NULL,
                    collection TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS ix_ingestion_sha ON ingestion(sha256)")
            connection.execute("CREATE INDEX IF NOT EXISTS ix_ingestion_status ON ingestion(status)")
            connection.execute("CREATE INDEX IF NOT EXISTS ix_ingestion_collection ON ingestion(collection)")

    def upsert(self, record: IngestionRecord) -> IngestionRecord:
        record.updated_at = datetime.utcnow()
        with self._lock, sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO ingestion
                (file_id, sha256, status, collection, payload, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.file_id,
                    record.sha256,
                    record.status.value,
                    record.collection,
                    record.model_dump_json(),
                    record.updated_at.isoformat(),
                ),
            )
        self._replicate(record)
        return record

    def get(self, file_id: str) -> Optional[IngestionRecord]:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload FROM ingestion WHERE file_id=?",
                (file_id,),
            ).fetchone()
        return IngestionRecord(**json.loads(row[0])) if row else None

    def find_by_sha(self, sha256: str) -> Optional[IngestionRecord]:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload FROM ingestion WHERE sha256=? ORDER BY updated_at DESC LIMIT 1",
                (sha256,),
            ).fetchone()
        return IngestionRecord(**json.loads(row[0])) if row else None

    def list(
        self,
        status: IngestionStatus | None = None,
        collection: str | None = None,
    ) -> list[IngestionRecord]:
        clauses = []
        args: list[str] = []
        if status:
            clauses.append("status=?")
            args.append(status.value)
        if collection:
            clauses.append("collection=?")
            args.append(collection)
        where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""

        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                f"SELECT payload FROM ingestion{where_clause} ORDER BY updated_at DESC",
                args,
            ).fetchall()
        return [IngestionRecord(**json.loads(row[0])) for row in rows]

    def count_by_status(self) -> dict[str, int]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT status, COUNT(*) FROM ingestion GROUP BY status"
            ).fetchall()
        return {status: total for status, total in rows}

    def transition(
        self,
        file_id: str,
        status: IngestionStatus,
        **patch,
    ) -> Optional[IngestionRecord]:
        record = self.get(file_id)
        if not record:
            return None

        data = record.model_dump() | patch | {"status": status}
        return self.upsert(IngestionRecord(**data))

    def delete(self, file_id: str) -> None:
        with self._lock, sqlite3.connect(self.db_path) as connection:
            connection.execute("DELETE FROM ingestion WHERE file_id=?", (file_id,))

        if self.supabase:
            try:
                self.supabase.table("ingestion").delete().eq("file_id", file_id).execute()
            except Exception:
                pass

    def _replicate(self, record: IngestionRecord) -> None:
        if not self.supabase:
            return
        try:
            self.supabase.table("ingestion").upsert(record.model_dump(mode="json")).execute()
        except Exception:
            pass
