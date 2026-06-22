`timescale 1ns/1ps

module copper_clpd_sram_dir_tb;

    localparam int LINE_TAG_W = 12;
    localparam int WORDS_PER_LINE = 16;
    localparam int WORD_OFF_W = 4;
    localparam int TOKEN_W = 4;
    localparam int EPOCH_W = 4;
    localparam int BANKS = 4;
    localparam int BANK_IDX_W = 2;
    localparam int SETS_PER_BANK = 16;
    localparam int SET_IDX_W = 4;
    localparam int TRIALS = 4000;

    localparam logic [1:0] CLPD_OP_COMMIT = 2'd0;
    localparam logic [1:0] CLPD_OP_PURGE = 2'd1;

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

    logic sb_valid [BANKS][SETS_PER_BANK];
    logic [LINE_TAG_W-1:0] sb_tag [BANKS][SETS_PER_BANK];
    logic [TOKEN_W-1:0] sb_token [BANKS][SETS_PER_BANK];
    logic [EPOCH_W-1:0] sb_epoch [BANKS][SETS_PER_BANK];
    logic [WORDS_PER_LINE-1:0] sb_mask [BANKS][SETS_PER_BANK];

    int errors;
    int allow_seen;
    int block_seen;
    int no_entry_seen;
    int word_unproven_seen;
    int stale_epoch_seen;
    int token_mismatch_seen;
    int fault_perm_seen;
    int pending_update_seen;
    int merge_seen;
    int replace_seen;
    int purge_match_seen;
    int purge_alias_seen;

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

    function automatic logic [LINE_TAG_W-1:0] fold_tag(
        input logic [LINE_TAG_W-1:0] tag
    );
        fold_tag = tag ^ (tag >> SET_IDX_W) ^ (tag >> (SET_IDX_W + BANK_IDX_W));
    endfunction

    function automatic int sb_bank(input logic [LINE_TAG_W-1:0] tag);
        logic [LINE_TAG_W-1:0] folded;
        folded = fold_tag(tag);
        sb_bank = folded[BANK_IDX_W-1:0];
    endfunction

    function automatic int sb_set(input logic [LINE_TAG_W-1:0] tag);
        logic [LINE_TAG_W-1:0] folded;
        folded = fold_tag(tag);
        sb_set = folded[BANK_IDX_W +: SET_IDX_W];
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

    task automatic sb_reset;
        begin
            for (int bank = 0; bank < BANKS; bank++) begin
                for (int set = 0; set < SETS_PER_BANK; set++) begin
                    sb_valid[bank][set] = 1'b0;
                    sb_tag[bank][set] = '0;
                    sb_token[bank][set] = '0;
                    sb_epoch[bank][set] = '0;
                    sb_mask[bank][set] = '0;
                end
            end
        end
    endtask

    task automatic sb_commit(
        input logic [LINE_TAG_W-1:0] tag,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] token,
        input logic [EPOCH_W-1:0] epoch
    );
        int bank;
        int set;
        logic [WORDS_PER_LINE-1:0] single_mask;
        begin
            bank = sb_bank(tag);
            set = sb_set(tag);
            if (
                sb_valid[bank][set]
                && sb_tag[bank][set] == tag
                && sb_token[bank][set] == token
                && sb_epoch[bank][set] == epoch
            ) begin
                sb_mask[bank][set][word] = 1'b1;
            end else begin
                single_mask = '0;
                single_mask[word] = 1'b1;
                sb_valid[bank][set] = 1'b1;
                sb_tag[bank][set] = tag;
                sb_token[bank][set] = token;
                sb_epoch[bank][set] = epoch;
                sb_mask[bank][set] = single_mask;
            end
        end
    endtask

    task automatic sb_purge(input logic [LINE_TAG_W-1:0] tag);
        int bank;
        int set;
        begin
            bank = sb_bank(tag);
            set = sb_set(tag);
            sb_valid[bank][set] = 1'b0;
            sb_mask[bank][set] = '0;
        end
    endtask

    task automatic issue_update(
        input logic [1:0] op,
        input logic [LINE_TAG_W-1:0] tag,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] token,
        input logic [EPOCH_W-1:0] epoch,
        input bit expect_merge,
        input bit expect_replace,
        input bit expect_purge_match,
        input bit expect_purge_alias
    );
        begin
            while (!update_ready) begin
                @(posedge clk);
            end
            @(negedge clk);
            update_valid = 1'b1;
            update_op = op;
            update_line_tag = tag;
            update_word = word;
            update_token = token;
            update_line_epoch = epoch;
            @(posedge clk);
            #1;
            update_valid = 1'b0;
            @(posedge clk);
            #1;

            if (update_commit_merged !== expect_merge) begin
                $error("update merge expected %0b got %0b", expect_merge, update_commit_merged);
                errors++;
            end
            if (update_commit_replaced !== expect_replace) begin
                $error("update replace expected %0b got %0b", expect_replace, update_commit_replaced);
                errors++;
            end
            if (update_purge_match !== expect_purge_match) begin
                $error("purge match expected %0b got %0b", expect_purge_match, update_purge_match);
                errors++;
            end
            if (update_purge_alias !== expect_purge_alias) begin
                $error("purge alias expected %0b got %0b", expect_purge_alias, update_purge_alias);
                errors++;
            end

            if (expect_merge) merge_seen++;
            if (expect_replace) replace_seen++;
            if (expect_purge_match) purge_match_seen++;
            if (expect_purge_alias) purge_alias_seen++;

            if (op == CLPD_OP_COMMIT) begin
                sb_commit(tag, word, token, epoch);
            end else begin
                sb_purge(tag);
            end
            clear_update_inputs();
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
        input logic permission_ok,
        input logic expect_pending
    );
        int bank;
        int set;
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

            bank = sb_bank(tag);
            set = sb_set(tag);
            exp_line_hit = sb_valid[bank][set] && sb_tag[bank][set] == tag;
            exp_epoch_match = exp_line_hit && sb_epoch[bank][set] == epoch;
            exp_token_match = exp_line_hit
                && sb_token[bank][set] == src_token
                && src_token == target_token;
            exp_word_proven = exp_line_hit && exp_epoch_match && sb_mask[bank][set][word];
            exp_src_auth = exp_word_proven && exp_token_match;
            exp_allow = exp_src_auth && translation_ok && permission_ok && !expect_pending;
            exp_block = !exp_allow;
            exp_no_entry = !expect_pending && !exp_line_hit;
            exp_word_unproven = !expect_pending && exp_line_hit && exp_epoch_match && !sb_mask[bank][set][word];
            exp_stale_epoch = !expect_pending && exp_line_hit && !exp_epoch_match;
            exp_token_mismatch = !expect_pending
                && exp_line_hit
                && exp_epoch_match
                && sb_mask[bank][set][word]
                && !exp_token_match;
            exp_fault_perm = !expect_pending && exp_src_auth && !(translation_ok && permission_ok);

            if (dmp_resp_valid !== 1'b1) begin
                $error("%s: response valid expected", name);
                errors++;
            end
            if (source_line_hit !== (expect_pending ? 1'b0 : exp_line_hit)) begin
                $error("%s: source_line_hit expected %0b got %0b", name, expect_pending ? 1'b0 : exp_line_hit, source_line_hit);
                errors++;
            end
            if (source_word_proven !== (expect_pending ? 1'b0 : exp_word_proven)) begin
                $error("%s: source_word_proven expected %0b got %0b", name, expect_pending ? 1'b0 : exp_word_proven, source_word_proven);
                errors++;
            end
            if (source_authorized !== (expect_pending ? 1'b0 : exp_src_auth)) begin
                $error("%s: source_authorized expected %0b got %0b", name, expect_pending ? 1'b0 : exp_src_auth, source_authorized);
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
            if (block_pending_update !== expect_pending) begin
                $error("%s: pending_update expected %0b got %0b", name, expect_pending, block_pending_update);
                errors++;
            end

            if (exp_allow) allow_seen++;
            if (exp_block) block_seen++;
            if (exp_no_entry) no_entry_seen++;
            if (exp_word_unproven) word_unproven_seen++;
            if (exp_stale_epoch) stale_epoch_seen++;
            if (exp_token_mismatch) token_mismatch_seen++;
            if (exp_fault_perm) fault_perm_seen++;
            if (expect_pending) pending_update_seen++;

            dmp_seed_valid = 1'b0;
            clear_query_inputs();
        end
    endtask

    task automatic same_cycle_purge_query_hazard(
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
            update_op = CLPD_OP_PURGE;
            update_line_tag = tag;
            update_word = '0;
            update_token = '0;
            update_line_epoch = '0;
            dmp_seed_valid = 1'b1;
            dmp_line_tag = tag;
            dmp_word = word;
            dmp_src_token = token;
            dmp_target_token = token;
            dmp_line_epoch = epoch;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
            @(posedge clk);
            #1;
            if (
                dmp_resp_valid !== 1'b1
                || dmp_seed_allow !== 1'b0
                || dmp_seed_block !== 1'b1
                || block_pending_update !== 1'b1
            ) begin
                $error("same-cycle purge/query hazard did not block");
                errors++;
            end else begin
                block_seen++;
                pending_update_seen++;
            end
            update_valid = 1'b0;
            clear_query_inputs();

            @(posedge clk);
            #1;
            if (update_purge_match !== 1'b1) begin
                $error("same-cycle purge expected purge_match");
                errors++;
            end
            purge_match_seen++;
            sb_purge(tag);
            clear_update_inputs();
        end
    endtask

    task automatic same_cycle_commit_query_hazard(
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
            dmp_seed_valid = 1'b1;
            dmp_line_tag = tag;
            dmp_word = word;
            dmp_src_token = token;
            dmp_target_token = token;
            dmp_line_epoch = epoch;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
            @(posedge clk);
            #1;
            if (
                dmp_resp_valid !== 1'b1
                || dmp_seed_allow !== 1'b0
                || dmp_seed_block !== 1'b1
                || block_pending_update !== 1'b1
            ) begin
                $error("same-cycle commit/query hazard did not block");
                errors++;
            end else begin
                block_seen++;
                pending_update_seen++;
            end
            update_valid = 1'b0;
            clear_query_inputs();

            @(posedge clk);
            #1;
            if (update_commit_replaced !== 1'b1) begin
                $error("same-cycle commit expected replacement");
                errors++;
            end
            replace_seen++;
            sb_commit(tag, word, token, epoch);
            clear_update_inputs();
        end
    endtask

    task automatic find_alias(
        input logic [LINE_TAG_W-1:0] base,
        output logic [LINE_TAG_W-1:0] alias_tag_out
    );
        logic [LINE_TAG_W-1:0] cand_tag;
        begin
            alias_tag_out = base;
            for (int cand = 0; cand < (1 << LINE_TAG_W); cand++) begin
                cand_tag = cand;
                if (
                    cand_tag != base
                    && sb_bank(cand_tag) == sb_bank(base)
                    && sb_set(cand_tag) == sb_set(base)
                ) begin
                    alias_tag_out = cand_tag;
                end
            end
        end
    endtask

    task automatic random_trial;
        logic [LINE_TAG_W-1:0] tag;
        logic [WORD_OFF_W-1:0] word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        int bank;
        int set;
        bit expect_merge;
        bit expect_replace;
        bit expect_purge_match;
        bit expect_purge_alias;
        bit do_commit;
        begin
            tag = $urandom_range(0, (1 << LINE_TAG_W) - 1);
            word = $urandom_range(0, WORDS_PER_LINE - 1);
            token = $urandom_range(0, (1 << TOKEN_W) - 1);
            epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            bank = sb_bank(tag);
            set = sb_set(tag);
            do_commit = $urandom_range(0, 99) < 65;

            if (do_commit) begin
                expect_merge =
                    sb_valid[bank][set]
                    && sb_tag[bank][set] == tag
                    && sb_token[bank][set] == token
                    && sb_epoch[bank][set] == epoch;
                expect_replace = !expect_merge;
                issue_update(CLPD_OP_COMMIT, tag, word, token, epoch, expect_merge, expect_replace, 1'b0, 1'b0);
            end else begin
                expect_purge_match = sb_valid[bank][set] && sb_tag[bank][set] == tag;
                expect_purge_alias = sb_valid[bank][set] && sb_tag[bank][set] != tag;
                issue_update(CLPD_OP_PURGE, tag, '0, '0, '0, 1'b0, 1'b0, expect_purge_match, expect_purge_alias);
            end

            tag = $urandom_range(0, (1 << LINE_TAG_W) - 1);
            check_query(
                "random",
                tag,
                $urandom_range(0, WORDS_PER_LINE - 1),
                $urandom_range(0, (1 << TOKEN_W) - 1),
                $urandom_range(0, (1 << TOKEN_W) - 1),
                $urandom_range(0, (1 << EPOCH_W) - 1),
                $urandom_range(0, 1),
                $urandom_range(0, 1),
                1'b0
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
        pending_update_seen = 0;
        merge_seen = 0;
        replace_seen = 0;
        purge_match_seen = 0;
        purge_alias_seen = 0;
        clear_update_inputs();
        clear_query_inputs();
        sb_reset();

        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        wait (init_done);
        repeat (2) @(posedge clk);

        check_query("reset_blocks", 12'h135, 4'h3, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1, 1'b0);

        issue_update(CLPD_OP_COMMIT, 12'h135, 4'h3, 4'h2, 4'h1, 1'b0, 1'b1, 1'b0, 1'b0);
        check_query("committed_word_allows", 12'h135, 4'h3, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1, 1'b0);
        check_query("unproven_neighbor_blocks", 12'h135, 4'h4, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1, 1'b0);

        issue_update(CLPD_OP_COMMIT, 12'h135, 4'h4, 4'h2, 4'h1, 1'b1, 1'b0, 1'b0, 1'b0);
        check_query("second_word_allows", 12'h135, 4'h4, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1, 1'b0);
        check_query("token_mismatch_blocks", 12'h135, 4'h4, 4'h3, 4'h3, 4'h1, 1'b1, 1'b1, 1'b0);
        check_query("src_target_token_mismatch_blocks", 12'h135, 4'h4, 4'h2, 4'h3, 4'h1, 1'b1, 1'b1, 1'b0);
        check_query("stale_epoch_blocks", 12'h135, 4'h4, 4'h2, 4'h2, 4'h2, 1'b1, 1'b1, 1'b0);
        check_query("translation_blocks", 12'h135, 4'h4, 4'h2, 4'h2, 4'h1, 1'b0, 1'b1, 1'b0);
        check_query("permission_blocks", 12'h135, 4'h4, 4'h2, 4'h2, 4'h1, 1'b1, 1'b0, 1'b0);

        same_cycle_purge_query_hazard(12'h135, 4'h4, 4'h2, 4'h1);
        check_query("after_purge_no_entry", 12'h135, 4'h4, 4'h2, 4'h2, 4'h1, 1'b1, 1'b1, 1'b0);

        begin
            logic [LINE_TAG_W-1:0] alias_tag;
            issue_update(CLPD_OP_COMMIT, 12'h241, 4'h1, 4'h6, 4'h2, 1'b0, 1'b1, 1'b0, 1'b0);
            find_alias(12'h241, alias_tag);
            issue_update(CLPD_OP_PURGE, alias_tag, '0, '0, '0, 1'b0, 1'b0, 1'b0, 1'b1);
            check_query("alias_purge_blocks_old", 12'h241, 4'h1, 4'h6, 4'h6, 4'h2, 1'b1, 1'b1, 1'b0);
        end

        same_cycle_commit_query_hazard(12'h2aa, 4'h7, 4'h9, 4'h3);
        check_query("after_commit_allows", 12'h2aa, 4'h7, 4'h9, 4'h9, 4'h3, 1'b1, 1'b1, 1'b0);

        for (int trial = 0; trial < TRIALS; trial++) begin
            random_trial();
        end

        if (
            allow_seen == 0
            || block_seen == 0
            || no_entry_seen == 0
            || word_unproven_seen == 0
            || stale_epoch_seen == 0
            || token_mismatch_seen == 0
            || fault_perm_seen == 0
            || pending_update_seen == 0
            || merge_seen == 0
            || replace_seen == 0
            || purge_match_seen == 0
            || purge_alias_seen == 0
        ) begin
            $error(
                "Missing SRAM CLPD coverage allow=%0d block=%0d no_entry=%0d word=%0d stale=%0d token=%0d fault=%0d pending=%0d merge=%0d replace=%0d purge_match=%0d purge_alias=%0d",
                allow_seen,
                block_seen,
                no_entry_seen,
                word_unproven_seen,
                stale_epoch_seen,
                token_mismatch_seen,
                fault_perm_seen,
                pending_update_seen,
                merge_seen,
                replace_seen,
                purge_match_seen,
                purge_alias_seen
            );
            errors++;
        end

        $display(
            "COPPER CLPD SRAM directory tests completed: directed=18 random=%0d allowed=%0d blocked=%0d no_entry=%0d word_unproven=%0d stale_epoch=%0d token=%0d fault_perm=%0d pending_update=%0d merge=%0d replace=%0d purge_match=%0d purge_alias=%0d errors=%0d",
            TRIALS,
            allow_seen,
            block_seen,
            no_entry_seen,
            word_unproven_seen,
            stale_epoch_seen,
            token_mismatch_seen,
            fault_perm_seen,
            pending_update_seen,
            merge_seen,
            replace_seen,
            purge_match_seen,
            purge_alias_seen,
            errors
        );

        if (errors != 0) begin
            $fatal(1, "COPPER CLPD SRAM directory test failed");
        end
        $finish;
    end

endmodule
