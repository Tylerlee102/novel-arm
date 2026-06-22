`timescale 1ns/1ps

module copper_rocca_clpd_commit_adapter_tb;

    localparam int LINE_TAG_W = 8;
    localparam int WORDS_PER_LINE = 8;
    localparam int WORD_OFF_W = 3;
    localparam int TOKEN_W = 5;
    localparam int EPOCH_W = 4;
    localparam int ENTRIES = 16;
    localparam int ENTRY_IDX_W = 4;
    localparam int TRIALS = 20000;

    logic clk;
    logic rst_n;

    logic ropl_proof_valid;
    logic [LINE_TAG_W-1:0] ropl_line_tag;
    logic [WORD_OFF_W-1:0] ropl_word;
    logic [TOKEN_W-1:0] ropl_token;
    logic [EPOCH_W-1:0] ropl_epoch;
    logic source_clean;
    logic source_epoch_match;
    logic commit_translation_ok;
    logic commit_permission_ok;
    logic global_clear_valid;
    logic source_write_valid;
    logic [LINE_TAG_W-1:0] source_write_line_tag;
    logic line_fill_valid;
    logic [LINE_TAG_W-1:0] line_fill_tag;
    logic invalidate_valid;
    logic [LINE_TAG_W-1:0] invalidate_line_tag;

    logic clpd_commit_ptr_valid;
    logic [LINE_TAG_W-1:0] clpd_commit_line_tag;
    logic [WORD_OFF_W-1:0] clpd_commit_word;
    logic [TOKEN_W-1:0] clpd_commit_token;
    logic [EPOCH_W-1:0] clpd_commit_line_epoch;
    logic same_cycle_clear_hit;
    logic blocked_no_retire_proof;
    logic blocked_source_not_clean;
    logic blocked_epoch_mismatch;
    logic blocked_fault_or_perm;
    logic blocked_clear_wins;

    logic dmp_seed_valid;
    logic [LINE_TAG_W-1:0] dmp_line_tag;
    logic [WORD_OFF_W-1:0] dmp_word;
    logic [TOKEN_W-1:0] dmp_src_token;
    logic [TOKEN_W-1:0] dmp_target_token;
    logic [EPOCH_W-1:0] dmp_line_epoch;
    logic dmp_translation_ok;
    logic dmp_permission_ok;
    logic source_line_hit;
    logic source_word_proven;
    logic source_authorized;
    logic dmp_seed_allow;
    logic dmp_seed_block;
    logic block_no_entry;
    logic block_word_unproven;
    logic block_stale_epoch;
    logic block_token_mismatch;
    logic block_fault_or_perm;

    logic exp_valid [ENTRIES];
    logic [LINE_TAG_W-1:0] exp_tag [ENTRIES];
    logic [TOKEN_W-1:0] exp_token [ENTRIES];
    logic [EPOCH_W-1:0] exp_epoch [ENTRIES];
    logic [WORDS_PER_LINE-1:0] exp_mask [ENTRIES];

    int errors;
    int legal_commit_seen;
    int clear_win_seen;
    int allow_seen;
    int token_mismatch_seen;
    int stale_epoch_seen;
    int fault_perm_seen;
    int source_not_clean_seen;
    int random_commit_seen;
    int random_clear_win_seen;

    logic [LINE_TAG_W-1:0] last_line;
    logic [WORD_OFF_W-1:0] last_word;
    logic [TOKEN_W-1:0] last_token;
    logic [EPOCH_W-1:0] last_epoch;

    copper_rocca_clpd_commit_adapter #(
        .LINE_TAG_W(LINE_TAG_W),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W)
    ) adapter (
        .ropl_proof_valid(ropl_proof_valid),
        .ropl_line_tag(ropl_line_tag),
        .ropl_word(ropl_word),
        .ropl_token(ropl_token),
        .ropl_epoch(ropl_epoch),
        .source_clean(source_clean),
        .source_epoch_match(source_epoch_match),
        .commit_translation_ok(commit_translation_ok),
        .commit_permission_ok(commit_permission_ok),
        .global_clear_valid(global_clear_valid),
        .source_write_valid(source_write_valid),
        .source_write_line_tag(source_write_line_tag),
        .line_fill_valid(line_fill_valid),
        .line_fill_tag(line_fill_tag),
        .invalidate_valid(invalidate_valid),
        .invalidate_line_tag(invalidate_line_tag),
        .clpd_commit_ptr_valid(clpd_commit_ptr_valid),
        .clpd_commit_line_tag(clpd_commit_line_tag),
        .clpd_commit_word(clpd_commit_word),
        .clpd_commit_token(clpd_commit_token),
        .clpd_commit_line_epoch(clpd_commit_line_epoch),
        .same_cycle_clear_hit(same_cycle_clear_hit),
        .blocked_no_retire_proof(blocked_no_retire_proof),
        .blocked_source_not_clean(blocked_source_not_clean),
        .blocked_epoch_mismatch(blocked_epoch_mismatch),
        .blocked_fault_or_perm(blocked_fault_or_perm),
        .blocked_clear_wins(blocked_clear_wins)
    );

    copper_clpd_gate #(
        .LINE_TAG_W(LINE_TAG_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W),
        .ENTRIES(ENTRIES),
        .ENTRY_IDX_W(ENTRY_IDX_W)
    ) clpd (
        .clk(clk),
        .rst_n(rst_n),
        .commit_ptr_valid(clpd_commit_ptr_valid),
        .commit_line_tag(clpd_commit_line_tag),
        .commit_word(clpd_commit_word),
        .commit_token(clpd_commit_token),
        .commit_line_epoch(clpd_commit_line_epoch),
        .source_write_valid(source_write_valid),
        .source_write_line_tag(source_write_line_tag),
        .line_fill_valid(line_fill_valid),
        .line_fill_tag(line_fill_tag),
        .invalidate_valid(invalidate_valid),
        .invalidate_line_tag(invalidate_line_tag),
        .dmp_seed_valid(dmp_seed_valid),
        .dmp_line_tag(dmp_line_tag),
        .dmp_word(dmp_word),
        .dmp_src_token(dmp_src_token),
        .dmp_target_token(dmp_target_token),
        .dmp_line_epoch(dmp_line_epoch),
        .dmp_translation_ok(dmp_translation_ok),
        .dmp_permission_ok(dmp_permission_ok),
        .source_line_hit(source_line_hit),
        .source_word_proven(source_word_proven),
        .source_authorized(source_authorized),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block(dmp_seed_block),
        .block_no_entry(block_no_entry),
        .block_word_unproven(block_word_unproven),
        .block_stale_epoch(block_stale_epoch),
        .block_token_mismatch(block_token_mismatch),
        .block_fault_or_perm(block_fault_or_perm)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    function automatic logic [ENTRY_IDX_W-1:0] dir_idx(input logic [LINE_TAG_W-1:0] tag);
        dir_idx = tag[ENTRY_IDX_W-1:0];
    endfunction

    function automatic logic exp_same_cycle_clear;
        exp_same_cycle_clear =
            global_clear_valid
            || (source_write_valid && (source_write_line_tag == ropl_line_tag))
            || (line_fill_valid && (line_fill_tag == ropl_line_tag))
            || (invalidate_valid && (invalidate_line_tag == ropl_line_tag));
    endfunction

    function automatic logic exp_adapter_commit;
        exp_adapter_commit =
            ropl_proof_valid
            && source_clean
            && source_epoch_match
            && commit_translation_ok
            && commit_permission_ok
            && !exp_same_cycle_clear();
    endfunction

    task automatic clear_exp(input logic [LINE_TAG_W-1:0] tag);
        logic [ENTRY_IDX_W-1:0] idx;
        begin
            idx = dir_idx(tag);
            if (exp_valid[idx] && exp_tag[idx] == tag) begin
                exp_valid[idx] = 1'b0;
                exp_mask[idx] = '0;
            end
        end
    endtask

    task automatic update_expected_after_edge;
        logic [ENTRY_IDX_W-1:0] idx;
        begin
            if (source_write_valid) begin
                clear_exp(source_write_line_tag);
            end
            if (line_fill_valid) begin
                clear_exp(line_fill_tag);
            end
            if (invalidate_valid) begin
                clear_exp(invalidate_line_tag);
            end
            if (clpd_commit_ptr_valid) begin
                idx = dir_idx(clpd_commit_line_tag);
                if (
                    exp_valid[idx]
                    && exp_tag[idx] == clpd_commit_line_tag
                    && exp_token[idx] == clpd_commit_token
                    && exp_epoch[idx] == clpd_commit_line_epoch
                ) begin
                    exp_mask[idx][clpd_commit_word] = 1'b1;
                end else begin
                    exp_valid[idx] = 1'b1;
                    exp_tag[idx] = clpd_commit_line_tag;
                    exp_token[idx] = clpd_commit_token;
                    exp_epoch[idx] = clpd_commit_line_epoch;
                    exp_mask[idx] = '0;
                    exp_mask[idx][clpd_commit_word] = 1'b1;
                end
            end
        end
    endtask

    task automatic compare_adapter(input string label);
        logic exp_commit;
        logic exp_clear;
        begin
            exp_commit = exp_adapter_commit();
            exp_clear = exp_same_cycle_clear();
            if (clpd_commit_ptr_valid !== exp_commit) begin
                $error("%s adapter commit expected %0b got %0b", label, exp_commit, clpd_commit_ptr_valid);
                errors++;
            end
            if (same_cycle_clear_hit !== exp_clear) begin
                $error("%s clear_hit expected %0b got %0b", label, exp_clear, same_cycle_clear_hit);
                errors++;
            end
            if (blocked_no_retire_proof !== !ropl_proof_valid) begin
                $error("%s no_retire block mismatch", label);
                errors++;
            end
            if (blocked_source_not_clean !== (ropl_proof_valid && !source_clean)) begin
                $error("%s source_not_clean block mismatch", label);
                errors++;
            end
            if (blocked_epoch_mismatch !== (ropl_proof_valid && source_clean && !source_epoch_match)) begin
                $error("%s epoch_mismatch block mismatch", label);
                errors++;
            end
            if (blocked_fault_or_perm !== (ropl_proof_valid && source_clean && source_epoch_match && !(commit_translation_ok && commit_permission_ok))) begin
                $error("%s fault_perm block mismatch", label);
                errors++;
            end
            if (blocked_clear_wins !== (ropl_proof_valid && source_clean && source_epoch_match && commit_translation_ok && commit_permission_ok && exp_clear)) begin
                $error("%s clear_wins block mismatch", label);
                errors++;
            end
            if (clpd_commit_ptr_valid) begin
                legal_commit_seen++;
                last_line = clpd_commit_line_tag;
                last_word = clpd_commit_word;
                last_token = clpd_commit_token;
                last_epoch = clpd_commit_line_epoch;
            end
            if (blocked_clear_wins) begin
                clear_win_seen++;
            end
            if (blocked_source_not_clean) begin
                source_not_clean_seen++;
            end
        end
    endtask

    task automatic compare_clpd(input string label);
        logic [ENTRY_IDX_W-1:0] idx;
        logic exp_line_hit;
        logic exp_epoch_match;
        logic exp_token_match;
        logic exp_word_proven;
        logic exp_authorized;
        logic exp_allow;
        begin
            idx = dir_idx(dmp_line_tag);
            exp_line_hit = exp_valid[idx] && (exp_tag[idx] == dmp_line_tag);
            exp_epoch_match = exp_line_hit && (exp_epoch[idx] == dmp_line_epoch);
            exp_token_match = exp_line_hit && (exp_token[idx] == dmp_src_token) && (dmp_src_token == dmp_target_token);
            exp_word_proven = exp_line_hit && exp_epoch_match && exp_mask[idx][dmp_word];
            exp_authorized = exp_word_proven && exp_token_match;
            exp_allow = dmp_seed_valid && exp_authorized && dmp_translation_ok && dmp_permission_ok;

            if (source_line_hit !== exp_line_hit) begin
                $error("%s line_hit expected %0b got %0b", label, exp_line_hit, source_line_hit);
                errors++;
            end
            if (source_word_proven !== exp_word_proven) begin
                $error("%s word_proven expected %0b got %0b", label, exp_word_proven, source_word_proven);
                errors++;
            end
            if (source_authorized !== exp_authorized) begin
                $error("%s source_authorized expected %0b got %0b", label, exp_authorized, source_authorized);
                errors++;
            end
            if (dmp_seed_allow !== exp_allow) begin
                $error("%s allow expected %0b got %0b", label, exp_allow, dmp_seed_allow);
                errors++;
            end
            if (dmp_seed_block !== (dmp_seed_valid && !exp_allow)) begin
                $error("%s block mismatch", label);
                errors++;
            end
            if (block_no_entry !== (dmp_seed_valid && !exp_line_hit)) begin
                $error("%s no_entry mismatch", label);
                errors++;
            end
            if (block_word_unproven !== (dmp_seed_valid && exp_line_hit && exp_epoch_match && !exp_mask[idx][dmp_word])) begin
                $error("%s word_unproven mismatch", label);
                errors++;
            end
            if (block_stale_epoch !== (dmp_seed_valid && exp_line_hit && !exp_epoch_match)) begin
                $error("%s stale_epoch mismatch", label);
                errors++;
            end
            if (block_token_mismatch !== (dmp_seed_valid && exp_line_hit && exp_epoch_match && exp_mask[idx][dmp_word] && !exp_token_match)) begin
                $error("%s token_mismatch mismatch", label);
                errors++;
            end
            if (block_fault_or_perm !== (dmp_seed_valid && exp_authorized && !(dmp_translation_ok && dmp_permission_ok))) begin
                $error("%s fault_or_perm mismatch", label);
                errors++;
            end
            if (dmp_seed_allow) begin
                allow_seen++;
            end
            if (block_token_mismatch) begin
                token_mismatch_seen++;
            end
            if (block_stale_epoch) begin
                stale_epoch_seen++;
            end
            if (block_fault_or_perm) begin
                fault_perm_seen++;
            end
        end
    endtask

    task automatic step_cycle(input string label);
        begin
            #1;
            compare_adapter(label);
            compare_clpd(label);
            @(posedge clk);
            update_expected_after_edge();
            #1;
        end
    endtask

    task automatic zero_inputs;
        begin
            ropl_proof_valid = 1'b0;
            ropl_line_tag = '0;
            ropl_word = '0;
            ropl_token = '0;
            ropl_epoch = '0;
            source_clean = 1'b1;
            source_epoch_match = 1'b1;
            commit_translation_ok = 1'b1;
            commit_permission_ok = 1'b1;
            global_clear_valid = 1'b0;
            source_write_valid = 1'b0;
            source_write_line_tag = '0;
            line_fill_valid = 1'b0;
            line_fill_tag = '0;
            invalidate_valid = 1'b0;
            invalidate_line_tag = '0;
            dmp_seed_valid = 1'b0;
            dmp_line_tag = '0;
            dmp_word = '0;
            dmp_src_token = '0;
            dmp_target_token = '0;
            dmp_line_epoch = '0;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
        end
    endtask

    task automatic legal_commit(input logic [LINE_TAG_W-1:0] line, input logic [WORD_OFF_W-1:0] word, input logic [TOKEN_W-1:0] token, input logic [EPOCH_W-1:0] epoch);
        begin
            zero_inputs();
            ropl_proof_valid = 1'b1;
            ropl_line_tag = line;
            ropl_word = word;
            ropl_token = token;
            ropl_epoch = epoch;
            source_clean = 1'b1;
            source_epoch_match = 1'b1;
            commit_translation_ok = 1'b1;
            commit_permission_ok = 1'b1;
        end
    endtask

    task automatic query(input logic [LINE_TAG_W-1:0] line, input logic [WORD_OFF_W-1:0] word, input logic [TOKEN_W-1:0] src_token, input logic [TOKEN_W-1:0] tgt_token, input logic [EPOCH_W-1:0] epoch, input logic trans_ok, input logic perm_ok);
        begin
            dmp_seed_valid = 1'b1;
            dmp_line_tag = line;
            dmp_word = word;
            dmp_src_token = src_token;
            dmp_target_token = tgt_token;
            dmp_line_epoch = epoch;
            dmp_translation_ok = trans_ok;
            dmp_permission_ok = perm_ok;
        end
    endtask

    task automatic randomize_cycle(input int trial);
        logic [LINE_TAG_W-1:0] line_choice;
        begin
            zero_inputs();
            ropl_proof_valid = ($urandom_range(0, 3) != 0);
            ropl_line_tag = $urandom();
            ropl_word = $urandom_range(0, WORDS_PER_LINE - 1);
            ropl_token = $urandom();
            ropl_epoch = $urandom();
            source_clean = ($urandom_range(0, 7) != 0);
            source_epoch_match = ($urandom_range(0, 7) != 0);
            commit_translation_ok = ($urandom_range(0, 11) != 0);
            commit_permission_ok = ($urandom_range(0, 11) != 0);
            global_clear_valid = ($urandom_range(0, 63) == 0);

            line_choice = ($urandom_range(0, 1) == 0) ? ropl_line_tag : $urandom();
            source_write_valid = ($urandom_range(0, 7) == 0);
            source_write_line_tag = line_choice;
            line_fill_valid = ($urandom_range(0, 11) == 0);
            line_fill_tag = ($urandom_range(0, 1) == 0) ? ropl_line_tag : $urandom();
            invalidate_valid = ($urandom_range(0, 11) == 0);
            invalidate_line_tag = ($urandom_range(0, 1) == 0) ? ropl_line_tag : $urandom();

            dmp_seed_valid = ($urandom_range(0, 3) != 0);
            if ($urandom_range(0, 2) == 0) begin
                dmp_line_tag = last_line;
                dmp_word = last_word;
                dmp_src_token = last_token;
                dmp_target_token = ($urandom_range(0, 5) == 0) ? (last_token ^ 5'h1) : last_token;
                dmp_line_epoch = ($urandom_range(0, 7) == 0) ? (last_epoch ^ 4'h1) : last_epoch;
            end else begin
                dmp_line_tag = $urandom();
                dmp_word = $urandom_range(0, WORDS_PER_LINE - 1);
                dmp_src_token = $urandom();
                dmp_target_token = ($urandom_range(0, 1) == 0) ? dmp_src_token : $urandom();
                dmp_line_epoch = $urandom();
            end
            dmp_translation_ok = ($urandom_range(0, 15) != 0);
            dmp_permission_ok = ($urandom_range(0, 15) != 0);

            if (exp_adapter_commit()) begin
                random_commit_seen++;
            end
            if (blocked_clear_wins) begin
                random_clear_win_seen++;
            end
        end
    endtask

    initial begin
        errors = 0;
        legal_commit_seen = 0;
        clear_win_seen = 0;
        allow_seen = 0;
        token_mismatch_seen = 0;
        stale_epoch_seen = 0;
        fault_perm_seen = 0;
        source_not_clean_seen = 0;
        random_commit_seen = 0;
        random_clear_win_seen = 0;
        last_line = 8'h22;
        last_word = 3'h1;
        last_token = 5'h3;
        last_epoch = 4'h2;

        for (int i = 0; i < ENTRIES; i++) begin
            exp_valid[i] = 1'b0;
            exp_tag[i] = '0;
            exp_token[i] = '0;
            exp_epoch[i] = '0;
            exp_mask[i] = '0;
        end

        rst_n = 1'b0;
        zero_inputs();
        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        repeat (2) @(posedge clk);

        legal_commit(8'h34, 3'h2, 5'h0a, 4'h3);
        step_cycle("directed_legal_commit");
        zero_inputs();
        query(8'h34, 3'h2, 5'h0a, 5'h0a, 4'h3, 1'b1, 1'b1);
        step_cycle("directed_query_allow");

        legal_commit(8'h41, 3'h5, 5'h07, 4'h4);
        source_write_valid = 1'b1;
        source_write_line_tag = 8'h41;
        step_cycle("directed_write_clear_wins");
        zero_inputs();
        query(8'h41, 3'h5, 5'h07, 5'h07, 4'h4, 1'b1, 1'b1);
        step_cycle("directed_write_clear_blocks_query");

        legal_commit(8'h42, 3'h1, 5'h08, 4'h5);
        line_fill_valid = 1'b1;
        line_fill_tag = 8'h42;
        step_cycle("directed_fill_clear_wins");

        legal_commit(8'h43, 3'h2, 5'h09, 4'h6);
        invalidate_valid = 1'b1;
        invalidate_line_tag = 8'h43;
        step_cycle("directed_invalidate_clear_wins");

        legal_commit(8'h50, 3'h3, 5'h11, 4'h7);
        step_cycle("directed_commit_for_mismatch_queries");
        zero_inputs();
        query(8'h50, 3'h3, 5'h11, 5'h12, 4'h7, 1'b1, 1'b1);
        step_cycle("directed_token_mismatch");
        zero_inputs();
        query(8'h50, 3'h3, 5'h11, 5'h11, 4'h6, 1'b1, 1'b1);
        step_cycle("directed_stale_epoch");
        zero_inputs();
        query(8'h50, 3'h3, 5'h11, 5'h11, 4'h7, 1'b0, 1'b1);
        step_cycle("directed_fault_block");

        legal_commit(8'h61, 3'h4, 5'h02, 4'h8);
        source_clean = 1'b0;
        step_cycle("directed_source_not_clean");
        legal_commit(8'h62, 3'h4, 5'h02, 4'h8);
        source_epoch_match = 1'b0;
        step_cycle("directed_epoch_mismatch");

        for (int t = 0; t < TRIALS; t++) begin
            randomize_cycle(t);
            step_cycle($sformatf("random_%0d", t));
        end

        if (legal_commit_seen == 0) begin
            $error("No legal ROCCA commits observed");
            errors++;
        end
        if (clear_win_seen == 0) begin
            $error("No clear-wins blocks observed");
            errors++;
        end
        if (allow_seen == 0) begin
            $error("No CLPD allows observed");
            errors++;
        end
        if (token_mismatch_seen == 0 || stale_epoch_seen == 0 || fault_perm_seen == 0) begin
            $error("Missing query-side block coverage token=%0d epoch=%0d fault=%0d", token_mismatch_seen, stale_epoch_seen, fault_perm_seen);
            errors++;
        end
        if (source_not_clean_seen == 0) begin
            $error("No source-not-clean adapter block observed");
            errors++;
        end

        $display(
            "COPPER ROCCA-CLPD adapter completed: directed=11 random=%0d commits=%0d clear_wins=%0d allows=%0d token_blocks=%0d epoch_blocks=%0d fault_blocks=%0d source_not_clean=%0d errors=%0d",
            TRIALS,
            legal_commit_seen,
            clear_win_seen,
            allow_seen,
            token_mismatch_seen,
            stale_epoch_seen,
            fault_perm_seen,
            source_not_clean_seen,
            errors
        );

        if (errors != 0) begin
            $fatal(1, "COPPER ROCCA-CLPD adapter failed");
        end
        $finish;
    end

endmodule
