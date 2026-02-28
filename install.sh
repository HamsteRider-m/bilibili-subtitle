#!/bin/bash

# bilibili-subtitle Skill Installer

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
echo -e "${BLUE}  Bilibili 字幕提取工具 安装程序${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 检查 pixi / 安装 Python 依赖
if [ -z "$SKIP_PYTHON_INSTALL" ]; then
    echo -e "${YELLOW}[1/4] 检查 pixi...${NC}"
    if ! command -v pixi &> /dev/null; then
        echo -e "${RED}❌ 未找到 pixi，请先安装 pixi${NC}"
        echo "安装方式："
        echo "  curl -fsSL https://pixi.sh/install.sh | bash"
        echo "安装完成后重新运行："
        echo "  ./install.sh"
        exit 1
    fi

    echo -e "${GREEN}✅ pixi 已安装${NC}"

    # 2. 初始化 pixi 环境
    echo ""
    echo -e "${YELLOW}[2/4] 初始化 pixi 环境...${NC}"
    if [ ! -f "$PIXI_MANIFEST" ]; then
        echo -e "${RED}❌ 未找到 pixi.toml，请确认安装目录正确${NC}"
        exit 1
    fi

    pixi install
    echo -e "${GREEN}✅ pixi 环境就绪${NC}"

    # 3. 安装 Python 依赖
    echo ""
    echo -e "${YELLOW}[3/4] 安装 Python 依赖...${NC}"
    pixi run python -m pip install --upgrade pip -q
    pixi run python -m pip install -e "$SKILL_DIR[claude,transcribe]" -q
    pixi run python -m pip install dashscope -q
    echo -e "${GREEN}✅ Python 依赖安装完成${NC}"
else
    echo -e "${YELLOW}[1/4] 跳过 pixi/Python 安装 (INSTALL_SKIP_PYTHON=1)${NC}"
fi

# 4. 检查外部工具
echo ""
echo -e "${YELLOW}[4/4] 检查外部工具...${NC}"

# 检查 BBDown（总是检查 nightly 更新）
BBDOWN_OS="${BBDOWN_OS:-$(uname -s)}"
BBDOWN_ARCH="${BBDOWN_ARCH:-$(uname -m)}"

case "$BBDOWN_OS" in
    Linux*) BBDOWN_OS="linux" ;;
    Darwin*) BBDOWN_OS="osx" ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT*) BBDOWN_OS="win" ;;
    *) echo -e "${RED}❌ 无法识别操作系统: $BBDOWN_OS${NC}"; exit 1 ;;
esac

case "$BBDOWN_ARCH" in
    x86_64|amd64) BBDOWN_ARCH="x64" ;;
    arm64|aarch64) BBDOWN_ARCH="arm64" ;;
    *) echo -e "${RED}❌ 无法识别架构: $BBDOWN_ARCH${NC}"; exit 1 ;;
esac

if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ 需要 gh CLI 来下载 BBDown nightly build${NC}"
    echo "安装方式: https://cli.github.com/"
    exit 1
fi

BBDOWN_ARTIFACT="BBDown_${BBDOWN_OS}-${BBDOWN_ARCH}"
BBDOWN_BIN="$HOME/.local/bin"
BBDOWN_TMP="/tmp/bbdown-dl"
mkdir -p "$BBDOWN_BIN" "$BBDOWN_TMP"

if [ -n "$BBDOWN_DRY_RUN" ]; then
    echo "BBDOWN_ARTIFACT=$BBDOWN_ARTIFACT"
else
    echo "正在检查 BBDown nightly 更新..."

    BBDOWN_RUN_ID=$(gh run list -R nilaoda/BBDown -b master -s success --limit 1 --json databaseId -q '.[0].databaseId')
    if [ -z "$BBDOWN_RUN_ID" ]; then
        echo -e "${RED}❌ 无法获取 BBDown 最新构建${NC}"
        exit 1
    fi

    rm -rf "$BBDOWN_TMP"/*
    if gh run download "$BBDOWN_RUN_ID" -R nilaoda/BBDown --name "$BBDOWN_ARTIFACT" -D "$BBDOWN_TMP"; then
        # 解压到临时目录
        BBDOWN_EXTRACT="/tmp/bbdown-extract"
        rm -rf "$BBDOWN_EXTRACT"
        mkdir -p "$BBDOWN_EXTRACT"
        BBDOWN_ZIP=$(find "$BBDOWN_TMP" -name '*.zip' | head -1)
        if [ -n "$BBDOWN_ZIP" ]; then
            unzip -q -o "$BBDOWN_ZIP" -d "$BBDOWN_EXTRACT"
        else
            cp "$BBDOWN_TMP"/BBDown "$BBDOWN_EXTRACT/" 2>/dev/null || cp "$BBDOWN_TMP"/BBDown* "$BBDOWN_EXTRACT/"
        fi

        NEW_BIN="$BBDOWN_EXTRACT/BBDown"
        OLD_BIN="$BBDOWN_BIN/BBDown"

        if [ -f "$OLD_BIN" ]; then
            OLD_MD5=$(md5sum "$OLD_BIN" 2>/dev/null | cut -d' ' -f1)
            NEW_MD5=$(md5sum "$NEW_BIN" 2>/dev/null | cut -d' ' -f1)
            if [ "$OLD_MD5" = "$NEW_MD5" ]; then
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
            if [[ ":$PATH:" != *":$BBDOWN_BIN:"* ]]; then
                echo -e "${YELLOW}⚠️  请将 $BBDOWN_BIN 添加到 PATH${NC}"
            fi
        fi

        rm -rf "$BBDOWN_TMP" "$BBDOWN_EXTRACT"
    else
        echo -e "${RED}❌ BBDown 下载失败${NC}"
        echo "请确认 gh 已登录: gh auth status"
        exit 1
    fi
fi

# 检查 ffmpeg
if [ -z "$SKIP_PYTHON_INSTALL" ]; then
    if pixi run ffmpeg -version &> /dev/null; then
        FFMPEG_VERSION=$(pixi run ffmpeg -version 2>/dev/null | head -n1 | awk '{print $3}' || echo "unknown")
        echo -e "${GREEN}✅ ffmpeg 已安装 ($FFMPEG_VERSION)${NC}"
    else
        echo -e "${YELLOW}⚠️  ffmpeg 未安装（pixi 环境内未找到）${NC}"
        echo "请检查 pixi 环境或重新运行："
        echo "  pixi install"
    fi
else
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version 2>/dev/null | head -n1 | awk '{print $3}' || echo "unknown")
        echo -e "${GREEN}✅ ffmpeg 已安装 ($FFMPEG_VERSION)${NC}"
    else
        echo -e "${YELLOW}⚠️  ffmpeg 未安装${NC}"
    fi
fi

# 5. 配置指导
echo ""
echo -e "${YELLOW}[5/5] 配置指导${NC}"
echo ""

echo -e "${BLUE}🔑 API Keys 配置${NC}"
echo ""
echo "请设置以下环境变量（添加到 ~/.zshrc 或 ~/.bashrc）："
echo ""
echo -e "${GREEN}# Anthropic API (校对/翻译/摘要)${NC}"
echo "export ANTHROPIC_API_KEY=\"your-api-key\""
echo ""
echo -e "${GREEN}# DashScope API (ASR 转录，仅无字幕时需要)${NC}"
echo "export DASHSCOPE_API_KEY=\"your-api-key\""
echo ""

echo -e "${BLUE}🔐 BBDown 认证${NC}"
echo ""
echo "首次使用前，请运行："
echo -e "${GREEN}  BBDown login${NC}"
echo "扫描二维码完成登录，Cookie 保存在 BBDown.data"
echo ""

echo -e "${BLUE}🧪 安装后自检${NC}"
echo ""
echo "建议运行："
echo -e "${GREEN}  pixi run python -m bilibili_subtitle --help${NC}"
echo -e "${GREEN}  pixi run python -m bilibili_subtitle \"BV1xx411c7mD\" --skip-proofread --skip-summary -o ./output${NC}"
echo ""

# 最终检查
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 安装完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "📦 安装位置：$SKILL_DIR"
echo ""
echo "🚀 使用示例："
echo -e "  ${GREEN}pixi run python -m bilibili_subtitle \"BV1234567890\" --skip-proofread --skip-summary${NC}"
echo ""
