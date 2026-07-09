from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WorkflowExecutionORM(Base):
    __tablename__ = "workflow_executions"

    id:           Mapped[str]            = mapped_column(String, primary_key=True)
    company_name: Mapped[str]            = mapped_column(String, nullable=False)
    status:       Mapped[str]            = mapped_column(String, nullable=False)
    route_taken:  Mapped[str | None]     = mapped_column(String, nullable=True)
    score:        Mapped[int | None]     = mapped_column(Integer, nullable=True)
    state_json:   Mapped[str]            = mapped_column(Text, nullable=False)
    created_at:   Mapped[datetime]       = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
