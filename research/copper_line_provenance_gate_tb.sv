`timescale 1ns/1ps

module copper_line_provenance_gate_tb;

    localparam int LINE_IDX_W = 3;
    localparam int WORDS_PER_LINE = 4;
    localparam int WORD_OFF_W = 2;
    localparam int DOMAIN_W = 4;
    localparam int LINES = 8;

    logic clk;
    logic rst_n;
    logic commit_ptr_valid;
    logic [LINE_IDX_W-1:0] commit_line_idx;
    logic [WORD_OFF_W-1:0] commit_word;
    logic [DOMAIN_W-1:0] commit_domain;
    logic write_valid;
    logic [LINE_IDX_W-1:0] write_line_idx;
    logic [WORD_OFF_W-1:0] write_word;
    logic line_fill_valid;
    logic [LINE_IDX_W-1:0] line_fill_idx;
    logic invalidate_valid;
    logic [LINE_IDX_W-1:0] invalidate_line_idx;
    logic dmp_seed_valid;
    logic [LINE_IDX_W-1:0] dmp_line_idx;
    logic [WORD_OFF_W-1:0] dmp_word;
    logic [DOMAIN_W-1:0] dmp_src_domain;
    logic [DOMAIN_W-1:0] dmp_target_domain;
    logic dmp_translation_ok;
    logic dmp_permission_ok;
    logic dmp_seed_allow;
    logic dmp_seed_block;
    logic source_proven_clean;

    copper_line_provenance_gate #(
        .LINE_IDX_W(LINE_IDX_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .LINES(LINES)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .commit_ptr_valid(commit_ptr_valid),
        .commit_line_idx(commit_line_idx),
        .commit_word(commit_word),
        .commit_domain(commit_domain),
        .write_valid(write_valid),
        .write_line_idx(write_line_idx),
        .write_word(write_word),
        .line_fill_valid(line_fill_valid),
        .line_fill_idx(line_fill_idx),
        .invalidate_valid(invalidate_valid),
        .invalidate_line_idx(invalidate_line_idx),
        .dmp_seed_valid(dmp_seed_valid),
        .dmp_line_idx(dmp_line_idx),
        .dmp_word(dmp_word),
        .dmp_src_domain(dmp_src_domain),
        .dmp_target_domain(dmp_target_domain),
        .dmp_translation_ok(dmp_translation_ok),
        .dmp_permission_ok(dmp_permission_ok),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block(dmp_seed_block),
        .source_proven_clean(source_proven_clean)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic clear_inputs;
        begin
            commit_ptr_valid = 1'b0;
            commit_line_idx = '0;
            commit_word = '0;
            commit_domain = '0;
            write_valid = 1'b0;
            write_line_idx = '0;
            write_word = '0;
            line_fill_valid = 1'b0;
            line_fill_idx = '0;
            invalidate_valid = 1'b0;
            invalidate_line_idx = '0;
            dmp_seed_valid = 1'b0;
            dmp_line_idx = '0;
            dmp_word = '0;
            dmp_src_domain = '0;
            dmp_target_domain = '0;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
        end
    endtask

    task automatic commit_word_proof(
        input [LINE_IDX_W-1:0] line_idx,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] domain
    );
        begin
            @(negedge clk);
            clear_inputs();
            commit_ptr_valid = 1'b1;
            commit_line_idx = line_idx;
            commit_word = word;
            commit_domain = domain;
            @(negedge clk);
            clear_inputs();
        end
    endtask

    task automatic write_word_clear(
        input [LINE_IDX_W-1:0] line_idx,
        input [WORD_OFF_W-1:0] word
    );
        begin
            @(negedge clk);
            clear_inputs();
            write_valid = 1'b1;
            write_line_idx = line_idx;
            write_word = word;
            @(negedge clk);
            clear_inputs();
        end
    endtask

    task automatic fill_line_clear(input [LINE_IDX_W-1:0] line_idx);
        begin
            @(negedge clk);
            clear_inputs();
            line_fill_valid = 1'b1;
            line_fill_idx = line_idx;
            @(negedge clk);
            clear_inputs();
        end
    endtask

    task automatic invalidate_line_clear(input [LINE_IDX_W-1:0] line_idx);
        begin
            @(negedge clk);
            clear_inputs();
            invalidate_valid = 1'b1;
            invalidate_line_idx = line_idx;
            @(negedge clk);
            clear_inputs();
        end
    endtask

    task automatic issue_dmp(
        input [LINE_IDX_W-1:0] line_idx,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] src_domain,
        input [DOMAIN_W-1:0] target_domain,
        input logic translation_ok,
        input logic permission_ok
    );
        begin
            clear_inputs();
            dmp_seed_valid = 1'b1;
            dmp_line_idx = line_idx;
            dmp_word = word;
            dmp_src_domain = src_domain;
            dmp_target_domain = target_domain;
            dmp_translation_ok = translation_ok;
            dmp_permission_ok = permission_ok;
            #1;
        end
    endtask

    task automatic check(
        input string label,
        input logic expected_allow,
        input logic expected_block
    );
        begin
            if (dmp_seed_allow !== expected_allow) begin
                $error("%s: allow expected %0b got %0b", label, expected_allow, dmp_seed_allow);
            end
            if (dmp_seed_block !== expected_block) begin
                $error("%s: block expected %0b got %0b", label, expected_block, dmp_seed_block);
            end
        end
    endtask

    initial begin
        clear_inputs();
        rst_n = 1'b0;
        repeat (3) @(negedge clk);
        rst_n = 1'b1;

        issue_dmp(3'h2, 2'h1, 4'h1, 4'h1, 1'b1, 1'b1);
        check("unproven word blocks", 1'b0, 1'b1);

        commit_word_proof(3'h2, 2'h1, 4'h1);
        issue_dmp(3'h2, 2'h1, 4'h1, 4'h1, 1'b1, 1'b1);
        check("clean committed word allows", 1'b1, 1'b0);

        issue_dmp(3'h2, 2'h1, 4'h2, 4'h2, 1'b1, 1'b1);
        check("source domain mismatch blocks", 1'b0, 1'b1);

        issue_dmp(3'h2, 2'h1, 4'h1, 4'h2, 1'b1, 1'b1);
        check("target domain mismatch blocks", 1'b0, 1'b1);

        issue_dmp(3'h2, 2'h1, 4'h1, 4'h1, 1'b0, 1'b1);
        check("translation failure blocks", 1'b0, 1'b1);

        issue_dmp(3'h2, 2'h1, 4'h1, 4'h1, 1'b1, 1'b0);
        check("permission failure blocks", 1'b0, 1'b1);

        commit_word_proof(3'h2, 2'h2, 4'h1);
        write_word_clear(3'h2, 2'h1);
        issue_dmp(3'h2, 2'h1, 4'h1, 4'h1, 1'b1, 1'b1);
        check("write clears written word", 1'b0, 1'b1);

        issue_dmp(3'h2, 2'h2, 4'h1, 4'h1, 1'b1, 1'b1);
        check("write does not clear sibling word", 1'b1, 1'b0);

        fill_line_clear(3'h2);
        issue_dmp(3'h2, 2'h2, 4'h1, 4'h1, 1'b1, 1'b1);
        check("line fill clears all words", 1'b0, 1'b1);

        commit_word_proof(3'h3, 2'h0, 4'h1);
        invalidate_line_clear(3'h3);
        issue_dmp(3'h3, 2'h0, 4'h1, 4'h1, 1'b1, 1'b1);
        check("invalidation clears all words", 1'b0, 1'b1);

        $display("COPPER line provenance directed tests completed");
        $finish;
    end

endmodule
