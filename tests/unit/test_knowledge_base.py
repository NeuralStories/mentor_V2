import pytest
from src.core.knowledge_base import KnowledgeBase, KBDocument, DocumentType


class TestKnowledgeBase:
    @pytest.mark.asyncio
    async def test_add_and_search(self, knowledge_base):
        results = await knowledge_base.search("vacaciones días")
        assert results.total_found >= 1
        assert "Vacaciones" in results.documents[0].title

    @pytest.mark.asyncio
    async def test_search_by_department(self, knowledge_base):
        results = await knowledge_base.search("contraseña", department="ti")
        assert results.total_found >= 1
        assert results.documents[0].department == "ti"

    @pytest.mark.asyncio
    async def test_search_no_results(self, knowledge_base):
        results = await knowledge_base.search("xyz123nonexistent")
        assert results.total_found == 0

    @pytest.mark.asyncio
    async def test_expired_excluded(self, knowledge_base):
        knowledge_base.add_document(KBDocument(
            doc_id="expired-001", title="Política Antigua",
            content="Esta política ya expiró con vacaciones",
            doc_type=DocumentType.POLICY, department="rrhh",
            tags=["vacaciones"], expiration_date="2020-01-01",
        ))
        results = await knowledge_base.search("política antigua vacaciones expiró")
        assert not any(d.doc_id == "expired-001" for d in results.documents)

    @pytest.mark.asyncio
    async def test_access_filtering(self, knowledge_base):
        knowledge_base.add_document(KBDocument(
            doc_id="restricted-001", title="Salarios Ejecutivos",
            content="Tabla de salarios confidencial",
            doc_type=DocumentType.POLICY, department="rrhh", access_level="hr_only",
        ))
        results_all = await knowledge_base.search("salarios", access_level="all")
        assert not any(d.doc_id == "restricted-001" for d in results_all.documents)
        results_hr = await knowledge_base.search("salarios", access_level="hr_only")
        assert any(d.doc_id == "restricted-001" for d in results_hr.documents)

    def test_stats(self, knowledge_base):
        stats = knowledge_base.get_stats()
        assert stats["total_documents"] >= 3
