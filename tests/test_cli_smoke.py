import subprocess
import sys


def test_cli_help_runs() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "bilibili_subtitle", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "bilibili-subtitle" in (proc.stdout + proc.stderr)

