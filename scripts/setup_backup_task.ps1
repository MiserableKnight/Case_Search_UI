# 使用 UTF-8 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$(Get-Location)\scripts\run_backup.bat`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

$TaskName = "WeeklyDataBackup"
$Description = "Weekly Data Backup Task"

# 如果任务已存在，则删除
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# 创建新任务
Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName $TaskName -Description $Description

Write-Host "Backup task has been set successfully! It will run every Sunday at 2 AM."
