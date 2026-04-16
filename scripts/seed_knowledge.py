#!/usr/bin/env python3
"""Script para indexar el conocimiento base inicial en ChromaDB."""
import sys
import os
import time

# Añadir raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag.indexer import KnowledgeIndexer
from core.llm.provider import LLMProvider

def main():
    print("🚀 Iniciando siembra de conocimiento (Seed)...")
    
    # 1. Verificar Ollama
    if not LLMProvider.check_ollama():
        print("❌ Error: Ollama no detectado. Asegúrate de que 'ollama serve' esté ejecutándose.")
        return

    # 2. Indexar
    indexer = KnowledgeIndexer()
    try:
        print("📂 Procesando archivos MD en knowledge_base/...")
        indexer.index_all()
        print("✅ Indexación completada con éxito.")
    except Exception as e:
        print(f"❌ Error durante la indexación: {e}")

if __name__ == "__main__":
    main()
