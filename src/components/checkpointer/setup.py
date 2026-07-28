from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from src.components.core.config import settings

def get_checkpointer():
    """
    Returns a SqliteSaver checkpointer for persisting the graph state.
    In a real production environment, you might use an AsyncPostgresSaver
    or maintain a global connection pool.
    """
    # Connect with check_same_thread=False since FastAPI might use different threads
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    
    # We initialize the SqliteSaver using the connection
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()
    return checkpointer
