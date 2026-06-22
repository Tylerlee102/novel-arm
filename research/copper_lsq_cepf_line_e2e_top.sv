`timescale 1ns/1ps

// Synthesizable COPPER backend-to-cache proof path wrapper.
//
// This module is the hardware-cost companion to
// copper_lsq_cepf_line_e2e_tb.sv. It wires the LSQ source-tag tracker into the
// commit-epoch bridge and line-resident provenance gate using default widths
// close to the rest of the COPPER line-gate artifacts.

module copper_lsq_cepf_line_e2e_top #(
    parameter int TAG_ENTRIES = 8,
    parameter int TAG_W = 3,
    parameter int LINE_IDX_W = 6,
    parameter int WORDS_PER_LINE = 8,
    parameter int WORD_OFF_W = 3,
    parameter int DOMAIN_W = 8,
    parameter int EPOCH_W = 4,
    parameter int VALUE_W = 16,
    parameter int LINES = 64
) (
    input  logic clk,
    input  logic rst_n,

    input  logic flush_valid,

    input  logic capture_valid,
    input  logic [TAG_W-1:0] capture_tag,
    input  logic [LINE_IDX_W-1:0] capture_src_line_idx,
    input  logic [WORD_OFF_W-1:0] capture_src_word,
    input  logic [DOMAIN_W-1:0] capture_src_domain,
    input  logic [EPOCH_W-1:0] capture_src_epoch,
    input  logic [VALUE_W-1:0] capture_src_value_hash,

    input  logic clear_tag_valid,
    input  logic [TAG_W-1:0] clear_tag,

    input  logic source_write_valid,
    input  logic [LINE_IDX_W-1:0] source_write_line_idx,
    input  logic [WORD_OFF_W-1:0] source_write_word,

    input  logic line_fill_valid,
    input  logic [LINE_IDX_W-1:0] line_fill_idx,

    input  logic invalidate_valid,
    input  logic [LINE_IDX_W-1:0] invalidate_line_idx,

    input  logic commit_valid,
    input  logic commit_is_memory,
    input  logic commit_dep_tag_valid,
    input  logic [TAG_W-1:0] commit_dep_tag,
    input  logic commit_exception,
    input  logic commit_squashed,
    input  logic commit_translation_ok,
    input  logic commit_permission_ok,
    input  logic [EPOCH_W-1:0] commit_src_current_epoch,
    input  logic [VALUE_W-1:0] commit_src_current_value_hash,

    input  logic dmp_seed_valid,
    input  logic [LINE_IDX_W-1:0] dmp_line_idx,
    input  logic [WORD_OFF_W-1:0] dmp_word,
    input  logic [DOMAIN_W-1:0] dmp_src_domain,
    input  logic [DOMAIN_W-1:0] dmp_target_domain,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    output logic dmp_seed_allow,
    output logic dmp_seed_block,
    output logic source_proven_clean,

    output logic lsq_proof_valid,
    output logic bridge_proof_valid,
    output logic blocked_not_commit,
    output logic blocked_no_tag,
    output logic blocked_fault_or_perm,
    output logic blocked_tag_stale,
    output logic blocked_epoch_value_mismatch
);

    logic [LINE_IDX_W-1:0] lsq_proof_line_idx;
    logic [WORD_OFF_W-1:0] lsq_proof_word;
    logic [DOMAIN_W-1:0] lsq_proof_domain;
    logic [EPOCH_W-1:0] lsq_proof_epoch;
    logic [VALUE_W-1:0] lsq_proof_value_hash;
    logic [LINE_IDX_W-1:0] bridge_proof_line_idx;
    logic [WORD_OFF_W-1:0] bridge_proof_word;
    logic [DOMAIN_W-1:0] bridge_proof_domain;
    logic bridge_blocked_not_commit;
    logic bridge_blocked_no_source;
    logic bridge_blocked_fault_or_perm;
    logic bridge_blocked_epoch_mismatch;

    copper_lsq_source_tag_tracker #(
        .TAG_ENTRIES(TAG_ENTRIES),
        .TAG_W(TAG_W),
        .LINE_IDX_W(LINE_IDX_W),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .EPOCH_W(EPOCH_W),
        .VALUE_W(VALUE_W)
    ) tracker (
        .clk(clk),
        .rst_n(rst_n),
        .flush_valid(flush_valid),
        .capture_valid(capture_valid),
        .capture_tag(capture_tag),
        .capture_src_line_idx(capture_src_line_idx),
        .capture_src_word(capture_src_word),
        .capture_src_domain(capture_src_domain),
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
        .proof_valid(lsq_proof_valid),
        .proof_line_idx(lsq_proof_line_idx),
        .proof_word(lsq_proof_word),
        .proof_domain(lsq_proof_domain),
        .proof_epoch(lsq_proof_epoch),
        .proof_value_hash(lsq_proof_value_hash),
        .blocked_not_commit(blocked_not_commit),
        .blocked_no_tag(blocked_no_tag),
        .blocked_fault_or_perm(blocked_fault_or_perm),
        .blocked_tag_stale(blocked_tag_stale),
        .blocked_epoch_value_mismatch(blocked_epoch_value_mismatch)
    );

    copper_commit_epoch_proof_bridge #(
        .LINE_IDX_W(LINE_IDX_W),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .EPOCH_W(EPOCH_W)
    ) bridge (
        .commit_valid(commit_valid),
        .commit_is_memory(commit_is_memory),
        .commit_addr_dep_valid(lsq_proof_valid),
        .commit_exception(commit_exception),
        .commit_squashed(commit_squashed),
        .commit_translation_ok(commit_translation_ok),
        .commit_permission_ok(commit_permission_ok),
        .commit_src_line_idx(lsq_proof_line_idx),
        .commit_src_word(lsq_proof_word),
        .commit_src_domain(lsq_proof_domain),
        .commit_src_epoch(lsq_proof_epoch),
        .source_current_epoch(commit_src_current_epoch),
        .proof_valid(bridge_proof_valid),
        .proof_line_idx(bridge_proof_line_idx),
        .proof_word(bridge_proof_word),
        .proof_domain(bridge_proof_domain),
        .blocked_not_commit(bridge_blocked_not_commit),
        .blocked_no_source(bridge_blocked_no_source),
        .blocked_fault_or_perm(bridge_blocked_fault_or_perm),
        .blocked_epoch_mismatch(bridge_blocked_epoch_mismatch)
    );

    copper_line_provenance_gate #(
        .LINE_IDX_W(LINE_IDX_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .LINES(LINES)
    ) line_gate (
        .clk(clk),
        .rst_n(rst_n),
        .commit_ptr_valid(bridge_proof_valid),
        .commit_line_idx(bridge_proof_line_idx),
        .commit_word(bridge_proof_word),
        .commit_domain(bridge_proof_domain),
        .write_valid(source_write_valid),
        .write_line_idx(source_write_line_idx),
        .write_word(source_write_word),
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

endmodule
