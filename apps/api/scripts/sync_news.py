from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import Settings
from app.integrations.news.config import NewsSourceRegistry
from app.services.news_sync_service import NewsSyncOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronize configured news sources.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--max-items", type=int, default=100)
    parser.add_argument("--no-extract-triggers", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configured = Settings(database_url=args.database_url, _env_file=None)
    registry = NewsSourceRegistry.load(
        configured.news_source_config,
        fixture_root=configured.news_fixture_root,
    )
    engine = create_engine(args.database_url, pool_pre_ping=True)
    try:
        with sessionmaker(bind=engine, expire_on_commit=False)() as db:
            version = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
            if version != "0004_milestone3_news_triggers":
                raise RuntimeError("Database must be migrated to the Milestone 3 head.")
            report = NewsSyncOrchestrator(
                db, registry=registry, settings=configured
            ).sync(
                source_ids=args.source_ids,
                extract_triggers=not args.no_extract_triggers,
                max_items_per_source=args.max_items,
            )
            print(report.model_dump_json())
            return 1 if report.status == "failed" else 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
