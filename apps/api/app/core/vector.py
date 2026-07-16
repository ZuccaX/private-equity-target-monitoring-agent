from sqlalchemy import text

from app.core.database import engine


def ensure_vector_extension() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS vector"
            )
        )