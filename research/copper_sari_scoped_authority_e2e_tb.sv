`timescale 1ns/1ps

// CS-SARI -> CLPD -> CTLW -> full authority integration harness.
//
// This harness checks that conflict-scoped SARI preserves the no-transient-
// authority invariant while avoiding global stalls for unrelated revocations.

module copper_sari_scoped_authority_e2e_tb;

    localparam int SRC_LINE_W = 8;
    localparam int WORDS_PER_LINE = 16;
    localparam int WORD_OFF_W = 4;
    localparam int VALUE_W = 12;
    localparam int EPOCH_W = 4;
    localparam int TOKEN_W = 4;
    localparam int CLPD_ENTRIES = 8;
    localparam int CLPD_IDX_W = 3;
    localparam int TGT_LINE_W = 12;
    localparam int CTLW_ENTRIES = 16;
    localparam int CTLW_IDX_W = 4;
    localparam int SARI_DEPTH = 8;
    localparam int SARI_COUNT_W = 4;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;
    logic started;

    logic commit_ptr_valid;
    logic [SRC_LINE_W-1:0] commit_line_tag;
    logic [WORD_OFF_W-1:0] commit_word;
    logic [TOKEN_W-1:0] commit_token;
    logic [EPOCH_W-1:0] commit_line_epoch;

    logic dma_write_valid;
    logic [SRC_LINE_W-1:0] dma_line_tag;
    logic chi_snoop_valid;
    logic chi_snoop_write;
    logic chi_snoop_invalidate;
    logic [SRC_LINE_W-1:0] chi_line_tag;
    logic io_write_valid;
    logic [SRC_LINE_W-1:0] io_line_tag;

    logic target_remap_valid;
    logic [TGT_LINE_W-1:0] target_remap_vline;
    logic [TOKEN_W-1:0] target_remap_token;
    logic tlbi_token_valid;
    logic [TOKEN_W-1:0] tlbi_token;
    logic tlbi_all_valid;

    logic source_clear_valid;
    logic [SRC_LINE_W-1:0] source_clear_line_tag;
    logic source_events_ready;
    logic ctlw_remap_valid;
    logic [TGT_LINE_W-1:0] ctlw_remap_vline;
    logic [TOKEN_W-1:0] ctlw_remap_token;
    logic ctlw_tlbi_token_valid;
    logic [TOKEN_W-1:0] ctlw_tlbi_token;
    logic ctlw_tlbi_all_valid;
    logic sari_conflict_hold;
    logic sari_global_hold;
    logic sari_overflow_sticky;
    logic [SARI_COUNT_W-1:0] sari_queued_count;

    logic raw_dmp_seed_valid;
    logic effective_dmp_seed_valid;
    logic [SRC_LINE_W-1:0] dmp_line_tag;
    logic [WORD_OFF_W-1:0] dmp_word;
    logic [TOKEN_W-1:0] current_token;
    logic [EPOCH_W-1:0] dmp_line_epoch;
    logic clpd_translation_ok;
    logic clpd_permission_ok;

    logic clpd_source_line_hit;
    logic clpd_source_word_proven;
    logic clpd_source_authorized;
    logic clpd_seed_allow;
    logic clpd_seed_block;
    logic clpd_block_no_entry;
    logic clpd_block_word_unproven;
    logic clpd_block_stale_epoch;
    logic clpd_block_token_mismatch;
    logic clpd_block_fault_or_perm;

    logic record_valid;
    logic [TGT_LINE_W-1:0] record_vline;
    logic [TGT_LINE_W-1:0] record_pline;
    logic [TOKEN_W-1:0] record_token;
    logic ctlw_query_valid;
    logic [TGT_LINE_W-1:0] candidate_target_line;
    logic ctlw_witness_valid;
    logic [TGT_LINE_W-1:0] ctlw_witness_pline;
    logic ctlw_query_miss;
    logic ctlw_token_mismatch_seen;
    logic ctlw_line_mismatch_seen;
    logic ctlw_remap_clear_hit;
    logic ctlw_tlbi_clear_hit;
    logic ctlw_collision_evict;

    logic target_same_page;
    logic same_page_translation_ok;
    logic target_permission_ok;
    logic terminal_source;

    logic source_valid;
    logic source_clean;
    logic [VALUE_W-1:0] source_value;
    logic [EPOCH_W-1:0] source_epoch;
    logic proof_valid;
    logic proof_sound;
    logic [VALUE_W-1:0] proof_value;
    logic [EPOCH_W-1:0] proof_epoch;
    logic [TOKEN_W-1:0] proof_token;

    logic gate_source_authorized;
    logic gate_target_authorized;
    logic dmp_seed_allow;
    logic dmp_seed_block;
    logic block_no_source_proof;
    logic block_stale_source;
    logic block_token_mismatch;
    logic block_terminal_source;
    logic block_no_target_authority;
    logic block_fault_or_perm;

    logic exp_target_authorized;
    logic exp_allow;
    logic exp_block;

    int errors;
    int initial_allow_seen;
    int conflict_hold_seen;
    int matching_source_hold_seen;
    int matching_source_post_block_seen;
    int queued_source_hold_seen;
    int unrelated_source_allow_seen;
    int queued_unrelated_source_allow_seen;
    int matching_remap_hold_seen;
    int matching_remap_post_block_seen;
    int unrelated_remap_allow_seen;
    int wrong_token_remap_allow_seen;
    int matching_tlbi_hold_seen;
    int matching_tlbi_post_block_seen;
    int unrelated_tlbi_allow_seen;
    int tlbi_all_hold_seen;
    int tlbi_all_post_block_seen;
    int avoided_global_hold_seen;
    int avoided_global_allow_seen;
    int random_hold_seen;
    int random_avoided_seen;
    int random_allow_seen;
    int random_block_seen;
    int overflow_hold_seen;

    copper_sari_scoped_revoker #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .DEPTH(SARI_DEPTH),
        .COUNT_W(SARI_COUNT_W)
    ) sari (
        .clk(clk),
        .rst_n(rst_n),
        .dma_write_valid(dma_write_valid),
        .dma_line_tag(dma_line_tag),
        .chi_snoop_valid(chi_snoop_valid),
        .chi_snoop_write(chi_snoop_write),
        .chi_snoop_invalidate(chi_snoop_invalidate),
        .chi_line_tag(chi_line_tag),
        .io_write_valid(io_write_valid),
        .io_line_tag(io_line_tag),
        .target_remap_valid(target_remap_valid),
        .target_remap_vline(target_remap_vline),
        .target_remap_token(target_remap_token),
        .tlbi_token_valid(tlbi_token_valid),
        .tlbi_token(tlbi_token),
        .tlbi_all_valid(tlbi_all_valid),
        .raw_dmp_seed_valid(raw_dmp_seed_valid),
        .dmp_source_line_tag(dmp_line_tag),
        .dmp_target_vline(candidate_target_line),
        .dmp_token(current_token),
        .source_clear_valid(source_clear_valid),
        .source_clear_line_tag(source_clear_line_tag),
        .source_events_ready(source_events_ready),
        .ctlw_remap_valid(ctlw_remap_valid),
        .ctlw_remap_vline(ctlw_remap_vline),
        .ctlw_remap_token(ctlw_remap_token),
        .ctlw_tlbi_token_valid(ctlw_tlbi_token_valid),
        .ctlw_tlbi_token(ctlw_tlbi_token),
        .ctlw_tlbi_all_valid(ctlw_tlbi_all_valid),
        .dmp_conflict_hold(sari_conflict_hold),
        .dmp_global_hold(sari_global_hold),
        .overflow_sticky(sari_overflow_sticky),
        .queued_count(sari_queued_count)
    );

    assign effective_dmp_seed_valid = raw_dmp_seed_valid && !sari_conflict_hold;

    copper_clpd_gate #(
        .LINE_TAG_W(SRC_LINE_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W),
        .ENTRIES(CLPD_ENTRIES),
        .ENTRY_IDX_W(CLPD_IDX_W)
    ) clpd (
        .clk(clk),
        .rst_n(rst_n),
        .commit_ptr_valid(commit_ptr_valid),
        .commit_line_tag(commit_line_tag),
        .commit_word(commit_word),
        .commit_token(commit_token),
        .commit_line_epoch(commit_line_epoch),
        .source_write_valid(1'b0),
        .source_write_line_tag('0),
        .line_fill_valid(1'b0),
        .line_fill_tag('0),
        .invalidate_valid(source_clear_valid),
        .invalidate_line_tag(source_clear_line_tag),
        .dmp_seed_valid(effective_dmp_seed_valid),
        .dmp_line_tag(dmp_line_tag),
        .dmp_word(dmp_word),
        .dmp_src_token(current_token),
        .dmp_target_token(current_token),
        .dmp_line_epoch(dmp_line_epoch),
        .dmp_translation_ok(clpd_translation_ok),
        .dmp_permission_ok(clpd_permission_ok),
        .source_line_hit(clpd_source_line_hit),
        .source_word_proven(clpd_source_word_proven),
        .source_authorized(clpd_source_authorized),
        .dmp_seed_allow(clpd_seed_allow),
        .dmp_seed_block(clpd_seed_block),
        .block_no_entry(clpd_block_no_entry),
        .block_word_unproven(clpd_block_word_unproven),
        .block_stale_epoch(clpd_block_stale_epoch),
        .block_token_mismatch(clpd_block_token_mismatch),
        .block_fault_or_perm(clpd_block_fault_or_perm)
    );

    assign ctlw_query_valid = effective_dmp_seed_valid && !target_same_page;

    copper_ctlw_witness_dir #(
        .VLINE_W(TGT_LINE_W),
        .PLINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .ENTRIES(CTLW_ENTRIES),
        .IDX_W(CTLW_IDX_W)
    ) ctlw (
        .clk(clk),
        .rst_n(rst_n),
        .record_valid(record_valid),
        .record_vline(record_vline),
        .record_pline(record_pline),
        .record_token(record_token),
        .remap_valid(ctlw_remap_valid),
        .remap_vline(ctlw_remap_vline),
        .remap_token(ctlw_remap_token),
        .tlbi_token_valid(ctlw_tlbi_token_valid),
        .tlbi_token(ctlw_tlbi_token),
        .tlbi_all_valid(ctlw_tlbi_all_valid),
        .query_valid(ctlw_query_valid),
        .query_vline(candidate_target_line),
        .query_token(current_token),
        .witness_valid(ctlw_witness_valid),
        .witness_pline(ctlw_witness_pline),
        .query_miss(ctlw_query_miss),
        .token_mismatch_seen(ctlw_token_mismatch_seen),
        .line_mismatch_seen(ctlw_line_mismatch_seen),
        .remap_clear_hit(ctlw_remap_clear_hit),
        .tlbi_clear_hit(ctlw_tlbi_clear_hit),
        .collision_evict(ctlw_collision_evict)
    );

    assign source_value = {dmp_line_tag, dmp_word};
    assign source_epoch = dmp_line_epoch;
    assign source_valid = 1'b1;
    assign source_clean = 1'b1;
    assign proof_valid = clpd_source_authorized;
    assign proof_sound = clpd_source_authorized;
    assign proof_value = source_value;
    assign proof_epoch = source_epoch;
    assign proof_token = current_token;

    copper_full_authority_gate #(
        .VALUE_W(VALUE_W),
        .EPOCH_W(EPOCH_W),
        .TOKEN_W(TOKEN_W),
        .LINE_W(TGT_LINE_W)
    ) authority (
        .dmp_seed_valid(effective_dmp_seed_valid),
        .source_valid(source_valid),
        .source_clean(source_clean),
        .source_value(source_value),
        .source_epoch(source_epoch),
        .current_token(current_token),
        .proof_valid(proof_valid),
        .proof_sound(proof_sound),
        .proof_value(proof_value),
        .proof_epoch(proof_epoch),
        .proof_token(proof_token),
        .target_same_page(target_same_page),
        .same_page_translation_ok(same_page_translation_ok),
        .target_permission_ok(target_permission_ok),
        .terminal_source(terminal_source),
        .candidate_target_line(candidate_target_line),
        .witness_valid(ctlw_witness_valid),
        .witness_target_line(ctlw_witness_valid ? candidate_target_line : '0),
        .witness_token(current_token),
        .source_authorized(gate_source_authorized),
        .target_authorized(gate_target_authorized),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block(dmp_seed_block),
        .block_no_source_proof(block_no_source_proof),
        .block_stale_source(block_stale_source),
        .block_token_mismatch(block_token_mismatch),
        .block_terminal_source(block_terminal_source),
        .block_no_target_authority(block_no_target_authority),
        .block_fault_or_perm(block_fault_or_perm)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    always_comb begin
        exp_target_authorized = target_same_page
            ? same_page_translation_ok
            : ctlw_witness_valid;

        exp_allow =
            effective_dmp_seed_valid
            && clpd_source_authorized
            && !terminal_source
            && exp_target_authorized
            && target_permission_ok;

        exp_block = effective_dmp_seed_valid && !exp_allow;
    end

    a_conflict_hold_prevents_issue:
        assert property (@(negedge clk) disable iff (!started)
            sari_conflict_hold |-> (!dmp_seed_allow && !dmp_seed_block));

    a_conflict_hold_is_subset_of_global_hold:
        assert property (@(negedge clk) disable iff (!started)
            sari_conflict_hold |-> sari_global_hold);

    a_effective_allow_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_allow == exp_allow);

    a_effective_block_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_block == exp_block);

    task automatic clear_inputs;
        begin
            commit_ptr_valid = 1'b0;
            commit_line_tag = '0;
            commit_word = '0;
            commit_token = '0;
            commit_line_epoch = '0;
            dma_write_valid = 1'b0;
            dma_line_tag = '0;
            chi_snoop_valid = 1'b0;
            chi_snoop_write = 1'b0;
            chi_snoop_invalidate = 1'b0;
            chi_line_tag = '0;
            io_write_valid = 1'b0;
            io_line_tag = '0;
            target_remap_valid = 1'b0;
            target_remap_vline = '0;
            target_remap_token = '0;
            tlbi_token_valid = 1'b0;
            tlbi_token = '0;
            tlbi_all_valid = 1'b0;
            record_valid = 1'b0;
            record_vline = '0;
            record_pline = '0;
            record_token = '0;
            raw_dmp_seed_valid = 1'b0;
            dmp_line_tag = 8'h35;
            dmp_word = 4'h3;
            current_token = 4'h2;
            dmp_line_epoch = 4'h1;
            clpd_translation_ok = 1'b1;
            clpd_permission_ok = 1'b1;
            target_same_page = 1'b0;
            same_page_translation_ok = 1'b1;
            target_permission_ok = 1'b1;
            terminal_source = 1'b0;
            candidate_target_line = 12'h234;
        end
    endtask

    task automatic reset_design;
        begin
            started = 1'b0;
            clear_inputs();
            rst_n = 1'b0;
            repeat (3) @(posedge clk);
            rst_n = 1'b1;
            @(posedge clk);
            #1;
            started = 1'b1;
        end
    endtask

    task automatic commit_source(
        input [SRC_LINE_W-1:0] tag,
        input [WORD_OFF_W-1:0] word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch
    );
        begin
            clear_inputs();
            commit_ptr_valid = 1'b1;
            commit_line_tag = tag;
            commit_word = word;
            commit_token = token;
            commit_line_epoch = epoch;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic record_target(
        input [TGT_LINE_W-1:0] vline,
        input [TOKEN_W-1:0] token
    );
        begin
            clear_inputs();
            record_valid = 1'b1;
            record_vline = vline;
            record_pline = vline ^ 12'h800;
            record_token = token;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic setup_live_cross(
        input [SRC_LINE_W-1:0] src_tag,
        input [WORD_OFF_W-1:0] src_word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] target_line
    );
        begin
            commit_source(src_tag, src_word, token, epoch);
            record_target(target_line, token);
        end
    endtask

    task automatic query_cross(
        input [SRC_LINE_W-1:0] src_tag,
        input [WORD_OFF_W-1:0] src_word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] target_line
    );
        begin
            clear_inputs();
            raw_dmp_seed_valid = 1'b1;
            dmp_line_tag = src_tag;
            dmp_word = src_word;
            current_token = token;
            dmp_line_epoch = epoch;
            candidate_target_line = target_line;
        end
    endtask

    task automatic sample_case(input string label);
        begin
            #1;
            if (dmp_seed_allow !== exp_allow) begin
                $error("%s: allow expected %0b got %0b", label, exp_allow, dmp_seed_allow);
                errors++;
            end
            if (dmp_seed_block !== exp_block) begin
                $error("%s: block expected %0b got %0b", label, exp_block, dmp_seed_block);
                errors++;
            end
            if (sari_conflict_hold) begin
                if (dmp_seed_allow || dmp_seed_block) begin
                    $error("%s: conflict hold should suppress both allow and block", label);
                    errors++;
                end
                conflict_hold_seen++;
            end
            if (raw_dmp_seed_valid && sari_global_hold && !sari_conflict_hold) begin
                avoided_global_hold_seen++;
                if (dmp_seed_allow) avoided_global_allow_seen++;
            end
            if (dmp_seed_allow) random_allow_seen++;
            if (dmp_seed_block) random_block_seen++;
            @(posedge clk);
            #1;
        end
    endtask

    task automatic drain_sari(input int cycles);
        begin
            clear_inputs();
            repeat (cycles) begin
                @(posedge clk);
                #1;
            end
            clear_inputs();
        end
    endtask

    task automatic enqueue_dma(input [SRC_LINE_W-1:0] tag);
        begin
            clear_inputs();
            dma_write_valid = 1'b1;
            dma_line_tag = tag;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic source_event_with_query(
        input [SRC_LINE_W-1:0] revoke_line,
        input [SRC_LINE_W-1:0] query_line,
        input [WORD_OFF_W-1:0] query_word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] target_line,
        input string label
    );
        begin
            query_cross(query_line, query_word, token, epoch, target_line);
            dma_write_valid = 1'b1;
            dma_line_tag = revoke_line;
            sample_case(label);
            clear_inputs();
        end
    endtask

    task automatic remap_with_query(
        input [TGT_LINE_W-1:0] remap_line,
        input [TOKEN_W-1:0] remap_token,
        input [SRC_LINE_W-1:0] query_line,
        input [WORD_OFF_W-1:0] query_word,
        input [TOKEN_W-1:0] query_token,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] query_target,
        input string label
    );
        begin
            query_cross(query_line, query_word, query_token, epoch, query_target);
            target_remap_valid = 1'b1;
            target_remap_vline = remap_line;
            target_remap_token = remap_token;
            sample_case(label);
            clear_inputs();
        end
    endtask

    task automatic tlbi_token_with_query(
        input [TOKEN_W-1:0] event_token,
        input [SRC_LINE_W-1:0] query_line,
        input [WORD_OFF_W-1:0] query_word,
        input [TOKEN_W-1:0] query_token,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] query_target,
        input string label
    );
        begin
            query_cross(query_line, query_word, query_token, epoch, query_target);
            tlbi_token_valid = 1'b1;
            tlbi_token = event_token;
            sample_case(label);
            clear_inputs();
        end
    endtask

    task automatic tlbi_all_with_query(
        input [SRC_LINE_W-1:0] query_line,
        input [WORD_OFF_W-1:0] query_word,
        input [TOKEN_W-1:0] query_token,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] query_target,
        input string label
    );
        begin
            query_cross(query_line, query_word, query_token, epoch, query_target);
            tlbi_all_valid = 1'b1;
            sample_case(label);
            clear_inputs();
        end
    endtask

    task automatic directed_tests;
        begin
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("initial live candidate allows");
            if (dmp_seed_allow) initial_allow_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            source_event_with_query(8'h35, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "matching DMA source revoke holds");
            if (sari_conflict_hold || conflict_hold_seen > 0) matching_source_hold_seen++;
            drain_sari(1);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("matching DMA source revoke post-drain blocks");
            if (dmp_seed_block && block_no_source_proof) matching_source_post_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            source_event_with_query(8'h7c, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "unrelated DMA source revoke does not hold");
            if (dmp_seed_allow && sari_global_hold && !sari_conflict_hold) unrelated_source_allow_seen++;
            drain_sari(1);

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            enqueue_dma(8'h35);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            #1;
            if (sari_conflict_hold) queued_source_hold_seen++;
            sample_case("queued matching source revoke holds before CLPD clear");
            drain_sari(1);

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            enqueue_dma(8'h7c);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            #1;
            if (dmp_seed_allow && sari_global_hold && !sari_conflict_hold) queued_unrelated_source_allow_seen++;
            sample_case("queued unrelated source revoke does not hold");
            drain_sari(1);

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            remap_with_query(12'h234, 4'h2, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "matching remap holds");
            if (conflict_hold_seen > 0) matching_remap_hold_seen++;
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("matching remap post-clear blocks target witness");
            if (dmp_seed_block && block_no_target_authority) matching_remap_post_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            remap_with_query(12'h555, 4'h2, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "unrelated remap does not hold");
            if (dmp_seed_allow && sari_global_hold && !sari_conflict_hold) unrelated_remap_allow_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            remap_with_query(12'h234, 4'h3, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "wrong-token remap does not hold");
            if (dmp_seed_allow && sari_global_hold && !sari_conflict_hold) wrong_token_remap_allow_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            tlbi_token_with_query(4'h2, 8'h35, 4'h3, 4'h2, 4'h1, 12'h345, "matching TLBI token holds");
            if (conflict_hold_seen > 0) matching_tlbi_hold_seen++;
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            sample_case("matching TLBI token post-clear blocks target witness");
            if (dmp_seed_block && block_no_target_authority) matching_tlbi_post_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            tlbi_token_with_query(4'h3, 8'h35, 4'h3, 4'h2, 4'h1, 12'h345, "unrelated TLBI token does not hold");
            if (dmp_seed_allow && sari_global_hold && !sari_conflict_hold) unrelated_tlbi_allow_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            tlbi_all_with_query(8'h35, 4'h3, 4'h2, 4'h1, 12'h456, "TLBI all holds every candidate");
            if (conflict_hold_seen > 0) tlbi_all_hold_seen++;
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            sample_case("TLBI all post-clear blocks target witness");
            if (dmp_seed_block && block_no_target_authority) tlbi_all_post_block_seen++;
        end
    endtask

    task automatic drive_random(input int trial);
        logic [SRC_LINE_W-1:0] src_tag;
        logic [WORD_OFF_W-1:0] src_word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        logic [TGT_LINE_W-1:0] tgt;
        int hold_before;
        int avoided_before;
        begin
            src_tag = $urandom_range(0, 255);
            src_word = $urandom_range(0, WORDS_PER_LINE - 1);
            token = $urandom_range(0, (1 << TOKEN_W) - 1);
            epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            tgt = $urandom_range(0, (1 << TGT_LINE_W) - 1);
            setup_live_cross(src_tag, src_word, token, epoch, tgt);

            hold_before = conflict_hold_seen;
            avoided_before = avoided_global_hold_seen;
            if ((trial % 17) == 0) begin
                source_event_with_query(src_tag, src_tag, src_word, token, epoch, tgt, $sformatf("random_matching_source_%0d", trial));
                drain_sari(1);
            end else if ((trial % 19) == 0) begin
                source_event_with_query(src_tag ^ 8'h80, src_tag, src_word, token, epoch, tgt, $sformatf("random_unrelated_source_%0d", trial));
                drain_sari(1);
            end else if ((trial % 23) == 0) begin
                remap_with_query(tgt, token, src_tag, src_word, token, epoch, tgt, $sformatf("random_matching_remap_%0d", trial));
            end else if ((trial % 29) == 0) begin
                remap_with_query(tgt ^ 12'h800, token, src_tag, src_word, token, epoch, tgt, $sformatf("random_unrelated_remap_%0d", trial));
            end else if ((trial % 31) == 0) begin
                tlbi_token_with_query(token, src_tag, src_word, token, epoch, tgt, $sformatf("random_matching_tlbi_%0d", trial));
            end else if ((trial % 37) == 0) begin
                tlbi_token_with_query(token ^ 4'h8, src_tag, src_word, token, epoch, tgt, $sformatf("random_unrelated_tlbi_%0d", trial));
            end else begin
                query_cross(src_tag, src_word, token, epoch, tgt);
                if ((trial % 11) == 0) dmp_word = src_word + 1'b1;
                if ((trial % 13) == 0) dmp_line_epoch = epoch + 1'b1;
                if ((trial % 41) == 0) terminal_source = 1'b1;
                if ((trial % 43) == 0) target_permission_ok = 1'b0;
                sample_case($sformatf("random_query_%0d", trial));
            end
            if (conflict_hold_seen > hold_before) random_hold_seen++;
            if (avoided_global_hold_seen > avoided_before) random_avoided_seen++;
        end
    endtask

    task automatic overflow_test;
        begin
            reset_design();
            for (int burst = 0; burst < 5; burst++) begin
                clear_inputs();
                dma_write_valid = 1'b1;
                dma_line_tag = 8'(burst * 3);
                chi_snoop_valid = 1'b1;
                chi_snoop_write = 1'b1;
                chi_line_tag = 8'(burst * 3 + 1);
                io_write_valid = 1'b1;
                io_line_tag = 8'(burst * 3 + 2);
                @(posedge clk);
                #1;
            end
            clear_inputs();
            raw_dmp_seed_valid = 1'b1;
            dmp_line_tag = 8'h35;
            dmp_word = 4'h3;
            current_token = 4'h2;
            dmp_line_epoch = 4'h1;
            candidate_target_line = 12'h234;
            #1;
            if (!sari_overflow_sticky || !sari_conflict_hold) begin
                $error("overflow test did not force conflict-scoped sticky hold");
                errors++;
            end else begin
                overflow_hold_seen++;
            end
        end
    endtask

    initial begin
        errors = 0;
        initial_allow_seen = 0;
        conflict_hold_seen = 0;
        matching_source_hold_seen = 0;
        matching_source_post_block_seen = 0;
        queued_source_hold_seen = 0;
        unrelated_source_allow_seen = 0;
        queued_unrelated_source_allow_seen = 0;
        matching_remap_hold_seen = 0;
        matching_remap_post_block_seen = 0;
        unrelated_remap_allow_seen = 0;
        wrong_token_remap_allow_seen = 0;
        matching_tlbi_hold_seen = 0;
        matching_tlbi_post_block_seen = 0;
        unrelated_tlbi_allow_seen = 0;
        tlbi_all_hold_seen = 0;
        tlbi_all_post_block_seen = 0;
        avoided_global_hold_seen = 0;
        avoided_global_allow_seen = 0;
        random_hold_seen = 0;
        random_avoided_seen = 0;
        random_allow_seen = 0;
        random_block_seen = 0;
        overflow_hold_seen = 0;

        reset_design();
        directed_tests();
        for (int trial = 0; trial < TRIALS; trial++) begin
            drive_random(trial);
        end
        overflow_test();

        if (
            errors != 0
            || initial_allow_seen == 0
            || conflict_hold_seen == 0
            || matching_source_hold_seen == 0
            || matching_source_post_block_seen == 0
            || queued_source_hold_seen == 0
            || unrelated_source_allow_seen == 0
            || queued_unrelated_source_allow_seen == 0
            || matching_remap_hold_seen == 0
            || matching_remap_post_block_seen == 0
            || unrelated_remap_allow_seen == 0
            || wrong_token_remap_allow_seen == 0
            || matching_tlbi_hold_seen == 0
            || matching_tlbi_post_block_seen == 0
            || unrelated_tlbi_allow_seen == 0
            || tlbi_all_hold_seen == 0
            || tlbi_all_post_block_seen == 0
            || avoided_global_hold_seen == 0
            || avoided_global_allow_seen == 0
            || random_hold_seen == 0
            || random_avoided_seen == 0
            || random_allow_seen == 0
            || random_block_seen == 0
            || overflow_hold_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER CS-SARI authority E2E coverage failed: errors=%0d initial_allow=%0d conflict_hold=%0d match_source_hold=%0d match_source_post=%0d queued_source_hold=%0d unrelated_source_allow=%0d queued_unrelated_allow=%0d match_remap_hold=%0d match_remap_post=%0d unrelated_remap_allow=%0d wrong_token_remap_allow=%0d match_tlbi_hold=%0d match_tlbi_post=%0d unrelated_tlbi_allow=%0d tlbi_all_hold=%0d tlbi_all_post=%0d avoided_global_hold=%0d avoided_global_allow=%0d random_hold=%0d random_avoided=%0d random_allow=%0d random_block=%0d overflow_hold=%0d",
                errors,
                initial_allow_seen,
                conflict_hold_seen,
                matching_source_hold_seen,
                matching_source_post_block_seen,
                queued_source_hold_seen,
                unrelated_source_allow_seen,
                queued_unrelated_source_allow_seen,
                matching_remap_hold_seen,
                matching_remap_post_block_seen,
                unrelated_remap_allow_seen,
                wrong_token_remap_allow_seen,
                matching_tlbi_hold_seen,
                matching_tlbi_post_block_seen,
                unrelated_tlbi_allow_seen,
                tlbi_all_hold_seen,
                tlbi_all_post_block_seen,
                avoided_global_hold_seen,
                avoided_global_allow_seen,
                random_hold_seen,
                random_avoided_seen,
                random_allow_seen,
                random_block_seen,
                overflow_hold_seen
            );
        end

        $display(
            "COPPER CS-SARI authority E2E tests completed: directed=12 random=%0d initial_allow=%0d conflict_hold=%0d matching_source_hold=%0d matching_source_post_block=%0d queued_source_hold=%0d unrelated_source_allow=%0d queued_unrelated_source_allow=%0d matching_remap_hold=%0d matching_remap_post_block=%0d unrelated_remap_allow=%0d wrong_token_remap_allow=%0d matching_tlbi_hold=%0d matching_tlbi_post_block=%0d unrelated_tlbi_allow=%0d tlbi_all_hold=%0d tlbi_all_post_block=%0d avoided_global_hold=%0d avoided_global_allow=%0d random_hold=%0d random_avoided=%0d random_allow=%0d random_block=%0d overflow_hold=%0d errors=%0d",
            TRIALS,
            initial_allow_seen,
            conflict_hold_seen,
            matching_source_hold_seen,
            matching_source_post_block_seen,
            queued_source_hold_seen,
            unrelated_source_allow_seen,
            queued_unrelated_source_allow_seen,
            matching_remap_hold_seen,
            matching_remap_post_block_seen,
            unrelated_remap_allow_seen,
            wrong_token_remap_allow_seen,
            matching_tlbi_hold_seen,
            matching_tlbi_post_block_seen,
            unrelated_tlbi_allow_seen,
            tlbi_all_hold_seen,
            tlbi_all_post_block_seen,
            avoided_global_hold_seen,
            avoided_global_allow_seen,
            random_hold_seen,
            random_avoided_seen,
            random_allow_seen,
            random_block_seen,
            overflow_hold_seen,
            errors
        );
        $finish;
    end

endmodule
