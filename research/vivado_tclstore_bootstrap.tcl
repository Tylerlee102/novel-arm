# Bootstrap Vivado TclStore package paths for batch synthesis on this machine.
#
# Vivado 2025.2 can fail before synthesis if a stale per-user Tcl app manifest
# is present. The synthesis scripts only need the installed Xilinx TclStore
# packages, so make those paths explicit and pre-load the appinit/xsim packages.

set copper_vivado_tclstore "C:/AMDDesignTools/2025.2/Vivado/data/XilinxTclStore"

foreach copper_tcl_path [list \
    "$copper_vivado_tclstore/support" \
    "$copper_vivado_tclstore/support/appinit" \
    "$copper_vivado_tclstore/tclapp" \
    "$copper_vivado_tclstore/tclapp/xilinx" \
    "$copper_vivado_tclstore/tclapp/xilinx/xsim"] {
    if {[file isdirectory $copper_tcl_path] && [lsearch -exact $auto_path $copper_tcl_path] < 0} {
        lappend auto_path $copper_tcl_path
    }
}

if {[catch {package require ::tclapp::support::appinit 1.2} copper_bootstrap_error]} {
    puts "WARNING: COPPER Vivado bootstrap could not load appinit: $copper_bootstrap_error"
}

if {[catch {package require ::tclapp::xilinx::xsim 2.520} copper_bootstrap_error]} {
    puts "WARNING: COPPER Vivado bootstrap could not load xsim Tcl app: $copper_bootstrap_error"
}

if {[llength [info commands ::tclapp::load_catalog]]} {
    if {[catch {::tclapp::load_catalog $copper_vivado_tclstore 2025.2} copper_bootstrap_error]} {
        puts "WARNING: COPPER Vivado bootstrap could not load TclStore catalog: $copper_bootstrap_error"
    }
}
