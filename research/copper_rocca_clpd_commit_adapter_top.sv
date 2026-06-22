`timescale 1ns/1ps

// Synthesizable ROCCA-to-CLPD boundary wrapper.

module copper_rocca_clpd_commit_adapter_top #(
    parameter int LINE_TAG_W = 12,
    parameter int WORDS_PER_LINE = 16,
    parameter int WORD_OFF_W = 4,
    parameter int TOKEN_W = 8,
    parameter int EPOCH_W = 4,
    parameter int ENTRIES = 64,
    parameter int ENTRY_IDX_W = 6
) (
    input  logic clk,
    input  logic rst_n,

    input  logic ropl_proof_valid,
    input  logic [LINE_TAG_W-1:0] ropl_line_tag,
    input  logic [WORD_OFF_W-1:0] ropl_word,
    input  logic [TOKEN_W-1:0] ropl_token,
    input  logic [EPOCH_W-1:0] ropl_epoch,
    input  logic source_clean,
    input  logic source_epoch_match,
    input  logic commit_translation_ok,
    input  logic commit_permission_ok,

    input  logic global_clear_valid,
    input  logic source_write_valid,
    input  logic [LINE_TAG_W-1:0] source_write_line_tag,
    input  logic line_fill_valid,
    input  logic [LINE_TAG_W-1:0] line_fill_tag,
    input  logic invalidate_valid,
    input  logic [LINE_TAG_W-1:0] invalidate_line_tag,

    input  logic dmp_seed_valid,
    input  logic [LINE_TAG_W-1:0] dmp_line_tag,
    input  logic [WORD_OFF_W-1:0] dmp_word,
    input  logic [TOKEN_W-1:0] dmp_src_token,
    input  logic [TOKEN_W-1:0] dmp_target_token,
    input  logic [EPOCH_W-1:0] dmp_line_epoch,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    output logic dmp_seed_allow,
    output logic dmp_seed_block,
    output logic source_authorized,
    output logic same_cycle_clear_hit,
    output logic blocked_clear_wins,
    output logic blocked_source_not_clean,
    output logic blocked_epoch_mismatch,
    output logic blocked_fault_or_perm
);

    logic clpd_commit_ptr_valid;
    logic [LINE_TAG_W-1:0] clpd_commit_line_tag;
    logic [WORD_OFF_W-1:0] clpd_commit_word;
    logic [TOKEN_W-1:0] clpd_commit_token;
    logic [EPOCH_W-1:0] clpd_commit_line_epoch;
    logic block_no_entry;
    logic block_word_unproven;
    logic block_stale_epoch;
    logic block_token_mismatch;
    logic block_fault_or_perm;
    logic source_line_hit;
    logic source_word_proven;

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
        .blocked_no_retire_proof(),
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

endmodule
