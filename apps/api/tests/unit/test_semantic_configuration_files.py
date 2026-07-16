import json
import os
from pathlib import Path
import subprocess


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def _compose_config(*files: str) -> dict:
    command = ["docker", "compose"]
    for file_name in files:
        command.extend(["-f", file_name])
    command.extend(["config", "--format", "json"])
    environment = {
        **os.environ,
        "HF_MODEL_CACHE_DIR": "/tmp/m2-fake-huggingface-cache",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    }
    result = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_base_compose_defaults_to_hashing_without_host_model_mount() -> None:
    configured = _compose_config("docker-compose.yml")
    api = configured["services"]["api"]
    assert api["environment"]["EMBEDDING_PROVIDER"] == "hashing"
    assert not any(
        volume.get("target") == "/models/huggingface"
        for volume in api.get("volumes", [])
    )


def test_semantic_override_uses_read_only_external_mounts_and_offline_flags() -> None:
    configured = _compose_config(
        "docker-compose.yml", "docker-compose.semantic.yml"
    )
    api = configured["services"]["api"]
    assert api["environment"]["EMBEDDING_PROVIDER"] == "sentence_transformer"
    assert api["environment"]["HF_HUB_OFFLINE"] == "1"
    assert api["environment"]["TRANSFORMERS_OFFLINE"] == "1"
    mounts = {volume["target"]: volume for volume in api["volumes"]}
    assert mounts["/models/huggingface"]["read_only"] is True
    assert mounts["/seed-data"]["read_only"] is True
    assert mounts["/evaluation-fixtures"]["read_only"] is True
