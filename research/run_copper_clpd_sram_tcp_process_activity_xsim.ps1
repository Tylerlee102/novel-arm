$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"
$Python = $env:COPPER_PYTHON
if (-not $Python) {
    $Python = "python"
}

if (!(Test-Path "$VivadoBin\xvlog.bat")) {
    Write-Error "xvlog.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

if (!(Get-Command $Python -ErrorAction SilentlyContinue) -and !(Test-Path $Python)) {
    Write-Error "Python was not found. Put python on PATH or set COPPER_PYTHON to the local interpreter."
    exit 1
}

New-Item -ItemType Directory -Force research\results | Out-Null

& $Python research\build_copper_tcp_process_clpd_replay.py | Out-Host
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$CountsPath = "research\results\copper_clpd_tcp_process_replay_counts_20260620.json"
if (!(Test-Path $CountsPath)) {
    Write-Error "TCP process replay count file was not generated."
    exit 1
}

& "$VivadoBin\xvlog.bat" -sv -d TCP_PROCESS_REPLAY `
    research\copper_clpd_sram_dir.sv `
    research\copper_clpd_sram_workload_activity_tb.sv `
    -log research\results\copper_clpd_sram_tcp_process_activity_xvlog.log
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" --debug wave `
    copper_clpd_sram_workload_activity_tb `
    -s copper_clpd_sram_tcp_process_activity_sim `
    --log research\results\copper_clpd_sram_tcp_process_activity_xelab.log
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_clpd_sram_tcp_process_activity_sim `
    -tclbatch research/copper_clpd_sram_tcp_process_activity_saif_xsim.tcl `
    -log research\results\copper_clpd_sram_tcp_process_activity_xsim.log
exit $LASTEXITCODE

