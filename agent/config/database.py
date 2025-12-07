import logging
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    JSON,
    MetaData,
    Table,
    select,
    insert,
    update,
    delete,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.settings import get_settings

if TYPE_CHECKING:
    from llama_index.core.memory import Memory

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Status of a workflow."""

    PENDING_INPUT = "pending_input"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class FlowRunStatus(str, Enum):
    """Status of a flow run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HITL_PENDING = "hitl_pending"
    CANCELLED = "cancelled"


class DatabaseManager:
    """Manages database connections, memory instances, and workflow states."""

    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._memory_cache: dict[tuple[str, str], "Memory"] = {}
        self._metadata = MetaData()
        self._workflow_table: Optional[Table] = None
        # In-memory fallback for workflow states (when DB not configured)
        self._workflow_cache: dict[str, dict] = {}
        # Flow run tracking tables
        self._flow_runs_table: Optional[Table] = None
        self._flow_steps_table: Optional[Table] = None
        # In-memory fallback for flow runs (when DB not configured)
        self._flow_runs_cache: dict[str, dict] = {}
        self._flow_steps_cache: dict[str, list[dict]] = {}

    async def connect(self) -> None:
        """Initialize the database connection pool and create tables."""
        settings = get_settings()
        if settings.memory_database_uri:
            self._engine = create_async_engine(
                settings.memory_database_uri,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_recycle=settings.db_pool_recycle,
            )
            self._session_factory = sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Create workflow states table
            await self._create_workflow_table()

            # Create flow run tracking tables
            await self._create_flow_tables()

            logger.info(
                "Database engine created with pool_size=%d, max_overflow=%d",
                settings.db_pool_size,
                settings.db_max_overflow,
            )

    async def _create_workflow_table(self) -> None:
        """Create the workflow_states table if it doesn't exist."""
        self._workflow_table = Table(
            "workflow_states",
            self._metadata,
            Column("workflow_id", String(36), primary_key=True),
            Column("session_id", String(255), nullable=True, index=True),
            Column("agent_name", String(100), nullable=False, index=True),
            Column("status", String(50), nullable=False, index=True),
            Column("prompt", Text, nullable=True),
            Column("context_data", JSON, nullable=False),
            Column("user_name", String(100), nullable=True),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        )

        async with self._engine.begin() as conn:
            await conn.run_sync(self._metadata.create_all)

        logger.info("Workflow states table ready")

    async def _create_flow_tables(self) -> None:
        """Create flow_runs and flow_steps tables if they don't exist."""
        self._flow_runs_table = Table(
            "flow_runs",
            self._metadata,
            Column("id", String(36), primary_key=True),
            Column("flow_id", String(100), nullable=False, index=True),
            Column("session_id", String(255), nullable=True, index=True),
            Column("status", String(20), nullable=False, index=True),
            Column("input_data", JSON, nullable=True),
            Column("result", Text, nullable=True),
            Column("error", Text, nullable=True),
            Column("started_at", TIMESTAMP(timezone=True), nullable=False),
            Column("completed_at", TIMESTAMP(timezone=True), nullable=True),
            Column("metadata", JSON, nullable=True),
        )

        self._flow_steps_table = Table(
            "flow_steps",
            self._metadata,
            Column("id", String(36), primary_key=True),
            Column("flow_run_id", String(36), nullable=False, index=True),
            Column("step_name", String(100), nullable=False),
            Column("step_index", Integer, nullable=False),
            Column("status", String(20), nullable=False),
            Column("event_type", String(100), nullable=True),
            Column("event_data", JSON, nullable=True),
            Column("started_at", TIMESTAMP(timezone=True), nullable=False),
            Column("completed_at", TIMESTAMP(timezone=True), nullable=True),
            Column("duration_ms", Integer, nullable=True),
        )

        async with self._engine.begin() as conn:
            await conn.run_sync(self._metadata.create_all)

        logger.info("Flow tables ready")

    async def disconnect(self) -> None:
        """Close the database connection pool."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine disposed")
        self._memory_cache.clear()

    @property
    def engine(self) -> Optional[AsyncEngine]:
        return self._engine

    # ─────────────────────────────────────────────────────────────
    # MEMORY MANAGEMENT
    # ─────────────────────────────────────────────────────────────

    def get_memory(self, session_id: str, agent_name: str) -> "Memory":
        """Get or create a Memory instance for a session."""
        from llama_index.core.memory import Memory

        settings = get_settings()
        cache_key = (session_id, agent_name)

        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        table_name = f"{agent_name}_memory"

        kwargs = {
            "session_id": session_id,
            "token_limit": settings.memory_token_limit,
            "table_name": table_name,
        }

        if self._engine:
            kwargs["async_engine"] = self._engine
        elif settings.memory_database_uri:
            kwargs["async_database_uri"] = settings.memory_database_uri

        memory = Memory.from_defaults(**kwargs)
        self._memory_cache[cache_key] = memory

        logger.debug("Created memory for session=%s, agent=%s", session_id, agent_name)
        return memory

    async def clear_memory(self, session_id: str, agent_name: str) -> bool:
        """Clear memory for a specific session and agent."""
        cache_key = (session_id, agent_name)

        if cache_key in self._memory_cache:
            await self._memory_cache[cache_key].areset()
            del self._memory_cache[cache_key]
            logger.info(
                "Cleared memory for session=%s, agent=%s", session_id, agent_name
            )
            return True
        return False

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW STATE MANAGEMENT (for HITL)
    # ─────────────────────────────────────────────────────────────

    async def save_workflow_state(
        self,
        workflow_id: str,
        agent_name: str,
        context_data: dict,
        prompt: str,
        session_id: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> None:
        """Save a workflow state for HITL resumption."""
        now = datetime.now(timezone.utc)

        # Use database if available, otherwise use in-memory cache
        if self._session_factory is not None and self._workflow_table is not None:
            async with self._session_factory() as session:
                await session.execute(
                    insert(self._workflow_table).values(
                        workflow_id=workflow_id,
                        session_id=session_id,
                        agent_name=agent_name,
                        status=WorkflowStatus.PENDING_INPUT.value,
                        prompt=prompt,
                        context_data=context_data,
                        user_name=user_name,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await session.commit()
            logger.info("Saved workflow state to DB: workflow_id=%s", workflow_id)
        else:
            # In-memory fallback
            self._workflow_cache[workflow_id] = {
                "workflow_id": workflow_id,
                "session_id": session_id,
                "agent_name": agent_name,
                "status": WorkflowStatus.PENDING_INPUT.value,
                "prompt": prompt,
                "context_data": context_data,
                "user_name": user_name,
                "created_at": now,
                "updated_at": now,
            }
            logger.info(
                "Saved workflow state to memory: workflow_id=%s (no DB configured)",
                workflow_id,
            )

    async def get_workflow_state(self, workflow_id: str) -> Optional[dict]:
        """Get a workflow state by ID."""
        # Use database if available
        if self._session_factory is not None and self._workflow_table is not None:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(self._workflow_table).where(
                        self._workflow_table.c.workflow_id == workflow_id
                    )
                )
                row = result.fetchone()

                if row:
                    return {
                        "workflow_id": row.workflow_id,
                        "session_id": row.session_id,
                        "agent_name": row.agent_name,
                        "status": row.status,
                        "prompt": row.prompt,
                        "context_data": row.context_data,
                        "user_name": row.user_name,
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                    }
                return None
        else:
            # In-memory fallback
            return self._workflow_cache.get(workflow_id)

    async def update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatus,
    ) -> None:
        """Update the status of a workflow."""
        # Use database if available
        if self._session_factory is not None and self._workflow_table is not None:
            async with self._session_factory() as session:
                await session.execute(
                    update(self._workflow_table)
                    .where(self._workflow_table.c.workflow_id == workflow_id)
                    .values(
                        status=status.value,
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
            logger.info(
                "Updated workflow status in DB: workflow_id=%s, status=%s",
                workflow_id,
                status.value,
            )
        else:
            # In-memory fallback
            if workflow_id in self._workflow_cache:
                self._workflow_cache[workflow_id]["status"] = status.value
                self._workflow_cache[workflow_id]["updated_at"] = datetime.now(
                    timezone.utc
                )
                logger.info(
                    "Updated workflow status in memory: workflow_id=%s, status=%s",
                    workflow_id,
                    status.value,
                )

    async def delete_workflow_state(self, workflow_id: str) -> bool:
        """Delete a workflow state."""
        # Use database if available
        if self._session_factory is not None and self._workflow_table is not None:
            async with self._session_factory() as session:
                result = await session.execute(
                    delete(self._workflow_table).where(
                        self._workflow_table.c.workflow_id == workflow_id
                    )
                )
                await session.commit()

                deleted = result.rowcount > 0
                if deleted:
                    logger.info(
                        "Deleted workflow state from DB: workflow_id=%s", workflow_id
                    )
                return deleted
        else:
            # In-memory fallback
            if workflow_id in self._workflow_cache:
                del self._workflow_cache[workflow_id]
                logger.info(
                    "Deleted workflow state from memory: workflow_id=%s", workflow_id
                )
                return True
            return False

    # ─────────────────────────────────────────────────────────────
    # FLOW RUN MANAGEMENT
    # ─────────────────────────────────────────────────────────────

    async def create_flow_run(
        self,
        run_id: str,
        flow_id: str,
        input_data: dict,
        session_id: Optional[str] = None,
    ) -> None:
        """Create a new flow run record."""
        now = datetime.now(timezone.utc)

        if self._session_factory is not None and self._flow_runs_table is not None:
            async with self._session_factory() as session:
                await session.execute(
                    insert(self._flow_runs_table).values(
                        id=run_id,
                        flow_id=flow_id,
                        session_id=session_id,
                        status=FlowRunStatus.PENDING.value,
                        input_data=input_data,
                        started_at=now,
                    )
                )
                await session.commit()
            logger.info(
                "Created flow run in DB: run_id=%s, flow_id=%s", run_id, flow_id
            )
        else:
            # In-memory fallback
            self._flow_runs_cache[run_id] = {
                "id": run_id,
                "flow_id": flow_id,
                "session_id": session_id,
                "status": FlowRunStatus.PENDING.value,
                "input_data": input_data,
                "result": None,
                "error": None,
                "started_at": now,
                "completed_at": None,
                "metadata": None,
            }
            self._flow_steps_cache[run_id] = []
            logger.info(
                "Created flow run in memory: run_id=%s (no DB configured)", run_id
            )

    async def update_flow_run_status(
        self,
        run_id: str,
        status: FlowRunStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Update flow run status, result, error, or metadata."""
        now = datetime.now(timezone.utc)

        if self._session_factory is not None and self._flow_runs_table is not None:
            values: dict = {"status": status.value}
            if result is not None:
                values["result"] = result
            if error is not None:
                values["error"] = error
            if metadata is not None:
                values["metadata"] = metadata
            if status in (FlowRunStatus.COMPLETED, FlowRunStatus.FAILED):
                values["completed_at"] = now

            async with self._session_factory() as session:
                await session.execute(
                    update(self._flow_runs_table)
                    .where(self._flow_runs_table.c.id == run_id)
                    .values(**values)
                )
                await session.commit()
            logger.info(
                "Updated flow run in DB: run_id=%s, status=%s", run_id, status.value
            )
        else:
            # In-memory fallback
            if run_id in self._flow_runs_cache:
                self._flow_runs_cache[run_id]["status"] = status.value
                if result is not None:
                    self._flow_runs_cache[run_id]["result"] = result
                if error is not None:
                    self._flow_runs_cache[run_id]["error"] = error
                if metadata is not None:
                    self._flow_runs_cache[run_id]["metadata"] = metadata
                if status in (FlowRunStatus.COMPLETED, FlowRunStatus.FAILED):
                    self._flow_runs_cache[run_id]["completed_at"] = now
                logger.info(
                    "Updated flow run in memory: run_id=%s, status=%s",
                    run_id,
                    status.value,
                )

    async def get_flow_run(self, run_id: str) -> Optional[dict]:
        """Get a flow run by ID."""
        if self._session_factory is not None and self._flow_runs_table is not None:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(self._flow_runs_table).where(
                        self._flow_runs_table.c.id == run_id
                    )
                )
                row = result.fetchone()

                if row:
                    return {
                        "id": row.id,
                        "flow_id": row.flow_id,
                        "session_id": row.session_id,
                        "status": row.status,
                        "input_data": row.input_data,
                        "result": row.result,
                        "error": row.error,
                        "started_at": row.started_at,
                        "completed_at": row.completed_at,
                        "metadata": row.metadata,
                    }
                return None
        else:
            # In-memory fallback
            return self._flow_runs_cache.get(run_id)

    # ─────────────────────────────────────────────────────────────
    # FLOW STEP MANAGEMENT
    # ─────────────────────────────────────────────────────────────

    async def add_flow_step(
        self,
        run_id: str,
        step_id: str,
        step_name: str,
        step_index: int,
        status: str,
        event_type: Optional[str] = None,
        event_data: Optional[dict] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """Add a step record to a flow run."""
        now = datetime.now(timezone.utc)
        started_at = started_at or now

        if self._session_factory is not None and self._flow_steps_table is not None:
            async with self._session_factory() as session:
                await session.execute(
                    insert(self._flow_steps_table).values(
                        id=step_id,
                        flow_run_id=run_id,
                        step_name=step_name,
                        step_index=step_index,
                        status=status,
                        event_type=event_type,
                        event_data=event_data,
                        started_at=started_at,
                        completed_at=completed_at,
                        duration_ms=duration_ms,
                    )
                )
                await session.commit()
            logger.debug("Added flow step to DB: run_id=%s, step=%s", run_id, step_name)
        else:
            # In-memory fallback
            if run_id not in self._flow_steps_cache:
                self._flow_steps_cache[run_id] = []
            self._flow_steps_cache[run_id].append(
                {
                    "id": step_id,
                    "flow_run_id": run_id,
                    "step_name": step_name,
                    "step_index": step_index,
                    "status": status,
                    "event_type": event_type,
                    "event_data": event_data,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "duration_ms": duration_ms,
                }
            )
            logger.debug(
                "Added flow step to memory: run_id=%s, step=%s", run_id, step_name
            )

    async def get_flow_steps(self, run_id: str) -> list[dict]:
        """Get all steps for a flow run, ordered by step_index."""
        if self._session_factory is not None and self._flow_steps_table is not None:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(self._flow_steps_table)
                    .where(self._flow_steps_table.c.flow_run_id == run_id)
                    .order_by(self._flow_steps_table.c.step_index)
                )
                rows = result.fetchall()

                return [
                    {
                        "id": row.id,
                        "flow_run_id": row.flow_run_id,
                        "step_name": row.step_name,
                        "step_index": row.step_index,
                        "status": row.status,
                        "event_type": row.event_type,
                        "event_data": row.event_data,
                        "started_at": row.started_at,
                        "completed_at": row.completed_at,
                        "duration_ms": row.duration_ms,
                    }
                    for row in rows
                ]
        else:
            # In-memory fallback
            steps = self._flow_steps_cache.get(run_id, [])
            return sorted(steps, key=lambda x: x["step_index"])


# Single instance - initialized via FastAPI lifespan
db_manager = DatabaseManager()
