@echo off
echo ========================================
echo 论文阅读助手 - 启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/5] 检查环境...
cd /d "%~dp0backend"

REM 检查虚拟环境
if not exist "venv" (
    echo [2/5] 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
)

echo [3/5] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [4/5] 安装依赖...
pip install -r requirements.txt -q

echo [5/5] 检查配置文件...
if not exist ".env" (
    echo 警告: 未找到.env配置文件
    echo 正在从.env.example创建...
    copy .env.example .env >nul
    echo.
    echo 重要: 请编辑backend\.env文件，填入你的DeepSeek API密钥！
    echo.
    pause
)

echo.
echo ========================================
echo 启动后端服务...
echo ========================================
echo 后端地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 请在前端目录中打开index.html文件，
echo 或使用: cd frontend && python -m http.server 8080
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python main.py
