$VivadoBat = "C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat"

if (!(Test-Path $VivadoBat)) {
    Write-Error "Vivado was not found at $VivadoBat. Edit this file and set `$VivadoBat to your installed vivado.bat path."
    exit 1
}

$VivadoBin = Split-Path $VivadoBat
$env:Path = "$VivadoBin;$env:Path"
Write-Host "Vivado linked for this PowerShell session:"
& $VivadoBat -version
