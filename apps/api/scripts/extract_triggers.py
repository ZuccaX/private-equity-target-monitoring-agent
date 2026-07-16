from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import Settings
from app.services.trigger_batch_service import TriggerBatchService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract triggers from persisted news.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--article-id", action="append", dest="article_ids", type=int)
    parser.add_argument("--company-id", type=int)
    parser.add_argument(
        "--status",
        choices=("pending", "processed", "no_trigger", "failed"),
        default="pending",
    )
    parser.add_argument("--extraction-version")
    parser.add_argument("--limit", type=int, default=100)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configured = Settings(database_url=args.database_url, _env_file=None)
    version = args.extraction_version or configured.trigger_extraction_version
    if version != configured.trigger_extraction_version:
        raise ValueError("Extraction version must match configured version.")
    engine = create_engine(args.database_url, pool_pre_ping=True)
    try:
        with sessionmaker(bind=engine, expire_on_commit=False)() as db:
            head = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
            if head != "0004_milestone3_news_triggers":
                raise RuntimeError("Database must be migrated to the Milestone 3 head.")
            report = TriggerBatchService(
                db,
                configured_settings=configured,
                version=version,
            ).process(
                article_ids=args.article_ids,
                company_id=args.company_id,
                status=args.status,
                limit=args.limit,
            )
            print(json.dumps(asdict(report), separators=(",", ":")))
            return 1 if report.status == "failed" else 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
