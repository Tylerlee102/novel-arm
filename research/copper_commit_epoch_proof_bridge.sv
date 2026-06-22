`timescale 1ns/1ps

// CEPF: Commit-Epoch Provenance Filter for COPPER.
//
// This bridge models the backend-to-cache proof path. The backend may carry a
// source-line/source-word tag from a loaded pointer into a dependent memory
// operation. COPPER must not turn that tag into cache proof until the dependent
// operation commits, translation and permission checks have succeeded, and the
// source word is still in the same clean epoch captured when the tag was made.
//
// The epoch check closes a subtle stale-tag race:
//   load source pointer -> dependent load waits -> store overwrites source word
//   -> dependent load commits using old value
// Without CEPF, the old tag could recreate proof for the overwritten word.

module copper_commit_epoch_proof_bridge #(
    parameter int LINE_IDX_W = 6,
    parameter int WORD_OFF_W = 3,
    parameter int DOMAIN_W = 8,
    parameter int EPOCH_W = 4
) (
    input  logic commit_valid,
    input  logic commit_is_memory,
    input  logic commit_addr_dep_valid,
    input  logic commit_exception,
    input  logic commit_squashed,
    input  logic commit_translation_ok,
    input  logic commit_permission_ok,

    input  logic [LINE_IDX_W-1:0] commit_src_line_idx,
    input  logic [WORD_OFF_W-1:0] commit_src_word,
    input  logic [DOMAIN_W-1:0] commit_src_domain,
    input  logic [EPOCH_W-1:0] commit_src_epoch,
    input  logic [EPOCH_W-1:0] source_current_epoch,

    output logic proof_valid,
    output logic [LINE_IDX_W-1:0] proof_line_idx,
    output logic [WORD_OFF_W-1:0] proof_word,
    output logic [DOMAIN_W-1:0] proof_domain,

    output logic blocked_not_commit,
    output logic blocked_no_source,
    output logic blocked_fault_or_perm,
    output logic blocked_epoch_mismatch
);

    logic base_commit_ok;
    logic source_ok;
    logic fault_perm_ok;
    logic epoch_ok;

    always_comb begin
        base_commit_ok =
            commit_valid
            && commit_is_memory
            && !commit_squashed;

        source_ok = commit_addr_dep_valid;

        fault_perm_ok =
            !commit_exception
            && commit_translation_ok
            && commit_permission_ok;

        epoch_ok = commit_src_epoch == source_current_epoch;

        proof_valid =
            base_commit_ok
            && source_ok
            && fault_perm_ok
            && epoch_ok;

        proof_line_idx = commit_src_line_idx;
        proof_word = commit_src_word;
        proof_domain = commit_src_domain;

        blocked_not_commit =
            commit_valid
            && (!commit_is_memory || commit_squashed);

        blocked_no_source =
            base_commit_ok
            && !source_ok;

        blocked_fault_or_perm =
            base_commit_ok
            && source_ok
            && !fault_perm_ok;

        blocked_epoch_mismatch =
            base_commit_ok
            && source_ok
            && fault_perm_ok
            && !epoch_ok;
    end

endmodule
