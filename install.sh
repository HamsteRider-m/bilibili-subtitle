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

# 检查 BBDown
if command -v BBDown &> /dev/null && [ -z "$BBDOWN_FORCE_INSTALL" ]; then
    BBDOWN_VERSION=$(BBDown --help 2>&1 | head -n1 | grep -o 'version [0-9.]*' || echo "installed")
    echo -e "${GREEN}✅ BBDown 已安装 ($BBDOWN_VERSION)${NC}"
else
    echo -e "${YELLOW}⚠️  BBDown 未安装${NC}"
    echo "正在下载 BBDown..."

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

    BBDOWN_ZIP=$(curl -sL "https://api.github.com/repos/nilaoda/BBDown/releases/latest" \
        | grep -o "\"browser_download_url\": \"[^\"]*_${BBDOWN_OS}-${BBDOWN_ARCH}\\.zip\"" \
        | head -n1 | cut -d'"' -f4)

    if [ -z "$BBDOWN_ZIP" ]; then
        echo -e "${RED}❌ BBDown 下载链接获取失败${NC}"
        echo "请手动下载: https://github.com/nilaoda/BBDown/releases"
        exit 1
    fi

    if [ -n "$BBDOWN_DRY_RUN" ]; then
        echo "BBDOWN_URL=$BBDOWN_ZIP"
    else
        BBDOWN_TMP="/tmp/BBDown.zip"
        BBDOWN_BIN="$HOME/.local/bin"
        mkdir -p "$BBDOWN_BIN"
        if curl -sL "$BBDOWN_ZIP" -o "$BBDOWN_TMP" && unzip -q -o "$BBDOWN_TMP" -d "$BBDOWN_BIN" 2>/dev/null; then
            chmod +x "$BBDOWN_BIN/BBDown"
            rm -f "$BBDOWN_TMP"
            echo -e "${GREEN}✅ BBDown 安装完成${NC}"
            if [[ ":$PATH:" != *":$BBDOWN_BIN:"* ]]; then
                echo -e "${YELLOW}⚠️  请将 $BBDOWN_BIN 添加到 PATH${NC}"
            fi
        else
            echo -e "${RED}❌ BBDown 解压失败${NC}"
            echo "请手动下载: https://github.com/nilaoda/BBDown/releases"
            exit 1
        fi
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
