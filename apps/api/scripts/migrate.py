from pathlib import Path

from alembic.config import Config

from app.core.config import API_ROOT, settings
from app.core.database import create_database_engine
from app.core.migrations import migrate_database


def main() -> None:
    config = Config(Path(API_ROOT) / "alembic.ini")
    config.attributes["database_url"] = settings.database_url
    engine = create_database_engine(settings.database_url)
    try:
        outcome = migrate_database(engine, config)
        print(outcome)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
