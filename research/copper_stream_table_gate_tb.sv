`timescale 1ns/1ps

module copper_stream_table_gate_tb;

    localparam int STREAM_ID_W = 4;
    localparam int LINE_TAG_W = 8;
    localparam int WORD_OFF_W = 2;
    localparam int DOMAIN_W = 4;
    localparam int STREAM_ENTRIES = 2;
    localparam int DIRTY_ENTRIES = 2;
    localparam int TRAIN_THRESHOLD = 3;

    logic clk;
    logic rst_n;
    logic epoch_advance;
    logic commit_ptr_valid;
    logic [STREAM_ID_W-1:0] commit_stream_id;
    logic [LINE_TAG_W-1:0] commit_src_line;
    logic [WORD_OFF_W-1:0] commit_src_word;
    logic [DOMAIN_W-1:0] commit_domain;
    logic source_dirty_valid;
    logic [LINE_TAG_W-1:0] source_dirty_line;
    logic [WORD_OFF_W-1:0] source_dirty_word;
    logic [DOMAIN_W-1:0] source_dirty_domain;
    logic dmp_seed_valid;
    logic [STREAM_ID_W-1:0] dmp_stream_id;
    logic [LINE_TAG_W-1:0] dmp_src_line;
    logic [WORD_OFF_W-1:0] dmp_src_word;
    logic [DOMAIN_W-1:0] dmp_src_domain;
    logic [DOMAIN_W-1:0] dmp_target_domain;
    logic dmp_translation_ok;
    logic dmp_permission_ok;
    logic dmp_seed_allow;
    logic dmp_seed_block;
    logic dirty_overflow;

    copper_stream_table_gate #(
        .STREAM_ID_W(STREAM_ID_W),
        .LINE_TAG_W(LINE_TAG_W),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .STREAM_ENTRIES(STREAM_ENTRIES),
        .DIRTY_ENTRIES(DIRTY_ENTRIES),
        .TRAIN_THRESHOLD(TRAIN_THRESHOLD)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .epoch_advance(epoch_advance),
        .commit_ptr_valid(commit_ptr_valid),
        .commit_stream_id(commit_stream_id),
        .commit_src_line(commit_src_line),
        .commit_src_word(commit_src_word),
        .commit_domain(commit_domain),
        .source_dirty_valid(source_dirty_valid),
        .source_dirty_line(source_dirty_line),
        .source_dirty_word(source_dirty_word),
        .source_dirty_domain(source_dirty_domain),
        .dmp_seed_valid(dmp_seed_valid),
        .dmp_stream_id(dmp_stream_id),
        .dmp_src_line(dmp_src_line),
        .dmp_src_word(dmp_src_word),
        .dmp_src_domain(dmp_src_domain),
        .dmp_target_domain(dmp_target_domain),
        .dmp_translation_ok(dmp_translation_ok),
        .dmp_permission_ok(dmp_permission_ok),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block(dmp_seed_block),
        .dirty_overflow(dirty_overflow)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic clear_inputs;
        begin
            epoch_advance = 1'b0;
            commit_ptr_valid = 1'b0;
            commit_stream_id = '0;
            commit_src_line = '0;
            commit_src_word = '0;
            commit_domain = '0;
            source_dirty_valid = 1'b0;
            source_dirty_line = '0;
            source_dirty_word = '0;
            source_dirty_domain = '0;
            dmp_seed_valid = 1'b0;
            dmp_stream_id = '0;
            dmp_src_line = '0;
            dmp_src_word = '0;
            dmp_src_domain = '0;
            dmp_target_domain = '0;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
        end
    endtask

    task automatic commit_source(
        input [STREAM_ID_W-1:0] stream_id,
        input [LINE_TAG_W-1:0] line,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] domain
    );
        begin
            @(negedge clk);
            clear_inputs();
            commit_ptr_valid = 1'b1;
            commit_stream_id = stream_id;
            commit_src_line = line;
            commit_src_word = word;
            commit_domain = domain;
            @(negedge clk);
            clear_inputs();
        end
    endtask

    task automatic mark_dirty(
        input [LINE_TAG_W-1:0] line,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] domain
    );
        begin
            @(negedge clk);
            clear_inputs();
            source_dirty_valid = 1'b1;
            source_dirty_line = line;
            source_dirty_word = word;
            source_dirty_domain = domain;
            @(negedge clk);
            clear_inputs();
        end
    endtask

    task automatic issue_dmp(
        input [STREAM_ID_W-1:0] stream_id,
        input [LINE_TAG_W-1:0] line,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] src_domain,
        input [DOMAIN_W-1:0] target_domain,
        input logic translation_ok,
        input logic permission_ok
    );
        begin
            clear_inputs();
            dmp_seed_valid = 1'b1;
            dmp_stream_id = stream_id;
            dmp_src_line = line;
            dmp_src_word = word;
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

        issue_dmp(4'h1, 8'h10, 2'h0, 4'h1, 4'h1, 1'b1, 1'b1);
        check("untrained stream blocks", 1'b0, 1'b1);

        commit_source(4'h1, 8'h10, 2'h0, 4'h1);
        commit_source(4'h1, 8'h11, 2'h0, 4'h1);
        commit_source(4'h1, 8'h12, 2'h0, 4'h1);

        @(negedge clk);
        clear_inputs();
        epoch_advance = 1'b1;
        @(negedge clk);
        clear_inputs();

        issue_dmp(4'h1, 8'h10, 2'h0, 4'h1, 4'h1, 1'b1, 1'b1);
        check("trained stream allows", 1'b1, 1'b0);

        issue_dmp(4'h2, 8'h10, 2'h0, 4'h1, 4'h1, 1'b1, 1'b1);
        check("unknown stream blocks", 1'b0, 1'b1);

        mark_dirty(8'h10, 2'h0, 4'h1);
        issue_dmp(4'h1, 8'h10, 2'h0, 4'h1, 4'h1, 1'b1, 1'b1);
        check("dirty source blocks", 1'b0, 1'b1);

        commit_source(4'h1, 8'h10, 2'h0, 4'h1);
        issue_dmp(4'h1, 8'h10, 2'h0, 4'h1, 4'h1, 1'b1, 1'b1);
        check("commit clears dirty", 1'b1, 1'b0);

        issue_dmp(4'h1, 8'h10, 2'h0, 4'h1, 4'h2, 1'b1, 1'b1);
        check("target domain mismatch blocks", 1'b0, 1'b1);

        issue_dmp(4'h1, 8'h10, 2'h0, 4'h1, 4'h1, 1'b0, 1'b1);
        check("translation failure blocks", 1'b0, 1'b1);

        issue_dmp(4'h1, 8'h10, 2'h0, 4'h1, 4'h1, 1'b1, 1'b0);
        check("permission failure blocks", 1'b0, 1'b1);

        mark_dirty(8'h20, 2'h0, 4'h1);
        mark_dirty(8'h21, 2'h0, 4'h1);
        mark_dirty(8'h22, 2'h0, 4'h1);
        if (!dirty_overflow) begin
            $error("dirty overflow should be set");
        end

        issue_dmp(4'h1, 8'h12, 2'h0, 4'h1, 4'h1, 1'b1, 1'b1);
        check("dirty overflow fails safe", 1'b0, 1'b1);

        $display("COPPER stream table gate directed tests completed");
        $finish;
    end

endmodule
