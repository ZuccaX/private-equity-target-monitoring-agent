from typing import Literal

from pydantic import BaseModel, Field, field_validator


class VectorSearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=2000,
    )

    company_id: int | None = Field(
        default=None,
        ge=1,
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )
    document_types: list[str] | None = None
    minimum_similarity: float | None = Field(default=None, ge=-1.0, le=1.0)
    embedding_provider: str | None = None
    embedding_model: str | None = None
    embedding_model_version: str | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized_value = value.strip()

        if normalized_value == "":
            raise ValueError("Query cannot be empty.")

        return normalized_value


class VectorSearchResultRead(BaseModel):
    chunk_id: int
    document_id: int
    company_id: int

    document_title: str
    document_type: str

    source_system: str
    source_path: str | None

    chunk_index: int
    chunk_text: str
    token_count: int

    embedding_model: str
    embedding_provider: str
    embedding_model_version: str
    embedding_dimension: int

    distance: float
    similarity: float


class EmbeddingIdentityRead(BaseModel):
    provider: str
    model: str
    version: str
    dimension: int


class VectorSearchResponse(BaseModel):
    query: str
    company_id: int | None
    top_k: int
    result_count: int
    results: list[VectorSearchResultRead]
    requested_provider: str = "hashing"
    effective_provider: str = "hashing"
    effective_model: str = "local-hashing-384-v1"
    effective_model_version: str = "1"
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)
    requested_embedding: EmbeddingIdentityRead
    effective_embedding: EmbeddingIdentityRead


class RAGRetrievalRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    company_id: int = Field(ge=1)
    top_k: int = Field(default=5, ge=1, le=20)
    document_types: list[str] | None = None
    minimum_similarity: float | None = Field(default=None, ge=-1.0, le=1.0)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Query cannot be empty.")
        return normalized


class RAGCitation(BaseModel):
    source_number: int
    chunk_id: int
    document_id: int
    document_title: str
    source_path: str | None


class RAGRetrievalResponse(BaseModel):
    query: str
    company_id: int
    top_k: int
    result_count: int
    context: str
    sources: list[VectorSearchResultRead]
    status: Literal["ok", "empty"] = "ok"
    minimum_similarity: float | None = None
    context_word_budget: int = 1200
    citations: list[RAGCitation] = Field(default_factory=list)
    requested_provider: str = "hashing"
    effective_provider: str = "hashing"
    effective_model: str = "local-hashing-384-v1"
    effective_model_version: str = "1"
    fallback_used: bool = False
    fallback_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    requested_embedding: EmbeddingIdentityRead
    effective_embedding: EmbeddingIdentityRead
