#!/bin/bash

# bilibili-subtitle Skill Installer (BBDown-only)

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIXI_MANIFEST="$SKILL_DIR/pixi.toml"

cd "$SKILL_DIR"

SKIP_PYTHON_INSTALL="${INSTALL_SKIP_PYTHON:-}"
BBDOWN_DRY_RUN="${BBDOWN_DRY_RUN:-}"
BBDOWN_FORCE_INSTALL="${BBDOWN_FORCE_INSTALL:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  bilibili-subtitle BBDown Installer${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ -z "$SKIP_PYTHON_INSTALL" ]; then
    echo -e "${YELLOW}[1/3] 检查 pixi...${NC}"
    if ! command -v pixi &> /dev/null; then
        echo -e "${RED}❌ 未找到 pixi，请先安装 pixi${NC}"
        echo "安装命令："
        echo "  curl -fsSL https://pixi.sh/install.sh | bash"
        exit 1
    fi
    echo -e "${GREEN}✅ pixi 已安装${NC}"

    echo -e "${YELLOW}[2/3] 初始化 pixi 环境...${NC}"
    if [ ! -f "$PIXI_MANIFEST" ]; then
        echo -e "${RED}❌ 未找到 pixi.toml，请确认安装目录正确${NC}"
        exit 1
    fi
    pixi install
    pixi run python -m pip install -e "$SKILL_DIR" -q
    echo -e "${GREEN}✅ Python 环境就绪${NC}"
else
    echo -e "${YELLOW}[1/3] 跳过 pixi/Python 安装 (INSTALL_SKIP_PYTHON=1)${NC}"
fi

BBDOWN_OS="${BBDOWN_OS:-$(uname -s)}"
BBDOWN_ARCH="${BBDOWN_ARCH:-$(uname -m)}"
case "$BBDOWN_OS" in
    Linux*) BBDOWN_PLATFORM="linux" ;;
    Darwin*) BBDOWN_PLATFORM="osx" ;;
    MINGW*|MSYS*|CYGWIN*) BBDOWN_PLATFORM="win" ;;
    *) echo -e "${RED}❌ 不支持的系统: $BBDOWN_OS${NC}"; exit 1 ;;
esac
case "$BBDOWN_ARCH" in
    x86_64|amd64) BBDOWN_ARCH_NAME="x64" ;;
    arm64|aarch64) BBDOWN_ARCH_NAME="arm64" ;;
    *) echo -e "${RED}❌ 不支持的架构: $BBDOWN_ARCH${NC}"; exit 1 ;;
esac
BBDOWN_ARTIFACT="BBDown_${BBDOWN_PLATFORM}-${BBDOWN_ARCH_NAME}"

if [ -n "$BBDOWN_DRY_RUN" ]; then
    echo "BBDOWN_ARTIFACT=$BBDOWN_ARTIFACT"
    exit 0
fi

echo -e "${YELLOW}[3/3] 安装/更新 BBDown nightly...${NC}"
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ 需要 gh CLI 来下载 BBDown nightly build${NC}"
    echo "请安装并登录 gh: https://cli.github.com/"
    echo "  gh auth login"
    exit 1
fi

BBDOWN_BIN="$HOME/.local/bin"
mkdir -p "$BBDOWN_BIN"

BBDOWN_TMP=$(mktemp -d)
trap 'rm -rf "$BBDOWN_TMP"' EXIT

BBDOWN_RUN_ID=$(gh run list -R nilaoda/BBDown -b master -s success --limit 1 --json databaseId -q '.[0].databaseId')
if [ -z "$BBDOWN_RUN_ID" ] || [ "$BBDOWN_RUN_ID" = "null" ]; then
    echo -e "${RED}❌ 无法获取 BBDown 最新构建${NC}"
    exit 1
fi

if ! gh run download "$BBDOWN_RUN_ID" -R nilaoda/BBDown --name "$BBDOWN_ARTIFACT" -D "$BBDOWN_TMP"; then
    echo -e "${RED}❌ BBDown 下载失败${NC}"
    echo "请确认 gh 已登录: gh auth status"
    exit 1
fi

BBDOWN_EXTRACT="$BBDOWN_TMP/extract"
mkdir -p "$BBDOWN_EXTRACT"
if ls "$BBDOWN_TMP"/*.zip >/dev/null 2>&1; then
    unzip -q "$BBDOWN_TMP"/*.zip -d "$BBDOWN_EXTRACT"
elif ls "$BBDOWN_TMP"/*.tar.gz >/dev/null 2>&1; then
    tar -xzf "$BBDOWN_TMP"/*.tar.gz -C "$BBDOWN_EXTRACT"
else
    cp "$BBDOWN_TMP"/BBDown "$BBDOWN_EXTRACT/" 2>/dev/null || cp "$BBDOWN_TMP"/BBDown* "$BBDOWN_EXTRACT/"
fi

NEW_BIN="$BBDOWN_EXTRACT/BBDown"
OLD_BIN="$BBDOWN_BIN/BBDown"
if [ ! -f "$NEW_BIN" ]; then
    NEW_BIN=$(find "$BBDOWN_EXTRACT" -type f -name 'BBDown*' | head -n1)
fi
if [ -z "$NEW_BIN" ] || [ ! -f "$NEW_BIN" ]; then
    echo -e "${RED}❌ 下载包中未找到 BBDown${NC}"
    exit 1
fi

chmod +x "$NEW_BIN"
if [ -f "$OLD_BIN" ] && [ -z "$BBDOWN_FORCE_INSTALL" ]; then
    if cmp -s "$NEW_BIN" "$OLD_BIN"; then
        echo -e "${GREEN}✅ BBDown 已是最新 (build #${BBDOWN_RUN_ID})${NC}"
    else
        cp "$NEW_BIN" "$OLD_BIN"
        chmod +x "$OLD_BIN"
        echo -e "${GREEN}✅ BBDown 已更新到 nightly build #${BBDOWN_RUN_ID}${NC}"
    fi
else
    cp "$NEW_BIN" "$OLD_BIN"
    chmod +x "$OLD_BIN"
    echo -e "${GREEN}✅ BBDown (nightly build #${BBDOWN_RUN_ID}) 安装完成${NC}"
fi

if ! echo "$PATH" | grep -q "$BBDOWN_BIN"; then
    echo ""
    echo -e "${YELLOW}提示：请确保 $BBDOWN_BIN 在 PATH 中${NC}"
    echo "  export PATH=\"$BBDOWN_BIN:\$PATH\""
fi

echo ""
echo -e "${BLUE}🔐 BBDown 认证${NC}"
echo "首次下载字幕前建议登录："
echo -e "${GREEN}  BBDown login${NC}"
echo "扫描二维码完成登录，Cookie 保存在 BBDown.data"
echo ""
echo -e "${BLUE}✅ 验证命令${NC}"
echo -e "${GREEN}  pixi run python -m bilibili_subtitle --check${NC}"
echo -e "${GREEN}  pixi run python -m bilibili_subtitle \"BV1xx411c7mD\" -o ./output${NC}"
echo ""
echo -e "${GREEN}✅ 安装完成！${NC}"
echo "📦 安装位置：$SKILL_DIR"
