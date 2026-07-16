from pathlib import Path
import subprocess
import sys


API_ROOT = Path(__file__).resolve().parents[2]


def test_direct_m2_script_entrypoints_can_import_application_package() -> None:
    for script_name in (
        "semantic_probe.py",
        "evaluate_retrieval.py",
        "seed_data.py",
        "prune_embedding_cohorts.py",
    ):
        result = subprocess.run(
            [sys.executable, f"scripts/{script_name}", "--help"],
            cwd=API_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
