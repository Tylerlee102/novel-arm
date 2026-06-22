`timescale 1ns/1ps

// ROCCA: Retirement-Ordered Clear-wins CLPD Adapter.
//
// This adapter is the narrow boundary between a retirement-only backend proof
// guard and the retained COPPER CLPD source-proof directory. The key invariant
// is clear-wins: a same-cycle source-line write, line fill, invalidation, or
// global proof clear suppresses the CLPD proof write even if the backend retire
// guard says the dependent memory operation may create proof.
//
// This is not a production LSQ or a proprietary ARM backend. It is a public
// executable contract for the final proof-write boundary reviewers often worry
// about: no stale same-cycle destructive event may be overwritten by a new
// retained CLPD proof.

module copper_rocca_clpd_commit_adapter #(
    parameter int LINE_TAG_W = 12,
    parameter int WORD_OFF_W = 4,
    parameter int TOKEN_W = 8,
    parameter int EPOCH_W = 4
) (
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

    output logic clpd_commit_ptr_valid,
    output logic [LINE_TAG_W-1:0] clpd_commit_line_tag,
    output logic [WORD_OFF_W-1:0] clpd_commit_word,
    output logic [TOKEN_W-1:0] clpd_commit_token,
    output logic [EPOCH_W-1:0] clpd_commit_line_epoch,

    output logic same_cycle_clear_hit,
    output logic blocked_no_retire_proof,
    output logic blocked_source_not_clean,
    output logic blocked_epoch_mismatch,
    output logic blocked_fault_or_perm,
    output logic blocked_clear_wins
);

    logic write_hit;
    logic fill_hit;
    logic invalidate_hit;
    logic fault_perm_ok;

    always_comb begin
        write_hit =
            source_write_valid
            && (source_write_line_tag == ropl_line_tag);

        fill_hit =
            line_fill_valid
            && (line_fill_tag == ropl_line_tag);

        invalidate_hit =
            invalidate_valid
            && (invalidate_line_tag == ropl_line_tag);

        same_cycle_clear_hit =
            global_clear_valid
            || write_hit
            || fill_hit
            || invalidate_hit;

        fault_perm_ok = commit_translation_ok && commit_permission_ok;

        clpd_commit_ptr_valid =
            ropl_proof_valid
            && source_clean
            && source_epoch_match
            && fault_perm_ok
            && !same_cycle_clear_hit;

        clpd_commit_line_tag = ropl_line_tag;
        clpd_commit_word = ropl_word;
        clpd_commit_token = ropl_token;
        clpd_commit_line_epoch = ropl_epoch;

        blocked_no_retire_proof = !ropl_proof_valid;

        blocked_source_not_clean =
            ropl_proof_valid
            && !source_clean;

        blocked_epoch_mismatch =
            ropl_proof_valid
            && source_clean
            && !source_epoch_match;

        blocked_fault_or_perm =
            ropl_proof_valid
            && source_clean
            && source_epoch_match
            && !fault_perm_ok;

        blocked_clear_wins =
            ropl_proof_valid
            && source_clean
            && source_epoch_match
            && fault_perm_ok
            && same_cycle_clear_hit;
    end

endmodule
