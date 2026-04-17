#!/usr/bin/env python3
"""
Setup inicial de Supabase para Mentor by EgeAI.
Ejecutar una vez: python scripts/setup_supabase.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_supabase_admin
from core.config import settings


def create_tables():
    """Crea todas las tablas necesarias en Supabase."""
    client = get_supabase_admin()
    
    # El SQL de arriba ejecutado via rpc o directamente
    # Supabase permite ejecutar SQL raw via la API de management
    # O se puede hacer desde el dashboard SQL Editor
    # Para este ejemplo, imprimiremos el SQL para copiar/pegar
    
    sql_statements = [
        # Incluir cada CREATE TABLE como string
    ]
    
    # Ejecutar cada statement
    for sql in sql_statements:
        try:
            client.postgrest.rpc('exec_sql', {'query': sql}).execute()
            # O alternativamente, dar instrucciones para ejecutar 
            # desde el Supabase Dashboard > SQL Editor
        except Exception as e:
            print(f"Nota: {e}")
    
    print("Tablas creadas correctamente")


def verify_tables():
    """Verifica que las tablas existen."""
    client = get_supabase_admin()
    
    tables = ['conversations', 'learned_knowledge', 'incidents', 
              'feedback', 'users_config']
    
    for table in tables:
        try:
            result = client.table(table).select("*").limit(1).execute()
            print(f"  ✅ {table}")
        except Exception as e:
            print(f"  ❌ {table}: {e}")


SQL_COMPLETE = """
-- Conversaciones
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

CREATE INDEX IF NOT EXISTS idx_conversations_session 
    ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user 
    ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created 
    ON conversations(created_at DESC);

-- Conocimiento aprendido
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

CREATE INDEX IF NOT EXISTS idx_knowledge_category 
    ON learned_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_status 
    ON learned_knowledge(validation_status);
CREATE INDEX IF NOT EXISTS idx_knowledge_confidence 
    ON learned_knowledge(confidence DESC);

-- Incidencias
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reported_by TEXT NOT NULL,
    project_id TEXT,
    category TEXT NOT NULL,
    problem_type TEXT,
    description TEXT NOT NULL,
    solution_applied TEXT,
    solution_effective BOOLEAN,
    severity TEXT DEFAULT 'media' 
        CHECK (severity IN ('baja', 'media', 'alta', 'critica')),
    status TEXT DEFAULT 'abierta' 
        CHECK (status IN ('abierta', 'en_proceso', 'resuelta', 'cerrada')),
    location TEXT,
    photos TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_incidents_category 
    ON incidents(category);
CREATE INDEX IF NOT EXISTS idx_incidents_status 
    ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_project 
    ON incidents(project_id);

-- Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    is_positive BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_conversation 
    ON feedback(conversation_id);

-- Configuración de usuarios
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

-- Vista útil: conocimiento aprobado con stats
CREATE OR REPLACE VIEW knowledge_approved AS
SELECT 
    lk.*,
    COUNT(DISTINCT c.id) as times_referenced
FROM learned_knowledge lk
LEFT JOIN conversations c ON c.sources_used::text LIKE '%' || lk.id::text || '%'
WHERE lk.validation_status = 'approved'
GROUP BY lk.id;

-- Vista útil: resumen de incidencias por categoría
CREATE OR REPLACE VIEW incidents_summary AS
SELECT 
    category,
    problem_type,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'resuelta') as resueltas,
    COUNT(*) FILTER (WHERE solution_effective = true) as efectivas
FROM incidents
GROUP BY category, problem_type
ORDER BY total DESC;
"""


if __name__ == "__main__":
    print("=" * 50)
    print("Mentor by EgeAI - Setup Supabase")
    print("=" * 50)

    print("\nINSTRUCCIONES:")
    print("1. Ve a tu proyecto en https://app.supabase.com")
    print("2. Abre SQL Editor")
    print("3. Copia y ejecuta el SQL que se muestra a continuacion")
    print("4. Vuelve aqui y ejecuta la verificacion")

    print("\n" + "=" * 50)
    print("SQL A EJECUTAR EN SUPABASE:")
    print("=" * 50)
    
    # Imprimir el SQL completo
    print(SQL_COMPLETE)
    
    print("\n" + "=" * 50)
    input("\nPresiona Enter después de ejecutar el SQL en Supabase...")
    
    print("\nVerificando tablas...")
    verify_tables()