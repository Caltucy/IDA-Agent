# PowerShell脚本：设置环境变量并启动服务
Write-Host "=== 数据分析服务启动脚本 ===" -ForegroundColor Green

# 设置环境变量
$env:OPENAI_BASE_URL = "https://bi.ganjiuwanshi.com/v1"
$env:OPENAI_MODEL_NAME = "gpt-4o"

Write-Host "环境变量已设置:" -ForegroundColor Yellow
Write-Host "OPENAI_BASE_URL: $env:OPENAI_BASE_URL"
Write-Host "OPENAI_MODEL_NAME: $env:OPENAI_MODEL_NAME"

# 检查API Key
if (-not $env:OPENAI_API_KEY) {
    Write-Host "❌ 警告: OPENAI_API_KEY 未设置" -ForegroundColor Red
    Write-Host "请设置您的API Key:" -ForegroundColor Yellow
    Write-Host '$env:OPENAI_API_KEY = "your_api_key_here"' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "或者运行以下命令设置API Key:" -ForegroundColor Yellow
    Write-Host 'Set-Item -Path "env:OPENAI_API_KEY" -Value "your_actual_api_key"' -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "是否继续启动服务? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "启动已取消" -ForegroundColor Red
        exit
    }
} else {
    Write-Host "✅ API Key已设置" -ForegroundColor Green
}

# 启动服务
Write-Host ""
Write-Host "启动数据分析服务..." -ForegroundColor Green
cd backend
python run.py




