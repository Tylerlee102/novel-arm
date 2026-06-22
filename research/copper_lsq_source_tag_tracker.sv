`timescale 1ns/1ps

// COPPER LSQ-style source-tag tracker.
//
// This block models the backend side of COPPER proof creation one step before
// the existing CEPF bridge. A source load that may feed a later memory address
// captures a compact tag carrying source line/word/domain, source epoch, and a
// value fingerprint. A dependent memory operation can create COPPER proof only
// when it commits cleanly with a live tag whose source epoch/value still match
// the current source word and no same-cycle destructive event kills that tag.
//
// This is not a full production LSQ. It is a research RTL contract for the
// proof interface a production LSQ would have to implement.

module copper_lsq_source_tag_tracker #(
    parameter int TAG_ENTRIES = 8,
    parameter int TAG_W = 3,
    parameter int LINE_IDX_W = 6,
    parameter int WORD_OFF_W = 3,
    parameter int DOMAIN_W = 8,
    parameter int EPOCH_W = 4,
    parameter int VALUE_W = 16
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

    output logic proof_valid,
    output logic [LINE_IDX_W-1:0] proof_line_idx,
    output logic [WORD_OFF_W-1:0] proof_word,
    output logic [DOMAIN_W-1:0] proof_domain,
    output logic [EPOCH_W-1:0] proof_epoch,
    output logic [VALUE_W-1:0] proof_value_hash,

    output logic blocked_not_commit,
    output logic blocked_no_tag,
    output logic blocked_fault_or_perm,
    output logic blocked_tag_stale,
    output logic blocked_epoch_value_mismatch
);

    logic tag_valid [TAG_ENTRIES];
    logic tag_stale [TAG_ENTRIES];
    logic [LINE_IDX_W-1:0] tag_line_idx [TAG_ENTRIES];
    logic [WORD_OFF_W-1:0] tag_word [TAG_ENTRIES];
    logic [DOMAIN_W-1:0] tag_domain [TAG_ENTRIES];
    logic [EPOCH_W-1:0] tag_epoch [TAG_ENTRIES];
    logic [VALUE_W-1:0] tag_value_hash [TAG_ENTRIES];

    logic commit_tag_live;
    logic commit_base_ok;
    logic commit_fault_perm_ok;
    logic commit_epoch_value_ok;
    logic commit_same_cycle_kill;
    logic commit_tag_current;

    always_comb begin
        commit_tag_live =
            commit_dep_tag_valid
            && tag_valid[commit_dep_tag];

        commit_base_ok =
            commit_valid
            && commit_is_memory
            && !commit_squashed;

        commit_fault_perm_ok =
            !commit_exception
            && commit_translation_ok
            && commit_permission_ok;

        commit_epoch_value_ok =
            commit_tag_live
            && (tag_epoch[commit_dep_tag] == commit_src_current_epoch)
            && (tag_value_hash[commit_dep_tag] == commit_src_current_value_hash);

        commit_same_cycle_kill =
            flush_valid
            || (
                commit_tag_live
                && source_write_valid
                && (source_write_line_idx == tag_line_idx[commit_dep_tag])
                && (source_write_word == tag_word[commit_dep_tag])
            )
            || (
                commit_tag_live
                && line_fill_valid
                && (line_fill_idx == tag_line_idx[commit_dep_tag])
            )
            || (
                commit_tag_live
                && invalidate_valid
                && (invalidate_line_idx == tag_line_idx[commit_dep_tag])
            );

        commit_tag_current =
            commit_tag_live
            && !tag_stale[commit_dep_tag]
            && !commit_same_cycle_kill
            && commit_epoch_value_ok;

        proof_valid =
            commit_base_ok
            && commit_tag_live
            && commit_fault_perm_ok
            && commit_tag_current;

        proof_line_idx = tag_line_idx[commit_dep_tag];
        proof_word = tag_word[commit_dep_tag];
        proof_domain = tag_domain[commit_dep_tag];
        proof_epoch = tag_epoch[commit_dep_tag];
        proof_value_hash = tag_value_hash[commit_dep_tag];

        blocked_not_commit =
            commit_valid
            && (!commit_is_memory || commit_squashed);

        blocked_no_tag =
            commit_base_ok
            && !commit_tag_live;

        blocked_fault_or_perm =
            commit_base_ok
            && commit_tag_live
            && !commit_fault_perm_ok;

        blocked_tag_stale =
            commit_base_ok
            && commit_tag_live
            && commit_fault_perm_ok
            && (tag_stale[commit_dep_tag] || commit_same_cycle_kill);

        blocked_epoch_value_mismatch =
            commit_base_ok
            && commit_tag_live
            && commit_fault_perm_ok
            && !tag_stale[commit_dep_tag]
            && !commit_same_cycle_kill
            && !commit_epoch_value_ok;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < TAG_ENTRIES; i++) begin
                tag_valid[i] <= 1'b0;
                tag_stale[i] <= 1'b0;
                tag_line_idx[i] <= '0;
                tag_word[i] <= '0;
                tag_domain[i] <= '0;
                tag_epoch[i] <= '0;
                tag_value_hash[i] <= '0;
            end
        end else begin
            if (flush_valid) begin
                for (int i = 0; i < TAG_ENTRIES; i++) begin
                    tag_valid[i] <= 1'b0;
                    tag_stale[i] <= 1'b1;
                end
            end

            for (int i = 0; i < TAG_ENTRIES; i++) begin
                if (tag_valid[i]) begin
                    if (
                        source_write_valid
                        && (source_write_line_idx == tag_line_idx[i])
                        && (source_write_word == tag_word[i])
                    ) begin
                        tag_stale[i] <= 1'b1;
                    end
                    if (
                        line_fill_valid
                        && (line_fill_idx == tag_line_idx[i])
                    ) begin
                        tag_stale[i] <= 1'b1;
                    end
                    if (
                        invalidate_valid
                        && (invalidate_line_idx == tag_line_idx[i])
                    ) begin
                        tag_stale[i] <= 1'b1;
                    end
                end
            end

            if (capture_valid) begin
                tag_valid[capture_tag] <= 1'b1;
                tag_stale[capture_tag] <= 1'b0;
                tag_line_idx[capture_tag] <= capture_src_line_idx;
                tag_word[capture_tag] <= capture_src_word;
                tag_domain[capture_tag] <= capture_src_domain;
                tag_epoch[capture_tag] <= capture_src_epoch;
                tag_value_hash[capture_tag] <= capture_src_value_hash;
            end

            if (clear_tag_valid) begin
                tag_valid[clear_tag] <= 1'b0;
                tag_stale[clear_tag] <= 1'b0;
            end
        end
    end

endmodule
