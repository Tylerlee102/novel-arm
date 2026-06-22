source research/vivado_tclstore_bootstrap.tcl
puts "COPPER probe auto_path=$auto_path"
puts "COPPER probe tclapp commands=[info commands ::tclapp::*load*]"
puts "COPPER probe package xsim=[catch {package require ::tclapp::xilinx::xsim 2.520} msg]; msg=$msg"
puts "COPPER probe help load_apps=[catch {help ::tclapp::load_apps} msg]; msg=$msg"
puts "COPPER probe help load_catalog=[catch {help ::tclapp::load_catalog} msg]; msg=$msg"
puts "COPPER probe load_catalog default=[catch {::tclapp::load_catalog} msg]; msg=$msg"
puts "COPPER probe load_catalog installed=[catch {::tclapp::load_catalog C:/AMDDesignTools/2025.2/Vivado/data/XilinxTclStore 2025.2} msg]; msg=$msg"
puts "COPPER probe list apps=[catch {::tclapp::list_apps} msg]; msg=$msg"
puts "COPPER probe loaded apps=[catch {::tclapp::loaded_apps} msg]; msg=$msg"
if {[llength [info commands ::tclapp::load_app]]} {
    puts "COPPER probe load_app namespace=[catch {::tclapp::load_app -namespace {xilinx::xsim} xilinx::xsim} msg]; msg=$msg"
    puts "COPPER probe load_app plain=[catch {::tclapp::load_app xilinx::xsim} msg]; msg=$msg"
}
if {[llength [info commands ::tclapp::load_apps]]} {
    puts "COPPER probe load_apps namespace=[catch {::tclapp::load_apps -namespace {xilinx::xsim} xilinx::xsim} msg]; msg=$msg"
    puts "COPPER probe load_apps plain=[catch {::tclapp::load_apps xilinx::xsim} msg]; msg=$msg"
}
quit
