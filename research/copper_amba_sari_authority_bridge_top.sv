`timescale 1ns/1ps

// Synthesizable COPPER AMBA-frontdoor -> SARI -> CLPD -> CTLW -> authority top.
//
// This top is an out-of-context timing/area vehicle for the public SoC
// authority path. It composes the generic AMBA-style event decoder, SARI
// revocation queue, CLPD source-provenance directory, CTLW target-witness
// directory, and final DMP authority predicate.

module copper_amba_sari_authority_bridge_top #(
    parameter int SRC_LINE_W = 12,
    parameter int WORDS_PER_LINE = 16,
    parameter int WORD_OFF_W = 4,
    parameter int VALUE_W = SRC_LINE_W + WORD_OFF_W,
    parameter int EPOCH_W = 4,
    parameter int TOKEN_W = 8,
    parameter int CLPD_ENTRIES = 64,
    parameter int CLPD_IDX_W = 6,
    parameter int TGT_LINE_W = 16,
    parameter int CTLW_ENTRIES = 16,
    parameter int CTLW_IDX_W = 4,
    parameter int SARI_DEPTH = 8,
    parameter int SARI_COUNT_W = 4,
    parameter int CHI_KIND_W = 3,
    parameter int DVM_KIND_W = 2
) (
    input  logic clk,
    input  logic rst_n,

    input  logic commit_ptr_valid,
    input  logic [SRC_LINE_W-1:0] commit_line_tag,
    input  logic [WORD_OFF_W-1:0] commit_word,
    input  logic [TOKEN_W-1:0] commit_token,
    input  logic [EPOCH_W-1:0] commit_line_epoch,

    input  logic dma_write_valid,
    input  logic [SRC_LINE_W-1:0] dma_line_tag,
    input  logic chi_event_valid,
    input  logic [CHI_KIND_W-1:0] chi_event_kind,
    input  logic [SRC_LINE_W-1:0] chi_line_tag,
    input  logic io_write_valid,
    input  logic [SRC_LINE_W-1:0] io_line_tag,

    input  logic target_remap_valid,
    input  logic [TGT_LINE_W-1:0] target_remap_vline,
    input  logic [TOKEN_W-1:0] target_remap_token,
    input  logic dvm_valid,
    input  logic [DVM_KIND_W-1:0] dvm_kind,
    input  logic [TOKEN_W-1:0] dvm_token,

    input  logic record_valid,
    input  logic [TGT_LINE_W-1:0] record_vline,
    input  logic [TGT_LINE_W-1:0] record_pline,
    input  logic [TOKEN_W-1:0] record_token,

    input  logic raw_dmp_seed_valid,
    input  logic [SRC_LINE_W-1:0] dmp_line_tag,
    input  logic [WORD_OFF_W-1:0] dmp_word,
    input  logic [TOKEN_W-1:0] current_token,
    input  logic [EPOCH_W-1:0] dmp_line_epoch,
    input  logic clpd_translation_ok,
    input  logic clpd_permission_ok,
    input  logic [TGT_LINE_W-1:0] candidate_target_line,
    input  logic target_same_page,
    input  logic same_page_translation_ok,
    input  logic target_permission_ok,
    input  logic terminal_source,

    output logic effective_dmp_seed_valid,
    output logic dmp_seed_allow,
    output logic dmp_seed_block,
    output logic frontdoor_ready,
    output logic dmp_frontdoor_hold,
    output logic source_backpressure,
    output logic sari_dmp_revocation_hold,
    output logic sari_overflow_sticky,
    output logic [SARI_COUNT_W-1:0] sari_queued_count,
    output logic clpd_source_authorized,
    output logic ctlw_witness_valid,
    output logic block_no_source_proof,
    output logic block_no_target_authority,
    output logic block_fault_or_perm
);

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
    logic decoded_source_event;
    logic decoded_target_event;

    logic source_clear_valid;
    logic [SRC_LINE_W-1:0] source_clear_line_tag;
    logic source_events_ready;
    logic ctlw_remap_valid;
    logic [TGT_LINE_W-1:0] ctlw_remap_vline;
    logic [TOKEN_W-1:0] ctlw_remap_token;
    logic ctlw_tlbi_token_valid;
    logic [TOKEN_W-1:0] ctlw_tlbi_token;
    logic ctlw_tlbi_all_valid;

    logic clpd_source_line_hit;
    logic clpd_source_word_proven;
    logic clpd_seed_allow;
    logic clpd_seed_block;
    logic clpd_block_no_entry;
    logic clpd_block_word_unproven;
    logic clpd_block_stale_epoch;
    logic clpd_block_token_mismatch;
    logic clpd_block_fault_or_perm;

    logic ctlw_query_valid;
    logic [TGT_LINE_W-1:0] ctlw_witness_pline;
    logic ctlw_query_miss;
    logic ctlw_token_mismatch_seen;
    logic ctlw_line_mismatch_seen;
    logic ctlw_remap_clear_hit;
    logic ctlw_tlbi_clear_hit;
    logic ctlw_collision_evict;

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
    logic block_stale_source;
    logic block_token_mismatch;
    logic block_terminal_source;

    copper_amba_sari_frontdoor #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .CHI_KIND_W(CHI_KIND_W),
        .DVM_KIND_W(DVM_KIND_W)
    ) frontdoor (
        .sari_source_events_ready(source_events_ready),
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

endmodule
