param()

$ErrorActionPreference = 'Stop'

$src = (Resolve-Path (Join-Path $PSScriptRoot 'COPPER_SCOOP_CONFERENCE_DRAFT.docx')).Path
$outDir = Join-Path $PSScriptRoot 'results\copper_scoop_docx_render_word'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$progress = Join-Path $outDir 'export_progress.txt'
Set-Content -LiteralPath $progress -Encoding ASCII -Value "start $(Get-Date -Format o)"

$tempDir = Join-Path $env:TEMP 'copper_scoop_docx_export'
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
$workDoc = Join-Path $tempDir 'input.docx'
$tempPdf = Join-Path $tempDir 'COPPER_SCOOP_CONFERENCE_DRAFT.pdf'
$pdf = Join-Path $outDir 'COPPER_SCOOP_CONFERENCE_DRAFT.pdf'

Copy-Item -LiteralPath $src -Destination $workDoc -Force
Remove-Item -LiteralPath $tempPdf,$pdf -Force -ErrorAction SilentlyContinue
Add-Content -LiteralPath $progress -Encoding ASCII -Value "copied $(Get-Date -Format o)"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
$word.Options.SaveNormalPrompt = $false

try {
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "before-open $(Get-Date -Format o)"
    $doc = $word.Documents.OpenNoRepairDialog($workDoc, $false, $true, $false)
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-open $(Get-Date -Format o)"
    $doc.Repaginate()
    $pages = $doc.ComputeStatistics(2)
    $words = $doc.ComputeStatistics(0)
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-count pages=$pages words=$words $(Get-Date -Format o)"
    $doc.ExportAsFixedFormat($tempPdf, 17, $false, 0, 0, 1, 1, 0, $false, $false, 0, $false, $true, $false)
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-pdf-export $(Get-Date -Format o)"
    $doc.Close(0)
    Copy-Item -LiteralPath $tempPdf -Destination $pdf -Force
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-copy-pdf $(Get-Date -Format o)"
    Write-Output "pages=$pages"
    Write-Output "words=$words"
    Write-Output "pdf=$pdf"
} finally {
    $word.Quit()
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "word-quit $(Get-Date -Format o)"
}
