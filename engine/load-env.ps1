# Load SPREAD_URL and SPREAD_KEY from .env into the current PowerShell session.
Get-Content "$PSScriptRoot\.env" | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}
if ($env:SPREAD_KEY) { Write-Host "Loaded SPREAD_URL and SPREAD_KEY ($($env:SPREAD_KEY.Length) characters in the key)." }
else { Write-Host "No SPREAD_KEY found in .env" }
