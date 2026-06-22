$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\xvlog.bat")) {
    Write-Error "xvlog.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

& "$VivadoBin\xvlog.bat" -sv research\copper_prefetch_gate.sv research\copper_prefetch_gate_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_prefetch_gate_tb -s copper_prefetch_gate_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_prefetch_gate_tb_sim -runall
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xvlog.bat" -sv research\copper_stream_gate.sv research\copper_stream_gate_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_stream_gate_tb -s copper_stream_gate_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_stream_gate_tb_sim -runall
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xvlog.bat" -sv research\copper_stream_table_gate.sv research\copper_stream_table_gate_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_stream_table_gate_tb -s copper_stream_table_gate_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_stream_table_gate_tb_sim -runall
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xvlog.bat" -sv research\copper_line_provenance_gate.sv research\copper_line_provenance_gate_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_line_provenance_gate_tb -s copper_line_provenance_gate_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_line_provenance_gate_tb_sim -runall
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xvlog.bat" -sv research\copper_line_provenance_gate.sv research\copper_line_provenance_random_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_line_provenance_random_tb -s copper_line_provenance_random_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_line_provenance_random_tb_sim -runall
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xvlog.bat" -sv research\copper_commit_epoch_proof_bridge.sv research\copper_commit_epoch_proof_bridge_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_commit_epoch_proof_bridge_tb -s copper_commit_epoch_proof_bridge_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_commit_epoch_proof_bridge_tb_sim -runall
exit $LASTEXITCODE
