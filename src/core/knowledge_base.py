from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum
import json
import hashlib


class DocumentType(str, Enum):
    POLICY = "policy"
    SOP = "sop"
    FAQ = "faq"
    MANUAL = "manual"
    FORM_GUIDE = "form_guide"
    CONTACT_DIR = "contact_directory"
    ANNOUNCEMENT = "announcement"
    REGULATION = "regulation"


@dataclass
class KBDocument:
    doc_id: str
    title: str
    content: str
    doc_type: DocumentType
    department: str = ""
    tags: list[str] = field(default_factory=list)
    version: str = "1.0"
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    last_updated: Optional[str] = None
    approved_by: str = ""
    access_level: str = "all"
    language: str = "es"

    @property
    def is_expired(self) -> bool:
        if not self.expiration_date:
            return False
        try:
            exp = datetime.fromisoformat(self.expiration_date)
            return datetime.utcnow() > exp
        except ValueError:
            return False


@dataclass
class SearchResult:
    documents: list[KBDocument]
    context: str
    relevance_scores: list[float]
    total_found: int


class KnowledgeBase:
    def __init__(self, vector_store=None):
        self._documents: dict[str, KBDocument] = {}
        self._tag_index: dict[str, list[str]] = {}
        self._dept_index: dict[str, list[str]] = {}
        self._type_index: dict[str, list[str]] = {}
        self._vector_store = vector_store

    def add_document(self, doc: KBDocument) -> str:
        if not doc.doc_id:
            doc.doc_id = hashlib.md5(f"{doc.title}{doc.content[:100]}".encode()).hexdigest()[:12]
        self._documents[doc.doc_id] = doc

        for tag in doc.tags:
            tag_lower = tag.lower()
            if tag_lower not in self._tag_index:
                self._tag_index[tag_lower] = []
            self._tag_index[tag_lower].append(doc.doc_id)

        if doc.department:
            dept = doc.department.lower()
            if dept not in self._dept_index:
                self._dept_index[dept] = []
            self._dept_index[dept].append(doc.doc_id)

        doc_type = doc.doc_type.value
        if doc_type not in self._type_index:
            self._type_index[doc_type] = []
        self._type_index[doc_type].append(doc.doc_id)

        return doc.doc_id

    async def search(self, query: str, category: str = "", department: str = "", doc_type: str = "", max_results: int = 5, access_level: str = "all") -> SearchResult:
        return self._keyword_search(query, category, department, doc_type, max_results, access_level)

    def _keyword_search(self, query: str, category: str, department: str, doc_type: str, max_results: int, access_level: str) -> SearchResult:
        query_words = set(query.lower().split())
        scored_docs = []
        candidates = set(self._documents.keys())

        if department:
            dept_docs = set(self._dept_index.get(department.lower(), []))
            if dept_docs:
                candidates &= dept_docs

        if doc_type:
            type_docs = set(self._type_index.get(doc_type, []))
            if type_docs:
                candidates &= type_docs

        for doc_id in candidates:
            doc = self._documents[doc_id]
            if doc.is_expired:
                continue
            if not self._check_access(doc, access_level):
                continue

            doc_text = f"{doc.title} {doc.content} {' '.join(doc.tags)}".lower()
            doc_words = set(doc_text.split())
            matches = query_words & doc_words
            if matches:
                score = len(matches) / len(query_words)
                title_words = set(doc.title.lower().split())
                title_matches = query_words & title_words
                score += len(title_matches) * 0.3
                scored_docs.append((doc, min(score, 1.0)))

        scored_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = scored_docs[:max_results]
        documents = [d[0] for d in top_docs]
        scores = [d[1] for d in top_docs]

        context_parts = []
        for doc in documents:
            context_parts.append(
                f"[{doc.doc_type.value.upper()}] {doc.title}\n"
                f"Departamento: {doc.department}\n"
                f"Versión: {doc.version} | Última actualización: {doc.last_updated or 'N/A'}\n"
                f"---\n{doc.content}\n"
            )

        return SearchResult(
            documents=documents,
            context="\n\n".join(context_parts),
            relevance_scores=scores,
            total_found=len(documents),
        )

    def _check_access(self, doc: KBDocument, access_level: str) -> bool:
        if doc.access_level == "all":
            return True
        if access_level == "admin":
            return True
        return doc.access_level == access_level

    def load_from_json(self, filepath: str) -> int:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        for item in data:
            doc = KBDocument(
                doc_id=item.get("id", ""),
                title=item["title"],
                content=item["content"],
                doc_type=DocumentType(item.get("type", "faq")),
                department=item.get("department", ""),
                tags=item.get("tags", []),
                version=item.get("version", "1.0"),
                effective_date=item.get("effective_date"),
                expiration_date=item.get("expiration_date"),
                last_updated=item.get("last_updated"),
                approved_by=item.get("approved_by", ""),
                access_level=item.get("access_level", "all"),
            )
            self.add_document(doc)
            count += 1
        return count

    def get_stats(self) -> dict:
        type_counts = {}
        for doc in self._documents.values():
            t = doc.doc_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        expired = sum(1 for d in self._documents.values() if d.is_expired)
        return {
            "total_documents": len(self._documents),
            "by_type": type_counts,
            "departments": list(self._dept_index.keys()),
            "expired_documents": expired,
            "total_tags": len(self._tag_index),
        }
