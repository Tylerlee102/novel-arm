`timescale 1ns/1ps

// Registered timing wrapper for the COPPER ROPL-LSQ retire guard.
//
// The guard itself is combinational so a backend can place it in the retirement
// proof path. This wrapper gives Vivado a concrete input-register to
// output-register timing boundary for reproducible local cost measurement.

module copper_ropl_lsq_retire_guard_top #(
    parameter int REPLAY_GEN_W = 4,
    parameter int SQUASH_EPOCH_W = 4,
    parameter int ALIAS_GEN_W = 4
) (
    input  logic clk,
    input  logic rst_n,

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

    logic r_src_tag_valid;
    logic r_src_executed;
    logic r_src_retired;
    logic r_src_exception;
    logic r_src_older_than_dep;
    logic r_tag_live;
    logic r_tag_stale;
    logic [REPLAY_GEN_W-1:0] r_tag_replay_gen;
    logic [REPLAY_GEN_W-1:0] r_dep_replay_gen;
    logic [SQUASH_EPOCH_W-1:0] r_tag_squash_epoch;
    logic [SQUASH_EPOCH_W-1:0] r_current_squash_epoch;
    logic [ALIAS_GEN_W-1:0] r_tag_alias_gen;
    logic [ALIAS_GEN_W-1:0] r_current_alias_gen;
    logic r_dep_execute_valid;
    logic r_dep_retire_valid;
    logic r_dep_is_memory;
    logic r_dep_exception;
    logic r_dep_squashed;
    logic r_memory_order_violation;
    logic r_target_translation_ok;
    logic r_target_permission_ok;

    logic w_proof_valid;
    logic w_blocked_execute_stage;
    logic w_blocked_not_retire;
    logic w_blocked_not_memory;
    logic w_blocked_no_live_tag;
    logic w_blocked_source_not_clean;
    logic w_blocked_exception_or_squash;
    logic w_blocked_replay_or_squash_epoch;
    logic w_blocked_alias_or_order;
    logic w_blocked_translation_or_permission;

    copper_ropl_lsq_retire_guard #(
        .REPLAY_GEN_W(REPLAY_GEN_W),
        .SQUASH_EPOCH_W(SQUASH_EPOCH_W),
        .ALIAS_GEN_W(ALIAS_GEN_W)
    ) guard (
        .src_tag_valid(r_src_tag_valid),
        .src_executed(r_src_executed),
        .src_retired(r_src_retired),
        .src_exception(r_src_exception),
        .src_older_than_dep(r_src_older_than_dep),
        .tag_live(r_tag_live),
        .tag_stale(r_tag_stale),
        .tag_replay_gen(r_tag_replay_gen),
        .dep_replay_gen(r_dep_replay_gen),
        .tag_squash_epoch(r_tag_squash_epoch),
        .current_squash_epoch(r_current_squash_epoch),
        .tag_alias_gen(r_tag_alias_gen),
        .current_alias_gen(r_current_alias_gen),
        .dep_execute_valid(r_dep_execute_valid),
        .dep_retire_valid(r_dep_retire_valid),
        .dep_is_memory(r_dep_is_memory),
        .dep_exception(r_dep_exception),
        .dep_squashed(r_dep_squashed),
        .memory_order_violation(r_memory_order_violation),
        .target_translation_ok(r_target_translation_ok),
        .target_permission_ok(r_target_permission_ok),
        .proof_valid(w_proof_valid),
        .blocked_execute_stage(w_blocked_execute_stage),
        .blocked_not_retire(w_blocked_not_retire),
        .blocked_not_memory(w_blocked_not_memory),
        .blocked_no_live_tag(w_blocked_no_live_tag),
        .blocked_source_not_clean(w_blocked_source_not_clean),
        .blocked_exception_or_squash(w_blocked_exception_or_squash),
        .blocked_replay_or_squash_epoch(w_blocked_replay_or_squash_epoch),
        .blocked_alias_or_order(w_blocked_alias_or_order),
        .blocked_translation_or_permission(w_blocked_translation_or_permission)
    );

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r_src_tag_valid <= 1'b0;
            r_src_executed <= 1'b0;
            r_src_retired <= 1'b0;
            r_src_exception <= 1'b0;
            r_src_older_than_dep <= 1'b0;
            r_tag_live <= 1'b0;
            r_tag_stale <= 1'b0;
            r_tag_replay_gen <= '0;
            r_dep_replay_gen <= '0;
            r_tag_squash_epoch <= '0;
            r_current_squash_epoch <= '0;
            r_tag_alias_gen <= '0;
            r_current_alias_gen <= '0;
            r_dep_execute_valid <= 1'b0;
            r_dep_retire_valid <= 1'b0;
            r_dep_is_memory <= 1'b0;
            r_dep_exception <= 1'b0;
            r_dep_squashed <= 1'b0;
            r_memory_order_violation <= 1'b0;
            r_target_translation_ok <= 1'b0;
            r_target_permission_ok <= 1'b0;
            proof_valid <= 1'b0;
            blocked_execute_stage <= 1'b0;
            blocked_not_retire <= 1'b0;
            blocked_not_memory <= 1'b0;
            blocked_no_live_tag <= 1'b0;
            blocked_source_not_clean <= 1'b0;
            blocked_exception_or_squash <= 1'b0;
            blocked_replay_or_squash_epoch <= 1'b0;
            blocked_alias_or_order <= 1'b0;
            blocked_translation_or_permission <= 1'b0;
        end else begin
            r_src_tag_valid <= src_tag_valid;
            r_src_executed <= src_executed;
            r_src_retired <= src_retired;
            r_src_exception <= src_exception;
            r_src_older_than_dep <= src_older_than_dep;
            r_tag_live <= tag_live;
            r_tag_stale <= tag_stale;
            r_tag_replay_gen <= tag_replay_gen;
            r_dep_replay_gen <= dep_replay_gen;
            r_tag_squash_epoch <= tag_squash_epoch;
            r_current_squash_epoch <= current_squash_epoch;
            r_tag_alias_gen <= tag_alias_gen;
            r_current_alias_gen <= current_alias_gen;
            r_dep_execute_valid <= dep_execute_valid;
            r_dep_retire_valid <= dep_retire_valid;
            r_dep_is_memory <= dep_is_memory;
            r_dep_exception <= dep_exception;
            r_dep_squashed <= dep_squashed;
            r_memory_order_violation <= memory_order_violation;
            r_target_translation_ok <= target_translation_ok;
            r_target_permission_ok <= target_permission_ok;
            proof_valid <= w_proof_valid;
            blocked_execute_stage <= w_blocked_execute_stage;
            blocked_not_retire <= w_blocked_not_retire;
            blocked_not_memory <= w_blocked_not_memory;
            blocked_no_live_tag <= w_blocked_no_live_tag;
            blocked_source_not_clean <= w_blocked_source_not_clean;
            blocked_exception_or_squash <= w_blocked_exception_or_squash;
            blocked_replay_or_squash_epoch <= w_blocked_replay_or_squash_epoch;
            blocked_alias_or_order <= w_blocked_alias_or_order;
            blocked_translation_or_permission <= w_blocked_translation_or_permission;
        end
    end

endmodule
