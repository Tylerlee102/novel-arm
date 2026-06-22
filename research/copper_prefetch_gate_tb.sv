`timescale 1ns/1ps

module copper_prefetch_gate_tb;

    localparam int LINE_TAG_W = 8;
    localparam int WORD_OFF_W = 2;
    localparam int VALUE_TOKEN_W = 16;
    localparam int DOMAIN_W = 4;
    localparam int ENTRIES = 4;

    logic clk;
    logic rst_n;

    logic commit_ptr_valid;
    logic [LINE_TAG_W-1:0] commit_src_line;
    logic [WORD_OFF_W-1:0] commit_src_word;
    logic [VALUE_TOKEN_W-1:0] commit_value_token;
    logic [DOMAIN_W-1:0] commit_domain;

    logic coh_update_valid;
    logic [LINE_TAG_W-1:0] coh_update_line;

    logic dmp_seed_valid;
    logic [LINE_TAG_W-1:0] dmp_src_line;
    logic [WORD_OFF_W-1:0] dmp_src_word;
    logic [VALUE_TOKEN_W-1:0] dmp_value_token;
    logic [DOMAIN_W-1:0] dmp_domain;
    logic dmp_translation_ok;
    logic dmp_permission_ok;

    logic dmp_seed_allow;
    logic dmp_seed_block_stale;

    copper_prefetch_gate #(
        .LINE_TAG_W(LINE_TAG_W),
        .WORD_OFF_W(WORD_OFF_W),
        .VALUE_TOKEN_W(VALUE_TOKEN_W),
        .DOMAIN_W(DOMAIN_W),
        .ENTRIES(ENTRIES)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .commit_ptr_valid(commit_ptr_valid),
        .commit_src_line(commit_src_line),
        .commit_src_word(commit_src_word),
        .commit_value_token(commit_value_token),
        .commit_domain(commit_domain),
        .coh_update_valid(coh_update_valid),
        .coh_update_line(coh_update_line),
        .dmp_seed_valid(dmp_seed_valid),
        .dmp_src_line(dmp_src_line),
        .dmp_src_word(dmp_src_word),
        .dmp_value_token(dmp_value_token),
        .dmp_domain(dmp_domain),
        .dmp_translation_ok(dmp_translation_ok),
        .dmp_permission_ok(dmp_permission_ok),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block_stale(dmp_seed_block_stale)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic clear_inputs;
        begin
            commit_ptr_valid = 1'b0;
            commit_src_line = '0;
            commit_src_word = '0;
            commit_value_token = '0;
            commit_domain = '0;
            coh_update_valid = 1'b0;
            coh_update_line = '0;
            dmp_seed_valid = 1'b0;
            dmp_src_line = '0;
            dmp_src_word = '0;
            dmp_value_token = '0;
            dmp_domain = '0;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
        end
    endtask

    task automatic check_allow(
        input string label,
        input logic expected_allow,
        input logic expected_block
    );
        begin
            #1;
            if (dmp_seed_allow !== expected_allow) begin
                $error("%s: allow expected %0b got %0b", label, expected_allow, dmp_seed_allow);
            end
            if (dmp_seed_block_stale !== expected_block) begin
                $error("%s: block expected %0b got %0b", label, expected_block, dmp_seed_block_stale);
            end
        end
    endtask

    task automatic issue_commit(
        input [LINE_TAG_W-1:0] src_line,
        input [WORD_OFF_W-1:0] src_word,
        input [VALUE_TOKEN_W-1:0] value_token,
        input [DOMAIN_W-1:0] domain
    );
        begin
            @(negedge clk);
            clear_inputs();
            commit_ptr_valid = 1'b1;
            commit_src_line = src_line;
            commit_src_word = src_word;
            commit_value_token = value_token;
            commit_domain = domain;
            @(negedge clk);
            clear_inputs();
        end
    endtask

    task automatic issue_dmp(
        input [LINE_TAG_W-1:0] src_line,
        input [WORD_OFF_W-1:0] src_word,
        input [VALUE_TOKEN_W-1:0] value_token,
        input [DOMAIN_W-1:0] domain,
        input logic translation_ok,
        input logic permission_ok
    );
        begin
            clear_inputs();
            dmp_seed_valid = 1'b1;
            dmp_src_line = src_line;
            dmp_src_word = src_word;
            dmp_value_token = value_token;
            dmp_domain = domain;
            dmp_translation_ok = translation_ok;
            dmp_permission_ok = permission_ok;
        end
    endtask

    initial begin
        clear_inputs();
        rst_n = 1'b0;
        repeat (3) @(negedge clk);
        rst_n = 1'b1;

        issue_dmp(8'h10, 2'h0, 16'h1040, 4'h1, 1'b1, 1'b1);
        check_allow("unproven seed blocks", 1'b0, 1'b1);

        issue_commit(8'h10, 2'h0, 16'h1040, 4'h1);

        issue_dmp(8'h10, 2'h0, 16'h1040, 4'h1, 1'b1, 1'b1);
        check_allow("exact committed value allows", 1'b1, 1'b0);

        issue_dmp(8'h10, 2'h0, 16'h1080, 4'h1, 1'b1, 1'b1);
        check_allow("stale different value blocks", 1'b0, 1'b1);

        issue_dmp(8'h10, 2'h0, 16'h1040, 4'h2, 1'b1, 1'b1);
        check_allow("domain mismatch blocks", 1'b0, 1'b1);

        issue_dmp(8'h10, 2'h0, 16'h1040, 4'h1, 1'b0, 1'b1);
        check_allow("translation failure blocks", 1'b0, 1'b1);

        issue_dmp(8'h10, 2'h0, 16'h1040, 4'h1, 1'b1, 1'b0);
        check_allow("permission failure blocks", 1'b0, 1'b1);

        @(negedge clk);
        clear_inputs();
        coh_update_valid = 1'b1;
        coh_update_line = 8'h10;
        @(negedge clk);
        clear_inputs();

        issue_dmp(8'h10, 2'h0, 16'h1040, 4'h1, 1'b1, 1'b1);
        check_allow("coherence invalidation blocks", 1'b0, 1'b1);

        $display("COPPER gate directed tests completed");
        $finish;
    end

endmodule
