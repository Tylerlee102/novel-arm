`timescale 1ns/1ps

// COPPER AMBA-frontdoor -> SARI -> CLPD -> CTLW -> authority bridge test.
//
// This is a public AMBA-style integration harness, not a proprietary ARM CHI
// model. It checks the cycle-level contract between the generic AMBA/SARI
// event decoder and COPPER's local authority metadata: a decoded source or
// target authority event must suppress same-cycle DMP issue, and once the event
// is consumed by SARI/CTLW, stale source or target authority must not reappear.

module copper_amba_sari_authority_bridge_tb;

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
    localparam int CHI_KIND_W = 3;
    localparam int DVM_KIND_W = 2;
    localparam int TRIALS = 10000;

    localparam logic [CHI_KIND_W-1:0] CHI_READ_SHARED      = CHI_KIND_W'(3'd0);
    localparam logic [CHI_KIND_W-1:0] CHI_READ_UNIQUE      = CHI_KIND_W'(3'd1);
    localparam logic [CHI_KIND_W-1:0] CHI_CLEAN_INVALIDATE = CHI_KIND_W'(3'd2);
    localparam logic [CHI_KIND_W-1:0] CHI_MAKE_INVALID     = CHI_KIND_W'(3'd3);
    localparam logic [CHI_KIND_W-1:0] CHI_WRITEBACK_DIRTY  = CHI_KIND_W'(3'd4);
    localparam logic [CHI_KIND_W-1:0] CHI_DVM              = CHI_KIND_W'(3'd5);
    localparam logic [DVM_KIND_W-1:0] DVM_NONE             = DVM_KIND_W'(2'd0);
    localparam logic [DVM_KIND_W-1:0] DVM_TLBI_TOKEN       = DVM_KIND_W'(2'd1);
    localparam logic [DVM_KIND_W-1:0] DVM_TLBI_ALL         = DVM_KIND_W'(2'd2);

    logic clk;
    logic rst_n;
    logic started;

    logic commit_ptr_valid;
    logic [SRC_LINE_W-1:0] commit_line_tag;
    logic [WORD_OFF_W-1:0] commit_word;
    logic [TOKEN_W-1:0] commit_token;
    logic [EPOCH_W-1:0] commit_line_epoch;

    logic fd_dma_write_valid;
    logic [SRC_LINE_W-1:0] fd_dma_line_tag;
    logic fd_chi_event_valid;
    logic [CHI_KIND_W-1:0] fd_chi_event_kind;
    logic [SRC_LINE_W-1:0] fd_chi_line_tag;
    logic fd_io_write_valid;
    logic [SRC_LINE_W-1:0] fd_io_line_tag;
    logic fd_target_remap_valid;
    logic [TGT_LINE_W-1:0] fd_target_remap_vline;
    logic [TOKEN_W-1:0] fd_target_remap_token;
    logic fd_dvm_valid;
    logic [DVM_KIND_W-1:0] fd_dvm_kind;
    logic [TOKEN_W-1:0] fd_dvm_token;

    logic sari_dma_write_valid;
    logic [SRC_LINE_W-1:0] sari_dma_line_tag;
    logic sari_chi_snoop_valid;
    logic sari_chi_snoop_write;
    logic sari_chi_snoop_invalidate;
    logic [SRC_LINE_W-1:0] sari_chi_line_tag;
    logic sari_io_write_valid;
    logic [SRC_LINE_W-1:0] sari_io_line_tag;
    logic sari_target_remap_valid;
    logic [TGT_LINE_W-1:0] sari_target_remap_vline;
    logic [TOKEN_W-1:0] sari_target_remap_token;
    logic sari_tlbi_token_valid;
    logic [TOKEN_W-1:0] sari_tlbi_token;
    logic sari_tlbi_all_valid;
    logic frontdoor_ready;
    logic dmp_frontdoor_hold;
    logic decoded_source_event;
    logic decoded_target_event;
    logic source_backpressure;

    logic source_clear_valid;
    logic [SRC_LINE_W-1:0] source_clear_line_tag;
    logic source_events_ready;
    logic ctlw_remap_valid;
    logic [TGT_LINE_W-1:0] ctlw_remap_vline;
    logic [TOKEN_W-1:0] ctlw_remap_token;
    logic ctlw_tlbi_token_valid;
    logic [TOKEN_W-1:0] ctlw_tlbi_token;
    logic ctlw_tlbi_all_valid;
    logic sari_dmp_revocation_hold;
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
    int baseline_allow_seen;
    int frontdoor_hold_seen;
    int backpressure_seen;
    int read_shared_allow_seen;
    int dma_block_seen;
    int chi_unique_block_seen;
    int chi_clean_inv_block_seen;
    int chi_make_inv_block_seen;
    int chi_writeback_block_seen;
    int io_block_seen;
    int remap_block_seen;
    int dvm_token_block_seen;
    int dvm_all_block_seen;
    int chi_dvm_block_seen;
    int random_hold_seen;
    int random_allow_seen;
    int random_block_seen;

    copper_amba_sari_frontdoor #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .CHI_KIND_W(CHI_KIND_W),
        .DVM_KIND_W(DVM_KIND_W)
    ) frontdoor (
        .sari_source_events_ready(source_events_ready),
        .dma_write_valid(fd_dma_write_valid),
        .dma_line_tag(fd_dma_line_tag),
        .chi_event_valid(fd_chi_event_valid),
        .chi_event_kind(fd_chi_event_kind),
        .chi_line_tag(fd_chi_line_tag),
        .io_write_valid(fd_io_write_valid),
        .io_line_tag(fd_io_line_tag),
        .target_remap_valid(fd_target_remap_valid),
        .target_remap_vline(fd_target_remap_vline),
        .target_remap_token(fd_target_remap_token),
        .dvm_valid(fd_dvm_valid),
        .dvm_kind(fd_dvm_kind),
        .dvm_token(fd_dvm_token),
        .sari_dma_write_valid(sari_dma_write_valid),
        .sari_dma_line_tag(sari_dma_line_tag),
        .sari_chi_snoop_valid(sari_chi_snoop_valid),
        .sari_chi_snoop_write(sari_chi_snoop_write),
        .sari_chi_snoop_invalidate(sari_chi_snoop_invalidate),
        .sari_chi_line_tag(sari_chi_line_tag),
        .sari_io_write_valid(sari_io_write_valid),
        .sari_io_line_tag(sari_io_line_tag),
        .sari_target_remap_valid(sari_target_remap_valid),
        .sari_target_remap_vline(sari_target_remap_vline),
        .sari_target_remap_token(sari_target_remap_token),
        .sari_tlbi_token_valid(sari_tlbi_token_valid),
        .sari_tlbi_token(sari_tlbi_token),
        .sari_tlbi_all_valid(sari_tlbi_all_valid),
        .frontdoor_ready(frontdoor_ready),
        .dmp_frontdoor_hold(dmp_frontdoor_hold),
        .decoded_source_event(decoded_source_event),
        .decoded_target_event(decoded_target_event),
        .source_backpressure(source_backpressure)
    );

    copper_sari_ring_revoker #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .DEPTH(SARI_DEPTH),
        .COUNT_W(SARI_COUNT_W)
    ) sari (
        .clk(clk),
        .rst_n(rst_n),
        .dma_write_valid(sari_dma_write_valid),
        .dma_line_tag(sari_dma_line_tag),
        .chi_snoop_valid(sari_chi_snoop_valid),
        .chi_snoop_write(sari_chi_snoop_write),
        .chi_snoop_invalidate(sari_chi_snoop_invalidate),
        .chi_line_tag(sari_chi_line_tag),
        .io_write_valid(sari_io_write_valid),
        .io_line_tag(sari_io_line_tag),
        .target_remap_valid(sari_target_remap_valid),
        .target_remap_vline(sari_target_remap_vline),
        .target_remap_token(sari_target_remap_token),
        .tlbi_token_valid(sari_tlbi_token_valid),
        .tlbi_token(sari_tlbi_token),
        .tlbi_all_valid(sari_tlbi_all_valid),
        .source_clear_valid(source_clear_valid),
        .source_clear_line_tag(source_clear_line_tag),
        .source_events_ready(source_events_ready),
        .ctlw_remap_valid(ctlw_remap_valid),
        .ctlw_remap_vline(ctlw_remap_vline),
        .ctlw_remap_token(ctlw_remap_token),
        .ctlw_tlbi_token_valid(ctlw_tlbi_token_valid),
        .ctlw_tlbi_token(ctlw_tlbi_token),
        .ctlw_tlbi_all_valid(ctlw_tlbi_all_valid),
        .dmp_revocation_hold(sari_dmp_revocation_hold),
        .overflow_sticky(sari_overflow_sticky),
        .queued_count(sari_queued_count)
    );

    assign effective_dmp_seed_valid =
        raw_dmp_seed_valid && !dmp_frontdoor_hold && !sari_dmp_revocation_hold;

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

    a_frontdoor_hold_suppresses_issue:
        assert property (@(negedge clk) disable iff (!started)
            (raw_dmp_seed_valid && (dmp_frontdoor_hold || sari_dmp_revocation_hold))
            |-> (!dmp_seed_allow && !dmp_seed_block));

    a_effective_allow_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_allow == exp_allow);

    a_effective_block_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_block == exp_block);

    a_backpressure_holds_source_event:
        assert property (@(negedge clk) disable iff (!started)
            source_backpressure |-> (!frontdoor_ready && dmp_frontdoor_hold));

    task automatic clear_inputs;
        begin
            commit_ptr_valid = 1'b0;
            commit_line_tag = '0;
            commit_word = '0;
            commit_token = '0;
            commit_line_epoch = '0;
            fd_dma_write_valid = 1'b0;
            fd_dma_line_tag = '0;
            fd_chi_event_valid = 1'b0;
            fd_chi_event_kind = CHI_READ_SHARED;
            fd_chi_line_tag = '0;
            fd_io_write_valid = 1'b0;
            fd_io_line_tag = '0;
            fd_target_remap_valid = 1'b0;
            fd_target_remap_vline = '0;
            fd_target_remap_token = '0;
            fd_dvm_valid = 1'b0;
            fd_dvm_kind = DVM_NONE;
            fd_dvm_token = '0;
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
            target_same_page = 1'b0;
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
            if (raw_dmp_seed_valid && (dmp_frontdoor_hold || sari_dmp_revocation_hold)) begin
                if (dmp_seed_allow || dmp_seed_block) begin
                    $error("%s: frontdoor/SARI hold should suppress both allow and block", label);
                    errors++;
                end
                frontdoor_hold_seen++;
            end
            if (source_backpressure && (!frontdoor_ready || dmp_frontdoor_hold)) begin
                backpressure_seen++;
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

    task automatic inject_source_with_query(
        input int kind,
        input logic [CHI_KIND_W-1:0] chi_kind,
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
            if (kind == 0) begin
                fd_dma_write_valid = 1'b1;
                fd_dma_line_tag = revoke_line;
            end else if (kind == 1) begin
                fd_chi_event_valid = 1'b1;
                fd_chi_event_kind = chi_kind;
                fd_chi_line_tag = revoke_line;
            end else begin
                fd_io_write_valid = 1'b1;
                fd_io_line_tag = revoke_line;
            end
            sample_case(label);
            clear_inputs();
        end
    endtask

    task automatic inject_remap_with_query(
        input [TGT_LINE_W-1:0] remap_line,
        input [TOKEN_W-1:0] token,
        input [SRC_LINE_W-1:0] query_line,
        input [WORD_OFF_W-1:0] query_word,
        input [EPOCH_W-1:0] epoch,
        input string label
    );
        begin
            query_cross(query_line, query_word, token, epoch, remap_line);
            fd_target_remap_valid = 1'b1;
            fd_target_remap_vline = remap_line;
            fd_target_remap_token = token;
            sample_case(label);
            clear_inputs();
        end
    endtask

    task automatic inject_dvm_with_query(
        input logic [CHI_KIND_W-1:0] chi_kind,
        input logic [DVM_KIND_W-1:0] dvm_kind,
        input [TOKEN_W-1:0] token,
        input [SRC_LINE_W-1:0] query_line,
        input [WORD_OFF_W-1:0] query_word,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] target_line,
        input string label
    );
        begin
            query_cross(query_line, query_word, token, epoch, target_line);
            fd_chi_event_valid = (chi_kind == CHI_DVM);
            fd_chi_event_kind = chi_kind;
            fd_dvm_valid = 1'b1;
            fd_dvm_kind = dvm_kind;
            fd_dvm_token = token;
            sample_case(label);
            clear_inputs();
        end
    endtask

    task automatic post_source_block_check(input string label);
        begin
            drain_sari(1);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case(label);
        end
    endtask

    task automatic directed_tests;
        int before_hold;
        begin
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("baseline live AMBA/SARI authority allows");
            if (dmp_seed_allow) baseline_allow_seen++;

            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            fd_chi_event_valid = 1'b1;
            fd_chi_event_kind = CHI_READ_SHARED;
            fd_chi_line_tag = 8'h35;
            sample_case("read-shared frontdoor event is non-authority and allows");
            if (dmp_seed_allow && !decoded_source_event && !decoded_target_event) read_shared_allow_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            inject_source_with_query(0, CHI_READ_SHARED, 8'h35, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "DMA frontdoor source event holds");
            post_source_block_check("DMA frontdoor source event clears CLPD");
            if (dmp_seed_block && block_no_source_proof) dma_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            inject_source_with_query(1, CHI_READ_UNIQUE, 8'h35, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "CHI ReadUnique frontdoor source event holds");
            post_source_block_check("CHI ReadUnique clears CLPD");
            if (dmp_seed_block && block_no_source_proof) chi_unique_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            inject_source_with_query(1, CHI_CLEAN_INVALIDATE, 8'h35, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "CHI CleanInvalidate frontdoor source event holds");
            post_source_block_check("CHI CleanInvalidate clears CLPD");
            if (dmp_seed_block && block_no_source_proof) chi_clean_inv_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            inject_source_with_query(1, CHI_MAKE_INVALID, 8'h35, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "CHI MakeInvalid frontdoor source event holds");
            post_source_block_check("CHI MakeInvalid clears CLPD");
            if (dmp_seed_block && block_no_source_proof) chi_make_inv_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            inject_source_with_query(1, CHI_WRITEBACK_DIRTY, 8'h35, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "CHI WritebackDirty frontdoor source event holds");
            post_source_block_check("CHI WritebackDirty clears CLPD");
            if (dmp_seed_block && block_no_source_proof) chi_writeback_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            inject_source_with_query(2, CHI_READ_SHARED, 8'h35, 8'h35, 4'h3, 4'h2, 4'h1, 12'h234, "IO frontdoor source event holds");
            post_source_block_check("IO frontdoor source event clears CLPD");
            if (dmp_seed_block && block_no_source_proof) io_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            inject_remap_with_query(12'h234, 4'h2, 8'h35, 4'h3, 4'h1, "target remap frontdoor event holds");
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("target remap clears CTLW witness");
            if (dmp_seed_block && block_no_target_authority) remap_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            inject_dvm_with_query(CHI_READ_SHARED, DVM_TLBI_TOKEN, 4'h2, 8'h35, 4'h3, 4'h1, 12'h345, "DVM token frontdoor event holds");
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            sample_case("DVM token clears matching CTLW witness");
            if (dmp_seed_block && block_no_target_authority) dvm_token_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            inject_dvm_with_query(CHI_READ_SHARED, DVM_TLBI_ALL, 4'h2, 8'h35, 4'h3, 4'h1, 12'h456, "DVM all frontdoor event holds");
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            sample_case("DVM all clears CTLW witnesses");
            if (dmp_seed_block && block_no_target_authority) dvm_all_block_seen++;

            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h567);
            inject_dvm_with_query(CHI_DVM, DVM_TLBI_TOKEN, 4'h2, 8'h35, 4'h3, 4'h1, 12'h567, "CHI-DVM token frontdoor event holds");
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h567);
            sample_case("CHI-DVM token clears CTLW witness");
            if (dmp_seed_block && block_no_target_authority) chi_dvm_block_seen++;

            reset_design();
            for (int burst = 0; burst < 3; burst++) begin
                clear_inputs();
                fd_dma_write_valid = 1'b1;
                fd_dma_line_tag = 8'(burst * 3);
                fd_chi_event_valid = 1'b1;
                fd_chi_event_kind = CHI_READ_UNIQUE;
                fd_chi_line_tag = 8'(burst * 3 + 1);
                fd_io_write_valid = 1'b1;
                fd_io_line_tag = 8'(burst * 3 + 2);
                @(posedge clk);
                #1;
            end
            before_hold = frontdoor_hold_seen;
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            fd_dma_write_valid = 1'b1;
            fd_dma_line_tag = 8'h35;
            sample_case("frontdoor backpressure holds source event when SARI queue lacks room");
            if (source_backpressure && !frontdoor_ready && frontdoor_hold_seen > before_hold) begin
                backpressure_seen++;
            end
            drain_sari(SARI_DEPTH + 2);
        end
    endtask

    task automatic drive_random(input int trial);
        logic [SRC_LINE_W-1:0] src_tag;
        logic [WORD_OFF_W-1:0] src_word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        logic [TGT_LINE_W-1:0] tgt;
        int hold_before;
        begin
            src_tag = $urandom_range(0, 255);
            src_word = $urandom_range(0, WORDS_PER_LINE - 1);
            token = $urandom_range(0, (1 << TOKEN_W) - 1);
            epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            tgt = $urandom_range(0, (1 << TGT_LINE_W) - 1);

            if ((trial % 4) == 0) begin
                setup_live_cross(src_tag, src_word, token, epoch, tgt);
            end

            hold_before = frontdoor_hold_seen;
            if ((trial % 17) == 0) begin
                inject_source_with_query(0, CHI_READ_SHARED, src_tag, src_tag, src_word, token, epoch, tgt, $sformatf("random_dma_%0d", trial));
                drain_sari(1);
            end else if ((trial % 23) == 0) begin
                inject_source_with_query(1, CHI_READ_UNIQUE, src_tag, src_tag, src_word, token, epoch, tgt, $sformatf("random_chi_unique_%0d", trial));
                drain_sari(1);
            end else if ((trial % 29) == 0) begin
                inject_source_with_query(1, CHI_MAKE_INVALID, src_tag, src_tag, src_word, token, epoch, tgt, $sformatf("random_chi_inv_%0d", trial));
                drain_sari(1);
            end else if ((trial % 31) == 0) begin
                inject_source_with_query(2, CHI_READ_SHARED, src_tag, src_tag, src_word, token, epoch, tgt, $sformatf("random_io_%0d", trial));
                drain_sari(1);
            end else if ((trial % 37) == 0) begin
                inject_remap_with_query(tgt, token, src_tag, src_word, epoch, $sformatf("random_remap_%0d", trial));
            end else if ((trial % 41) == 0) begin
                inject_dvm_with_query(CHI_READ_SHARED, DVM_TLBI_TOKEN, token, src_tag, src_word, epoch, tgt, $sformatf("random_dvm_token_%0d", trial));
            end else if ((trial % 43) == 0) begin
                query_cross(src_tag, src_word, token, epoch, tgt);
                fd_chi_event_valid = 1'b1;
                fd_chi_event_kind = CHI_READ_SHARED;
                fd_chi_line_tag = src_tag;
                sample_case($sformatf("random_read_shared_%0d", trial));
            end else begin
                query_cross(src_tag, src_word, token, epoch, tgt);
                if ((trial % 11) == 0) dmp_word = src_word + 1'b1;
                if ((trial % 13) == 0) dmp_line_epoch = epoch + 1'b1;
                if ((trial % 19) == 0) candidate_target_line = tgt + 12'h010;
                if ((trial % 47) == 0) target_same_page = 1'b1;
                if ((trial % 53) == 0) terminal_source = 1'b1;
                if ((trial % 59) == 0) target_permission_ok = 1'b0;
                sample_case($sformatf("random_query_%0d", trial));
            end

            if (frontdoor_hold_seen > hold_before) random_hold_seen++;
        end
    endtask

    initial begin
        errors = 0;
        baseline_allow_seen = 0;
        frontdoor_hold_seen = 0;
        backpressure_seen = 0;
        read_shared_allow_seen = 0;
        dma_block_seen = 0;
        chi_unique_block_seen = 0;
        chi_clean_inv_block_seen = 0;
        chi_make_inv_block_seen = 0;
        chi_writeback_block_seen = 0;
        io_block_seen = 0;
        remap_block_seen = 0;
        dvm_token_block_seen = 0;
        dvm_all_block_seen = 0;
        chi_dvm_block_seen = 0;
        random_hold_seen = 0;
        random_allow_seen = 0;
        random_block_seen = 0;

        reset_design();
        directed_tests();
        reset_design();
        for (int trial = 0; trial < TRIALS; trial++) begin
            drive_random(trial);
        end

        if (
            errors != 0
            || baseline_allow_seen == 0
            || frontdoor_hold_seen == 0
            || backpressure_seen == 0
            || read_shared_allow_seen == 0
            || dma_block_seen == 0
            || chi_unique_block_seen == 0
            || chi_clean_inv_block_seen == 0
            || chi_make_inv_block_seen == 0
            || chi_writeback_block_seen == 0
            || io_block_seen == 0
            || remap_block_seen == 0
            || dvm_token_block_seen == 0
            || dvm_all_block_seen == 0
            || chi_dvm_block_seen == 0
            || random_hold_seen == 0
            || random_allow_seen == 0
            || random_block_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER AMBA-SARI authority bridge coverage failed: errors=%0d baseline=%0d hold=%0d backpressure=%0d read_shared=%0d dma=%0d chi_unique=%0d chi_clean_inv=%0d chi_make_inv=%0d chi_wb=%0d io=%0d remap=%0d dvm_token=%0d dvm_all=%0d chi_dvm=%0d random_hold=%0d random_allow=%0d random_block=%0d",
                errors,
                baseline_allow_seen,
                frontdoor_hold_seen,
                backpressure_seen,
                read_shared_allow_seen,
                dma_block_seen,
                chi_unique_block_seen,
                chi_clean_inv_block_seen,
                chi_make_inv_block_seen,
                chi_writeback_block_seen,
                io_block_seen,
                remap_block_seen,
                dvm_token_block_seen,
                dvm_all_block_seen,
                chi_dvm_block_seen,
                random_hold_seen,
                random_allow_seen,
                random_block_seen
            );
        end

        $display(
            "COPPER AMBA-SARI authority bridge completed: directed=15 random=%0d baseline_allow=%0d frontdoor_hold=%0d backpressure=%0d read_shared_allow=%0d dma_block=%0d chi_unique_block=%0d chi_clean_inv_block=%0d chi_make_inv_block=%0d chi_writeback_block=%0d io_block=%0d remap_block=%0d dvm_token_block=%0d dvm_all_block=%0d chi_dvm_block=%0d random_hold=%0d random_allow=%0d random_block=%0d errors=%0d",
            TRIALS,
            baseline_allow_seen,
            frontdoor_hold_seen,
            backpressure_seen,
            read_shared_allow_seen,
            dma_block_seen,
            chi_unique_block_seen,
            chi_clean_inv_block_seen,
            chi_make_inv_block_seen,
            chi_writeback_block_seen,
            io_block_seen,
            remap_block_seen,
            dvm_token_block_seen,
            dvm_all_block_seen,
            chi_dvm_block_seen,
            random_hold_seen,
            random_allow_seen,
            random_block_seen,
            errors
        );
        $finish;
    end

endmodule
