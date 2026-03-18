#!/bin/bash

echo "========================================"
echo "论文阅读助手 - 启动脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

cd "$(dirname "$0")/backend"

echo "[1/5] 检查环境..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[2/5] 创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败"
        exit 1
    fi
fi

echo "[3/5] 激活虚拟环境..."
source venv/bin/activate

echo "[4/5] 安装依赖..."
pip install -r requirements.txt -q

echo "[5/5] 检查配置文件..."
if [ ! -f ".env" ]; then
    echo "警告: 未找到.env配置文件"
    echo "正在从.env.example创建..."
    cp .env.example .env
    echo ""
    echo "重要: 请编辑backend/.env文件，填入你的DeepSeek API密钥！"
    echo ""
    read -p "按Enter键继续..."
fi

echo ""
echo "========================================"
echo "启动后端服务..."
echo "========================================"
echo "后端地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "请在前端目录中打开index.html文件，"
echo "或使用: cd frontend && python3 -m http.server 8080"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

python main.py
