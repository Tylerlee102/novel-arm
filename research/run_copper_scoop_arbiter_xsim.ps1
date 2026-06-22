$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\xvlog.bat")) {
    Write-Error "xvlog.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

& "$VivadoBin\xvlog.bat" -sv research\copper_scoop_companion_arbiter.sv research\copper_scoop_companion_arbiter_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_scoop_companion_arbiter_tb -s copper_scoop_companion_arbiter_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_scoop_companion_arbiter_tb_sim -runall
exit $LASTEXITCODE
