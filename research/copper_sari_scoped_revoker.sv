`timescale 1ns/1ps

// COPPER CS-SARI: Conflict-Scoped SoC Authority Revocation Interface.
//
// CS-SARI keeps SARI's revocation queue and CTLW forwarding contract, but
// replaces a global DMP hold with a candidate-specific conflict hold. A raw DMP
// candidate is held only when its source line, target line, or token conflicts
// with an incoming or queued authority-changing event. Overflow remains a
// global hold because the local revocation set is no longer precisely known.

module copper_sari_scoped_revoker #(
    parameter int SRC_LINE_W = 12,
    parameter int TGT_LINE_W = 16,
    parameter int TOKEN_W = 8,
    parameter int DEPTH = 8,
    parameter int COUNT_W = 4
) (
    input  logic clk,
    input  logic rst_n,

    input  logic dma_write_valid,
    input  logic [SRC_LINE_W-1:0] dma_line_tag,

    input  logic chi_snoop_valid,
    input  logic chi_snoop_write,
    input  logic chi_snoop_invalidate,
    input  logic [SRC_LINE_W-1:0] chi_line_tag,

    input  logic io_write_valid,
    input  logic [SRC_LINE_W-1:0] io_line_tag,

    input  logic target_remap_valid,
    input  logic [TGT_LINE_W-1:0] target_remap_vline,
    input  logic [TOKEN_W-1:0] target_remap_token,

    input  logic tlbi_token_valid,
    input  logic [TOKEN_W-1:0] tlbi_token,
    input  logic tlbi_all_valid,

    input  logic raw_dmp_seed_valid,
    input  logic [SRC_LINE_W-1:0] dmp_source_line_tag,
    input  logic [TGT_LINE_W-1:0] dmp_target_vline,
    input  logic [TOKEN_W-1:0] dmp_token,

    output logic source_clear_valid,
    output logic [SRC_LINE_W-1:0] source_clear_line_tag,
    output logic source_events_ready,

    output logic ctlw_remap_valid,
    output logic [TGT_LINE_W-1:0] ctlw_remap_vline,
    output logic [TOKEN_W-1:0] ctlw_remap_token,
    output logic ctlw_tlbi_token_valid,
    output logic [TOKEN_W-1:0] ctlw_tlbi_token,
    output logic ctlw_tlbi_all_valid,

    output logic dmp_conflict_hold,
    output logic dmp_global_hold,
    output logic overflow_sticky,
    output logic [COUNT_W-1:0] queued_count
);

    logic [SRC_LINE_W-1:0] queue [DEPTH];
    logic [SRC_LINE_W-1:0] next_queue [DEPTH];
    logic [COUNT_W-1:0] count;
    logic [COUNT_W-1:0] next_count;
    logic source_event_dma;
    logic source_event_chi;
    logic source_event_io;
    logic incoming_source_event;
    logic incoming_target_event;
    logic incoming_source_conflict;
    logic queued_source_conflict;
    logic target_remap_conflict;
    logic tlbi_token_conflict;
    logic tlbi_all_conflict;
    logic incoming_target_conflict;
    logic next_overflow;
    int temp_count;
    int space_after_dequeue;

    assign source_event_dma = dma_write_valid;
    assign source_event_chi = chi_snoop_valid && (chi_snoop_write || chi_snoop_invalidate);
    assign source_event_io = io_write_valid;
    assign incoming_source_event = source_event_dma || source_event_chi || source_event_io;
    assign incoming_target_event = target_remap_valid || tlbi_token_valid || tlbi_all_valid;

    assign source_clear_valid = count != '0;
    assign source_clear_line_tag = source_clear_valid ? queue[0] : '0;
    assign queued_count = count;

    assign space_after_dequeue = DEPTH - int'(count) + ((count != '0) ? 1 : 0);
    assign source_events_ready = space_after_dequeue >= 3;

    assign ctlw_remap_valid = target_remap_valid;
    assign ctlw_remap_vline = target_remap_vline;
    assign ctlw_remap_token = target_remap_token;
    assign ctlw_tlbi_token_valid = tlbi_token_valid;
    assign ctlw_tlbi_token = tlbi_token;
    assign ctlw_tlbi_all_valid = tlbi_all_valid;

    always_comb begin
        queued_source_conflict = 1'b0;
        for (int i = 0; i < DEPTH; i++) begin
            if ((i < int'(count)) && (queue[i] == dmp_source_line_tag)) begin
                queued_source_conflict = 1'b1;
            end
        end
    end

    assign incoming_source_conflict =
        (source_event_dma && (dma_line_tag == dmp_source_line_tag))
        || (source_event_chi && (chi_line_tag == dmp_source_line_tag))
        || (source_event_io && (io_line_tag == dmp_source_line_tag));

    assign target_remap_conflict =
        target_remap_valid
        && (target_remap_token == dmp_token)
        && (target_remap_vline == dmp_target_vline);

    assign tlbi_token_conflict = tlbi_token_valid && (tlbi_token == dmp_token);
    assign tlbi_all_conflict = tlbi_all_valid;
    assign incoming_target_conflict =
        target_remap_conflict || tlbi_token_conflict || tlbi_all_conflict;

    assign dmp_global_hold =
        overflow_sticky
        || (count != '0)
        || incoming_source_event
        || incoming_target_event;

    assign dmp_conflict_hold =
        raw_dmp_seed_valid
        && (
            overflow_sticky
            || incoming_source_conflict
            || queued_source_conflict
            || incoming_target_conflict
        );

    always_comb begin
        for (int i = 0; i < DEPTH; i++) begin
            next_queue[i] = queue[i];
        end
        temp_count = int'(count);
        next_overflow = overflow_sticky;

        if (temp_count > 0) begin
            for (int i = 0; i < DEPTH - 1; i++) begin
                next_queue[i] = queue[i + 1];
            end
            next_queue[DEPTH - 1] = '0;
            temp_count--;
        end

        if (source_event_dma) begin
            if (temp_count < DEPTH) begin
                next_queue[temp_count] = dma_line_tag;
                temp_count++;
            end else begin
                next_overflow = 1'b1;
            end
        end

        if (source_event_chi) begin
            if (temp_count < DEPTH) begin
                next_queue[temp_count] = chi_line_tag;
                temp_count++;
            end else begin
                next_overflow = 1'b1;
            end
        end

        if (source_event_io) begin
            if (temp_count < DEPTH) begin
                next_queue[temp_count] = io_line_tag;
                temp_count++;
            end else begin
                next_overflow = 1'b1;
            end
        end

        next_count = COUNT_W'(temp_count);
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= '0;
            overflow_sticky <= 1'b0;
            for (int i = 0; i < DEPTH; i++) begin
                queue[i] <= '0;
            end
        end else begin
            count <= next_count;
            overflow_sticky <= next_overflow;
            for (int i = 0; i < DEPTH; i++) begin
                queue[i] <= next_queue[i];
            end
        end
    end

endmodule
