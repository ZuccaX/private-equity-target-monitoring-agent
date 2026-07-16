from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.download_embedding_model import download_and_verify_model


def test_downloader_requires_an_explicit_cache_directory() -> None:
    with pytest.raises(ValueError, match="cache"):
        download_and_verify_model(cache_dir=None, model_factory=Mock())


def test_downloader_uses_pinned_local_identity_and_verifies_dimension(
    tmp_path: Path,
) -> None:
    model = Mock()
    model.encode.return_value = [[0.0] * 384]
    factory = Mock(return_value=model)

    identity = download_and_verify_model(
        cache_dir=tmp_path,
        model_factory=factory,
    )

    factory.assert_called_once_with(
        "sentence-transformers/all-MiniLM-L6-v2",
        revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        cache_folder=str(tmp_path),
        device="cpu",
    )
    model.encode.assert_called_once()
    assert identity["dimension"] == 384
    assert identity["cache_dir"] == str(tmp_path)


def test_downloader_rejects_wrong_dimension(tmp_path: Path) -> None:
    model = Mock()
    model.encode.return_value = [[0.0] * 383]

    with pytest.raises(ValueError, match="384"):
        download_and_verify_model(
            cache_dir=tmp_path,
            model_factory=Mock(return_value=model),
        )
