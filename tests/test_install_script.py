"""Tests for install.sh — BBDown nightly download via gh CLI."""

import os
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "install.sh"


def _make_fake_bin(tmpdir: Path, name: str, body: str = "exit 0") -> Path:
    """Create a fake executable in tmpdir."""
    p = tmpdir / name
    p.write_text(f"#!/bin/sh\n{body}\n")
    p.chmod(0o755)
    return p


def _base_env(fake_bin: str) -> dict:
    """Env with only fake_bin + essentials on PATH, skip python install."""
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:/usr/bin:/bin"
    env["INSTALL_SKIP_PYTHON"] = "1"
    env["BBDOWN_FORCE_INSTALL"] = "1"
    return env


def _run(env: dict, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        **kwargs,
    )


# ── 1. pixi 前置检查 ──


def test_install_requires_pixi_when_missing():
    """No pixi on PATH → exit 1 with helpful message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()
        _make_fake_bin(fake_bin, "python3", 'echo 3.10')

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:/usr/bin:/bin"

        result = _run(env)

    combined = (result.stdout + result.stderr).lower()
    assert result.returncode != 0
    assert "pixi" in combined


# ── 2. gh CLI 前置检查 ──


def test_requires_gh_when_missing():
    """BBDown not installed + no gh on PATH → exit 1 mentioning gh."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()
        # provide ffmpeg stub so script doesn't fail on that check
        _make_fake_bin(fake_bin, "ffmpeg", 'echo "ffmpeg version 6.0"')

        env = _base_env(str(fake_bin))
        env["BBDOWN_OS"] = "Linux"
        env["BBDOWN_ARCH"] = "x86_64"

        result = _run(env)

    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "gh" in combined.lower()
    assert "cli.github.com" in combined


# ── 3. dry-run artifact 名称 ──


def test_dryrun_artifact_linux_x64():
    """Dry-run with Linux/x86_64 → artifact name BBDown_linux-x64."""
    env = os.environ.copy()
    env["BBDOWN_DRY_RUN"] = "1"
    env["BBDOWN_OS"] = "Linux"
    env["BBDOWN_ARCH"] = "x86_64"
    env["BBDOWN_FORCE_INSTALL"] = "1"
    env["INSTALL_SKIP_PYTHON"] = "1"

    result = _run(env)

    assert result.returncode == 0
    assert "BBDOWN_ARTIFACT=BBDown_linux-x64" in result.stdout


def test_dryrun_artifact_osx_arm64():
    """Dry-run with Darwin/arm64 → artifact name BBDown_osx-arm64."""
    env = os.environ.copy()
    env["BBDOWN_DRY_RUN"] = "1"
    env["BBDOWN_OS"] = "Darwin"
    env["BBDOWN_ARCH"] = "aarch64"
    env["BBDOWN_FORCE_INSTALL"] = "1"
    env["INSTALL_SKIP_PYTHON"] = "1"

    result = _run(env)

    assert result.returncode == 0
    assert "BBDOWN_ARTIFACT=BBDown_osx-arm64" in result.stdout


def test_dryrun_artifact_win_x64():
    """Dry-run with Windows/amd64 → artifact name BBDown_win-x64."""
    env = os.environ.copy()
    env["BBDOWN_DRY_RUN"] = "1"
    env["BBDOWN_OS"] = "MINGW64_NT"
    env["BBDOWN_ARCH"] = "amd64"
    env["BBDOWN_FORCE_INSTALL"] = "1"
    env["INSTALL_SKIP_PYTHON"] = "1"

    result = _run(env)

    assert result.returncode == 0
    assert "BBDOWN_ARTIFACT=BBDown_win-x64" in result.stdout


# ── 4. 不支持的 OS/架构 ──


def test_unsupported_os_exits():
    """Unknown OS → exit 1 with error message."""
    env = os.environ.copy()
    env["BBDOWN_DRY_RUN"] = "1"
    env["BBDOWN_OS"] = "FreeBSD"
    env["BBDOWN_ARCH"] = "x86_64"
    env["BBDOWN_FORCE_INSTALL"] = "1"
    env["INSTALL_SKIP_PYTHON"] = "1"

    result = _run(env)

    assert result.returncode != 0
    assert "freebsd" in (result.stdout + result.stderr).lower()


def test_unsupported_arch_exits():
    """Unknown arch → exit 1 with error message."""
    env = os.environ.copy()
    env["BBDOWN_DRY_RUN"] = "1"
    env["BBDOWN_OS"] = "Linux"
    env["BBDOWN_ARCH"] = "riscv64"
    env["BBDOWN_FORCE_INSTALL"] = "1"
    env["INSTALL_SKIP_PYTHON"] = "1"

    result = _run(env)

    assert result.returncode != 0
    assert "riscv64" in (result.stdout + result.stderr).lower()


# ── 5. gh run list 失败（无成功构建） ──


def test_gh_run_list_empty_exits():
    """gh run list returns empty → exit 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()
        # fake gh that returns empty for run list
        _make_fake_bin(fake_bin, "gh", 'echo ""')
        _make_fake_bin(fake_bin, "ffmpeg", 'echo "ffmpeg version 6.0"')

        env = _base_env(str(fake_bin))
        env["BBDOWN_OS"] = "Linux"
        env["BBDOWN_ARCH"] = "x86_64"

        result = _run(env)

    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "无法获取" in combined or "最新构建" in combined


# ── 6. gh run download 失败 ──


def test_gh_download_failure_exits():
    """gh run download fails → exit 1 with auth hint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()
        # gh: run list returns an ID, but download fails
        _make_fake_bin(
            fake_bin, "gh",
            'if echo "$@" | grep -q "run list"; then echo 12345; '
            'else exit 1; fi',
        )
        _make_fake_bin(fake_bin, "ffmpeg", 'echo "ffmpeg version 6.0"')

        env = _base_env(str(fake_bin))
        env["BBDOWN_OS"] = "Linux"
        env["BBDOWN_ARCH"] = "x86_64"

        result = _run(env)

    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "gh auth" in combined.lower() or "下载失败" in combined


# ── 7. 已安装时跳过下载 ──


def test_skip_download_when_bbdown_exists():
    """BBDown already on PATH + no FORCE → skip download, show version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()
        _make_fake_bin(
            fake_bin, "BBDown",
            'echo "BBDown version 1.6.3, Bilibili Downloader."',
        )
        _make_fake_bin(fake_bin, "ffmpeg", 'echo "ffmpeg version 6.0"')

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:/usr/bin:/bin"
        env["INSTALL_SKIP_PYTHON"] = "1"
        # no BBDOWN_FORCE_INSTALL → should skip

        result = _run(env)

    combined = result.stdout + result.stderr
    assert result.returncode == 0
    assert "1.6.3" in combined
    assert "正在下载" not in combined
