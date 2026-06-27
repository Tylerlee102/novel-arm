`timescale 1ns/1ps

module copper_prefetch_unit_open_tb;
    logic clk;
    logic rst_n;
    logic copper_enable;
    logic commit_valid;
    logic commit_speculative;
    logic [47:0] commit_src_addr;
    logic [15:0] commit_value_token;
    logic demand_valid;
    logic [47:0] demand_src_addr;
    logic [15:0] demand_value_token;
    logic demand_translation_ok;
    logic demand_permission_ok;
    logic queue_pop;
    logic prefetch_valid;
    logic queue_full;
    logic blocked_unproven;
    logic blocked_disabled;
    logic blocked_permission;
    logic architectural_state_mutated;
    logic [3:0] queue_count;
    integer checks;
    integer errors;

    copper_prefetch_unit_open dut (
        .clk(clk),
        .rst_n(rst_n),
        .copper_enable(copper_enable),
        .commit_valid(commit_valid),
        .commit_speculative(commit_speculative),
        .commit_src_addr(commit_src_addr),
        .commit_value_token(commit_value_token),
        .demand_valid(demand_valid),
        .demand_src_addr(demand_src_addr),
        .demand_value_token(demand_value_token),
        .demand_translation_ok(demand_translation_ok),
        .demand_permission_ok(demand_permission_ok),
        .queue_pop(queue_pop),
        .prefetch_valid(prefetch_valid),
        .queue_full(queue_full),
        .blocked_unproven(blocked_unproven),
        .blocked_disabled(blocked_disabled),
        .blocked_permission(blocked_permission),
        .architectural_state_mutated(architectural_state_mutated),
        .queue_count(queue_count)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic clear_inputs;
        begin
            copper_enable = 1'b1;
            commit_valid = 1'b0;
            commit_speculative = 1'b0;
            commit_src_addr = '0;
            commit_value_token = '0;
            demand_valid = 1'b0;
            demand_src_addr = '0;
            demand_value_token = '0;
            demand_translation_ok = 1'b1;
            demand_permission_ok = 1'b1;
            queue_pop = 1'b0;
        end
    endtask

    task automatic check_bit(input string label, input logic actual, input logic expected);
        begin
            #1;
            checks = checks + 1;
            if (actual !== expected) begin
                $display("COPPER_ASSERTION_FAIL %s expected=%0b actual=%0b", label, expected, actual);
                errors = errors + 1;
            end
        end
    endtask

    task automatic commit_proof(input logic speculative);
        begin
            @(negedge clk);
            clear_inputs();
            commit_valid = 1'b1;
            commit_speculative = speculative;
            commit_src_addr = 48'h1000;
            commit_value_token = 16'h1040;
            @(negedge clk);
            clear_inputs();
        end
    endtask

    task automatic demand_candidate;
        begin
            clear_inputs();
            demand_valid = 1'b1;
            demand_src_addr = 48'h1000;
            demand_value_token = 16'h1040;
        end
    endtask

    initial begin
        checks = 0;
        errors = 0;
        clear_inputs();
        rst_n = 1'b0;
        repeat (3) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        check_bit("reset queue empty", queue_full, 1'b0);
        check_bit("reset no architectural mutation", architectural_state_mutated, 1'b0);

        demand_candidate();
        check_bit("unproven blocks", blocked_unproven, 1'b1);
        check_bit("unproven does not prefetch", prefetch_valid, 1'b0);

        commit_proof(1'b1);
        demand_candidate();
        check_bit("speculative commit rejected", prefetch_valid, 1'b0);

        commit_proof(1'b0);
        demand_candidate();
        check_bit("committed proof prefetches", prefetch_valid, 1'b1);
        check_bit("prefetch path no architectural mutation", architectural_state_mutated, 1'b0);
        @(negedge clk);
        clear_inputs();

        demand_candidate();
        check_bit("second request fills queue", prefetch_valid, 1'b1);
        @(negedge clk);
        clear_inputs();

        demand_candidate();
        check_bit("queue full blocks request", prefetch_valid, 1'b0);
        check_bit("queue full flag", queue_full, 1'b1);

        clear_inputs();
        copper_enable = 1'b0;
        demand_valid = 1'b1;
        demand_src_addr = 48'h1000;
        demand_value_token = 16'h1040;
        check_bit("disabled blocks", blocked_disabled, 1'b1);
        check_bit("disabled no prefetch", prefetch_valid, 1'b0);

        clear_inputs();
        demand_valid = 1'b1;
        demand_src_addr = 48'h1000;
        demand_value_token = 16'h1040;
        demand_permission_ok = 1'b0;
        check_bit("permission block", blocked_permission, 1'b1);
        check_bit("permission no prefetch", prefetch_valid, 1'b0);
        check_bit("blocked path no architectural mutation", architectural_state_mutated, 1'b0);

        if (errors == 0) begin
            $display("COPPER_ASSERTIONS_PASSED=%0d", checks);
            $display("COPPER_ASSERTIONS_FAILED=0");
            $display("COPPER open RTL directed tests completed");
            $finish;
        end
        $display("COPPER_ASSERTIONS_PASSED=%0d", checks - errors);
        $display("COPPER_ASSERTIONS_FAILED=%0d", errors);
        $display("COPPER open RTL directed tests failed");
        $finish;
    end
endmodule
