import sys
from pathlib import Path

from sqlalchemy import inspect


API_ROOT = Path(__file__).resolve().parents[1]

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


from app import models
from app.core.database import Base, engine


def check_tables() -> None:
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    print("Current database tables:")

    for table_name in sorted(table_names):
        print(f"- {table_name}")


if __name__ == "__main__":
    check_tables()