from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MODEL_DIMENSION = 384


def download_and_verify_model(
    *,
    cache_dir: Path | None,
    model_factory: Callable[..., Any] | None = None,
) -> dict[str, str | int]:
    if cache_dir is None:
        raise ValueError("An explicit model cache directory is required.")

    cache_dir = cache_dir.expanduser().resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)

    if model_factory is None:
        from sentence_transformers import SentenceTransformer

        model_factory = SentenceTransformer

    model = model_factory(
        MODEL_NAME,
        revision=MODEL_REVISION,
        cache_folder=str(cache_dir),
        device="cpu",
    )
    vectors = model.encode(
        ["Private equity semantic retrieval verification."],
        convert_to_numpy=False,
        normalize_embeddings=True,
        batch_size=1,
    )
    vector = list(vectors[0])
    if len(vector) != MODEL_DIMENSION:
        raise ValueError(
            f"Expected a {MODEL_DIMENSION}-dimensional vector, got {len(vector)}."
        )

    return {
        "model": MODEL_NAME,
        "revision": MODEL_REVISION,
        "dimension": MODEL_DIMENSION,
        "cache_dir": str(cache_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", required=True, type=Path)
    args = parser.parse_args()
    identity = download_and_verify_model(cache_dir=args.cache_dir)
    print(
        "Downloaded and verified "
        f"{identity['model']}@{identity['revision']} "
        f"({identity['dimension']} dimensions) in {identity['cache_dir']}"
    )


if __name__ == "__main__":
    main()
