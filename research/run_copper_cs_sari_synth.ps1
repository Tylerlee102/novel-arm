$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"
$TclStore = "C:\AMDDesignTools\2025.2\Vivado\data\XilinxTclStore"

if (!(Test-Path "$VivadoBin\vivado.bat")) {
    Write-Error "vivado.bat was not found. Edit `$VivadoBin in this script."
    exit 1
}

$TclStoreUnix = $TclStore -replace "\\", "/"
$env:TCLLIBPATH = @(
    "{$TclStoreUnix/support}",
    "{$TclStoreUnix/support/appinit}",
    "{$TclStoreUnix/tclapp}",
    "{$TclStoreUnix/tclapp/xilinx}",
    "{$TclStoreUnix/tclapp/xilinx/xsim}"
) -join " "

& "$VivadoBin\vivado.bat" -mode batch -source research\run_copper_cs_sari_synth.tcl
exit $LASTEXITCODE
