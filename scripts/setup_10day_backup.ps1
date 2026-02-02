# 使用 UTF-8 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ============================================================================
# 10天定期备份任务设置脚本
# 功能: 创建Windows计划任务，每10天自动执行智能备份检查
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      10天定期备份任务设置工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptPath
$BackupBatchFile = Join-Path $ScriptPath "smart_backup_check.bat"

# 检查备份脚本是否存在
if (-not (Test-Path $BackupBatchFile)) {
    Write-Host "[错误] 备份脚本不存在: $BackupBatchFile" -ForegroundColor Red
    Write-Host "请确保 smart_backup_check.bat 文件存在于 scripts 目录中" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 任务设置
$TaskName = "TenDaySmartBackup"
$TaskDescription = "每10天自动执行智能数据备份检查"
$BatchFilePath = $BackupBatchFile

# 创建任务动作
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchFilePath`""

# 创建触发器 - 每10天执行一次，凌晨2点开始
$Trigger = New-ScheduledTaskTrigger -Daily -DaysInterval 10 -At 2am

# 任务设置
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# 检查任务是否已存在
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "发现已存在的备份任务，正在删除..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Write-Host "旧任务已删除" -ForegroundColor Green
}

# 注册新任务
try {
    Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName $TaskName -Description $TaskDescription -ErrorAction Stop
    Write-Host "✓ 10天定期备份任务创建成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "任务详情:" -ForegroundColor Cyan
    Write-Host "  任务名称: $TaskName"
    Write-Host "  执行频率: 每10天一次"
    Write-Host "  执行时间: 凌晨2:00"
    Write-Host "  执行脚本: $BatchFilePath"
    Write-Host "  任务描述: $TaskDescription"
    Write-Host ""
    Write-Host "下次执行时间:" -ForegroundColor Cyan
    $NextRun = (Get-ScheduledTask -TaskName $TaskName).Triggers[0].StartBoundary
    $NextRunTime = [DateTime]::Parse($NextRun)
    Write-Host "  $NextRunTime"
    Write-Host ""

    # 询问是否立即测试
    $TestTask = Read-Host "是否立即测试备份任务? (Y/N) [默认: N]"
    if ($TestTask -eq "Y" -or $TestTask -eq "y") {
        Write-Host "正在测试备份任务..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "任务已启动，请查看输出结果" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "你可以通过以下方式管理任务:" -ForegroundColor Cyan
    Write-Host "  1. Windows任务计划程序 -> 任务计划程序库"
    Write-Host "  2. PowerShell命令: Get-ScheduledTask -TaskName `"$TaskName`""
    Write-Host "  3. 手动运行: Start-ScheduledTask -TaskName `"$TaskName`""
    Write-Host ""
    Write-Host "如需删除任务，请运行:" -ForegroundColor Red
    Write-Host "  Unregister-ScheduledTask -TaskName `"$TaskName`" -Confirm:`$false"

} catch {
    Write-Host "[错误] 任务创建失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "请检查是否有管理员权限" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "按回车键退出"
