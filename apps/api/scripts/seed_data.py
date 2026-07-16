from __future__ import annotations

import argparse
from pathlib import Path
import sys

API_DIRECTORY = Path(__file__).resolve().parents[1]
if str(API_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(API_DIRECTORY))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import assert_safe_test_database_url, settings
from app.services.demo_seed_service import DemoSeedService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--seed-dir", type=Path, default=settings.seed_data_dir)
    args = parser.parse_args()
    assert_safe_test_database_url(args.database_url)
    engine = create_engine(args.database_url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as db:
        version = db.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one_or_none()
        if version != "0004_milestone3_news_triggers":
            raise RuntimeError("Database must be migrated to the current schema head.")
        summary = DemoSeedService(db, args.seed_dir).seed()
        print(f"Milestone 2 demo seed complete: {summary}")
    engine.dispose()


if __name__ == "__main__":
    main()
