`timescale 1ns/1ps

// COPPER TLB/coherence authority filter.
//
// This small synthesizable block is the RTL-facing counterpart of the bounded
// TLB/coherence contract checker. It does not decode a proprietary Arm
// hierarchy. It closes DMP issue over the authority-changing events that a
// production AArch64-style SoC must feed into COPPER: source-line revocation,
// target remap, token/global TLBI, queued invalidation drain, permission
// downgrade, and overflow fallback. The hold is conflict-scoped: unrelated
// source/target events need not stop an otherwise authorized candidate.

module copper_tlb_coherence_authority_filter #(
    parameter int SRC_LINE_W = 12,
    parameter int TGT_LINE_W = 16,
    parameter int TOKEN_W = 8,
    parameter int SOURCE_Q_DEPTH = 4,
    parameter int TARGET_Q_DEPTH = 4,
    parameter int COUNT_W = 3
) (
    input  logic clk,
    input  logic rst_n,

    input  logic candidate_valid,
    input  logic [SRC_LINE_W-1:0] candidate_src_line,
    input  logic [TGT_LINE_W-1:0] candidate_tgt_line,
    input  logic [TOKEN_W-1:0] candidate_token,
    input  logic source_proof_valid,
    input  logic target_witness_valid,
    input  logic target_exact_match,
    input  logic target_permission_ok,

    input  logic source_revoke_valid,
    input  logic [SRC_LINE_W-1:0] source_revoke_line,

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

    output logic dmp_allow,
    output logic dmp_block,
    output logic conflict_hold,
    output logic block_no_source_proof,
    output logic block_no_target_witness,
    output logic block_permission,
    output logic block_revocation,
    output logic block_overflow,

    output logic source_clear_valid,
    output logic [SRC_LINE_W-1:0] source_clear_line,
    output logic target_clear_valid,
    output logic target_clear_is_remap,
    output logic target_clear_is_token,
    output logic target_clear_is_global,
    output logic [TGT_LINE_W-1:0] target_clear_line,
    output logic [TOKEN_W-1:0] target_clear_token,
    output logic source_events_ready,
    output logic target_events_ready,
    output logic overflow_sticky,
    output logic [COUNT_W-1:0] source_queued_count,
    output logic [COUNT_W-1:0] target_queued_count
);

    localparam int SOURCE_PTR_W = (SOURCE_Q_DEPTH <= 2) ? 1 : $clog2(SOURCE_Q_DEPTH);
    localparam int TARGET_PTR_W = (TARGET_Q_DEPTH <= 2) ? 1 : $clog2(TARGET_Q_DEPTH);

    localparam logic [1:0] TARGET_REMAP = 2'd0;
    localparam logic [1:0] TARGET_TOKEN = 2'd1;
    localparam logic [1:0] TARGET_GLOBAL = 2'd2;

    logic [SRC_LINE_W-1:0] source_queue [SOURCE_Q_DEPTH];
    logic [SOURCE_PTR_W-1:0] source_head;
    logic [SOURCE_PTR_W-1:0] source_tail;
    logic [COUNT_W-1:0] source_count;
    logic [SOURCE_PTR_W-1:0] source_head_next;
    logic [SOURCE_PTR_W-1:0] source_tail_next;
    logic [COUNT_W-1:0] source_count_next;
    logic source_dequeue;
    logic source_enqueue;
    logic source_ready_after_drain;

    logic [1:0] target_kind_queue [TARGET_Q_DEPTH];
    logic [TGT_LINE_W-1:0] target_line_queue [TARGET_Q_DEPTH];
    logic [TOKEN_W-1:0] target_token_queue [TARGET_Q_DEPTH];
    logic [TARGET_PTR_W-1:0] target_head;
    logic [TARGET_PTR_W-1:0] target_tail;
    logic [COUNT_W-1:0] target_count;
    logic [TARGET_PTR_W-1:0] target_head_next;
    logic [TARGET_PTR_W-1:0] target_tail_next;
    logic [COUNT_W-1:0] target_count_next;
    logic target_dequeue;
    logic target_enqueue;
    logic target_ready_after_drain;
    logic [1:0] target_in_kind;
    logic [TGT_LINE_W-1:0] target_in_line;
    logic [TOKEN_W-1:0] target_in_token;
    logic target_in_valid;

    logic incoming_source_conflict;
    logic queued_source_conflict;
    logic incoming_target_conflict;
    logic queued_target_conflict;
    logic incoming_permission_conflict;
    logic target_authorized;

    function automatic logic [SOURCE_PTR_W-1:0] bump_source(
        input logic [SOURCE_PTR_W-1:0] ptr
    );
        if (ptr == SOURCE_PTR_W'(SOURCE_Q_DEPTH - 1)) begin
            bump_source = '0;
        end else begin
            bump_source = ptr + {{(SOURCE_PTR_W-1){1'b0}}, 1'b1};
        end
    endfunction

    function automatic logic [TARGET_PTR_W-1:0] bump_target(
        input logic [TARGET_PTR_W-1:0] ptr
    );
        if (ptr == TARGET_PTR_W'(TARGET_Q_DEPTH - 1)) begin
            bump_target = '0;
        end else begin
            bump_target = ptr + {{(TARGET_PTR_W-1){1'b0}}, 1'b1};
        end
    endfunction

    function automatic logic target_conflicts(
        input logic [1:0] kind,
        input logic [TGT_LINE_W-1:0] line,
        input logic [TOKEN_W-1:0] token
    );
        unique case (kind)
            TARGET_REMAP: target_conflicts =
                (line == candidate_tgt_line) && (token == candidate_token);
            TARGET_TOKEN: target_conflicts = token == candidate_token;
            TARGET_GLOBAL: target_conflicts = 1'b1;
            default: target_conflicts = 1'b0;
        endcase
    endfunction

    assign source_dequeue = source_drain_enable && (source_count != '0);
    assign target_dequeue = target_drain_enable && (target_count != '0);

    assign source_ready_after_drain =
        (source_count < COUNT_W'(SOURCE_Q_DEPTH)) || source_dequeue;
    assign target_ready_after_drain =
        (target_count < COUNT_W'(TARGET_Q_DEPTH)) || target_dequeue;

    assign source_events_ready = source_ready_after_drain;
    assign target_events_ready = target_ready_after_drain;
    assign source_enqueue = source_revoke_valid && source_ready_after_drain;

    always_comb begin
        target_in_valid = 1'b0;
        target_in_kind = TARGET_REMAP;
        target_in_line = target_remap_line;
        target_in_token = target_remap_token;

        if (tlbi_all_valid) begin
            target_in_valid = 1'b1;
            target_in_kind = TARGET_GLOBAL;
            target_in_line = '0;
            target_in_token = '0;
        end else if (tlbi_token_valid) begin
            target_in_valid = 1'b1;
            target_in_kind = TARGET_TOKEN;
            target_in_line = '0;
            target_in_token = tlbi_token;
        end else if (target_remap_valid) begin
            target_in_valid = 1'b1;
            target_in_kind = TARGET_REMAP;
            target_in_line = target_remap_line;
            target_in_token = target_remap_token;
        end
    end

    assign target_enqueue = target_in_valid && target_ready_after_drain;

    always_comb begin
        queued_source_conflict = 1'b0;
        for (int i = 0; i < SOURCE_Q_DEPTH; i++) begin
            if (i < source_count && source_queue[(source_head + SOURCE_PTR_W'(i)) % SOURCE_Q_DEPTH] == candidate_src_line) begin
                queued_source_conflict = 1'b1;
            end
        end

        queued_target_conflict = 1'b0;
        for (int i = 0; i < TARGET_Q_DEPTH; i++) begin
            if (i < target_count
                && target_conflicts(
                    target_kind_queue[(target_head + TARGET_PTR_W'(i)) % TARGET_Q_DEPTH],
                    target_line_queue[(target_head + TARGET_PTR_W'(i)) % TARGET_Q_DEPTH],
                    target_token_queue[(target_head + TARGET_PTR_W'(i)) % TARGET_Q_DEPTH])) begin
                queued_target_conflict = 1'b1;
            end
        end
    end

    assign incoming_source_conflict =
        source_revoke_valid && (source_revoke_line == candidate_src_line);

    assign incoming_target_conflict =
        (target_remap_valid
            && target_remap_line == candidate_tgt_line
            && target_remap_token == candidate_token)
        || (tlbi_token_valid && tlbi_token == candidate_token)
        || tlbi_all_valid;

    assign incoming_permission_conflict =
        permission_downgrade_valid
        && permission_line == candidate_tgt_line
        && permission_token == candidate_token;

    assign target_authorized = target_witness_valid && target_exact_match;

    assign block_no_source_proof = candidate_valid && !source_proof_valid;
    assign block_no_target_witness = candidate_valid && !target_authorized;
    assign block_permission =
        candidate_valid && (!target_permission_ok || incoming_permission_conflict);
    assign block_overflow = candidate_valid && overflow_sticky;
    assign block_revocation =
        candidate_valid
        && (incoming_source_conflict
            || queued_source_conflict
            || incoming_target_conflict
            || queued_target_conflict);

    assign conflict_hold =
        overflow_sticky
        || incoming_source_conflict
        || queued_source_conflict
        || incoming_target_conflict
        || queued_target_conflict
        || incoming_permission_conflict;

    assign dmp_allow =
        candidate_valid
        && source_proof_valid
        && target_authorized
        && target_permission_ok
        && !conflict_hold;

    assign dmp_block = candidate_valid && !dmp_allow;

    assign source_clear_valid = source_dequeue;
    assign source_clear_line = source_dequeue ? source_queue[source_head] : '0;
    assign target_clear_valid = target_dequeue;
    assign target_clear_is_remap =
        target_dequeue && target_kind_queue[target_head] == TARGET_REMAP;
    assign target_clear_is_token =
        target_dequeue && target_kind_queue[target_head] == TARGET_TOKEN;
    assign target_clear_is_global =
        target_dequeue && target_kind_queue[target_head] == TARGET_GLOBAL;
    assign target_clear_line = target_dequeue ? target_line_queue[target_head] : '0;
    assign target_clear_token = target_dequeue ? target_token_queue[target_head] : '0;
    assign source_queued_count = source_count;
    assign target_queued_count = target_count;

    always_comb begin
        source_head_next = source_head;
        source_tail_next = source_tail;
        source_count_next = source_count;

        if (source_dequeue) begin
            source_head_next = bump_source(source_head);
            source_count_next = source_count_next - COUNT_W'(1);
        end
        if (source_enqueue) begin
            source_tail_next = bump_source(source_tail);
            source_count_next = source_count_next + COUNT_W'(1);
        end
    end

    always_comb begin
        target_head_next = target_head;
        target_tail_next = target_tail;
        target_count_next = target_count;

        if (target_dequeue) begin
            target_head_next = bump_target(target_head);
            target_count_next = target_count_next - COUNT_W'(1);
        end
        if (target_enqueue) begin
            target_tail_next = bump_target(target_tail);
            target_count_next = target_count_next + COUNT_W'(1);
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            source_head <= '0;
            source_tail <= '0;
            source_count <= '0;
            target_head <= '0;
            target_tail <= '0;
            target_count <= '0;
            overflow_sticky <= 1'b0;
            for (int i = 0; i < SOURCE_Q_DEPTH; i++) begin
                source_queue[i] <= '0;
            end
            for (int i = 0; i < TARGET_Q_DEPTH; i++) begin
                target_kind_queue[i] <= TARGET_REMAP;
                target_line_queue[i] <= '0;
                target_token_queue[i] <= '0;
            end
        end else begin
            source_head <= source_head_next;
            source_tail <= source_tail_next;
            source_count <= source_count_next;
            target_head <= target_head_next;
            target_tail <= target_tail_next;
            target_count <= target_count_next;

            if (source_revoke_valid && !source_ready_after_drain) begin
                overflow_sticky <= 1'b1;
            end
            if (target_in_valid && !target_ready_after_drain) begin
                overflow_sticky <= 1'b1;
            end

            if (source_enqueue) begin
                source_queue[source_tail] <= source_revoke_line;
            end
            if (target_enqueue) begin
                target_kind_queue[target_tail] <= target_in_kind;
                target_line_queue[target_tail] <= target_in_line;
                target_token_queue[target_tail] <= target_in_token;
            end
        end
    end

endmodule
