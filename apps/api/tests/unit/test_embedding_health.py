from pathlib import Path
from unittest.mock import Mock

from app.api.routes_health import get_embedding_health
from app.core.config import Settings
from app.services.embeddings.registry import EmbeddingProviderRegistry


def test_embedding_health_reports_effective_fallback_without_sensitive_detail() -> None:
    configured = Settings(
        embedding_provider="sentence_transformer",
        hf_model_cache_dir=Path("/Volumes/private-secret/cache"),
        _env_file=None,
    )
    registry = EmbeddingProviderRegistry(
        configured,
        semantic_factory=Mock(
            side_effect=RuntimeError("raw loader secret /Volumes/private-secret")
        ),
    )

    component = get_embedding_health(configured=configured, registry=registry)
    rendered = component.model_dump_json()

    assert component.name == "embeddings"
    assert component.status == "degraded"
    assert component.mode == "sentence_transformer->hashing"
    assert component.detail == "model_unavailable"
    assert "/Volumes" not in rendered
    assert "raw loader" not in rendered


def test_hashing_embedding_health_is_ok() -> None:
    configured = Settings(_env_file=None)
    component = get_embedding_health(configured=configured)

    assert component.status == "ok"
    assert component.mode == "hashing"
    assert component.detail is None
