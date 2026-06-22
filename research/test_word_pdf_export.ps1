$ErrorActionPreference = 'Stop'

$outDir = Join-Path $PSScriptRoot 'results\word_pdf_smoke'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$progress = Join-Path $outDir 'progress.txt'
Set-Content -LiteralPath $progress -Encoding ASCII -Value "start $(Get-Date -Format o)"

$tempDir = Join-Path $env:TEMP 'word_pdf_smoke'
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
$docx = Join-Path $tempDir 'smoke.docx'
$pdf = Join-Path $tempDir 'smoke.pdf'
$finalPdf = Join-Path $outDir 'smoke.pdf'

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
$word.Options.SaveNormalPrompt = $false

try {
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "word-created $(Get-Date -Format o)"
    $doc = $word.Documents.Add()
    $doc.Content.Text = "COPPER Word PDF export smoke test"
    $doc.SaveAs2($docx, 16)
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-docx-save $(Get-Date -Format o)"
    if (Test-Path -LiteralPath $pdf) {
        Remove-Item -LiteralPath $pdf -Force
    }
    if (Test-Path -LiteralPath $finalPdf) {
        Remove-Item -LiteralPath $finalPdf -Force
    }
    $doc.ExportAsFixedFormat($pdf, 17, $false, 0, 0, 1, 1, 0, $false, $false, 0, $false, $true, $false)
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-export $(Get-Date -Format o)"
    $doc.Close(0)
    Copy-Item -LiteralPath $pdf -Destination $finalPdf -Force
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-copy $(Get-Date -Format o)"
    Write-Output "pdf=$finalPdf"
    Get-Item -LiteralPath $finalPdf | Select-Object FullName,Length
} finally {
    $word.Quit()
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "word-quit $(Get-Date -Format o)"
}
