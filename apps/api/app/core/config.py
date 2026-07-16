from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def resolve_repository_root(api_root: Path) -> Path:
    repository_candidate = api_root.parent.parent
    if (repository_candidate / "docker-compose.yml").exists():
        return repository_candidate
    return api_root


API_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = resolve_repository_root(API_ROOT)


class Settings(BaseSettings):
    environment: Literal["development", "test", "production"] = (
        "development"
    )

    app_name: str = "Private Equity Origination Agent API"
    app_version: str = "0.2.0"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+psycopg://pe_agent:local-development-only@localhost:5432/pe_agent_db"
    )

    test_database_url: str = (
        "postgresql+psycopg://pe_agent:local-development-only@localhost:5432/pe_agent_test"
    )

    cors_origins: str = "http://localhost:3000"
    crm_integration_mode: Literal["direct", "mcp"] = "direct"
    document_integration_mode: Literal["direct", "mcp"] = "direct"
    max_upload_bytes: int = Field(default=10_000_000, ge=1)

    embedding_provider: Literal["hashing", "sentence_transformer"] = "hashing"
    embedding_model_name: str = "local-hashing-384-v1"
    semantic_embedding_model_name: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    embedding_model_revision: str = (
        "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    )
    embedding_dimension: Literal[384] = 384
    embedding_batch_size: int = Field(default=32, ge=1, le=512)
    vector_min_similarity: float = Field(default=0.15, ge=-1.0, le=1.0)
    vector_max_top_k: int = Field(default=50, ge=1, le=100)
    rag_max_context_words: int = Field(default=1_200, ge=1, le=10_000)
    hf_model_cache_dir: Path | None = None
    seed_data_dir: Path = REPO_ROOT / "data" / "seed"
    retrieval_evaluation_fixture: Path = (
        API_ROOT / "tests" / "fixtures" / "retrieval_evaluation.json"
    )

    news_source_config: Path = REPO_ROOT / "data" / "news_sources.json"
    news_fixture_root: Path = REPO_ROOT / "data" / "seed"
    news_allowed_hosts: str = ""
    news_sync_api_enabled: bool | None = None
    news_max_items: int = Field(default=100, ge=1, le=500)
    news_max_response_bytes: int = Field(
        default=2_000_000, ge=1_024, le=10_000_000
    )
    news_http_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    news_http_connect_timeout_seconds: float = Field(
        default=5.0, gt=0, le=30
    )
    news_max_redirects: int = Field(default=3, ge=0, le=10)
    news_max_retries: int = Field(default=2, ge=0, le=5)
    news_host_min_interval_seconds: float = Field(
        default=0.5, ge=0, le=60
    )
    news_company_match_threshold: float = Field(default=0.8, ge=0, le=1)
    news_event_merge_days: int = Field(default=7, ge=0, le=90)
    news_event_merge_similarity: float = Field(default=0.7, ge=0, le=1)
    trigger_extraction_mode: Literal["rules", "hybrid"] = "rules"
    trigger_extraction_version: str = "m3-rules-v1"
    trigger_llm_endpoint: str | None = None
    trigger_llm_model: str | None = None
    trigger_llm_api_key_env: str = "OPENAI_API_KEY"
    trigger_llm_allowed_hosts: str = ""

    @model_validator(mode="after")
    def select_provider_model(self) -> "Settings":
        if (
            self.embedding_provider == "sentence_transformer"
            and self.embedding_model_name == "local-hashing-384-v1"
        ):
            self.embedding_model_name = self.semantic_embedding_model_name
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def news_allowed_host_list(self) -> list[str]:
        return [
            host.strip().lower()
            for host in self.news_allowed_hosts.split(",")
            if host.strip()
        ]

    @property
    def trigger_llm_allowed_host_list(self) -> list[str]:
        return [
            host.strip().lower()
            for host in self.trigger_llm_allowed_hosts.split(",")
            if host.strip()
        ]

    @property
    def news_sync_api_effective(self) -> bool:
        if self.news_sync_api_enabled is not None:
            return self.news_sync_api_enabled
        return self.environment != "production"

    model_config = SettingsConfigDict(
        env_file=(
            str(REPO_ROOT / ".env"),
            str(API_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def assert_safe_test_database_url(database_url: str) -> None:
    parsed_url = urlparse(database_url)
    database_name = parsed_url.path.removeprefix("/")

    if not database_name or "test" not in database_name.lower():
        raise ValueError(
            "Refusing to run destructive test setup against a database "
            "whose name does not contain 'test'."
        )

    development_url = urlparse(settings.database_url)
    test_identity = (parsed_url.hostname, parsed_url.port, database_name)
    development_identity = (
        development_url.hostname,
        development_url.port,
        development_url.path.removeprefix("/"),
    )

    if test_identity == development_identity:
        raise ValueError(
            "TEST_DATABASE_URL must not match DATABASE_URL."
        )
