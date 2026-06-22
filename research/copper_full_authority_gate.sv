`timescale 1ns/1ps

// COPPER full authority gate.
//
// This block is intentionally narrow: it does not implement a DMP predictor,
// proof table, MMU, or cache. It is the hardware-shaped allow/block predicate
// for a data-memory-dependent prefetch candidate after those structures have
// supplied their metadata.
//
// Invariant:
//   A DMP candidate may issue only if its source word is clean, backed by a
//   sound committed source proof for the current value/epoch and address-space
//   token, is not a CTLW-terminal source, and the target is either same-page
//   translated or backed by an exact committed target-line witness.

module copper_full_authority_gate #(
    parameter int VALUE_W = 16,
    parameter int EPOCH_W = 4,
    parameter int TOKEN_W = 8,
    parameter int LINE_W = 16
) (
    input  logic dmp_seed_valid,

    input  logic source_valid,
    input  logic source_clean,
    input  logic [VALUE_W-1:0] source_value,
    input  logic [EPOCH_W-1:0] source_epoch,
    input  logic [TOKEN_W-1:0] current_token,

    input  logic proof_valid,
    input  logic proof_sound,
    input  logic [VALUE_W-1:0] proof_value,
    input  logic [EPOCH_W-1:0] proof_epoch,
    input  logic [TOKEN_W-1:0] proof_token,

    input  logic target_same_page,
    input  logic same_page_translation_ok,
    input  logic target_permission_ok,
    input  logic terminal_source,

    input  logic [LINE_W-1:0] candidate_target_line,
    input  logic witness_valid,
    input  logic [LINE_W-1:0] witness_target_line,
    input  logic [TOKEN_W-1:0] witness_token,

    output logic source_authorized,
    output logic target_authorized,
    output logic dmp_seed_allow,
    output logic dmp_seed_block,

    output logic block_no_source_proof,
    output logic block_stale_source,
    output logic block_token_mismatch,
    output logic block_terminal_source,
    output logic block_no_target_authority,
    output logic block_fault_or_perm
);

    logic proof_exact;
    logic token_match;
    logic witness_exact;

    always_comb begin
        proof_exact =
            proof_valid
            && proof_sound
            && (proof_value == source_value)
            && (proof_epoch == source_epoch);

        token_match = proof_valid && (proof_token == current_token);

        witness_exact =
            witness_valid
            && (witness_target_line == candidate_target_line)
            && (witness_token == current_token);

        source_authorized =
            source_valid
            && source_clean
            && proof_exact
            && token_match;

        target_authorized = target_same_page
            ? same_page_translation_ok
            : witness_exact;

        dmp_seed_allow =
            dmp_seed_valid
            && source_authorized
            && !terminal_source
            && target_authorized
            && target_permission_ok;

        dmp_seed_block = dmp_seed_valid && !dmp_seed_allow;

        block_no_source_proof =
            dmp_seed_valid
            && !(source_valid && source_clean && proof_valid && proof_sound);

        block_stale_source =
            dmp_seed_valid
            && source_valid
            && source_clean
            && proof_valid
            && proof_sound
            && ((proof_value != source_value) || (proof_epoch != source_epoch));

        block_token_mismatch =
            dmp_seed_valid
            && source_valid
            && source_clean
            && proof_valid
            && proof_sound
            && (proof_value == source_value)
            && (proof_epoch == source_epoch)
            && (proof_token != current_token);

        block_terminal_source =
            dmp_seed_valid
            && source_authorized
            && terminal_source;

        block_no_target_authority =
            dmp_seed_valid
            && source_authorized
            && !terminal_source
            && !target_authorized;

        block_fault_or_perm =
            dmp_seed_valid
            && source_authorized
            && !terminal_source
            && target_authorized
            && !target_permission_ok;
    end

endmodule
