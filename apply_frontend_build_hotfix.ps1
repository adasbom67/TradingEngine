$path = "operator-console\src\App.tsx"

if (-not (Test-Path $path)) {
    throw "Could not find $path. Run this script from the TradingEngine project root."
}

$content = Get-Content $path -Raw

$content = $content.Replace(
    'check.name.replaceAll("_", " ")',
    'check.name.replace(/_/g, " ")'
)

$content = $content.Replace(
    'trade.exit_reason.replaceAll("_", " ")',
    'trade.exit_reason.replace(/_/g, " ")'
)

Set-Content -Path $path -Value $content -Encoding UTF8

Write-Host "Updated $path"
