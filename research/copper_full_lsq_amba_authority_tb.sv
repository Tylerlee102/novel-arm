`timescale 1ns/1ps

// COPPER full LSQ + AMBA/SARI authority integration test.
//
// This test exercises the full public COPPER proof/authority path:
// LSQ source tag -> CEPF -> CLPD source proof -> AMBA frontdoor/SARI-RQ
// revocation -> CTLW target witness -> final DMP allow/block predicate.

module copper_full_lsq_amba_authority_tb;

    localparam int TAG_ENTRIES = 8;
    localparam int TAG_W = 3;
    localparam int SRC_LINE_W = 8;
    localparam int WORDS_PER_LINE = 16;
    localparam int WORD_OFF_W = 4;
    localparam int TOKEN_W = 4;
    localparam int EPOCH_W = 4;
    localparam int VALUE_W = 16;
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

    logic flush_valid;
    logic capture_valid;
    logic [TAG_W-1:0] capture_tag;
    logic [SRC_LINE_W-1:0] capture_src_line_idx;
    logic [WORD_OFF_W-1:0] capture_src_word;
    logic [TOKEN_W-1:0] capture_src_token;
    logic [EPOCH_W-1:0] capture_src_epoch;
    logic [VALUE_W-1:0] capture_src_value_hash;
    logic clear_tag_valid;
    logic [TAG_W-1:0] clear_tag;
    logic source_write_valid;
    logic [SRC_LINE_W-1:0] source_write_line_idx;
    logic [WORD_OFF_W-1:0] source_write_word;
    logic line_fill_valid;
    logic [SRC_LINE_W-1:0] line_fill_idx;
    logic invalidate_valid;
    logic [SRC_LINE_W-1:0] invalidate_line_idx;
    logic commit_valid;
    logic commit_is_memory;
    logic commit_dep_tag_valid;
    logic [TAG_W-1:0] commit_dep_tag;
    logic commit_exception;
    logic commit_squashed;
    logic commit_translation_ok;
    logic commit_permission_ok;
    logic [EPOCH_W-1:0] commit_src_current_epoch;
    logic [VALUE_W-1:0] commit_src_current_value_hash;

    logic dma_write_valid;
    logic [SRC_LINE_W-1:0] dma_line_tag;
    logic chi_event_valid;
    logic [CHI_KIND_W-1:0] chi_event_kind;
    logic [SRC_LINE_W-1:0] chi_line_tag;
    logic io_write_valid;
    logic [SRC_LINE_W-1:0] io_line_tag;
    logic target_remap_valid;
    logic [TGT_LINE_W-1:0] target_remap_vline;
    logic [TOKEN_W-1:0] target_remap_token;
    logic dvm_valid;
    logic [DVM_KIND_W-1:0] dvm_kind;
    logic [TOKEN_W-1:0] dvm_token;
    logic record_valid;
    logic [TGT_LINE_W-1:0] record_vline;
    logic [TGT_LINE_W-1:0] record_pline;
    logic [TOKEN_W-1:0] record_token;

    logic raw_dmp_seed_valid;
    logic [SRC_LINE_W-1:0] dmp_line_tag;
    logic [WORD_OFF_W-1:0] dmp_word;
    logic [TOKEN_W-1:0] current_token;
    logic [EPOCH_W-1:0] dmp_line_epoch;
    logic clpd_translation_ok;
    logic clpd_permission_ok;
    logic [TGT_LINE_W-1:0] candidate_target_line;
    logic target_same_page;
    logic same_page_translation_ok;
    logic target_permission_ok;
    logic terminal_source;

    logic effective_dmp_seed_valid;
    logic dmp_seed_allow;
    logic dmp_seed_block;
    logic lsq_proof_valid;
    logic bridge_proof_valid;
    logic frontdoor_ready;
    logic dmp_frontdoor_hold;
    logic source_backpressure;
    logic sari_dmp_revocation_hold;
    logic sari_overflow_sticky;
    logic [SARI_COUNT_W-1:0] sari_queued_count;
    logic clpd_source_authorized;
    logic ctlw_witness_valid;
    logic block_no_source_proof;
    logic block_no_target_authority;
    logic block_fault_or_perm;
    logic blocked_no_tag;
    logic blocked_tag_stale;
    logic blocked_epoch_value_mismatch;

    int errors;
    int baseline_allow_seen;
    int lsq_proof_seen;
    int bridge_proof_seen;
    int no_tag_seen;
    int stale_tag_seen;
    int epoch_value_mismatch_seen;
    int dma_hold_seen;
    int dma_post_block_seen;
    int chi_hold_seen;
    int chi_post_block_seen;
    int io_hold_seen;
    int io_post_block_seen;
    int remap_hold_seen;
    int remap_post_block_seen;
    int dvm_token_hold_seen;
    int dvm_token_post_block_seen;
    int dvm_all_hold_seen;
    int dvm_all_post_block_seen;
    int same_page_allow_seen;
    int terminal_block_seen;
    int perm_block_seen;
    int random_hold_seen;
    int random_allow_seen;
    int random_block_seen;

    copper_full_lsq_amba_authority_top #(
        .TAG_ENTRIES(TAG_ENTRIES),
        .TAG_W(TAG_W),
        .SRC_LINE_W(SRC_LINE_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W),
        .VALUE_W(VALUE_W),
        .CLPD_ENTRIES(CLPD_ENTRIES),
        .CLPD_IDX_W(CLPD_IDX_W),
        .TGT_LINE_W(TGT_LINE_W),
        .CTLW_ENTRIES(CTLW_ENTRIES),
        .CTLW_IDX_W(CTLW_IDX_W),
        .SARI_DEPTH(SARI_DEPTH),
        .SARI_COUNT_W(SARI_COUNT_W),
        .CHI_KIND_W(CHI_KIND_W),
        .DVM_KIND_W(DVM_KIND_W)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .flush_valid(flush_valid),
        .capture_valid(capture_valid),
        .capture_tag(capture_tag),
        .capture_src_line_idx(capture_src_line_idx),
        .capture_src_word(capture_src_word),
        .capture_src_token(capture_src_token),
        .capture_src_epoch(capture_src_epoch),
        .capture_src_value_hash(capture_src_value_hash),
        .clear_tag_valid(clear_tag_valid),
        .clear_tag(clear_tag),
        .source_write_valid(source_write_valid),
        .source_write_line_idx(source_write_line_idx),
        .source_write_word(source_write_word),
        .line_fill_valid(line_fill_valid),
        .line_fill_idx(line_fill_idx),
        .invalidate_valid(invalidate_valid),
        .invalidate_line_idx(invalidate_line_idx),
        .commit_valid(commit_valid),
        .commit_is_memory(commit_is_memory),
        .commit_dep_tag_valid(commit_dep_tag_valid),
        .commit_dep_tag(commit_dep_tag),
        .commit_exception(commit_exception),
        .commit_squashed(commit_squashed),
        .commit_translation_ok(commit_translation_ok),
        .commit_permission_ok(commit_permission_ok),
        .commit_src_current_epoch(commit_src_current_epoch),
        .commit_src_current_value_hash(commit_src_current_value_hash),
        .dma_write_valid(dma_write_valid),
        .dma_line_tag(dma_line_tag),
        .chi_event_valid(chi_event_valid),
        .chi_event_kind(chi_event_kind),
        .chi_line_tag(chi_line_tag),
        .io_write_valid(io_write_valid),
        .io_line_tag(io_line_tag),
        .target_remap_valid(target_remap_valid),
        .target_remap_vline(target_remap_vline),
        .target_remap_token(target_remap_token),
        .dvm_valid(dvm_valid),
        .dvm_kind(dvm_kind),
        .dvm_token(dvm_token),
        .record_valid(record_valid),
        .record_vline(record_vline),
        .record_pline(record_pline),
        .record_token(record_token),
        .raw_dmp_seed_valid(raw_dmp_seed_valid),
        .dmp_line_tag(dmp_line_tag),
        .dmp_word(dmp_word),
        .current_token(current_token),
        .dmp_line_epoch(dmp_line_epoch),
        .clpd_translation_ok(clpd_translation_ok),
        .clpd_permission_ok(clpd_permission_ok),
        .candidate_target_line(candidate_target_line),
        .target_same_page(target_same_page),
        .same_page_translation_ok(same_page_translation_ok),
        .target_permission_ok(target_permission_ok),
        .terminal_source(terminal_source),
        .effective_dmp_seed_valid(effective_dmp_seed_valid),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block(dmp_seed_block),
        .lsq_proof_valid(lsq_proof_valid),
        .bridge_proof_valid(bridge_proof_valid),
        .frontdoor_ready(frontdoor_ready),
        .dmp_frontdoor_hold(dmp_frontdoor_hold),
        .source_backpressure(source_backpressure),
        .sari_dmp_revocation_hold(sari_dmp_revocation_hold),
        .sari_overflow_sticky(sari_overflow_sticky),
        .sari_queued_count(sari_queued_count),
        .clpd_source_authorized(clpd_source_authorized),
        .ctlw_witness_valid(ctlw_witness_valid),
        .block_no_source_proof(block_no_source_proof),
        .block_no_target_authority(block_no_target_authority),
        .block_fault_or_perm(block_fault_or_perm),
        .blocked_no_tag(blocked_no_tag),
        .blocked_tag_stale(blocked_tag_stale),
        .blocked_epoch_value_mismatch(blocked_epoch_value_mismatch)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    a_hold_suppresses_issue:
        assert property (@(negedge clk) disable iff (!started)
            (raw_dmp_seed_valid && (dmp_frontdoor_hold || sari_dmp_revocation_hold))
            |-> (!dmp_seed_allow && !dmp_seed_block));

    a_allow_requires_source_and_target:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_allow |-> (clpd_source_authorized && !terminal_source && target_permission_ok
                && (target_same_page ? same_page_translation_ok : ctlw_witness_valid)));

    task automatic clear_inputs;
        begin
            flush_valid = 1'b0;
            capture_valid = 1'b0;
            capture_tag = '0;
            capture_src_line_idx = '0;
            capture_src_word = '0;
            capture_src_token = '0;
            capture_src_epoch = '0;
            capture_src_value_hash = '0;
            clear_tag_valid = 1'b0;
            clear_tag = '0;
            source_write_valid = 1'b0;
            source_write_line_idx = '0;
            source_write_word = '0;
            line_fill_valid = 1'b0;
            line_fill_idx = '0;
            invalidate_valid = 1'b0;
            invalidate_line_idx = '0;
            commit_valid = 1'b0;
            commit_is_memory = 1'b1;
            commit_dep_tag_valid = 1'b0;
            commit_dep_tag = '0;
            commit_exception = 1'b0;
            commit_squashed = 1'b0;
            commit_translation_ok = 1'b1;
            commit_permission_ok = 1'b1;
            commit_src_current_epoch = 4'h1;
            commit_src_current_value_hash = 16'hc0de;
            dma_write_valid = 1'b0;
            dma_line_tag = '0;
            chi_event_valid = 1'b0;
            chi_event_kind = CHI_READ_SHARED;
            chi_line_tag = '0;
            io_write_valid = 1'b0;
            io_line_tag = '0;
            target_remap_valid = 1'b0;
            target_remap_vline = '0;
            target_remap_token = '0;
            dvm_valid = 1'b0;
            dvm_kind = DVM_NONE;
            dvm_token = '0;
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
            candidate_target_line = 12'h234;
            target_same_page = 1'b0;
            same_page_translation_ok = 1'b1;
            target_permission_ok = 1'b1;
            terminal_source = 1'b0;
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

    task automatic capture_source(
        input [TAG_W-1:0] tag,
        input [SRC_LINE_W-1:0] line,
        input [WORD_OFF_W-1:0] word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch,
        input [VALUE_W-1:0] value_hash
    );
        begin
            clear_inputs();
            capture_valid = 1'b1;
            capture_tag = tag;
            capture_src_line_idx = line;
            capture_src_word = word;
            capture_src_token = token;
            capture_src_epoch = epoch;
            capture_src_value_hash = value_hash;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic commit_from_tag(
        input [TAG_W-1:0] tag,
        input [EPOCH_W-1:0] epoch,
        input [VALUE_W-1:0] value_hash,
        input bit expect_proof,
        input string label
    );
        begin
            clear_inputs();
            commit_valid = 1'b1;
            commit_is_memory = 1'b1;
            commit_dep_tag_valid = 1'b1;
            commit_dep_tag = tag;
            commit_src_current_epoch = epoch;
            commit_src_current_value_hash = value_hash;
            #1;
            if (expect_proof && (!lsq_proof_valid || !bridge_proof_valid)) begin
                $error("%s: expected LSQ/bridge proof", label);
                errors++;
            end
            if (!expect_proof && (lsq_proof_valid || bridge_proof_valid)) begin
                $error("%s: unexpected LSQ/bridge proof", label);
                errors++;
            end
            if (lsq_proof_valid) lsq_proof_seen++;
            if (bridge_proof_valid) bridge_proof_seen++;
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
        input [SRC_LINE_W-1:0] line,
        input [WORD_OFF_W-1:0] word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch,
        input [VALUE_W-1:0] value_hash,
        input [TGT_LINE_W-1:0] target_line
    );
        begin
            drain(2);
            capture_source(3'h1, line, word, token, epoch, value_hash);
            commit_from_tag(3'h1, epoch, value_hash, 1'b1, "setup commit");
            record_target(target_line, token);
        end
    endtask

    task automatic query_cross(
        input [SRC_LINE_W-1:0] line,
        input [WORD_OFF_W-1:0] word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] target_line
    );
        begin
            clear_inputs();
            raw_dmp_seed_valid = 1'b1;
            dmp_line_tag = line;
            dmp_word = word;
            current_token = token;
            dmp_line_epoch = epoch;
            candidate_target_line = target_line;
            target_same_page = 1'b0;
        end
    endtask

    task automatic sample_query(input string label);
        begin
            #1;
            if (raw_dmp_seed_valid && (dmp_frontdoor_hold || sari_dmp_revocation_hold)) begin
                if (dmp_seed_allow || dmp_seed_block) begin
                    $error("%s: hold should suppress allow/block", label);
                    errors++;
                end
                random_hold_seen++;
            end else if (dmp_seed_allow) begin
                if (!clpd_source_authorized) begin
                    $error("%s: allow without source authority", label);
                    errors++;
                end
                if (!target_same_page && !ctlw_witness_valid) begin
                    $error("%s: cross-page allow without CTLW witness", label);
                    errors++;
                end
                random_allow_seen++;
            end else if (dmp_seed_block) begin
                random_block_seen++;
            end
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic drain(input int cycles);
        begin
            clear_inputs();
            repeat (cycles) begin
                @(posedge clk);
                #1;
            end
        end
    endtask

    task automatic directed_tests;
        begin
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de, 12'h234);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_query("baseline full path allow");
            if (dmp_seed_allow) baseline_allow_seen++;

            clear_inputs();
            commit_valid = 1'b1;
            commit_is_memory = 1'b1;
            commit_dep_tag_valid = 1'b1;
            commit_dep_tag = 3'h7;
            #1;
            if (blocked_no_tag) no_tag_seen++;
            if (lsq_proof_valid || bridge_proof_valid) begin
                $error("missing tag should not create proof");
                errors++;
            end
            @(posedge clk);
            #1;

            reset_design();
            capture_source(3'h1, 8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de);
            clear_inputs();
            source_write_valid = 1'b1;
            source_write_line_idx = 8'h35;
            source_write_word = 4'h3;
            commit_valid = 1'b1;
            commit_is_memory = 1'b1;
            commit_dep_tag_valid = 1'b1;
            commit_dep_tag = 3'h1;
            commit_src_current_epoch = 4'h1;
            commit_src_current_value_hash = 16'hc0de;
            #1;
            if (blocked_tag_stale) stale_tag_seen++;
            if (lsq_proof_valid || bridge_proof_valid) begin
                $error("same-cycle source write should block proof");
                errors++;
            end
            @(posedge clk);
            #1;

            reset_design();
            capture_source(3'h1, 8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de);
            commit_from_tag(3'h1, 4'h2, 16'hc0de, 1'b0, "epoch mismatch");
            if (blocked_epoch_value_mismatch) epoch_value_mismatch_seen++;

            reset_design();
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de, 12'h234);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            dma_write_valid = 1'b1;
            dma_line_tag = 8'h35;
            sample_query("DMA same-cycle hold");
            if (dmp_frontdoor_hold) dma_hold_seen++;
            drain(2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_query("DMA post-clear blocks source");
            if (dmp_seed_block && block_no_source_proof) dma_post_block_seen++;

            reset_design();
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de, 12'h234);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            chi_event_valid = 1'b1;
            chi_event_kind = CHI_MAKE_INVALID;
            chi_line_tag = 8'h35;
            sample_query("CHI same-cycle hold");
            if (dmp_frontdoor_hold) chi_hold_seen++;
            drain(2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_query("CHI post-clear blocks source");
            if (dmp_seed_block && block_no_source_proof) chi_post_block_seen++;

            reset_design();
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de, 12'h234);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            io_write_valid = 1'b1;
            io_line_tag = 8'h35;
            sample_query("IO same-cycle hold");
            if (dmp_frontdoor_hold) io_hold_seen++;
            drain(2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_query("IO post-clear blocks source");
            if (dmp_seed_block && block_no_source_proof) io_post_block_seen++;

            reset_design();
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de, 12'h234);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            target_remap_valid = 1'b1;
            target_remap_vline = 12'h234;
            target_remap_token = 4'h2;
            sample_query("target remap same-cycle hold");
            if (dmp_frontdoor_hold) remap_hold_seen++;
            drain(1);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_query("target remap post-clear blocks target");
            if (dmp_seed_block && block_no_target_authority) remap_post_block_seen++;

            reset_design();
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de, 12'h345);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            dvm_valid = 1'b1;
            dvm_kind = DVM_TLBI_TOKEN;
            dvm_token = 4'h2;
            sample_query("DVM token same-cycle hold");
            if (dmp_frontdoor_hold) dvm_token_hold_seen++;
            drain(1);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            sample_query("DVM token post-clear blocks target");
            if (dmp_seed_block && block_no_target_authority) dvm_token_post_block_seen++;

            reset_design();
            setup_live_cross(8'h35, 4'h3, 4'h2, 4'h1, 16'hc0de, 12'h456);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            dvm_valid = 1'b1;
            dvm_kind = DVM_TLBI_ALL;
            dvm_token = 4'h2;
            sample_query("DVM all same-cycle hold");
            if (dmp_frontdoor_hold) dvm_all_hold_seen++;
            drain(1);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            sample_query("DVM all post-clear blocks target");
            if (dmp_seed_block && block_no_target_authority) dvm_all_post_block_seen++;

            reset_design();
            setup_live_cross(8'h45, 4'h5, 4'h2, 4'h1, 16'hcafe, 12'h567);
            clear_inputs();
            raw_dmp_seed_valid = 1'b1;
            dmp_line_tag = 8'h45;
            dmp_word = 4'h5;
            current_token = 4'h2;
            dmp_line_epoch = 4'h1;
            target_same_page = 1'b1;
            same_page_translation_ok = 1'b1;
            sample_query("same-page target allow");
            if (dmp_seed_allow) same_page_allow_seen++;

            clear_inputs();
            raw_dmp_seed_valid = 1'b1;
            dmp_line_tag = 8'h45;
            dmp_word = 4'h5;
            current_token = 4'h2;
            dmp_line_epoch = 4'h1;
            target_same_page = 1'b1;
            terminal_source = 1'b1;
            sample_query("terminal source block");
            if (dmp_seed_block && !dmp_seed_allow) terminal_block_seen++;

            clear_inputs();
            raw_dmp_seed_valid = 1'b1;
            dmp_line_tag = 8'h45;
            dmp_word = 4'h5;
            current_token = 4'h2;
            dmp_line_epoch = 4'h1;
            target_same_page = 1'b1;
            target_permission_ok = 1'b0;
            sample_query("permission block");
            if (dmp_seed_block && block_fault_or_perm) perm_block_seen++;
        end
    endtask

    task automatic drive_random(input int trial);
        logic [SRC_LINE_W-1:0] src;
        logic [WORD_OFF_W-1:0] word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        logic [VALUE_W-1:0] value_hash;
        logic [TGT_LINE_W-1:0] tgt;
        begin
            src = $urandom_range(0, 255);
            word = $urandom_range(0, WORDS_PER_LINE - 1);
            token = $urandom_range(0, (1 << TOKEN_W) - 1);
            epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            value_hash = $urandom();
            tgt = $urandom_range(0, (1 << TGT_LINE_W) - 1);

            if ((trial % 5) == 0) begin
                setup_live_cross(src, word, token, epoch, value_hash, tgt);
            end

            query_cross(src, word, token, epoch, tgt);
            if ((trial % 11) == 0) dmp_word = word + 1'b1;
            if ((trial % 13) == 0) dmp_line_epoch = epoch + 1'b1;
            if ((trial % 17) == 0) begin
                dma_write_valid = 1'b1;
                dma_line_tag = src;
            end else if ((trial % 19) == 0) begin
                chi_event_valid = 1'b1;
                chi_event_kind = CHI_READ_UNIQUE;
                chi_line_tag = src;
            end else if ((trial % 23) == 0) begin
                io_write_valid = 1'b1;
                io_line_tag = src;
            end else if ((trial % 29) == 0) begin
                target_remap_valid = 1'b1;
                target_remap_vline = tgt;
                target_remap_token = token;
            end else if ((trial % 31) == 0) begin
                dvm_valid = 1'b1;
                dvm_kind = DVM_TLBI_TOKEN;
                dvm_token = token;
            end else if ((trial % 37) == 0) begin
                target_same_page = 1'b1;
            end else if ((trial % 41) == 0) begin
                terminal_source = 1'b1;
            end else if ((trial % 43) == 0) begin
                target_permission_ok = 1'b0;
            end
            sample_query($sformatf("random_%0d", trial));
        end
    endtask

    initial begin
        errors = 0;
        baseline_allow_seen = 0;
        lsq_proof_seen = 0;
        bridge_proof_seen = 0;
        no_tag_seen = 0;
        stale_tag_seen = 0;
        epoch_value_mismatch_seen = 0;
        dma_hold_seen = 0;
        dma_post_block_seen = 0;
        chi_hold_seen = 0;
        chi_post_block_seen = 0;
        io_hold_seen = 0;
        io_post_block_seen = 0;
        remap_hold_seen = 0;
        remap_post_block_seen = 0;
        dvm_token_hold_seen = 0;
        dvm_token_post_block_seen = 0;
        dvm_all_hold_seen = 0;
        dvm_all_post_block_seen = 0;
        same_page_allow_seen = 0;
        terminal_block_seen = 0;
        perm_block_seen = 0;
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
            || lsq_proof_seen == 0
            || bridge_proof_seen == 0
            || no_tag_seen == 0
            || stale_tag_seen == 0
            || epoch_value_mismatch_seen == 0
            || dma_hold_seen == 0
            || dma_post_block_seen == 0
            || chi_hold_seen == 0
            || chi_post_block_seen == 0
            || io_hold_seen == 0
            || io_post_block_seen == 0
            || remap_hold_seen == 0
            || remap_post_block_seen == 0
            || dvm_token_hold_seen == 0
            || dvm_token_post_block_seen == 0
            || dvm_all_hold_seen == 0
            || dvm_all_post_block_seen == 0
            || same_page_allow_seen == 0
            || terminal_block_seen == 0
            || perm_block_seen == 0
            || random_hold_seen == 0
            || random_allow_seen == 0
            || random_block_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER full LSQ-AMBA authority coverage failed: errors=%0d baseline=%0d lsq=%0d bridge=%0d no_tag=%0d stale=%0d mismatch=%0d dma_hold=%0d dma_post=%0d chi_hold=%0d chi_post=%0d io_hold=%0d io_post=%0d remap_hold=%0d remap_post=%0d dvm_token_hold=%0d dvm_token_post=%0d dvm_all_hold=%0d dvm_all_post=%0d same_page=%0d terminal=%0d perm=%0d random_hold=%0d random_allow=%0d random_block=%0d",
                errors,
                baseline_allow_seen,
                lsq_proof_seen,
                bridge_proof_seen,
                no_tag_seen,
                stale_tag_seen,
                epoch_value_mismatch_seen,
                dma_hold_seen,
                dma_post_block_seen,
                chi_hold_seen,
                chi_post_block_seen,
                io_hold_seen,
                io_post_block_seen,
                remap_hold_seen,
                remap_post_block_seen,
                dvm_token_hold_seen,
                dvm_token_post_block_seen,
                dvm_all_hold_seen,
                dvm_all_post_block_seen,
                same_page_allow_seen,
                terminal_block_seen,
                perm_block_seen,
                random_hold_seen,
                random_allow_seen,
                random_block_seen
            );
        end

        $display(
            "COPPER full LSQ-AMBA authority completed: directed=18 random=%0d baseline_allow=%0d lsq_proof=%0d bridge_proof=%0d no_tag=%0d stale_tag=%0d epoch_value_mismatch=%0d dma_hold=%0d dma_post_block=%0d chi_hold=%0d chi_post_block=%0d io_hold=%0d io_post_block=%0d remap_hold=%0d remap_post_block=%0d dvm_token_hold=%0d dvm_token_post_block=%0d dvm_all_hold=%0d dvm_all_post_block=%0d same_page_allow=%0d terminal_block=%0d perm_block=%0d random_hold=%0d random_allow=%0d random_block=%0d errors=%0d",
            TRIALS,
            baseline_allow_seen,
            lsq_proof_seen,
            bridge_proof_seen,
            no_tag_seen,
            stale_tag_seen,
            epoch_value_mismatch_seen,
            dma_hold_seen,
            dma_post_block_seen,
            chi_hold_seen,
            chi_post_block_seen,
            io_hold_seen,
            io_post_block_seen,
            remap_hold_seen,
            remap_post_block_seen,
            dvm_token_hold_seen,
            dvm_token_post_block_seen,
            dvm_all_hold_seen,
            dvm_all_post_block_seen,
            same_page_allow_seen,
            terminal_block_seen,
            perm_block_seen,
            random_hold_seen,
            random_allow_seen,
            random_block_seen,
            errors
        );
        $finish;
    end

endmodule
