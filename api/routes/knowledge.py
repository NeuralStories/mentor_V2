from fastapi import APIRouter, HTTPException
from core.supabase_client import get_supabase_admin
from core.rag.indexer import KnowledgeIndexer

router = APIRouter()
indexer = KnowledgeIndexer()

@router.get("/pending")
async def get_pending_knowledge():
    """Obtiene conocimientos extraídos pendientes de validación."""
    supabase = get_supabase_admin()
    res = supabase.table("learned_knowledge")\
        .select("*")\
        .eq("validation_status", "pending")\
        .execute()
    return res.data

@router.post("/validate/{id}")
async def validate_knowledge(id: str, approve: bool):
    """Aprueba o rechaza un conocimiento aprendido."""
    supabase = get_supabase_admin()
    status = "approved" if approve else "rejected"
    
    res = supabase.table("learned_knowledge")\
        .update({"validation_status": status})\
        .eq("id", id)\
        .execute()
    
    # Si se aprueba, indexarlo en ChromaDB inmediatamente
    if approve and res.data:
        item = res.data[0]
        indexer.index_learned_item(
            title=item["title"],
            content=item["content"],
            metadata={"id": id, "category": item["category"]}
        )
        
    return {"status": status}

@router.post("/reindex")
async def trigger_reindex():
    """Fuerza la re-indexación de toda la base de conocimiento."""
    indexer.index_all()
    return {"status": "indexing_started"}
