@echo off
echo === 数据分析服务启动脚本 ===
echo.

REM 设置环境变量
set OPENAI_BASE_URL=https://bi.ganjiuwanshi.com/v1
set OPENAI_MODEL_NAME=gpt-4o

echo 环境变量已设置:
echo OPENAI_BASE_URL=%OPENAI_BASE_URL%
echo OPENAI_MODEL_NAME=%OPENAI_MODEL_NAME%
echo.

REM 检查API Key
if "%OPENAI_API_KEY%"=="" (
    echo ❌ 警告: OPENAI_API_KEY 未设置
    echo 请设置您的API Key:
    echo set OPENAI_API_KEY=your_api_key_here
    echo.
    echo 或者运行以下命令设置API Key:
    echo set OPENAI_API_KEY=your_actual_api_key
    echo.
    set /p continue="是否继续启动服务? (y/n): "
    if /i not "%continue%"=="y" (
        echo 启动已取消
        pause
        exit /b
    )
) else (
    echo ✅ API Key已设置
)

echo.
echo 启动数据分析服务...
cd backend
python run.py
pause




