param(
    [switch]$AttemptPdfExport,
    [switch]$UseWordPdfExport
)

$ErrorActionPreference = 'Stop'

$src = (Resolve-Path (Join-Path $PSScriptRoot 'COPPER_CONFERENCE_DRAFT.docx')).Path
$outDir = Join-Path $PSScriptRoot 'results\copper_full_docx_render_word'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$progress = Join-Path $outDir 'export_progress.txt'
Set-Content -LiteralPath $progress -Encoding ASCII -Value "start $(Get-Date -Format o)"

$tempDir = Join-Path $env:TEMP 'copper_docx_export'
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

$workDoc = Join-Path $tempDir 'input.docx'
$pdf = Join-Path $outDir 'COPPER_CONFERENCE_DRAFT.pdf'
$tempPdf = Join-Path $tempDir 'COPPER_CONFERENCE_DRAFT.pdf'
Copy-Item -LiteralPath $src -Destination $workDoc -Force
Add-Content -LiteralPath $progress -Encoding ASCII -Value "copied $(Get-Date -Format o)"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
$word.Options.SaveNormalPrompt = $false
Add-Content -LiteralPath $progress -Encoding ASCII -Value "word-created $(Get-Date -Format o)"

try {
    if ($AttemptPdfExport -and $UseWordPdfExport) {
        if (Test-Path -LiteralPath $pdf) {
            Remove-Item -LiteralPath $pdf -Force
        }
        if (Test-Path -LiteralPath $tempPdf) {
            Remove-Item -LiteralPath $tempPdf -Force
        }
    }
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "before-open $(Get-Date -Format o)"
    $doc = $word.Documents.OpenNoRepairDialog($workDoc, $false, $true, $false)
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-open $(Get-Date -Format o)"
    $doc.Repaginate()
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-repaginate $(Get-Date -Format o)"
    $pages = $doc.ComputeStatistics(2)
    $words = $doc.ComputeStatistics(0)
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-count pages=$pages words=$words $(Get-Date -Format o)"
    if ($AttemptPdfExport -and $UseWordPdfExport) {
        $doc.ExportAsFixedFormat($tempPdf, 17, $false, 0, 0, 1, 1, 0, $false, $false, 0, $false, $true, $false)
        Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-temp-pdf-export $(Get-Date -Format o)"
    } elseif ($AttemptPdfExport) {
        Add-Content -LiteralPath $progress -Encoding ASCII -Value "word-pdf-export-disabled $(Get-Date -Format o)"
    } else {
        Add-Content -LiteralPath $progress -Encoding ASCII -Value "pdf-export-skipped $(Get-Date -Format o)"
    }
    $doc.Close(0)
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-close $(Get-Date -Format o)"
    if ($AttemptPdfExport -and $UseWordPdfExport) {
        Copy-Item -LiteralPath $tempPdf -Destination $pdf -Force
        Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-copy-pdf $(Get-Date -Format o)"
    }
    if ($AttemptPdfExport -and !$UseWordPdfExport) {
        $python = $env:COPPER_PYTHON
        if (-not $python) {
            $python = 'python'
        }
        $builder = Join-Path $PSScriptRoot 'build_copper_review_pdf.py'
        & $python $builder | Out-File -FilePath (Join-Path $outDir 'direct_pdf_build.txt') -Encoding ASCII
        if ($LASTEXITCODE -ne 0) {
            throw "direct PDF builder failed with exit code $LASTEXITCODE"
        }
        $directPdf = Join-Path $PSScriptRoot 'results\COPPER_CONFERENCE_DRAFT_REVIEW.pdf'
        Copy-Item -LiteralPath $directPdf -Destination $pdf -Force
        Add-Content -LiteralPath $progress -Encoding ASCII -Value "after-direct-pdf-copy $(Get-Date -Format o)"
    }

    Write-Output "pages=$pages"
    Write-Output "words=$words"
    Write-Output "pdf_export=$($AttemptPdfExport.IsPresent)"
    if ($AttemptPdfExport) {
        Write-Output "pdf=$pdf"
        Write-Output "word_pdf_export=$($UseWordPdfExport.IsPresent)"
    }
} finally {
    $word.Quit()
    Add-Content -LiteralPath $progress -Encoding ASCII -Value "word-quit $(Get-Date -Format o)"
}

