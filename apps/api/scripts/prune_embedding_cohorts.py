from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

API_DIRECTORY = Path(__file__).resolve().parents[1]
if str(API_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(API_DIRECTORY))

from sqlalchemy import create_engine, text

from app.core.config import assert_safe_test_database_url


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export then prune every cohort except an explicit identity."
    )
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--keep-provider", required=True)
    parser.add_argument("--keep-model", required=True)
    parser.add_argument("--keep-version", required=True)
    parser.add_argument("--keep-dimension", type=int, default=384)
    parser.add_argument("--export-path", required=True, type=Path)
    args = parser.parse_args()
    assert_safe_test_database_url(args.database_url)
    engine = create_engine(args.database_url, pool_pre_ping=True)
    parameters = {
        "provider": args.keep_provider,
        "model": args.keep_model,
        "version": args.keep_version,
        "dimension": args.keep_dimension,
    }
    predicate = (
        "NOT (embedding_provider=:provider AND embedding_model=:model AND "
        "embedding_model_version=:version AND embedding_dimension=:dimension)"
    )
    with engine.begin() as connection:
        rows = connection.execute(
            text(
                "SELECT id, document_id, chunk_index, embedding_provider, "
                "embedding_model, embedding_model_version, embedding_dimension "
                f"FROM document_chunks WHERE {predicate} ORDER BY id"
            ),
            parameters,
        ).mappings().all()
        args.export_path.write_text(
            json.dumps([dict(row) for row in rows], indent=2), encoding="utf-8"
        )
        connection.execute(
            text(f"DELETE FROM document_chunks WHERE {predicate}"), parameters
        )
    engine.dispose()
    print(f"Exported and pruned {len(rows)} non-kept cohort rows.")


if __name__ == "__main__":
    main()
