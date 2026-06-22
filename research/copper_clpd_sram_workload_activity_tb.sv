`timescale 1ns/1ps

module copper_clpd_sram_workload_activity_tb;

    localparam int LINE_TAG_W = 32;
    localparam int WORDS_PER_LINE = 16;
    localparam int WORD_OFF_W = 4;
    localparam int TOKEN_W = 8;
    localparam int EPOCH_W = 8;
    localparam int BANKS = 4;
    localparam int BANK_IDX_W = 2;
    localparam int SETS_PER_BANK = 256;
    localparam int SET_IDX_W = 8;
    localparam int TOTAL_ENTRIES = BANKS * SETS_PER_BANK;
    localparam int TOTAL_IDX_W = BANK_IDX_W + SET_IDX_W;

    localparam logic [1:0] CLPD_OP_COMMIT = 2'd0;

`ifdef TCP_PROCESS_REPLAY
    `include "research/results/copper_clpd_tcp_process_replay_counts_20260620.svh"
    localparam string DEFAULT_REPLAY_LABEL = "tcp_process_spp_copper_slack";
`else
    `include "research/results/copper_clpd_workload_replay_counts_20260619.svh"
    localparam string DEFAULT_REPLAY_LABEL = "app_service_copper_clpd64k_peb";
`endif

    logic clk;
    logic rst_n;

    logic update_valid;
    logic [1:0] update_op;
    logic [LINE_TAG_W-1:0] update_line_tag;
    logic [WORD_OFF_W-1:0] update_word;
    logic [TOKEN_W-1:0] update_token;
    logic [EPOCH_W-1:0] update_line_epoch;
    logic update_ready;
    logic update_commit_merged;
    logic update_commit_replaced;
    logic update_purge_match;
    logic update_purge_alias;

    logic dmp_seed_valid;
    logic [LINE_TAG_W-1:0] dmp_line_tag;
    logic [WORD_OFF_W-1:0] dmp_word;
    logic [TOKEN_W-1:0] dmp_src_token;
    logic [TOKEN_W-1:0] dmp_target_token;
    logic [EPOCH_W-1:0] dmp_line_epoch;
    logic dmp_translation_ok;
    logic dmp_permission_ok;

    logic init_done;
    logic dmp_resp_valid;
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
    logic block_pending_update;

    bit sb_valid [TOTAL_ENTRIES];
    logic [LINE_TAG_W-1:0] sb_tag [TOTAL_ENTRIES];
    logic [TOKEN_W-1:0] sb_token [TOTAL_ENTRIES];
    logic [EPOCH_W-1:0] sb_epoch [TOTAL_ENTRIES];
    logic [WORDS_PER_LINE-1:0] sb_mask [TOTAL_ENTRIES];

    int commit_ops;
    int allow_queries;
    int block_queries;
    int fault_queries;
    int seed;

    int remaining_commits;
    int remaining_allows;
    int remaining_blocks;
    int remaining_faults;
    int source_rows;
    int raw_total;
    int scaled_total;

    int issued_commits;
    int issued_allow_queries;
    int issued_block_queries;
    int issued_fault_queries;
    int observed_allow;
    int observed_block;
    int observed_no_entry;
    int observed_word_unproven;
    int observed_stale_epoch;
    int observed_token_mismatch;
    int observed_fault_perm;
    int observed_pending_update;
    int errors;

    logic [31:0] rng_state;

    copper_clpd_sram_dir #(
        .LINE_TAG_W(LINE_TAG_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W),
        .BANKS(BANKS),
        .BANK_IDX_W(BANK_IDX_W),
        .SETS_PER_BANK(SETS_PER_BANK),
        .SET_IDX_W(SET_IDX_W)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .update_valid(update_valid),
        .update_op(update_op),
        .update_line_tag(update_line_tag),
        .update_word(update_word),
        .update_token(update_token),
        .update_line_epoch(update_line_epoch),
        .update_ready(update_ready),
        .update_commit_merged(update_commit_merged),
        .update_commit_replaced(update_commit_replaced),
        .update_purge_match(update_purge_match),
        .update_purge_alias(update_purge_alias),
        .dmp_seed_valid(dmp_seed_valid),
        .dmp_line_tag(dmp_line_tag),
        .dmp_word(dmp_word),
        .dmp_src_token(dmp_src_token),
        .dmp_target_token(dmp_target_token),
        .dmp_line_epoch(dmp_line_epoch),
        .dmp_translation_ok(dmp_translation_ok),
        .dmp_permission_ok(dmp_permission_ok),
        .init_done(init_done),
        .dmp_resp_valid(dmp_resp_valid),
        .source_line_hit(source_line_hit),
        .source_word_proven(source_word_proven),
        .source_authorized(source_authorized),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block(dmp_seed_block),
        .block_no_entry(block_no_entry),
        .block_word_unproven(block_word_unproven),
        .block_stale_epoch(block_stale_epoch),
        .block_token_mismatch(block_token_mismatch),
        .block_fault_or_perm(block_fault_or_perm),
        .block_pending_update(block_pending_update)
    );

    always #5 clk = ~clk;

    function automatic logic [31:0] next_rand;
        begin
            rng_state = (rng_state * 32'd1664525) + 32'd1013904223;
            next_rand = rng_state;
        end
    endfunction

    function automatic logic [LINE_TAG_W-1:0] fold_tag(
        input logic [LINE_TAG_W-1:0] tag
    );
        fold_tag = tag ^ (tag >> SET_IDX_W) ^ (tag >> (SET_IDX_W + BANK_IDX_W));
    endfunction

    function automatic int dir_idx(input logic [LINE_TAG_W-1:0] tag);
        logic [LINE_TAG_W-1:0] folded;
        begin
            folded = fold_tag(tag);
            dir_idx = {folded[BANK_IDX_W-1:0], folded[BANK_IDX_W +: SET_IDX_W]};
        end
    endfunction

    task automatic clear_update_inputs;
        begin
            update_valid = 1'b0;
            update_op = CLPD_OP_COMMIT;
            update_line_tag = '0;
            update_word = '0;
            update_token = '0;
            update_line_epoch = '0;
        end
    endtask

    task automatic clear_query_inputs;
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

    task automatic sb_clear;
        begin
            for (int i = 0; i < TOTAL_ENTRIES; i++) begin
                sb_valid[i] = 1'b0;
                sb_tag[i] = '0;
                sb_token[i] = '0;
                sb_epoch[i] = '0;
                sb_mask[i] = '0;
            end
        end
    endtask

    task automatic sb_commit(
        input logic [LINE_TAG_W-1:0] tag,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] token,
        input logic [EPOCH_W-1:0] epoch
    );
        int idx;
        logic [WORDS_PER_LINE-1:0] single_mask;
        begin
            idx = dir_idx(tag);
            if (
                sb_valid[idx]
                && sb_tag[idx] == tag
                && sb_token[idx] == token
                && sb_epoch[idx] == epoch
            ) begin
                sb_mask[idx][word] = 1'b1;
            end else begin
                single_mask = '0;
                single_mask[word] = 1'b1;
                sb_valid[idx] = 1'b1;
                sb_tag[idx] = tag;
                sb_token[idx] = token;
                sb_epoch[idx] = epoch;
                sb_mask[idx] = single_mask;
            end
        end
    endtask

    task automatic choose_valid_proof(
        output bit found,
        output logic [LINE_TAG_W-1:0] tag,
        output logic [WORD_OFF_W-1:0] word,
        output logic [TOKEN_W-1:0] token,
        output logic [EPOCH_W-1:0] epoch
    );
        int start_idx;
        int idx;
        int start_word;
        int w;
        logic [31:0] r;
        begin
            found = 1'b0;
            tag = '0;
            word = '0;
            token = '0;
            epoch = '0;
            r = next_rand();
            start_idx = r % TOTAL_ENTRIES;
            for (int i = 0; i < TOTAL_ENTRIES; i++) begin
                idx = (start_idx + i) % TOTAL_ENTRIES;
                if (sb_valid[idx] && sb_mask[idx] != '0 && !found) begin
                    r = next_rand();
                    start_word = r % WORDS_PER_LINE;
                    for (int j = 0; j < WORDS_PER_LINE; j++) begin
                        w = (start_word + j) % WORDS_PER_LINE;
                        if (sb_mask[idx][w] && !found) begin
                            found = 1'b1;
                            tag = sb_tag[idx];
                            word = WORD_OFF_W'(w);
                            token = sb_token[idx];
                            epoch = sb_epoch[idx];
                        end
                    end
                end
            end
        end
    endtask

    task automatic make_commit_fields(
        output logic [LINE_TAG_W-1:0] tag,
        output logic [WORD_OFF_W-1:0] word,
        output logic [TOKEN_W-1:0] token,
        output logic [EPOCH_W-1:0] epoch
    );
        logic [31:0] r0;
        logic [31:0] r1;
        begin
            r0 = next_rand();
            r1 = next_rand();
            tag = {r0[30:0], r1[0]};
            word = r1[WORD_OFF_W-1:0];
            token = TOKEN_W'((r0 >> 7) ^ (r1 >> 3) ^ 32'h5a);
            epoch = EPOCH_W'((r0 >> 17) ^ (r1 >> 11) ^ 32'h21);
        end
    endtask

    task automatic make_no_provenance_query(
        output logic [LINE_TAG_W-1:0] tag,
        output logic [WORD_OFF_W-1:0] word,
        output logic [TOKEN_W-1:0] token,
        output logic [EPOCH_W-1:0] epoch
    );
        logic [31:0] r;
        int idx;
        bit done;
        begin
            done = 1'b0;
            tag = '0;
            word = '0;
            token = '0;
            epoch = '0;
            for (int attempt = 0; attempt < 32; attempt++) begin
                r = next_rand();
                tag = r ^ 32'hf00d_4000 ^ (32'(attempt) << 18);
                idx = dir_idx(tag);
                if ((!sb_valid[idx] || sb_tag[idx] != tag) && !done) begin
                    done = 1'b1;
                    word = WORD_OFF_W'(r[3:0]);
                    token = TOKEN_W'((r >> 5) ^ 32'hc3);
                    epoch = EPOCH_W'((r >> 13) ^ 32'h6d);
                end
            end
            if (!done) begin
                tag = tag ^ 32'h8000_0000;
                word = WORD_OFF_W'(next_rand());
                token = TOKEN_W'(next_rand());
                epoch = EPOCH_W'(next_rand());
            end
        end
    endtask

    task automatic issue_commit(
        input logic [LINE_TAG_W-1:0] tag,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] token,
        input logic [EPOCH_W-1:0] epoch
    );
        begin
            while (!update_ready) begin
                @(posedge clk);
            end
            @(negedge clk);
            update_valid = 1'b1;
            update_op = CLPD_OP_COMMIT;
            update_line_tag = tag;
            update_word = word;
            update_token = token;
            update_line_epoch = epoch;
            @(posedge clk);
            #1;
            update_valid = 1'b0;
            @(posedge clk);
            #1;
            sb_commit(tag, word, token, epoch);
            issued_commits++;
            clear_update_inputs();
        end
    endtask

    task automatic issue_query(
        input int query_kind,
        input logic [LINE_TAG_W-1:0] tag,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] src_token,
        input logic [TOKEN_W-1:0] target_token,
        input logic [EPOCH_W-1:0] epoch,
        input logic translation_ok,
        input logic permission_ok
    );
        begin
            @(negedge clk);
            dmp_seed_valid = 1'b1;
            dmp_line_tag = tag;
            dmp_word = word;
            dmp_src_token = src_token;
            dmp_target_token = target_token;
            dmp_line_epoch = epoch;
            dmp_translation_ok = translation_ok;
            dmp_permission_ok = permission_ok;
            @(posedge clk);
            #1;

            if (dmp_resp_valid !== 1'b1) begin
                $error("workload replay query response was not valid");
                errors++;
            end
            if (dmp_seed_allow) observed_allow++;
            if (dmp_seed_block) observed_block++;
            if (block_no_entry) observed_no_entry++;
            if (block_word_unproven) observed_word_unproven++;
            if (block_stale_epoch) observed_stale_epoch++;
            if (block_token_mismatch) observed_token_mismatch++;
            if (block_fault_or_perm) observed_fault_perm++;
            if (block_pending_update) observed_pending_update++;

            if (query_kind == 0) begin
                issued_allow_queries++;
                if (!dmp_seed_allow) begin
                    $error("expected workload allow query to be allowed");
                    errors++;
                end
            end else if (query_kind == 1) begin
                issued_block_queries++;
                if (!dmp_seed_block) begin
                    $error("expected workload no-provenance query to block");
                    errors++;
                end
            end else begin
                issued_fault_queries++;
                if (!dmp_seed_block || !block_fault_or_perm) begin
                    $error("expected workload fault/permission query to block by authority fault");
                    errors++;
                end
            end

            dmp_seed_valid = 1'b0;
            clear_query_inputs();
        end
    endtask

    task automatic do_commit_from_random;
        logic [LINE_TAG_W-1:0] tag;
        logic [WORD_OFF_W-1:0] word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        begin
            make_commit_fields(tag, word, token, epoch);
            issue_commit(tag, word, token, epoch);
        end
    endtask

    task automatic do_allow_query;
        bit found;
        logic [LINE_TAG_W-1:0] tag;
        logic [WORD_OFF_W-1:0] word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        begin
            choose_valid_proof(found, tag, word, token, epoch);
            if (!found) begin
                do_commit_from_random();
                choose_valid_proof(found, tag, word, token, epoch);
            end
            issue_query(0, tag, word, token, token, epoch, 1'b1, 1'b1);
        end
    endtask

    task automatic do_block_query;
        logic [LINE_TAG_W-1:0] tag;
        logic [WORD_OFF_W-1:0] word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        begin
            make_no_provenance_query(tag, word, token, epoch);
            issue_query(1, tag, word, token, token, epoch, 1'b1, 1'b1);
        end
    endtask

    task automatic do_fault_query;
        bit found;
        logic [LINE_TAG_W-1:0] tag;
        logic [WORD_OFF_W-1:0] word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        logic translation_ok;
        logic [31:0] r;
        begin
            choose_valid_proof(found, tag, word, token, epoch);
            if (!found) begin
                do_commit_from_random();
                choose_valid_proof(found, tag, word, token, epoch);
            end
            r = next_rand();
            translation_ok = r[0];
            issue_query(2, tag, word, token, token, epoch, translation_ok, !translation_ok);
        end
    endtask

    task automatic read_replay_config;
        begin
            commit_ops = DEFAULT_COMMIT_OPS;
            allow_queries = DEFAULT_ALLOW_QUERIES;
            block_queries = DEFAULT_BLOCK_QUERIES;
            fault_queries = DEFAULT_FAULT_QUERIES;
            seed = DEFAULT_REPLAY_SEED;
            source_rows = DEFAULT_SOURCE_ROWS;
            raw_total = DEFAULT_RAW_TOTAL;
            scaled_total = DEFAULT_SCALED_TOTAL;

            if (commit_ops < 0) commit_ops = 0;
            if (allow_queries < 0) allow_queries = 0;
            if (block_queries < 0) block_queries = 0;
            if (fault_queries < 0) fault_queries = 0;
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        clear_update_inputs();
        clear_query_inputs();
        sb_clear();

        read_replay_config();
        rng_state = seed;

        errors = 0;
        issued_commits = 0;
        issued_allow_queries = 0;
        issued_block_queries = 0;
        issued_fault_queries = 0;
        observed_allow = 0;
        observed_block = 0;
        observed_no_entry = 0;
        observed_word_unproven = 0;
        observed_stale_epoch = 0;
        observed_token_mismatch = 0;
        observed_fault_perm = 0;
        observed_pending_update = 0;

        repeat (5) @(posedge clk);
        rst_n = 1'b1;
        wait (init_done);
        repeat (2) @(posedge clk);

        remaining_commits = commit_ops;
        remaining_allows = allow_queries;
        remaining_blocks = block_queries;
        remaining_faults = fault_queries;

        for (int i = 0; i < 128 && remaining_commits > 0; i++) begin
            do_commit_from_random();
            remaining_commits--;
        end

        while ((remaining_commits + remaining_allows + remaining_blocks + remaining_faults) > 0) begin
            int total_remaining;
            int pick;
            total_remaining = remaining_commits + remaining_allows + remaining_blocks + remaining_faults;
            pick = int'(next_rand() % total_remaining);

            if (pick < remaining_commits) begin
                do_commit_from_random();
                remaining_commits--;
            end else if (pick < remaining_commits + remaining_allows) begin
                do_allow_query();
                remaining_allows--;
            end else if (pick < remaining_commits + remaining_allows + remaining_blocks) begin
                do_block_query();
                remaining_blocks--;
            end else begin
                do_fault_query();
                remaining_faults--;
            end
        end

        repeat (8) @(posedge clk);
        $display(
            "COPPER CLPD workload activity replay completed: source_label=%s rows=%0d raw_total=%0d scaled_total=%0d commits=%0d allow=%0d block=%0d fault=%0d observed_allow=%0d observed_block=%0d no_entry=%0d word_unproven=%0d stale_epoch=%0d token_mismatch=%0d fault_perm=%0d pending_update=%0d errors=%0d",
            DEFAULT_REPLAY_LABEL,
            source_rows,
            raw_total,
            scaled_total,
            issued_commits,
            issued_allow_queries,
            issued_block_queries,
            issued_fault_queries,
            observed_allow,
            observed_block,
            observed_no_entry,
            observed_word_unproven,
            observed_stale_epoch,
            observed_token_mismatch,
            observed_fault_perm,
            observed_pending_update,
            errors
        );

        if (errors != 0) begin
            $fatal(1, "COPPER CLPD workload activity replay failed");
        end
        $finish;
    end

endmodule
