import asyncio
from src.core.engine import MentorEngine
from src.core.worker_context import WorkerProfile

async def main():
    print("Iniciando MENTOR Engine - Demo de Interacción")
    engine = MentorEngine()
    
    # 1. Cargar Base de Conocimiento
    count = engine.kb.load_from_json('data/knowledge_base.json')
    print(f"\n[+] {count} documentos cargados en la KB.")
    
    # 2. Registrar Trabajador de Prueba
    worker = WorkerProfile(
        worker_id="demo-user-1",
        name="Carlos Empleado",
        department="ventas",
        role="ejecutivo",
        location="Oficina Central"
    )
    engine.register_worker(worker)
    print(f"[+] Trabajador '{worker.name}' registrado exitosamente.\n")
    
    # 3. Prueba de Consulta 1 (Pregunta de RRHH)
    query_1 = "¿Cuántos días de vacaciones me tocan si llevo 3 años trabajando?"
    print(f"[Usuario]: Trabajador: {query_1}")
    response_1 = await engine.handle_query(query_1, worker_id="demo-user-1")
    print(f"[Agente]: MENTOR (Estrategia: {response_1.strategy_used}):\n   {response_1.content}")
    print(f"   [Latencia: {response_1.latency_ms}ms, Fuentes: {response_1.sources_used}]\n")
    
    # 4. Prueba de Consulta 2 (Directa para forzar escalamiento)
    query_2 = "Necesito reportar a alguien del equipo por acoso, esto es muy grave."
    print(f"[Usuario]: Trabajador: {query_2}")
    response_2 = await engine.handle_query(query_2, worker_id="demo-user-1")
    print(f"[Agente]: MENTOR (Escalado: {response_2.was_escalated}):\n   {response_2.content}")
    print(f"   [Ticket Creado: {response_2.escalation_ticket}]\n")
    
    # 5. Obtener Estadísticas
    stats = await engine.get_analytics()
    print("[+] Estadísticas Generadas del Motor:")
    print(stats)

if __name__ == "__main__":
    asyncio.run(main())
