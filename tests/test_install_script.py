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


# ── 7. checksum 对比：已是最新 vs 已更新 ──


def test_same_checksum_shows_up_to_date():
    """Same binary checksum → prints '已是最新'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()
        bbdown_bin = Path(tmpdir) / "local_bin"
        bbdown_bin.mkdir()

        # existing BBDown binary
        existing = bbdown_bin / "BBDown"
        existing.write_bytes(b"FAKE_BBDOWN_BINARY_V1")
        existing.chmod(0o755)

        # fake gh: run list → ID, run download → copy same binary
        dl_dir_holder = [None]
        gh_body = (
            'if echo "$@" | grep -q "run list"; then echo 99999; '
            'elif echo "$@" | grep -q "run download"; then '
            '  DEST=$(echo "$@" | grep -oP "(?<=-D )\\S+"); '
            '  mkdir -p "$DEST"; '
            f'  cp {existing} "$DEST/BBDown"; '
            'fi'
        )
        _make_fake_bin(fake_bin, "gh", gh_body)
        _make_fake_bin(fake_bin, "ffmpeg", 'echo "ffmpeg version 6.0"')

        env = _base_env(str(fake_bin))
        env["BBDOWN_OS"] = "Linux"
        env["BBDOWN_ARCH"] = "x86_64"
        env["HOME"] = tmpdir
        # ensure ~/.local/bin has the same binary
        local_bin = Path(tmpdir) / ".local" / "bin"
        local_bin.mkdir(parents=True)
        (local_bin / "BBDown").write_bytes(b"FAKE_BBDOWN_BINARY_V1")
        (local_bin / "BBDown").chmod(0o755)

        result = _run(env)

    combined = result.stdout + result.stderr
    assert result.returncode == 0
    assert "已是最新" in combined


def test_different_checksum_shows_updated():
    """Different binary checksum → prints '已更新'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()

        # fake gh: run list → ID, run download → write NEW binary
        gh_body = (
            'if echo "$@" | grep -q "run list"; then echo 99999; '
            'elif echo "$@" | grep -q "run download"; then '
            '  DEST=$(echo "$@" | grep -oP "(?<=-D )\\S+"); '
            '  mkdir -p "$DEST"; '
            '  echo "NEW_BINARY_V2" > "$DEST/BBDown"; '
            'fi'
        )
        _make_fake_bin(fake_bin, "gh", gh_body)
        _make_fake_bin(fake_bin, "ffmpeg", 'echo "ffmpeg version 6.0"')

        env = _base_env(str(fake_bin))
        env["BBDOWN_OS"] = "Linux"
        env["BBDOWN_ARCH"] = "x86_64"
        env["HOME"] = tmpdir
        # old binary at ~/.local/bin
        local_bin = Path(tmpdir) / ".local" / "bin"
        local_bin.mkdir(parents=True)
        (local_bin / "BBDown").write_bytes(b"OLD_BINARY_V1")
        (local_bin / "BBDown").chmod(0o755)

        result = _run(env)

    combined = result.stdout + result.stderr
    assert result.returncode == 0
    assert "已更新" in combined


def test_fresh_install_shows_installed():
    """No existing BBDown → prints '安装完成'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_bin = Path(tmpdir) / "bin"
        fake_bin.mkdir()

        gh_body = (
            'if echo "$@" | grep -q "run list"; then echo 99999; '
            'elif echo "$@" | grep -q "run download"; then '
            '  DEST=$(echo "$@" | grep -oP "(?<=-D )\\S+"); '
            '  mkdir -p "$DEST"; '
            '  echo "NEW_BINARY" > "$DEST/BBDown"; '
            'fi'
        )
        _make_fake_bin(fake_bin, "gh", gh_body)
        _make_fake_bin(fake_bin, "ffmpeg", 'echo "ffmpeg version 6.0"')

        env = _base_env(str(fake_bin))
        env["BBDOWN_OS"] = "Linux"
        env["BBDOWN_ARCH"] = "x86_64"
        env["HOME"] = tmpdir
        # no ~/.local/bin/BBDown exists

        result = _run(env)

    combined = result.stdout + result.stderr
    assert result.returncode == 0
    assert "安装完成" in combined
