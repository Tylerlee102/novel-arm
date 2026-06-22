`timescale 1ns/1ps

module copper_clpd_gate_tb;

    localparam int LINE_TAG_W = 8;
    localparam int WORDS_PER_LINE = 16;
    localparam int WORD_OFF_W = 4;
    localparam int TOKEN_W = 4;
    localparam int EPOCH_W = 4;
    localparam int ENTRIES = 8;
    localparam int ENTRY_IDX_W = 3;
    localparam int TRIALS = 5000;

    logic clk;
    logic rst_n;

    logic commit_ptr_valid;
    logic [LINE_TAG_W-1:0] commit_line_tag;
    logic [WORD_OFF_W-1:0] commit_word;
    logic [TOKEN_W-1:0] commit_token;
    logic [EPOCH_W-1:0] commit_line_epoch;

    logic source_write_valid;
    logic [LINE_TAG_W-1:0] source_write_line_tag;
    logic line_fill_valid;
    logic [LINE_TAG_W-1:0] line_fill_tag;
    logic invalidate_valid;
    logic [LINE_TAG_W-1:0] invalidate_line_tag;

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

    logic sb_valid [ENTRIES];
    logic [LINE_TAG_W-1:0] sb_tag [ENTRIES];
    logic [TOKEN_W-1:0] sb_token [ENTRIES];
    logic [EPOCH_W-1:0] sb_epoch [ENTRIES];
    logic [WORDS_PER_LINE-1:0] sb_mask [ENTRIES];

    int errors;
    int allow_seen;
    int block_seen;
    int no_entry_seen;
    int word_unproven_seen;
    int stale_epoch_seen;
    int token_mismatch_seen;
    int fault_perm_seen;
    int write_clear_seen;
    int fill_clear_seen;
    int invalidate_clear_seen;
    int collision_seen;

    copper_clpd_gate #(
        .LINE_TAG_W(LINE_TAG_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W),
        .ENTRIES(ENTRIES),
        .ENTRY_IDX_W(ENTRY_IDX_W)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .commit_ptr_valid(commit_ptr_valid),
        .commit_line_tag(commit_line_tag),
        .commit_word(commit_word),
        .commit_token(commit_token),
        .commit_line_epoch(commit_line_epoch),
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

    always #5 clk = ~clk;

    function automatic int sb_idx(input logic [LINE_TAG_W-1:0] tag);
        sb_idx = tag[ENTRY_IDX_W-1:0];
    endfunction

    task automatic clear_seq_inputs;
        begin
            commit_ptr_valid = 1'b0;
            commit_line_tag = '0;
            commit_word = '0;
            commit_token = '0;
            commit_line_epoch = '0;
            source_write_valid = 1'b0;
            source_write_line_tag = '0;
            line_fill_valid = 1'b0;
            line_fill_tag = '0;
            invalidate_valid = 1'b0;
            invalidate_line_tag = '0;
        end
    endtask

    task automatic clear_dmp_inputs;
        begin
            dmp_seed_valid = 1'b0;
            dmp_line_tag = '0;
            dmp_word = '0;
            dmp_src_token = '0;
            dmp_target_token = '0;
            dmp_line_epoch = '0;
            dmp_translation_ok = 1'b0;
            dmp_permission_ok = 1'b0;
        end
    endtask

    task automatic sb_reset;
        begin
            for (int i = 0; i < ENTRIES; i++) begin
                sb_valid[i] = 1'b0;
                sb_tag[i] = '0;
                sb_token[i] = '0;
                sb_epoch[i] = '0;
                sb_mask[i] = '0;
            end
        end
    endtask

    task automatic sb_clear_if_match(input logic [LINE_TAG_W-1:0] tag);
        int idx;
        begin
            idx = sb_idx(tag);
            if (sb_valid[idx] && sb_tag[idx] == tag) begin
                sb_valid[idx] = 1'b0;
                sb_mask[idx] = '0;
            end
        end
    endtask

    task automatic sb_apply_current_cycle;
        int idx;
        logic [WORDS_PER_LINE-1:0] new_mask;
        begin
            if (source_write_valid) begin
                sb_clear_if_match(source_write_line_tag);
            end
            if (line_fill_valid) begin
                sb_clear_if_match(line_fill_tag);
            end
            if (invalidate_valid) begin
                sb_clear_if_match(invalidate_line_tag);
            end
            if (commit_ptr_valid) begin
                idx = sb_idx(commit_line_tag);
                if (
                    sb_valid[idx]
                    && sb_tag[idx] == commit_line_tag
                    && sb_token[idx] == commit_token
                    && sb_epoch[idx] == commit_line_epoch
                ) begin
                    sb_mask[idx][commit_word] = 1'b1;
                end else begin
                    new_mask = '0;
                    new_mask[commit_word] = 1'b1;
                    sb_valid[idx] = 1'b1;
                    sb_tag[idx] = commit_line_tag;
                    sb_token[idx] = commit_token;
                    sb_epoch[idx] = commit_line_epoch;
                    sb_mask[idx] = new_mask;
                end
            end
        end
    endtask

    task automatic step_state;
        begin
            @(posedge clk);
            sb_apply_current_cycle();
            #1;
            clear_seq_inputs();
        end
    endtask

    task automatic commit_word_event(
        input logic [LINE_TAG_W-1:0] tag,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] token,
        input logic [EPOCH_W-1:0] epoch
    );
        begin
            clear_seq_inputs();
            commit_ptr_valid = 1'b1;
            commit_line_tag = tag;
            commit_word = word;
            commit_token = token;
            commit_line_epoch = epoch;
            step_state();
        end
    endtask

    task automatic write_line_event(input logic [LINE_TAG_W-1:0] tag);
        begin
            clear_seq_inputs();
            source_write_valid = 1'b1;
            source_write_line_tag = tag;
            step_state();
        end
    endtask

    task automatic fill_line_event(input logic [LINE_TAG_W-1:0] tag);
        begin
            clear_seq_inputs();
            line_fill_valid = 1'b1;
            line_fill_tag = tag;
            step_state();
        end
    endtask

    task automatic invalidate_line_event(input logic [LINE_TAG_W-1:0] tag);
        begin
            clear_seq_inputs();
            invalidate_valid = 1'b1;
            invalidate_line_tag = tag;
            step_state();
        end
    endtask

    task automatic check_query(
        input string name,
        input logic [LINE_TAG_W-1:0] tag,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] src_token,
        input logic [TOKEN_W-1:0] target_token,
        input logic [EPOCH_W-1:0] epoch,
        input logic translation_ok,
        input logic permission_ok
    );
        int idx;
        logic exp_line_hit;
        logic exp_epoch_match;
        logic exp_token_match;
        logic exp_word_proven;
        logic exp_src_auth;
        logic exp_allow;
        logic exp_block;
        logic exp_no_entry;
        logic exp_word_unproven;
        logic exp_stale_epoch;
        logic exp_token_mismatch;
        logic exp_fault_perm;
        begin
            dmp_seed_valid = 1'b1;
            dmp_line_tag = tag;
            dmp_word = word;
            dmp_src_token = src_token;
            dmp_target_token = target_token;
            dmp_line_epoch = epoch;
            dmp_translation_ok = translation_ok;
            dmp_permission_ok = permission_ok;
            #1;

            idx = sb_idx(tag);
            exp_line_hit = sb_valid[idx] && sb_tag[idx] == tag;
            exp_epoch_match = exp_line_hit && sb_epoch[idx] == epoch;
            exp_token_match = exp_line_hit
                && sb_token[idx] == src_token
                && src_token == target_token;
            exp_word_proven = exp_line_hit && exp_epoch_match && sb_mask[idx][word];
            exp_src_auth = exp_word_proven && exp_token_match;
            exp_allow = exp_src_auth && translation_ok && permission_ok;
            exp_block = !exp_allow;
            exp_no_entry = !exp_line_hit;
            exp_word_unproven = exp_line_hit && exp_epoch_match && !sb_mask[idx][word];
            exp_stale_epoch = exp_line_hit && !exp_epoch_match;
            exp_token_mismatch = exp_line_hit
                && exp_epoch_match
                && sb_mask[idx][word]
                && !exp_token_match;
            exp_fault_perm = exp_src_auth && !(translation_ok && permission_ok);

            if (source_line_hit !== exp_line_hit) begin
                $error("%s: source_line_hit expected %0b got %0b", name, exp_line_hit, source_line_hit);
                errors++;
            end
            if (source_word_proven !== exp_word_proven) begin
                $error("%s: source_word_proven expected %0b got %0b", name, exp_word_proven, source_word_proven);
                errors++;
            end
            if (source_authorized !== exp_src_auth) begin
                $error("%s: source_authorized expected %0b got %0b", name, exp_src_auth, source_authorized);
                errors++;
            end
            if (dmp_seed_allow !== exp_allow) begin
                $error("%s: allow expected %0b got %0b", name, exp_allow, dmp_seed_allow);
                errors++;
            end
            if (dmp_seed_block !== exp_block) begin
                $error("%s: block expected %0b got %0b", name, exp_block, dmp_seed_block);
                errors++;
            end
            if (block_no_entry !== exp_no_entry) begin
                $error("%s: no_entry expected %0b got %0b", name, exp_no_entry, block_no_entry);
                errors++;
            end
            if (block_word_unproven !== exp_word_unproven) begin
                $error("%s: word_unproven expected %0b got %0b", name, exp_word_unproven, block_word_unproven);
                errors++;
            end
            if (block_stale_epoch !== exp_stale_epoch) begin
                $error("%s: stale_epoch expected %0b got %0b", name, exp_stale_epoch, block_stale_epoch);
                errors++;
            end
            if (block_token_mismatch !== exp_token_mismatch) begin
                $error("%s: token_mismatch expected %0b got %0b", name, exp_token_mismatch, block_token_mismatch);
                errors++;
            end
            if (block_fault_or_perm !== exp_fault_perm) begin
                $error("%s: fault_perm expected %0b got %0b", name, exp_fault_perm, block_fault_or_perm);
                errors++;
            end

            if (exp_allow) allow_seen++;
            if (exp_block) block_seen++;
            if (exp_no_entry) no_entry_seen++;
            if (exp_word_unproven) word_unproven_seen++;
            if (exp_stale_epoch) stale_epoch_seen++;
            if (exp_token_mismatch) token_mismatch_seen++;
            if (exp_fault_perm) fault_perm_seen++;
            clear_dmp_inputs();
        end
    endtask

    task automatic random_state_cycle;
        logic [LINE_TAG_W-1:0] rand_tag;
        begin
            clear_seq_inputs();
            if ($urandom_range(0, 99) < 35) begin
                commit_ptr_valid = 1'b1;
                commit_line_tag = $urandom_range(0, 255);
                commit_word = $urandom_range(0, WORDS_PER_LINE - 1);
                commit_token = $urandom_range(0, 15);
                commit_line_epoch = $urandom_range(0, 15);
            end
            if ($urandom_range(0, 99) < 12) begin
                source_write_valid = 1'b1;
                source_write_line_tag = $urandom_range(0, 255);
            end
            if ($urandom_range(0, 99) < 8) begin
                line_fill_valid = 1'b1;
                line_fill_tag = $urandom_range(0, 255);
            end
            if ($urandom_range(0, 99) < 8) begin
                invalidate_valid = 1'b1;
                invalidate_line_tag = $urandom_range(0, 255);
            end
            step_state();

            rand_tag = $urandom_range(0, 255);
            check_query(
                "random",
                rand_tag,
                $urandom_range(0, WORDS_PER_LINE - 1),
                $urandom_range(0, 15),
                $urandom_range(0, 15),
                $urandom_range(0, 15),
                $urandom_range(0, 1),
                $urandom_range(0, 1)
            );
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        errors = 0;
        allow_seen = 0;
        block_seen = 0;
        no_entry_seen = 0;
        word_unproven_seen = 0;
        stale_epoch_seen = 0;
        token_mismatch_seen = 0;
        fault_perm_seen = 0;
        write_clear_seen = 0;
        fill_clear_seen = 0;
        invalidate_clear_seen = 0;
        collision_seen = 0;
        clear_seq_inputs();
        clear_dmp_inputs();
        sb_reset();

        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        #1;

        check_query("reset_blocks", 8'h35, 4'h3, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1);

        commit_word_event(8'h35, 4'h3, 4'h2, 4'h1);
        check_query("committed_word_allows", 8'h35, 4'h3, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1);
        check_query("unproven_neighbor_blocks", 8'h35, 4'h4, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1);

        commit_word_event(8'h35, 4'h4, 4'h2, 4'h1);
        check_query("second_word_allows", 8'h35, 4'h4, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1);
        check_query("token_mismatch_blocks", 8'h35, 4'h4, 4'h3, 4'h3, 4'h1, 1'b1, 1'b1);
        check_query("src_target_token_mismatch_blocks", 8'h35, 4'h4, 4'h2, 4'h3, 4'h1, 1'b1, 1'b1);
        check_query("stale_epoch_blocks", 8'h35, 4'h4, 4'h2, 4'h2, 4'h2, 1'b1, 1'b1);
        check_query("translation_blocks", 8'h35, 4'h4, 4'h2, 4'h2, 4'h1, 1'b0, 1'b1);
        check_query("permission_blocks", 8'h35, 4'h4, 4'h2, 4'h2, 4'h1, 1'b1, 1'b0);

        write_line_event(8'h35);
        check_query("write_clears_whole_line", 8'h35, 4'h3, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1);
        write_clear_seen++;

        commit_word_event(8'h35, 4'h8, 4'h2, 4'h2);
        check_query("new_epoch_word_allows", 8'h35, 4'h8, 4'h2, 4'h2, 4'h2, 1'b1, 1'b1);
        check_query("old_word_after_line_clear_blocks", 8'h35, 4'h3, 4'h2, 4'h2, 4'h2, 1'b1, 1'b1);

        fill_line_event(8'h35);
        check_query("fill_clears_whole_line", 8'h35, 4'h8, 4'h2, 4'h2, 4'h2, 1'b1, 1'b1);
        fill_clear_seen++;

        commit_word_event(8'h35, 4'h1, 4'h2, 4'h3);
        commit_word_event(8'h3d, 4'h1, 4'h2, 4'h3);
        check_query("collision_evicts_old_tag", 8'h35, 4'h1, 4'h2, 4'h2, 4'h3, 1'b1, 1'b1);
        check_query("collision_new_tag_allows", 8'h3d, 4'h1, 4'h2, 4'h2, 4'h3, 1'b1, 1'b1);
        collision_seen++;

        invalidate_line_event(8'h3d);
        check_query("invalidate_clears_whole_line", 8'h3d, 4'h1, 4'h2, 4'h2, 4'h3, 1'b1, 1'b1);
        invalidate_clear_seen++;

        for (int trial = 0; trial < TRIALS; trial++) begin
            random_state_cycle();
        end

        if (
            allow_seen == 0
            || block_seen == 0
            || no_entry_seen == 0
            || word_unproven_seen == 0
            || stale_epoch_seen == 0
            || token_mismatch_seen == 0
            || fault_perm_seen == 0
            || write_clear_seen == 0
            || fill_clear_seen == 0
            || invalidate_clear_seen == 0
            || collision_seen == 0
        ) begin
            $error(
                "Missing CLPD coverage allow=%0d block=%0d no_entry=%0d word=%0d stale=%0d token=%0d fault=%0d write=%0d fill=%0d inval=%0d collision=%0d",
                allow_seen,
                block_seen,
                no_entry_seen,
                word_unproven_seen,
                stale_epoch_seen,
                token_mismatch_seen,
                fault_perm_seen,
                write_clear_seen,
                fill_clear_seen,
                invalidate_clear_seen,
                collision_seen
            );
            errors++;
        end

        $display(
            "COPPER CLPD gate tests completed: directed=14 random=%0d allowed=%0d blocked=%0d no_entry=%0d word_unproven=%0d stale_epoch=%0d token=%0d fault_perm=%0d write_clear=%0d fill_clear=%0d invalidate_clear=%0d collision=%0d errors=%0d",
            TRIALS,
            allow_seen,
            block_seen,
            no_entry_seen,
            word_unproven_seen,
            stale_epoch_seen,
            token_mismatch_seen,
            fault_perm_seen,
            write_clear_seen,
            fill_clear_seen,
            invalidate_clear_seen,
            collision_seen,
            errors
        );

        if (errors != 0) begin
            $fatal(1, "COPPER CLPD gate test failed");
        end
        $finish;
    end

endmodule
