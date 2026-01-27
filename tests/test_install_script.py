import os
import subprocess
import tempfile
from pathlib import Path


def test_install_requires_pixi_when_missing():
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "install.sh"

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()
        python3_path = fake_bin / "python3"
        python3_path.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"-c\" ]; then\n"
            "  echo 3.10\n"
            "  exit 0\n"
            "fi\n"
            "exit 1\n"
        )
        python3_path.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:/usr/bin:/bin"

        result = subprocess.run(
            ["/bin/bash", str(script)],
            cwd=repo_root,
            env=env,
            text=True,
            capture_output=True,
        )

    combined = (result.stdout + result.stderr).lower()
    assert result.returncode != 0
    assert "pixi" in combined


def test_bbdown_url_selects_linux_x64():
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "install.sh"

    env = os.environ.copy()
    env["BBDOWN_DRY_RUN"] = "1"
    env["BBDOWN_OS"] = "Linux"
    env["BBDOWN_ARCH"] = "x86_64"
    env["BBDOWN_FORCE_INSTALL"] = "1"
    env["INSTALL_SKIP_PYTHON"] = "1"

    result = subprocess.run(
        ["/bin/bash", str(script)],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
    )

    combined = (result.stdout + result.stderr).lower()
    assert result.returncode == 0
    assert "linux-x64.zip" in combined
