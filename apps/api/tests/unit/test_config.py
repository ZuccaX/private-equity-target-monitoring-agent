from pathlib import Path

import pytest

from app.core.config import (
    Settings,
    assert_safe_test_database_url,
    resolve_repository_root,
)


def test_settings_parse_comma_separated_cors_origins() -> None:
    settings = Settings(
        cors_origins="http://localhost:3000, https://example.test",
        _env_file=None,
    )

    assert settings.cors_origin_list == [
        "http://localhost:3000",
        "https://example.test",
    ]


def test_embedding_settings_default_to_pinned_hashing_cohort() -> None:
    configured = Settings(_env_file=None)

    assert configured.embedding_provider == "hashing"
    assert configured.embedding_model_name == "local-hashing-384-v1"
    assert configured.embedding_dimension == 384
    assert configured.embedding_model_revision == (
        "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    )
    assert configured.hf_model_cache_dir is None


def test_embedding_settings_allow_explicit_semantic_opt_in() -> None:
    configured = Settings(
        embedding_provider="sentence_transformer",
        hf_model_cache_dir="/models/huggingface",
        _env_file=None,
    )

    assert configured.embedding_provider == "sentence_transformer"
    assert configured.embedding_model_name == (
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    assert configured.hf_model_cache_dir == Path("/models/huggingface")


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("embedding_dimension", 0),
        ("embedding_dimension", 383),
        ("embedding_batch_size", 0),
        ("vector_max_top_k", 0),
        ("rag_max_context_words", 0),
        ("vector_min_similarity", 1.1),
    ],
)
def test_embedding_settings_reject_invalid_bounds(
    field_name: str,
    invalid_value: int | float,
) -> None:
    with pytest.raises(ValueError):
        Settings(**{field_name: invalid_value}, _env_file=None)


def test_repository_root_falls_back_for_shallow_container_layout() -> None:
    assert resolve_repository_root(Path("/app")) == Path("/app")


def test_test_database_guard_accepts_test_database() -> None:
    assert_safe_test_database_url(
        "postgresql+psycopg://user:password@localhost:5432/pe_agent_test"
    )


def test_test_database_guard_rejects_same_database_with_different_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core import config

    monkeypatch.setattr(
        config.settings,
        "database_url",
        "postgresql+psycopg://developer:one@localhost:5432/shared_test",
    )
    with pytest.raises(ValueError, match="must not match"):
        assert_safe_test_database_url(
            "postgresql+psycopg://runner:two@localhost:5432/shared_test"
        )


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+psycopg://user:password@localhost:5432/pe_agent_db",
        "postgresql+psycopg://user:password@localhost:5432/postgres",
        "postgresql+psycopg://user:password@localhost:5432/",
    ],
)
def test_test_database_guard_rejects_unsafe_database(
    database_url: str,
) -> None:
    with pytest.raises(ValueError, match="test"):
        assert_safe_test_database_url(database_url)


def test_news_defaults_are_mock_only_and_environment_safe() -> None:
    configured = Settings(_env_file=None)

    assert configured.news_source_config.name == "news_sources.json"
    assert configured.news_sync_api_effective is True
    assert configured.news_allowed_host_list == []
    assert configured.trigger_extraction_mode == "rules"

    production = Settings(environment="production", _env_file=None)
    assert production.news_sync_api_effective is False
    assert (
        Settings(
            environment="production",
            news_sync_api_enabled=True,
            _env_file=None,
        ).news_sync_api_effective
        is True
    )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("news_max_items", 0),
        ("news_max_response_bytes", 10_000_001),
        ("news_http_timeout_seconds", 0),
    ],
)
def test_news_settings_enforce_bounds(
    field_name: str,
    invalid_value: int | float,
) -> None:
    with pytest.raises(ValueError):
        Settings(**{field_name: invalid_value}, _env_file=None)
