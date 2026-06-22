$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\vivado.bat")) {
    Write-Error "vivado.bat was not found. Edit `$VivadoBin in this script."
    exit 1
}

& "$VivadoBin\vivado.bat" -mode batch -source research\run_copper_line_synth.tcl
exit $LASTEXITCODE
