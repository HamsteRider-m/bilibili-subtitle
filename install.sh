#!/bin/bash

# bilibili-subtitle Skill Installer

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SKILL_DIR/.venv"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Bilibili 字幕提取工具 安装程序${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 检查 Python 版本
echo -e "${YELLOW}[1/5] 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python3，请先安装 Python 3.11+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python 版本过低（当前 $PYTHON_VERSION，需要 3.11+）${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# 2. 创建虚拟环境
echo ""
echo -e "${YELLOW}[2/5] 创建虚拟环境...${NC}"
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✅ 虚拟环境已存在${NC}"
else
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"

# 3. 安装 Python 依赖
echo ""
echo -e "${YELLOW}[3/5] 安装 Python 依赖...${NC}"
if python -c "import bilibili_subtitle; import anthropic; import dashscope" 2>/dev/null; then
    echo -e "${GREEN}✅ Python 依赖已安装${NC}"
else
    pip install -e "$SKILL_DIR[claude,transcribe]" -q
    pip install dashscope -q
    echo -e "${GREEN}✅ Python 依赖安装完成${NC}"
fi

# 4. 检查外部工具
echo ""
echo -e "${YELLOW}[4/5] 检查外部工具...${NC}"

# 检查 BBDown
if command -v BBDown &> /dev/null; then
    BBDOWN_VERSION=$(BBDown --help 2>&1 | head -n1 | grep -o 'version [0-9.]*' || echo "installed")
    echo -e "${GREEN}✅ BBDown 已安装 ($BBDOWN_VERSION)${NC}"
else
    echo -e "${YELLOW}⚠️  BBDown 未安装${NC}"
    echo "正在下载 BBDown..."
    BBDOWN_ZIP=$(curl -sL "https://api.github.com/repos/nilaoda/BBDown/releases/latest" | grep -o '"browser_download_url": "[^"]*osx-arm64.zip"' | cut -d'"' -f4)
    if [ -n "$BBDOWN_ZIP" ]; then
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
        fi
    else
        echo -e "${RED}❌ BBDown 下载链接获取失败${NC}"
        echo "请手动下载: https://github.com/nilaoda/BBDown/releases"
    fi
fi

# 检查 ffmpeg
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version 2>/dev/null | head -n1 | awk '{print $3}' || echo "unknown")
    echo -e "${GREEN}✅ ffmpeg 已安装 ($FFMPEG_VERSION)${NC}"
else
    echo -e "${YELLOW}⚠️  ffmpeg 未安装${NC}"
    if command -v brew &> /dev/null; then
        echo "正在通过 Homebrew 安装 ffmpeg..."
        brew install ffmpeg
        echo -e "${GREEN}✅ ffmpeg 安装完成${NC}"
    else
        echo -e "${RED}请手动安装 ffmpeg: brew install ffmpeg${NC}"
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
echo -e "  ${GREEN}source $VENV_DIR/bin/activate${NC}"
echo -e "  ${GREEN}python -m bilibili_subtitle \"BV1234567890\" --skip-proofread --skip-summary${NC}"
echo ""
