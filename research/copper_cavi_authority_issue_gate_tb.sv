`timescale 1ns/1ps

module copper_cavi_authority_issue_gate_tb;

    localparam int SRC_LINE_W = 8;
    localparam int TGT_LINE_W = 10;
    localparam int WORDS_PER_LINE = 8;
    localparam int WORD_OFF_W = 3;
    localparam int TOKEN_W = 5;
    localparam int EPOCH_W = 4;
    localparam int CLPD_ENTRIES = 16;
    localparam int CLPD_IDX_W = 4;
    localparam int TRIALS = 20000;

    logic clk;
    logic rst_n;

    logic ropl_proof_valid;
    logic [SRC_LINE_W-1:0] ropl_line_tag;
    logic [WORD_OFF_W-1:0] ropl_word;
    logic [TOKEN_W-1:0] ropl_token;
    logic [EPOCH_W-1:0] ropl_epoch;
    logic source_clean;
    logic source_epoch_match;
    logic commit_translation_ok;
    logic commit_permission_ok;
    logic global_clear_valid;
    logic source_write_valid;
    logic [SRC_LINE_W-1:0] source_write_line_tag;
    logic line_fill_valid;
    logic [SRC_LINE_W-1:0] line_fill_tag;
    logic source_revoke_valid;
    logic [SRC_LINE_W-1:0] source_revoke_line;
    logic dmp_seed_valid;
    logic [SRC_LINE_W-1:0] dmp_line_tag;
    logic [WORD_OFF_W-1:0] dmp_word;
    logic [TOKEN_W-1:0] dmp_src_token;
    logic [TOKEN_W-1:0] dmp_target_token;
    logic [EPOCH_W-1:0] dmp_line_epoch;
    logic dmp_translation_ok;
    logic dmp_permission_ok;
    logic [TGT_LINE_W-1:0] dmp_target_line;
    logic target_witness_valid;
    logic target_exact_match;
    logic target_permission_ok;
    logic target_remap_valid;
    logic [TGT_LINE_W-1:0] target_remap_line;
    logic [TOKEN_W-1:0] target_remap_token;
    logic tlbi_token_valid;
    logic [TOKEN_W-1:0] tlbi_token;
    logic tlbi_all_valid;
    logic permission_downgrade_valid;
    logic [TGT_LINE_W-1:0] permission_line;
    logic [TOKEN_W-1:0] permission_token;
    logic source_drain_enable;
    logic target_drain_enable;

    logic dmp_issue_allow;
    logic dmp_issue_block;
    logic source_gate_allow;
    logic source_gate_block;
    logic target_gate_allow;
    logic target_gate_block;
    logic source_authorized;
    logic target_conflict_hold;
    logic same_cycle_clear_hit;
    logic blocked_clear_wins;
    logic source_block_no_entry;
    logic source_block_word_unproven;
    logic source_block_stale_epoch;
    logic source_block_token_mismatch;
    logic source_block_fault_or_perm;
    logic target_block_no_source_proof;
    logic target_block_no_witness;
    logic target_block_permission;
    logic target_block_revocation;
    logic target_block_overflow;
    logic overflow_sticky;

    int errors;
    int directed_count;
    int random_allows;
    int random_blocks;
    int random_source_blocks;
    int random_target_blocks;
    int random_clear_wins;
    int random_target_revokes;

    logic [SRC_LINE_W-1:0] r_line;
    logic [WORD_OFF_W-1:0] r_word;
    logic [TOKEN_W-1:0] r_token;
    logic [EPOCH_W-1:0] r_epoch;
    logic [TGT_LINE_W-1:0] r_target_line;
    logic r_clear_on_commit;
    logic r_post_source_clear;
    logic r_src_token_mismatch;
    logic r_src_translation_ok;
    logic r_src_permission_ok;
    logic r_target_witness;
    logic r_target_exact;
    logic r_target_permission;
    logic r_remap_valid;
    logic r_remap_hit;
    logic r_tlbi_valid;
    logic r_tlbi_hit;
    logic r_tlbi_all;
    logic r_perm_down_valid;
    logic r_perm_down_hit;
    logic r_expected_source_ok;
    logic r_expected_target_conflict;
    logic r_expected_target_ok;
    logic r_expected_allow;

    copper_cavi_authority_issue_gate #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W),
        .CLPD_ENTRIES(CLPD_ENTRIES),
        .CLPD_IDX_W(CLPD_IDX_W),
        .SOURCE_Q_DEPTH(4),
        .TARGET_Q_DEPTH(4),
        .COUNT_W(3)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
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
        .source_revoke_valid(source_revoke_valid),
        .source_revoke_line(source_revoke_line),
        .dmp_seed_valid(dmp_seed_valid),
        .dmp_line_tag(dmp_line_tag),
        .dmp_word(dmp_word),
        .dmp_src_token(dmp_src_token),
        .dmp_target_token(dmp_target_token),
        .dmp_line_epoch(dmp_line_epoch),
        .dmp_translation_ok(dmp_translation_ok),
        .dmp_permission_ok(dmp_permission_ok),
        .dmp_target_line(dmp_target_line),
        .target_witness_valid(target_witness_valid),
        .target_exact_match(target_exact_match),
        .target_permission_ok(target_permission_ok),
        .target_remap_valid(target_remap_valid),
        .target_remap_line(target_remap_line),
        .target_remap_token(target_remap_token),
        .tlbi_token_valid(tlbi_token_valid),
        .tlbi_token(tlbi_token),
        .tlbi_all_valid(tlbi_all_valid),
        .permission_downgrade_valid(permission_downgrade_valid),
        .permission_line(permission_line),
        .permission_token(permission_token),
        .source_drain_enable(source_drain_enable),
        .target_drain_enable(target_drain_enable),
        .dmp_issue_allow(dmp_issue_allow),
        .dmp_issue_block(dmp_issue_block),
        .source_gate_allow(source_gate_allow),
        .source_gate_block(source_gate_block),
        .target_gate_allow(target_gate_allow),
        .target_gate_block(target_gate_block),
        .source_authorized(source_authorized),
        .target_conflict_hold(target_conflict_hold),
        .same_cycle_clear_hit(same_cycle_clear_hit),
        .blocked_clear_wins(blocked_clear_wins),
        .source_block_no_entry(source_block_no_entry),
        .source_block_word_unproven(source_block_word_unproven),
        .source_block_stale_epoch(source_block_stale_epoch),
        .source_block_token_mismatch(source_block_token_mismatch),
        .source_block_fault_or_perm(source_block_fault_or_perm),
        .target_block_no_source_proof(target_block_no_source_proof),
        .target_block_no_witness(target_block_no_witness),
        .target_block_permission(target_block_permission),
        .target_block_revocation(target_block_revocation),
        .target_block_overflow(target_block_overflow),
        .overflow_sticky(overflow_sticky)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic defaults;
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
            source_revoke_valid = 1'b0;
            source_revoke_line = '0;
            dmp_seed_valid = 1'b0;
            dmp_line_tag = '0;
            dmp_word = '0;
            dmp_src_token = '0;
            dmp_target_token = '0;
            dmp_line_epoch = '0;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
            dmp_target_line = '0;
            target_witness_valid = 1'b1;
            target_exact_match = 1'b1;
            target_permission_ok = 1'b1;
            target_remap_valid = 1'b0;
            target_remap_line = '0;
            target_remap_token = '0;
            tlbi_token_valid = 1'b0;
            tlbi_token = '0;
            tlbi_all_valid = 1'b0;
            permission_downgrade_valid = 1'b0;
            permission_line = '0;
            permission_token = '0;
            source_drain_enable = 1'b0;
            target_drain_enable = 1'b0;
        end
    endtask

    task automatic reset_unit;
        begin
            defaults();
            rst_n = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            @(posedge clk);
            #1;
        end
    endtask

    task automatic tick;
        begin
            @(posedge clk);
            #1;
        end
    endtask

    task automatic commit_proof(
        input logic [SRC_LINE_W-1:0] line,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] token,
        input logic [EPOCH_W-1:0] epoch
    );
        begin
            defaults();
            ropl_proof_valid = 1'b1;
            ropl_line_tag = line;
            ropl_word = word;
            ropl_token = token;
            ropl_epoch = epoch;
            tick();
            defaults();
        end
    endtask

    task automatic query_candidate(
        input logic [SRC_LINE_W-1:0] line,
        input logic [WORD_OFF_W-1:0] word,
        input logic [TOKEN_W-1:0] src_token,
        input logic [TOKEN_W-1:0] target_token,
        input logic [EPOCH_W-1:0] epoch,
        input logic [TGT_LINE_W-1:0] target_line
    );
        begin
            dmp_seed_valid = 1'b1;
            dmp_line_tag = line;
            dmp_word = word;
            dmp_src_token = src_token;
            dmp_target_token = target_token;
            dmp_line_epoch = epoch;
            dmp_target_line = target_line;
        end
    endtask

    task automatic check_allow(input string label, input logic expected_allow);
        begin
            #1;
            directed_count++;
            if (dmp_issue_allow !== expected_allow) begin
                $error("%s final allow expected %0b got %0b", label, expected_allow, dmp_issue_allow);
                errors++;
            end
            if (dmp_issue_block !== (dmp_seed_valid && !expected_allow)) begin
                $error("%s final block mismatch", label);
                errors++;
            end
        end
    endtask

    task automatic check_random(input int trial, input logic expected_allow);
        begin
            #1;
            if (dmp_issue_allow !== expected_allow) begin
                $error("random[%0d] final allow expected %0b got %0b", trial, expected_allow, dmp_issue_allow);
                errors++;
            end
            if (dmp_issue_block !== (dmp_seed_valid && !expected_allow)) begin
                $error("random[%0d] final block mismatch", trial);
                errors++;
            end
        end
    endtask

    initial begin
        errors = 0;
        directed_count = 0;
        random_allows = 0;
        random_blocks = 0;
        random_source_blocks = 0;
        random_target_blocks = 0;
        random_clear_wins = 0;
        random_target_revokes = 0;
        rst_n = 1'b0;
        defaults();

        reset_unit();
        commit_proof(8'h12, 3'd3, 5'h07, 4'h2);
        defaults();
        query_candidate(8'h12, 3'd3, 5'h07, 5'h07, 4'h2, 10'h155);
        check_allow("direct legal source and target", 1'b1);

        reset_unit();
        commit_proof(8'h12, 3'd3, 5'h07, 4'h2);
        defaults();
        query_candidate(8'h12, 3'd4, 5'h07, 5'h07, 4'h2, 10'h155);
        check_allow("direct unproven source word", 1'b0);
        if (!source_block_word_unproven) begin
            $error("direct unproven source word did not raise source block");
            errors++;
        end

        reset_unit();
        defaults();
        ropl_proof_valid = 1'b1;
        ropl_line_tag = 8'h21;
        ropl_word = 3'd2;
        ropl_token = 5'h09;
        ropl_epoch = 4'h1;
        source_revoke_valid = 1'b1;
        source_revoke_line = 8'h21;
        tick();
        defaults();
        query_candidate(8'h21, 3'd2, 5'h09, 5'h09, 4'h1, 10'h011);
        check_allow("direct clear-wins commit suppression", 1'b0);
        if (!source_block_no_entry && !target_block_no_source_proof) begin
            $error("direct clear-wins did not remove source authority");
            errors++;
        end

        reset_unit();
        commit_proof(8'h31, 3'd1, 5'h03, 4'h4);
        defaults();
        source_write_valid = 1'b1;
        source_write_line_tag = 8'h31;
        tick();
        defaults();
        query_candidate(8'h31, 3'd1, 5'h03, 5'h03, 4'h4, 10'h012);
        check_allow("direct source write clears retained proof", 1'b0);

        reset_unit();
        commit_proof(8'h42, 3'd5, 5'h11, 4'h3);
        defaults();
        query_candidate(8'h42, 3'd5, 5'h11, 5'h11, 4'h3, 10'h1aa);
        target_remap_valid = 1'b1;
        target_remap_line = 10'h1aa;
        target_remap_token = 5'h11;
        check_allow("direct target remap blocks issue", 1'b0);
        if (!target_block_revocation) begin
            $error("direct target remap did not raise revocation block");
            errors++;
        end

        reset_unit();
        commit_proof(8'h42, 3'd5, 5'h11, 4'h3);
        defaults();
        query_candidate(8'h42, 3'd5, 5'h11, 5'h11, 4'h3, 10'h1aa);
        target_remap_valid = 1'b1;
        target_remap_line = 10'h1ab;
        target_remap_token = 5'h11;
        check_allow("direct unrelated target remap does not block", 1'b1);

        reset_unit();
        commit_proof(8'h52, 3'd0, 5'h12, 4'h3);
        defaults();
        query_candidate(8'h52, 3'd0, 5'h12, 5'h12, 4'h3, 10'h077);
        tlbi_token_valid = 1'b1;
        tlbi_token = 5'h12;
        check_allow("direct token TLBI blocks issue", 1'b0);

        reset_unit();
        commit_proof(8'h52, 3'd0, 5'h12, 4'h3);
        defaults();
        query_candidate(8'h52, 3'd0, 5'h12, 5'h12, 4'h3, 10'h077);
        permission_downgrade_valid = 1'b1;
        permission_line = 10'h077;
        permission_token = 5'h12;
        check_allow("direct permission downgrade blocks issue", 1'b0);

        reset_unit();
        commit_proof(8'h62, 3'd6, 5'h13, 4'h6);
        defaults();
        query_candidate(8'h62, 3'd6, 5'h13, 5'h13, 4'h6, 10'h044);
        target_witness_valid = 1'b0;
        check_allow("direct missing target witness blocks issue", 1'b0);

        reset_unit();
        commit_proof(8'h62, 3'd6, 5'h13, 4'h6);
        defaults();
        query_candidate(8'h62, 3'd6, 5'h13, 5'h14, 4'h6, 10'h044);
        check_allow("direct source-target token mismatch blocks issue", 1'b0);

        reset_unit();
        commit_proof(8'h72, 3'd7, 5'h15, 4'h7);
        defaults();
        query_candidate(8'h72, 3'd7, 5'h15, 5'h15, 4'h7, 10'h055);
        dmp_translation_ok = 1'b0;
        check_allow("direct source translation fault blocks issue", 1'b0);

        reset_unit();
        defaults();
        ropl_proof_valid = 1'b1;
        ropl_line_tag = 8'h82;
        ropl_word = 3'd1;
        ropl_token = 5'h16;
        ropl_epoch = 4'h8;
        global_clear_valid = 1'b1;
        tick();
        defaults();
        query_candidate(8'h82, 3'd1, 5'h16, 5'h16, 4'h8, 10'h066);
        check_allow("direct global clear suppresses new proof", 1'b0);

        reset_unit();
        commit_proof(8'h92, 3'd4, 5'h17, 4'h9);
        defaults();
        target_remap_valid = 1'b1;
        target_remap_line = 10'h123;
        target_remap_token = 5'h17;
        tick();
        defaults();
        query_candidate(8'h92, 3'd4, 5'h17, 5'h17, 4'h9, 10'h123);
        check_allow("direct queued target remap blocks until drained", 1'b0);
        defaults();
        target_drain_enable = 1'b1;
        tick();
        defaults();
        query_candidate(8'h92, 3'd4, 5'h17, 5'h17, 4'h9, 10'h123);
        check_allow("direct drained target remap allows refreshed witness", 1'b1);

        for (int trial = 0; trial < TRIALS; trial++) begin
            reset_unit();

            r_line = $urandom();
            r_word = $urandom_range(0, WORDS_PER_LINE - 1);
            r_token = $urandom_range(1, (1 << TOKEN_W) - 1);
            r_epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            r_target_line = $urandom();
            r_clear_on_commit = ($urandom_range(0, 9) == 0);
            r_post_source_clear = ($urandom_range(0, 9) == 0);
            r_src_token_mismatch = ($urandom_range(0, 9) == 0);
            r_src_translation_ok = ($urandom_range(0, 11) != 0);
            r_src_permission_ok = ($urandom_range(0, 11) != 0);
            r_target_witness = ($urandom_range(0, 11) != 0);
            r_target_exact = ($urandom_range(0, 11) != 0);
            r_target_permission = ($urandom_range(0, 11) != 0);
            r_remap_valid = ($urandom_range(0, 7) == 0);
            r_remap_hit = ($urandom_range(0, 1) == 1);
            r_tlbi_valid = ($urandom_range(0, 9) == 0);
            r_tlbi_hit = ($urandom_range(0, 1) == 1);
            r_tlbi_all = ($urandom_range(0, 31) == 0);
            r_perm_down_valid = ($urandom_range(0, 8) == 0);
            r_perm_down_hit = ($urandom_range(0, 1) == 1);

            defaults();
            ropl_proof_valid = 1'b1;
            ropl_line_tag = r_line;
            ropl_word = r_word;
            ropl_token = r_token;
            ropl_epoch = r_epoch;
            if (r_clear_on_commit) begin
                source_revoke_valid = 1'b1;
                source_revoke_line = r_line;
            end
            tick();

            if (!r_clear_on_commit && r_post_source_clear) begin
                defaults();
                source_write_valid = 1'b1;
                source_write_line_tag = r_line;
                tick();
            end

            defaults();
            query_candidate(
                r_line,
                r_word,
                r_src_token_mismatch ? (r_token ^ 5'h01) : r_token,
                r_token,
                r_epoch,
                r_target_line
            );
            dmp_translation_ok = r_src_translation_ok;
            dmp_permission_ok = r_src_permission_ok;
            target_witness_valid = r_target_witness;
            target_exact_match = r_target_exact;
            target_permission_ok = r_target_permission;

            if (r_remap_valid) begin
                target_remap_valid = 1'b1;
                target_remap_line = r_remap_hit ? r_target_line : (r_target_line ^ 10'h001);
                target_remap_token = r_token;
            end
            if (r_tlbi_valid) begin
                tlbi_token_valid = 1'b1;
                tlbi_token = r_tlbi_hit ? r_token : (r_token ^ 5'h01);
            end
            if (r_tlbi_all) begin
                tlbi_all_valid = 1'b1;
            end
            if (r_perm_down_valid) begin
                permission_downgrade_valid = 1'b1;
                permission_line = r_perm_down_hit ? r_target_line : (r_target_line ^ 10'h002);
                permission_token = r_token;
            end

            r_expected_source_ok =
                !r_clear_on_commit
                && !r_post_source_clear
                && !r_src_token_mismatch
                && r_src_translation_ok
                && r_src_permission_ok;

            r_expected_target_conflict =
                (r_remap_valid && r_remap_hit)
                || (r_tlbi_valid && r_tlbi_hit)
                || r_tlbi_all
                || (r_perm_down_valid && r_perm_down_hit);

            r_expected_target_ok =
                r_target_witness
                && r_target_exact
                && r_target_permission
                && !r_expected_target_conflict;

            r_expected_allow = r_expected_source_ok && r_expected_target_ok;

            check_random(trial, r_expected_allow);

            if (r_expected_allow) begin
                random_allows++;
            end else begin
                random_blocks++;
            end
            if (!r_expected_source_ok) begin
                random_source_blocks++;
            end
            if (r_expected_source_ok && !r_expected_target_ok) begin
                random_target_blocks++;
            end
            if (r_clear_on_commit) begin
                random_clear_wins++;
            end
            if (r_expected_target_conflict) begin
                random_target_revokes++;
            end
        end

        if (errors == 0) begin
            $display(
                "COPPER CAVI authority issue gate completed: directed=%0d random=%0d random_allows=%0d random_blocks=%0d source_blocks=%0d target_blocks=%0d clear_wins=%0d target_revokes=%0d errors=%0d",
                directed_count,
                TRIALS,
                random_allows,
                random_blocks,
                random_source_blocks,
                random_target_blocks,
                random_clear_wins,
                random_target_revokes,
                errors
            );
        end else begin
            $fatal(1, "COPPER CAVI authority issue gate failed: errors=%0d", errors);
        end
        $finish;
    end

endmodule
