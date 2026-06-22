$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\xvlog.bat")) {
    Write-Error "xvlog.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

New-Item -ItemType Directory -Force research\results | Out-Null

& "$VivadoBin\xvlog.bat" -sv `
    research\copper_clpd_sram_dir.sv `
    research\copper_clpd_sram_dir_tb.sv `
    -log research\results\copper_clpd_sram_activity_xvlog.log
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" --debug wave `
    copper_clpd_sram_dir_tb `
    -s copper_clpd_sram_dir_tb_activity_sim `
    --log research\results\copper_clpd_sram_activity_xelab.log
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_clpd_sram_dir_tb_activity_sim `
    -tclbatch research/copper_clpd_sram_activity_xsim.tcl `
    -log research\results\copper_clpd_sram_activity_xsim.log
exit $LASTEXITCODE
