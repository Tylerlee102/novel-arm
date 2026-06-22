$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $Root '.venv'
$Python = Join-Path $Venv 'Scripts\python.exe'
$BasePythonArgs = @()
$BasePython = $env:COPPER_PYTHON
if (-not $BasePython) {
    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCmd) {
        $BasePython = $PythonCmd.Source
    } else {
        $PyCmd = Get-Command py -ErrorAction SilentlyContinue
        if ($PyCmd) {
            $BasePython = $PyCmd.Source
            $BasePythonArgs = @('-3')
        }
    }
}
if (-not $BasePython) {
    throw 'Python was not found. Install Python 3 or set COPPER_PYTHON to a Python 3 interpreter.'
}

if (!(Test-Path $Python)) {
    & $BasePython @BasePythonArgs -m venv $Venv
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Root 'requirements.txt')
& $Python (Join-Path $Root 'reproduce.py') --mode all-local
