from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

API_DIRECTORY = Path(__file__).resolve().parents[1]
if str(API_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(API_DIRECTORY))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import API_ROOT, Settings, assert_safe_test_database_url
from app.services.demo_seed_service import DemoSeedService
from app.services.document_indexing_service import DocumentIndexingService
from app.services.embedding_service import EmbeddingService
from app.services.embeddings.hashing import HashingEmbeddingProvider
from app.services.embeddings.registry import EmbeddingProviderRegistry
from scripts.evaluate_retrieval import evaluate_session


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect-fallback", action="store_true")
    parser.add_argument("--no-write-report", action="store_true")
    args = parser.parse_args()
    database_url = os.environ["TEST_DATABASE_URL"]
    assert_safe_test_database_url(database_url)
    cache_override = os.environ.get("EMBEDDING_CACHE_DIR")
    configured = Settings(
        embedding_provider="sentence_transformer",
        hf_model_cache_dir=cache_override or os.environ.get("HF_MODEL_CACHE_DIR"),
        _env_file=None,
    )
    registry = EmbeddingProviderRegistry(configured)
    resolution = registry.resolve()
    if args.expect_fallback:
        if resolution.effective_provider != "hashing" or not resolution.fallback_category:
            raise RuntimeError("Expected a reported hashing fallback.")
        print("Semantic fallback verified: model_unavailable -> hashing")
        return
    if resolution.effective_provider != "sentence_transformer":
        raise RuntimeError("Pinned semantic provider did not load from local cache.")

    engine = create_engine(database_url, pool_pre_ping=True)
    config = Config(API_ROOT / "alembic.ini")
    config.attributes["database_url"] = database_url
    command.upgrade(config, "head")
    with sessionmaker(bind=engine, expire_on_commit=False)() as db:
        DemoSeedService(db, configured.seed_data_dir).seed()
        DocumentIndexingService(
            db,
            embedding_services=[
                EmbeddingService(HashingEmbeddingProvider()),
                EmbeddingService(resolution.provider),
            ],
        ).index_all_documents()
        mixed = db.execute(
            text(
                "SELECT count(*) FROM document_chunks WHERE "
                "embedding_provider='sentence_transformer' AND "
                "(embedding_model <> :model OR embedding_model_version <> :version "
                "OR embedding_dimension <> 384)"
            ),
            {
                "model": resolution.provider.identity.model,
                "version": resolution.provider.identity.version,
            },
        ).scalar_one()
        if mixed:
            raise RuntimeError("Mixed or invalid semantic cohort rows detected.")
        metrics = evaluate_session(db, configured.retrieval_evaluation_fixture)
        if metrics.recall_at_k != 1.0 or metrics.leakage_count != 0:
            raise RuntimeError(f"Semantic retrieval quality gate failed: {metrics}")
    engine.dispose()
    report = (
        "# Milestone 2 Retrieval Evaluation\n\n"
        "- Fixture cases: `3` (expected hit, injection-isolation hit, "
        "type-filtered empty)\n"
        f"- Provider: `{resolution.provider.identity.provider}`\n"
        f"- Model: `{resolution.provider.identity.model}`\n"
        f"- Revision: `{resolution.provider.identity.version}`\n"
        f"- Dimension: `{resolution.provider.identity.dimension}`\n"
        f"- Recall@K: `{metrics.recall_at_k:.3f}`\n"
        f"- MRR: `{metrics.mean_reciprocal_rank:.3f}`\n"
        f"- Cross-company/forbidden leakage: `{metrics.leakage_count}`\n"
        f"- Empty cases: `{metrics.empty_count}`\n"
        "- Model loading: offline/local-files-only\n"
        "\nThe same deterministic fixture is intended for host and disposable "
        "Docker checks. A separate missing-cache probe verifies the explicit "
        "`model_unavailable -> hashing` fallback without mixing cohorts.\n"
        "\nThe fixture resolves companies by stable domain, requires company-"
        "scoped RAG, checks forbidden cross-company document IDs, validates "
        "the empty case and confirms prompt-injection isolation. These are "
        "deterministic demo-corpus regression metrics, not a claim of general "
        "production retrieval quality.\n"
    )
    if not args.no_write_report:
        report_path = API_ROOT.parent.parent / "docs" / "RETRIEVAL_EVALUATION.md"
        report_path.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
