$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\xvlog.bat")) {
    Write-Error "xvlog.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

if (!(Test-Path "research\results")) {
    New-Item -ItemType Directory -Path "research\results" | Out-Null
}

& "$VivadoBin\xvlog.bat" -sv research\copper_ropl_lsq_retire_guard.sv research\copper_ropl_lsq_retire_guard_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_ropl_lsq_retire_guard_tb -s copper_ropl_lsq_retire_guard_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_ropl_lsq_retire_guard_tb_sim -runall -log research\results\copper_ropl_lsq_retire_guard_xsim_20260620.log
exit $LASTEXITCODE
