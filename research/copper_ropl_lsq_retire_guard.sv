`timescale 1ns/1ps

// COPPER ROPL-LSQ retire guard.
//
// ROPL means Retirement-Only Provenance Latching. This guard is the small
// backend interface that sits between an LSQ/dependency tracker and the COPPER
// authority table. It deliberately creates proof_valid only at dependent-memory
// retirement, and only if the carried source tag survived source retirement,
// replay, squash, exception, same-line alias, memory-order, translation, and
// permission hazards.
//
// This is not a production ARM LSQ. It is a synthesizable public contract for
// the signals a production backend would have to provide.

module copper_ropl_lsq_retire_guard #(
    parameter int REPLAY_GEN_W = 4,
    parameter int SQUASH_EPOCH_W = 4,
    parameter int ALIAS_GEN_W = 4
) (
    input  logic src_tag_valid,
    input  logic src_executed,
    input  logic src_retired,
    input  logic src_exception,
    input  logic src_older_than_dep,
    input  logic tag_live,
    input  logic tag_stale,
    input  logic [REPLAY_GEN_W-1:0] tag_replay_gen,
    input  logic [REPLAY_GEN_W-1:0] dep_replay_gen,
    input  logic [SQUASH_EPOCH_W-1:0] tag_squash_epoch,
    input  logic [SQUASH_EPOCH_W-1:0] current_squash_epoch,
    input  logic [ALIAS_GEN_W-1:0] tag_alias_gen,
    input  logic [ALIAS_GEN_W-1:0] current_alias_gen,

    input  logic dep_execute_valid,
    input  logic dep_retire_valid,
    input  logic dep_is_memory,
    input  logic dep_exception,
    input  logic dep_squashed,
    input  logic memory_order_violation,
    input  logic target_translation_ok,
    input  logic target_permission_ok,

    output logic proof_valid,
    output logic blocked_execute_stage,
    output logic blocked_not_retire,
    output logic blocked_not_memory,
    output logic blocked_no_live_tag,
    output logic blocked_source_not_clean,
    output logic blocked_exception_or_squash,
    output logic blocked_replay_or_squash_epoch,
    output logic blocked_alias_or_order,
    output logic blocked_translation_or_permission
);

    logic retire_memory_attempt;
    logic tag_ok;
    logic source_ok;
    logic exception_ok;
    logic replay_ok;
    logic squash_epoch_ok;
    logic alias_ok;
    logic order_ok;
    logic target_ok;
    logic gen_ok;
    logic backend_hazard_ok;

    always_comb begin
        retire_memory_attempt = dep_retire_valid && dep_is_memory;

        tag_ok =
            src_tag_valid
            && tag_live
            && !tag_stale;

        source_ok =
            src_executed
            && src_retired
            && !src_exception
            && src_older_than_dep;

        exception_ok =
            !dep_exception
            && !dep_squashed;

        replay_ok = tag_replay_gen == dep_replay_gen;
        squash_epoch_ok = tag_squash_epoch == current_squash_epoch;
        alias_ok = tag_alias_gen == current_alias_gen;
        order_ok = !memory_order_violation;
        target_ok = target_translation_ok && target_permission_ok;
        gen_ok = replay_ok && squash_epoch_ok;
        backend_hazard_ok = alias_ok && order_ok;

        proof_valid =
            retire_memory_attempt
            && tag_ok
            && source_ok
            && exception_ok
            && gen_ok
            && backend_hazard_ok
            && target_ok;

        blocked_execute_stage =
            dep_execute_valid
            && !dep_retire_valid
            && src_tag_valid;

        blocked_not_retire =
            src_tag_valid
            && dep_is_memory
            && !dep_retire_valid;

        blocked_not_memory =
            src_tag_valid
            && dep_retire_valid
            && !dep_is_memory;

        blocked_no_live_tag =
            retire_memory_attempt
            && !tag_ok;

        blocked_source_not_clean =
            retire_memory_attempt
            && tag_ok
            && !source_ok;

        blocked_exception_or_squash =
            retire_memory_attempt
            && tag_ok
            && source_ok
            && !exception_ok;

        blocked_replay_or_squash_epoch =
            retire_memory_attempt
            && tag_ok
            && source_ok
            && exception_ok
            && !gen_ok;

        blocked_alias_or_order =
            retire_memory_attempt
            && tag_ok
            && source_ok
            && exception_ok
            && gen_ok
            && !backend_hazard_ok;

        blocked_translation_or_permission =
            retire_memory_attempt
            && tag_ok
            && source_ok
            && exception_ok
            && gen_ok
            && backend_hazard_ok
            && !target_ok;
    end

endmodule
