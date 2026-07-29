from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from src.components.core.config import settings

# Global connection pool for the checkpointer
pool = ConnectionPool(
    conninfo=settings.DATABASE_URL,
    max_size=20,
    kwargs={"autocommit": True}
)

def get_checkpointer():
    """
    Returns a PostgresSaver checkpointer for persisting the graph state.
    """
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    return checkpointer
