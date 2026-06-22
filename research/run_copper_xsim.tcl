create_project copper_gate_sim .copper_vivado_sim -part xc7a35tcpg236-1 -force
set_property target_language SystemVerilog [current_project]

add_files -fileset sim_1 {research/copper_prefetch_gate.sv}
add_files -fileset sim_1 {research/copper_prefetch_gate_tb.sv}
set_property top copper_prefetch_gate_tb [get_filesets sim_1]

launch_simulation -simset sim_1 -mode behavioral
run all
quit
