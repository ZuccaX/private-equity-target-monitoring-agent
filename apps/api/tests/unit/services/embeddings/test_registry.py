from pathlib import Path
from unittest.mock import Mock

import pytest

from app.core.config import Settings
from app.services.embeddings.registry import EmbeddingProviderRegistry


def test_implicit_semantic_primary_falls_back_with_safe_metadata() -> None:
    configured = Settings(
        embedding_provider="sentence_transformer",
        hf_model_cache_dir=Path("/private/model-cache"),
        _env_file=None,
    )
    registry = EmbeddingProviderRegistry(
        configured,
        semantic_factory=Mock(side_effect=RuntimeError("secret loader detail")),
    )

    resolution = registry.resolve()

    assert resolution.provider.identity.provider == "hashing"
    assert resolution.requested_provider == "sentence_transformer"
    assert resolution.fallback_category == "model_unavailable"
    assert "secret" not in repr(resolution)
    assert "/private" not in repr(resolution)


def test_explicit_semantic_selection_never_silently_falls_back() -> None:
    configured = Settings(
        embedding_provider="hashing",
        hf_model_cache_dir=Path("/missing"),
        _env_file=None,
    )
    registry = EmbeddingProviderRegistry(
        configured,
        semantic_factory=Mock(side_effect=RuntimeError("not loaded")),
    )

    with pytest.raises(RuntimeError, match="unavailable"):
        registry.resolve(explicit_provider="sentence_transformer")


def test_unknown_explicit_provider_is_refused() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        EmbeddingProviderRegistry(Settings(_env_file=None)).resolve(
            explicit_provider="remote-provider"
        )
