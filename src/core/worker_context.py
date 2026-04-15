from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class WorkerProfile:
    worker_id: str
    name: str = ""
    department: str = ""
    role: str = ""
    location: str = ""
    hire_date: Optional[str] = None
    manager: str = ""
    access_level: str = "all"
    language: str = "es"

    total_queries: int = 0
    queries_by_category: dict[str, int] = field(default_factory=dict)
    last_query_date: Optional[datetime] = None
    unresolved_tickets: list[str] = field(default_factory=list)
    satisfaction_scores: list[int] = field(default_factory=list)

    prefers_detailed: bool = True
    prefers_step_by_step: bool = True

    def record_query(self, category: str) -> None:
        self.total_queries += 1
        self.queries_by_category[category] = self.queries_by_category.get(category, 0) + 1
        self.last_query_date = datetime.utcnow()

    def record_satisfaction(self, score: int) -> None:
        self.satisfaction_scores.append(max(1, min(5, score)))
        self.satisfaction_scores = self.satisfaction_scores[-50:]

    @property
    def avg_satisfaction(self) -> float:
        if not self.satisfaction_scores:
            return 0.0
        return sum(self.satisfaction_scores) / len(self.satisfaction_scores)

    @property
    def seniority_days(self) -> int:
        if not self.hire_date:
            return 0
        try:
            hire = datetime.fromisoformat(self.hire_date)
            return (datetime.utcnow() - hire).days
        except ValueError:
            return 0

    @property
    def is_new_employee(self) -> bool:
        return self.seniority_days < 90

    def get_context_summary(self) -> str:
        return (
            f"Trabajador: {self.name or self.worker_id}\n"
            f"Departamento: {self.department}\n"
            f"Rol: {self.role}\n"
            f"Ubicación: {self.location}\n"
            f"Antigüedad: {self.seniority_days} días\n"
            f"Empleado nuevo: {'Sí' if self.is_new_employee else 'No'}\n"
            f"Consultas previas: {self.total_queries}\n"
            f"Tickets abiertos: {len(self.unresolved_tickets)}"
        )
