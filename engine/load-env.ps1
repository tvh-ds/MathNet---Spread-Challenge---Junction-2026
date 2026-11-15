# Nap SPREAD_URL va SPREAD_KEY tu file .env vao phien PowerShell hien tai.
Get-Content "$PSScriptRoot\.env" | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}
if ($env:SPREAD_KEY) { Write-Host "Da nap SPREAD_URL va SPREAD_KEY (key dai $($env:SPREAD_KEY.Length) ky tu)." }
else { Write-Host "Chua thay SPREAD_KEY trong .env" }
