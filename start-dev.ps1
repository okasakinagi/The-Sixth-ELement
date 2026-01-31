# The Sixth Element 一键启动开发环境
# 使用方法: 右键点击此文件 -> "使用 PowerShell 运行"
# 或在终端执行: .\start-dev.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  The Sixth Element 开发环境启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# 启动后端 Django
Write-Host "[1/2] 启动后端 Django 服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python Main.py runserver; Read-Host 'Press Enter to exit'"

Start-Sleep -Seconds 2

# 启动前端 Vite
Write-Host "[2/2] 启动前端 Vite 服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend\sixth_element'; npm run dev; Read-Host 'Press Enter to exit'"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host "  后端: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  前端: http://localhost:5173" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
