`timescale 1ns/1ps

module copper_scoop_companion_arbiter_tb;
    localparam int ID_W = 8;

    logic primary_valid;
    logic [ID_W-1:0] primary_id;
    logic companion_valid;
    logic [ID_W-1:0] companion_id;
    logic sink_ready;
    logic primary_ready;
    logic companion_ready;
    logic issue_valid;
    logic issue_is_companion;
    logic [ID_W-1:0] issue_id;
    logic companion_blocked_by_primary;

    int errors;
    int directed;
    int random_cases;
    int primary_issues;
    int companion_issues;
    int companion_blocks;
    int sink_stalls;

    copper_scoop_companion_arbiter #(
        .ID_W(ID_W)
    ) dut (
        .primary_valid(primary_valid),
        .primary_id(primary_id),
        .companion_valid(companion_valid),
        .companion_id(companion_id),
        .sink_ready(sink_ready),
        .primary_ready(primary_ready),
        .companion_ready(companion_ready),
        .issue_valid(issue_valid),
        .issue_is_companion(issue_is_companion),
        .issue_id(issue_id),
        .companion_blocked_by_primary(companion_blocked_by_primary)
    );

    task automatic fail(input string msg);
        begin
            $error("%s", msg);
            errors++;
        end
    endtask

    task automatic drive_check(
        input string name,
        input logic p_valid,
        input logic c_valid,
        input logic ready
    );
        logic exp_issue_valid;
        logic exp_is_companion;
        logic exp_primary_ready;
        logic exp_companion_ready;
        logic [ID_W-1:0] exp_id;
        begin
            primary_valid = p_valid;
            companion_valid = c_valid;
            sink_ready = ready;
            primary_id = 8'hA0 ^ {7'b0, p_valid};
            companion_id = 8'h50 ^ {7'b0, c_valid};
            #1;

            exp_issue_valid = p_valid || c_valid;
            exp_is_companion = (!p_valid && c_valid);
            exp_primary_ready = p_valid && ready;
            exp_companion_ready = (!p_valid && c_valid && ready);
            exp_id = p_valid ? primary_id : (c_valid ? companion_id : '0);

            if (issue_valid !== exp_issue_valid) begin
                fail($sformatf("%s issue_valid expected %0b got %0b",
                    name, exp_issue_valid, issue_valid));
            end
            if (issue_is_companion !== exp_is_companion) begin
                fail($sformatf("%s issue_is_companion expected %0b got %0b",
                    name, exp_is_companion, issue_is_companion));
            end
            if (primary_ready !== exp_primary_ready) begin
                fail($sformatf("%s primary_ready expected %0b got %0b",
                    name, exp_primary_ready, primary_ready));
            end
            if (companion_ready !== exp_companion_ready) begin
                fail($sformatf("%s companion_ready expected %0b got %0b",
                    name, exp_companion_ready, companion_ready));
            end
            if (issue_id !== exp_id) begin
                fail($sformatf("%s issue_id expected 0x%0h got 0x%0h",
                    name, exp_id, issue_id));
            end
            if (primary_valid && issue_is_companion) begin
                fail($sformatf("%s violated primary-priority invariant", name));
            end
            if (primary_valid && companion_ready) begin
                fail($sformatf("%s companion was ready while primary valid", name));
            end
            if (companion_blocked_by_primary !== (p_valid && c_valid)) begin
                fail($sformatf("%s blocked flag mismatch", name));
            end

            if (ready && p_valid) primary_issues++;
            if (ready && !p_valid && c_valid) companion_issues++;
            if (p_valid && c_valid) companion_blocks++;
            if (!ready && (p_valid || c_valid)) sink_stalls++;
        end
    endtask

    initial begin
        errors = 0;
        directed = 0;
        random_cases = 0;
        primary_issues = 0;
        companion_issues = 0;
        companion_blocks = 0;
        sink_stalls = 0;

        drive_check("none_idle", 1'b0, 1'b0, 1'b1); directed++;
        drive_check("primary_only", 1'b1, 1'b0, 1'b1); directed++;
        drive_check("companion_only", 1'b0, 1'b1, 1'b1); directed++;
        drive_check("both_primary_wins", 1'b1, 1'b1, 1'b1); directed++;
        drive_check("both_stalled", 1'b1, 1'b1, 1'b0); directed++;
        drive_check("companion_stalled", 1'b0, 1'b1, 1'b0); directed++;

        for (int i = 0; i < 10000; i++) begin
            drive_check(
                $sformatf("random_%0d", i),
                $urandom_range(0, 1),
                $urandom_range(0, 1),
                $urandom_range(0, 1)
            );
            random_cases++;
        end

        $display(
            "SCOOP arbiter completed: directed=%0d random=%0d primary_issues=%0d companion_issues=%0d companion_blocks=%0d sink_stalls=%0d errors=%0d",
            directed,
            random_cases,
            primary_issues,
            companion_issues,
            companion_blocks,
            sink_stalls,
            errors
        );
        if (errors != 0) $finish(1);
        $finish(0);
    end

endmodule
