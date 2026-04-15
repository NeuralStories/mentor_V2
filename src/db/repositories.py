from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models import DBWorkerProfile, DBEscalationTicket
from src.core.worker_context import WorkerProfile

class WorkerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, worker_id: str) -> WorkerProfile | None:
        result = await self.session.execute(select(DBWorkerProfile).where(DBWorkerProfile.worker_id == worker_id))
        db_worker = result.scalars().first()
        if db_worker:
            return WorkerProfile(
                worker_id=db_worker.worker_id,
                name=db_worker.name,
                department=db_worker.department,
                role=db_worker.role,
                location=db_worker.location,
                hire_date=db_worker.hire_date,
                manager=db_worker.manager,
                access_level=db_worker.access_level
            )
        return None

    async def save(self, worker: WorkerProfile) -> None:
        db_worker = await self.session.get(DBWorkerProfile, worker.worker_id)
        if db_worker:
            db_worker.name = worker.name
            db_worker.department = worker.department
            db_worker.role = worker.role
            db_worker.location = worker.location
            db_worker.hire_date = worker.hire_date
            db_worker.manager = worker.manager
            db_worker.access_level = worker.access_level
        else:
            db_worker = DBWorkerProfile(
                worker_id=worker.worker_id,
                name=worker.name,
                department=worker.department,
                role=worker.role,
                location=worker.location,
                hire_date=worker.hire_date,
                manager=worker.manager,
                access_level=worker.access_level
            )
            self.session.add(db_worker)
        await self.session.commit()

class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, ticket) -> None:
        db_ticket = DBEscalationTicket(
            ticket_id=ticket.ticket_id,
            worker_id=ticket.worker_id,
            category=ticket.category,
            urgency=ticket.urgency,
            reason=ticket.reason,
            status=ticket.status,
            assigned_to=ticket.assigned_to,
            created_at=ticket.created_at,
            resolved_at=ticket.resolved_at
        )
        self.session.add(db_ticket)
        await self.session.commit()

    async def get_open(self, worker_id: str = None) -> list[DBEscalationTicket]:
        query = select(DBEscalationTicket).where(DBEscalationTicket.status == "open")
        if worker_id:
            query = query.where(DBEscalationTicket.worker_id == worker_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def resolve(self, ticket_id: str, notes: str) -> bool:
        result = await self.session.execute(select(DBEscalationTicket).where(DBEscalationTicket.ticket_id == ticket_id))
        db_ticket = result.scalars().first()
        if db_ticket:
            db_ticket.status = "resolved"
            db_ticket.resolved_at = func.now() if hasattr(func, "now") else None # Usually imported from sqlalchemy.sql
            await self.session.commit()
            return True
        return False
