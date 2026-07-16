import argparse
import sys
from pathlib import Path
from sqlalchemy import text


API_ROOT = Path(__file__).resolve().parents[1]

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


from app.core.database import (
    SessionLocal,
)
from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.embeddings.registry import EmbeddingProviderRegistry
from app.services.document_indexing_service import (
    DocumentIndexingService,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=("hashing", "sentence_transformer", "all"),
        default=settings.embedding_provider,
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()

    try:
        current = db.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one_or_none()
        if current != "0004_milestone3_news_triggers":
            raise RuntimeError("Database must be migrated to the current schema head.")
        registry = EmbeddingProviderRegistry(settings)
        providers = (
            [registry.resolve(explicit_provider=name).provider for name in (
                "hashing", "sentence_transformer"
            )]
            if args.provider == "all"
            else [registry.resolve(explicit_provider=args.provider).provider]
        )
        service = DocumentIndexingService(
            db,
            embedding_services=[EmbeddingService(provider) for provider in providers],
        )

        summary = service.index_all_documents()

        print(
            "Document indexing completed."
        )

        print(
            "Documents indexed: "
            f"{summary.documents_indexed}"
        )

        print(
            "Documents skipped: "
            f"{summary.documents_skipped}"
        )

        print(
            "Chunks created: "
            f"{summary.chunks_created}"
        )
        print(f"Indexed identities: {', '.join(summary.indexed_identities)}")
        if summary.provider_failures:
            print(f"Provider failures: {', '.join(summary.provider_failures)}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
