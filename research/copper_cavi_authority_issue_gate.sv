`timescale 1ns/1ps

// CAVI: Commit-Authority Validity Interlock.
//
// CAVI is the executable end-to-end issue contract for COPPER's retained
// source proofs and target-line authority witnesses. ROCCA/CLPD may say that a
// committed source word is allowed to seed a DMP. The target authority filter
// may say that the predicted target line is still valid after remap, TLBI, and
// permission events. CAVI allows issue only when both are true in the same
// cycle, with revocation and clear events taking priority over proof reuse.

module copper_cavi_authority_issue_gate #(
    parameter int SRC_LINE_W = 12,
    parameter int TGT_LINE_W = 16,
    parameter int WORDS_PER_LINE = 16,
    parameter int WORD_OFF_W = 4,
    parameter int TOKEN_W = 8,
    parameter int EPOCH_W = 4,
    parameter int CLPD_ENTRIES = 64,
    parameter int CLPD_IDX_W = 6,
    parameter int SOURCE_Q_DEPTH = 4,
    parameter int TARGET_Q_DEPTH = 4,
    parameter int COUNT_W = 3
) (
    input  logic clk,
    input  logic rst_n,

    input  logic ropl_proof_valid,
    input  logic [SRC_LINE_W-1:0] ropl_line_tag,
    input  logic [WORD_OFF_W-1:0] ropl_word,
    input  logic [TOKEN_W-1:0] ropl_token,
    input  logic [EPOCH_W-1:0] ropl_epoch,
    input  logic source_clean,
    input  logic source_epoch_match,
    input  logic commit_translation_ok,
    input  logic commit_permission_ok,

    input  logic global_clear_valid,
    input  logic source_write_valid,
    input  logic [SRC_LINE_W-1:0] source_write_line_tag,
    input  logic line_fill_valid,
    input  logic [SRC_LINE_W-1:0] line_fill_tag,
    input  logic source_revoke_valid,
    input  logic [SRC_LINE_W-1:0] source_revoke_line,

    input  logic dmp_seed_valid,
    input  logic [SRC_LINE_W-1:0] dmp_line_tag,
    input  logic [WORD_OFF_W-1:0] dmp_word,
    input  logic [TOKEN_W-1:0] dmp_src_token,
    input  logic [TOKEN_W-1:0] dmp_target_token,
    input  logic [EPOCH_W-1:0] dmp_line_epoch,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    input  logic [TGT_LINE_W-1:0] dmp_target_line,
    input  logic target_witness_valid,
    input  logic target_exact_match,
    input  logic target_permission_ok,

    input  logic target_remap_valid,
    input  logic [TGT_LINE_W-1:0] target_remap_line,
    input  logic [TOKEN_W-1:0] target_remap_token,
    input  logic tlbi_token_valid,
    input  logic [TOKEN_W-1:0] tlbi_token,
    input  logic tlbi_all_valid,
    input  logic permission_downgrade_valid,
    input  logic [TGT_LINE_W-1:0] permission_line,
    input  logic [TOKEN_W-1:0] permission_token,
    input  logic source_drain_enable,
    input  logic target_drain_enable,

    output logic dmp_issue_allow,
    output logic dmp_issue_block,
    output logic source_gate_allow,
    output logic source_gate_block,
    output logic target_gate_allow,
    output logic target_gate_block,
    output logic source_authorized,
    output logic target_conflict_hold,
    output logic same_cycle_clear_hit,
    output logic blocked_clear_wins,
    output logic source_block_no_entry,
    output logic source_block_word_unproven,
    output logic source_block_stale_epoch,
    output logic source_block_token_mismatch,
    output logic source_block_fault_or_perm,
    output logic target_block_no_source_proof,
    output logic target_block_no_witness,
    output logic target_block_permission,
    output logic target_block_revocation,
    output logic target_block_overflow,
    output logic overflow_sticky
);

    logic clpd_commit_ptr_valid;
    logic [SRC_LINE_W-1:0] clpd_commit_line_tag;
    logic [WORD_OFF_W-1:0] clpd_commit_word;
    logic [TOKEN_W-1:0] clpd_commit_token;
    logic [EPOCH_W-1:0] clpd_commit_line_epoch;
    logic source_line_hit;
    logic source_word_proven;
    logic source_events_ready;
    logic target_events_ready;
    logic source_clear_valid;
    logic [SRC_LINE_W-1:0] source_clear_line;
    logic target_clear_valid;
    logic target_clear_is_remap;
    logic target_clear_is_token;
    logic target_clear_is_global;
    logic [TGT_LINE_W-1:0] target_clear_line;
    logic [TOKEN_W-1:0] target_clear_token;
    logic [COUNT_W-1:0] source_queued_count;
    logic [COUNT_W-1:0] target_queued_count;

    copper_rocca_clpd_commit_adapter #(
        .LINE_TAG_W(SRC_LINE_W),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W)
    ) rocca (
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
        .invalidate_valid(source_revoke_valid),
        .invalidate_line_tag(source_revoke_line),
        .clpd_commit_ptr_valid(clpd_commit_ptr_valid),
        .clpd_commit_line_tag(clpd_commit_line_tag),
        .clpd_commit_word(clpd_commit_word),
        .clpd_commit_token(clpd_commit_token),
        .clpd_commit_line_epoch(clpd_commit_line_epoch),
        .same_cycle_clear_hit(same_cycle_clear_hit),
        .blocked_no_retire_proof(),
        .blocked_source_not_clean(),
        .blocked_epoch_mismatch(),
        .blocked_fault_or_perm(),
        .blocked_clear_wins(blocked_clear_wins)
    );

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
        .commit_ptr_valid(clpd_commit_ptr_valid),
        .commit_line_tag(clpd_commit_line_tag),
        .commit_word(clpd_commit_word),
        .commit_token(clpd_commit_token),
        .commit_line_epoch(clpd_commit_line_epoch),
        .source_write_valid(source_write_valid),
        .source_write_line_tag(source_write_line_tag),
        .line_fill_valid(line_fill_valid),
        .line_fill_tag(line_fill_tag),
        .invalidate_valid(source_revoke_valid),
        .invalidate_line_tag(source_revoke_line),
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
        .dmp_seed_allow(source_gate_allow),
        .dmp_seed_block(source_gate_block),
        .block_no_entry(source_block_no_entry),
        .block_word_unproven(source_block_word_unproven),
        .block_stale_epoch(source_block_stale_epoch),
        .block_token_mismatch(source_block_token_mismatch),
        .block_fault_or_perm(source_block_fault_or_perm)
    );

    copper_tlb_coherence_authority_filter #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .SOURCE_Q_DEPTH(SOURCE_Q_DEPTH),
        .TARGET_Q_DEPTH(TARGET_Q_DEPTH),
        .COUNT_W(COUNT_W)
    ) target_authority (
        .clk(clk),
        .rst_n(rst_n),
        .candidate_valid(dmp_seed_valid),
        .candidate_src_line(dmp_line_tag),
        .candidate_tgt_line(dmp_target_line),
        .candidate_token(dmp_target_token),
        .source_proof_valid(source_gate_allow),
        .target_witness_valid(target_witness_valid),
        .target_exact_match(target_exact_match),
        .target_permission_ok(target_permission_ok),
        .source_revoke_valid(source_revoke_valid),
        .source_revoke_line(source_revoke_line),
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
        .dmp_allow(target_gate_allow),
        .dmp_block(target_gate_block),
        .conflict_hold(target_conflict_hold),
        .block_no_source_proof(target_block_no_source_proof),
        .block_no_target_witness(target_block_no_witness),
        .block_permission(target_block_permission),
        .block_revocation(target_block_revocation),
        .block_overflow(target_block_overflow),
        .source_clear_valid(source_clear_valid),
        .source_clear_line(source_clear_line),
        .target_clear_valid(target_clear_valid),
        .target_clear_is_remap(target_clear_is_remap),
        .target_clear_is_token(target_clear_is_token),
        .target_clear_is_global(target_clear_is_global),
        .target_clear_line(target_clear_line),
        .target_clear_token(target_clear_token),
        .source_events_ready(source_events_ready),
        .target_events_ready(target_events_ready),
        .overflow_sticky(overflow_sticky),
        .source_queued_count(source_queued_count),
        .target_queued_count(target_queued_count)
    );

    assign dmp_issue_allow = target_gate_allow;
    assign dmp_issue_block = dmp_seed_valid && !dmp_issue_allow;

endmodule
