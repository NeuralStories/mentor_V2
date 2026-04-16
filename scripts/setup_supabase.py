#!/usr/bin/env python3
"""
Setup inicial de Supabase para CarpinteroAI.
Muestra el SQL necesario para crear las tablas y verifica su existencia.
"""
import sys
import os

# Añadir el directorio raíz al path para poder importar core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_supabase_admin
from core.config import settings

SQL_COMPLETE = """
-- 1. Conversaciones
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    user_role TEXT NOT NULL DEFAULT 'general',
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    intent TEXT DEFAULT 'general',
    context JSONB DEFAULT '{}',
    sources_used JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at DESC);

-- 2. Conocimiento aprendido
CREATE TABLE IF NOT EXISTS learned_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT DEFAULT 'general',
    source_type TEXT DEFAULT 'conversation',
    source_conversation_id UUID REFERENCES conversations(id),
    confidence FLOAT DEFAULT 0.5,
    validation_status TEXT DEFAULT 'pending' 
        CHECK (validation_status IN ('pending', 'approved', 'rejected')),
    validated_by TEXT,
    tags TEXT[] DEFAULT '{}',
    usage_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    validated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON learned_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_status ON learned_knowledge(validation_status);

-- 3. Incidencias
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reported_by TEXT NOT NULL,
    project_id TEXT,
    category TEXT NOT NULL,
    problem_type TEXT,
    description TEXT NOT NULL,
    solution_applied TEXT,
    solution_effective BOOLEAN,
    severity TEXT DEFAULT 'media' CHECK (severity IN ('baja', 'media', 'alta', 'critica')),
    status TEXT DEFAULT 'abierta' CHECK (status IN ('abierta', 'en_proceso', 'resuelta', 'cerrada')),
    location TEXT,
    photos TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_project ON incidents(project_id);

-- 4. Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    is_positive BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Configuración de usuarios
CREATE TABLE IF NOT EXISTS users_config (
    user_id TEXT PRIMARY KEY,
    display_name TEXT,
    default_role TEXT DEFAULT 'general',
    default_location TEXT DEFAULT 'taller',
    current_project TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""

def verify_tables():
    """Verifica que las tablas existen en Supabase."""
    client = get_supabase_admin()
    tables = ['conversations', 'learned_knowledge', 'incidents', 'feedback', 'users_config']
    
    print("\nVerificando conexión y tablas...")
    for table in tables:
        try:
            # Intentamos una consulta simple que fallará si la tabla no existe
            client.table(table).select("*").limit(1).execute()
            print(f"  ✅ {table}: OK")
        except Exception as e:
            print(f"  ❌ {table}: Error o no existe ({e})")

if __name__ == "__main__":
    print("=" * 60)
    print("CarpinteroAI - Setup de Base de Datos (Supabase)")
    print("=" * 60)
    
    print("\n📋 INSTRUCCIONES:")
    print("1. Ve a tu proyecto en https://app.supabase.com")
    print("2. Abre el 'SQL Editor'")
    print("3. Crea una 'New Query' y pega el siguiente SQL:")
    
    print("\n" + "-" * 20 + " COPIAR DESDE AQUÍ " + "-" * 20)
    print(SQL_COMPLETE)
    print("-" * 59)
    
    input("\nPresiona Enter después de haber ejecutado el SQL en Supabase...")
    
    verify_tables()
