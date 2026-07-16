import math
import sys
from unittest.mock import Mock, patch

import pytest

from app.services.embeddings.base import (
    EmbeddingIdentity,
    validate_embedding_batch,
)
from app.services.embeddings.hashing import HashingEmbeddingProvider
from app.services.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)


def test_hashing_provider_is_normalized_deterministic_and_compatible() -> None:
    provider = HashingEmbeddingProvider()
    first = provider.embed_query("Healthcare software growth")
    second = provider.embed_documents(["Healthcare software growth"])[0]

    assert first == second
    assert len(first) == 384
    assert math.isclose(sum(value * value for value in first), 1.0)
    assert provider.identity == EmbeddingIdentity(
        provider="hashing",
        model="local-hashing-384-v1",
        version="1",
        dimension=384,
    )
    assert provider.embed_documents([]) == []


@pytest.mark.parametrize(
    "vectors,expected_rows,error",
    [
        ([[0.0] * 384], 2, "row"),
        ([[0.0] * 383], 1, "dimension"),
        ([[float("nan")] + [0.0] * 383], 1, "finite"),
    ],
)
def test_batch_validation_fails_closed(
    vectors: list[list[float]], expected_rows: int, error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        validate_embedding_batch(
            vectors,
            expected_rows=expected_rows,
            dimension=384,
        )


def test_sentence_transformer_import_is_lazy_and_loads_local_only(
    tmp_path,
) -> None:
    sys.modules.pop("sentence_transformers", None)
    provider = SentenceTransformerEmbeddingProvider(cache_dir=tmp_path)
    assert "sentence_transformers" not in sys.modules

    model = Mock()
    model.encode.return_value = [[1.0] + [0.0] * 383]
    fake_module = Mock()
    fake_module.SentenceTransformer.return_value = model
    with patch.dict(sys.modules, {"sentence_transformers": fake_module}):
        assert provider.embed_query("query")[0] == 1.0

    fake_module.SentenceTransformer.assert_called_once_with(
        "sentence-transformers/all-MiniLM-L6-v2",
        revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        cache_folder=str(tmp_path),
        device="cpu",
        local_files_only=True,
    )
