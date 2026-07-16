import subprocess
import sys
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[3]


def test_cli_entrypoints_expose_safe_persisted_scope_only() -> None:
    sync = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.sync_news",
            "--help",
        ],
        cwd=API_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    extract = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.extract_triggers",
            "--help",
        ],
        cwd=API_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert sync.returncode == 0
    assert "--source-id" in sync.stdout
    assert "--url" not in sync.stdout
    assert extract.returncode == 0
    assert "--company-id" in extract.stdout
    assert "--company-domain" not in extract.stdout
