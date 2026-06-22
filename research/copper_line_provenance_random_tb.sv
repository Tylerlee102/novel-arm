`timescale 1ns/1ps

module copper_line_provenance_random_tb;

    localparam int LINE_IDX_W = 3;
    localparam int WORDS_PER_LINE = 4;
    localparam int WORD_OFF_W = 2;
    localparam int DOMAIN_W = 4;
    localparam int LINES = 8;
    localparam int TRIALS = 2000;

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

    logic [WORDS_PER_LINE-1:0] model_proof [LINES];
    logic [DOMAIN_W-1:0] model_domain [LINES];
    logic last_commit_valid;
    logic [LINE_IDX_W-1:0] last_commit_line;
    logic [WORD_OFF_W-1:0] last_commit_word;
    logic [DOMAIN_W-1:0] last_commit_domain;
    int errors;
    int allowed_seen;
    int blocked_seen;

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

    function automatic logic expected_clean;
        expected_clean =
            model_proof[dmp_line_idx][dmp_word]
            && model_domain[dmp_line_idx] == dmp_src_domain;
    endfunction

    function automatic logic expected_allow;
        expected_allow =
            dmp_seed_valid
            && expected_clean()
            && dmp_src_domain == dmp_target_domain
            && dmp_translation_ok
            && dmp_permission_ok;
    endfunction

    task automatic check_outputs(input int trial);
        logic exp_clean;
        logic exp_allow;
        logic exp_block;
        begin
            exp_clean = expected_clean();
            exp_allow = expected_allow();
            exp_block = dmp_seed_valid && !exp_allow;

            if (source_proven_clean !== exp_clean) begin
                $error("trial %0d: clean expected %0b got %0b", trial, exp_clean, source_proven_clean);
                errors++;
            end
            if (dmp_seed_allow !== exp_allow) begin
                $error("trial %0d: allow expected %0b got %0b", trial, exp_allow, dmp_seed_allow);
                errors++;
            end
            if (dmp_seed_block !== exp_block) begin
                $error("trial %0d: block expected %0b got %0b", trial, exp_block, dmp_seed_block);
                errors++;
            end

            if (exp_allow) begin
                allowed_seen++;
            end
            if (exp_block) begin
                blocked_seen++;
            end
        end
    endtask

    task automatic update_model;
        begin
            if (line_fill_valid) begin
                model_proof[line_fill_idx] = '0;
                model_domain[line_fill_idx] = '0;
            end
            if (invalidate_valid) begin
                model_proof[invalidate_line_idx] = '0;
                model_domain[invalidate_line_idx] = '0;
            end
            if (write_valid) begin
                model_proof[write_line_idx][write_word] = 1'b0;
            end
            if (commit_ptr_valid) begin
                model_proof[commit_line_idx][commit_word] = 1'b1;
                model_domain[commit_line_idx] = commit_domain;
                last_commit_valid = 1'b1;
                last_commit_line = commit_line_idx;
                last_commit_word = commit_word;
                last_commit_domain = commit_domain;
            end
        end
    endtask

    task automatic drive_random(input int trial);
        int r;
        begin
            @(negedge clk);
            r = $urandom();

            commit_ptr_valid = (r[3:0] < 5);
            write_valid = (r[7:4] < 4);
            line_fill_valid = (r[11:8] < 2);
            invalidate_valid = (r[15:12] < 2);
            dmp_seed_valid = (r[19:16] < 12);

            commit_line_idx = $urandom_range(0, LINES - 1);
            commit_word = $urandom_range(0, WORDS_PER_LINE - 1);
            commit_domain = $urandom_range(0, (1 << DOMAIN_W) - 1);

            write_line_idx = $urandom_range(0, LINES - 1);
            write_word = $urandom_range(0, WORDS_PER_LINE - 1);
            line_fill_idx = $urandom_range(0, LINES - 1);
            invalidate_line_idx = $urandom_range(0, LINES - 1);

            dmp_line_idx = $urandom_range(0, LINES - 1);
            dmp_word = $urandom_range(0, WORDS_PER_LINE - 1);

            if (last_commit_valid && ((trial % 4) == 0)) begin
                dmp_line_idx = last_commit_line;
                dmp_word = last_commit_word;
                dmp_src_domain = last_commit_domain;
                dmp_target_domain = last_commit_domain;
                dmp_translation_ok = 1'b1;
                dmp_permission_ok = 1'b1;
            end else begin
                dmp_src_domain = $urandom_range(0, (1 << DOMAIN_W) - 1);
                dmp_target_domain = (trial % 3 == 0)
                    ? dmp_src_domain
                    : $urandom_range(0, (1 << DOMAIN_W) - 1);
                dmp_translation_ok = ($urandom_range(0, 9) != 0);
                dmp_permission_ok = ($urandom_range(0, 9) != 0);
            end

            #1;
            check_outputs(trial);
            @(posedge clk);
            #1;
            update_model();
        end
    endtask

    initial begin
        clear_inputs();
        errors = 0;
        allowed_seen = 0;
        blocked_seen = 0;
        last_commit_valid = 1'b0;
        last_commit_line = '0;
        last_commit_word = '0;
        last_commit_domain = '0;
        rst_n = 1'b0;

        for (int i = 0; i < LINES; i++) begin
            model_proof[i] = '0;
            model_domain[i] = '0;
        end

        repeat (3) @(negedge clk);
        rst_n = 1'b1;

        for (int trial = 0; trial < TRIALS; trial++) begin
            drive_random(trial);
        end

        clear_inputs();

        if (allowed_seen == 0) begin
            $error("random test did not exercise any allowed DMP seeds");
            errors++;
        end
        if (blocked_seen == 0) begin
            $error("random test did not exercise any blocked DMP seeds");
            errors++;
        end
        if (errors != 0) begin
            $fatal(1, "COPPER line provenance random invariant tests failed: errors=%0d", errors);
        end

        $display(
            "COPPER line provenance random invariant tests completed: trials=%0d allowed=%0d blocked=%0d errors=%0d",
            TRIALS,
            allowed_seen,
            blocked_seen,
            errors
        );
        $finish;
    end

endmodule
