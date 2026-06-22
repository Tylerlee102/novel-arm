$ErrorActionPreference = "Stop"

$Scripts = @(
    "run_copper_full_authority_xsim.ps1",
    "run_copper_full_authority_sva_xsim.ps1",
    "run_copper_cepf_line_e2e_xsim.ps1",
    "run_copper_ctlw_witness_xsim.ps1",
    "run_copper_ctlw_full_authority_e2e_xsim.ps1",
    "run_copper_clpd_xsim.ps1",
    "run_copper_clpd_ctlw_authority_e2e_xsim.ps1",
    "run_copper_sari_revoker_xsim.ps1",
    "run_copper_sari_clpd_ctlw_authority_e2e_xsim.ps1",
    "run_copper_sari_scoped_authority_e2e_xsim.ps1"
)

$OutDir = "research\results\authority_regression"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Failed = @()

foreach ($Script in $Scripts) {
    $Base = [System.IO.Path]::GetFileNameWithoutExtension($Script)
    $Log = Join-Path $OutDir "$Base.log"
    Write-Host "RUN $Script"
    & ".\research\$Script" *>&1 | Tee-Object -FilePath $Log
    if ($LASTEXITCODE -ne 0) {
        $Failed += "$Script exit=$LASTEXITCODE"
        continue
    }
    $BadLog = Select-String -Path $Log -Pattern "Fatal:|ERROR:|errors=[1-9][0-9]*" -Quiet
    if ($BadLog) {
        $Failed += "$Script log_check_failed"
    }
}

if ($Failed.Count -ne 0) {
    Write-Error ("COPPER authority regression failed: " + ($Failed -join "; "))
    exit 1
}

Write-Host "COPPER authority regression completed: scripts=$($Scripts.Count) failed=0"
exit 0
