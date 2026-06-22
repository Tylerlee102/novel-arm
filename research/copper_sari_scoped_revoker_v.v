`timescale 1ns/1ps

// Synthesis-only Verilog-2001 form of copper_sari_scoped_revoker.sv.
// The logic is intentionally kept isomorphic to the SystemVerilog RTL so
// Vivado batch synthesis can avoid the local SystemVerilog/xsim Tcl app issue.

module copper_sari_scoped_revoker #(
    parameter SRC_LINE_W = 12,
    parameter TGT_LINE_W = 16,
    parameter TOKEN_W = 8,
    parameter DEPTH = 8,
    parameter COUNT_W = 4
) (
    input clk,
    input rst_n,

    input dma_write_valid,
    input [SRC_LINE_W-1:0] dma_line_tag,

    input chi_snoop_valid,
    input chi_snoop_write,
    input chi_snoop_invalidate,
    input [SRC_LINE_W-1:0] chi_line_tag,

    input io_write_valid,
    input [SRC_LINE_W-1:0] io_line_tag,

    input target_remap_valid,
    input [TGT_LINE_W-1:0] target_remap_vline,
    input [TOKEN_W-1:0] target_remap_token,

    input tlbi_token_valid,
    input [TOKEN_W-1:0] tlbi_token,
    input tlbi_all_valid,

    input raw_dmp_seed_valid,
    input [SRC_LINE_W-1:0] dmp_source_line_tag,
    input [TGT_LINE_W-1:0] dmp_target_vline,
    input [TOKEN_W-1:0] dmp_token,

    output source_clear_valid,
    output [SRC_LINE_W-1:0] source_clear_line_tag,
    output source_events_ready,

    output ctlw_remap_valid,
    output [TGT_LINE_W-1:0] ctlw_remap_vline,
    output [TOKEN_W-1:0] ctlw_remap_token,
    output ctlw_tlbi_token_valid,
    output [TOKEN_W-1:0] ctlw_tlbi_token,
    output ctlw_tlbi_all_valid,

    output dmp_conflict_hold,
    output dmp_global_hold,
    output reg overflow_sticky,
    output [COUNT_W-1:0] queued_count
);

    reg [SRC_LINE_W-1:0] queue [0:DEPTH-1];
    reg [SRC_LINE_W-1:0] next_queue [0:DEPTH-1];
    reg [COUNT_W-1:0] count;
    reg [COUNT_W-1:0] next_count;
    wire source_event_dma;
    wire source_event_chi;
    wire source_event_io;
    wire incoming_source_event;
    wire incoming_target_event;
    wire incoming_source_conflict;
    reg queued_source_conflict;
    wire target_remap_conflict;
    wire tlbi_token_conflict;
    wire tlbi_all_conflict;
    wire incoming_target_conflict;
    reg next_overflow;
    integer temp_count;
    integer i;

    assign source_event_dma = dma_write_valid;
    assign source_event_chi = chi_snoop_valid && (chi_snoop_write || chi_snoop_invalidate);
    assign source_event_io = io_write_valid;
    assign incoming_source_event = source_event_dma || source_event_chi || source_event_io;
    assign incoming_target_event = target_remap_valid || tlbi_token_valid || tlbi_all_valid;

    assign source_clear_valid = count != {COUNT_W{1'b0}};
    assign source_clear_line_tag = source_clear_valid ? queue[0] : {SRC_LINE_W{1'b0}};
    assign queued_count = count;

    assign source_events_ready = (DEPTH - count + ((count != {COUNT_W{1'b0}}) ? 1 : 0)) >= 3;

    assign ctlw_remap_valid = target_remap_valid;
    assign ctlw_remap_vline = target_remap_vline;
    assign ctlw_remap_token = target_remap_token;
    assign ctlw_tlbi_token_valid = tlbi_token_valid;
    assign ctlw_tlbi_token = tlbi_token;
    assign ctlw_tlbi_all_valid = tlbi_all_valid;

    always @* begin
        queued_source_conflict = 1'b0;
        for (i = 0; i < DEPTH; i = i + 1) begin
            if ((i < count) && (queue[i] == dmp_source_line_tag)) begin
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
        || (count != {COUNT_W{1'b0}})
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

    always @* begin
        for (i = 0; i < DEPTH; i = i + 1) begin
            next_queue[i] = queue[i];
        end
        temp_count = count;
        next_overflow = overflow_sticky;

        if (temp_count > 0) begin
            for (i = 0; i < DEPTH - 1; i = i + 1) begin
                next_queue[i] = queue[i + 1];
            end
            next_queue[DEPTH - 1] = {SRC_LINE_W{1'b0}};
            temp_count = temp_count - 1;
        end

        if (source_event_dma) begin
            if (temp_count < DEPTH) begin
                next_queue[temp_count] = dma_line_tag;
                temp_count = temp_count + 1;
            end else begin
                next_overflow = 1'b1;
            end
        end

        if (source_event_chi) begin
            if (temp_count < DEPTH) begin
                next_queue[temp_count] = chi_line_tag;
                temp_count = temp_count + 1;
            end else begin
                next_overflow = 1'b1;
            end
        end

        if (source_event_io) begin
            if (temp_count < DEPTH) begin
                next_queue[temp_count] = io_line_tag;
                temp_count = temp_count + 1;
            end else begin
                next_overflow = 1'b1;
            end
        end

        next_count = temp_count;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {COUNT_W{1'b0}};
            overflow_sticky <= 1'b0;
            for (i = 0; i < DEPTH; i = i + 1) begin
                queue[i] <= {SRC_LINE_W{1'b0}};
            end
        end else begin
            count <= next_count;
            overflow_sticky <= next_overflow;
            for (i = 0; i < DEPTH; i = i + 1) begin
                queue[i] <= next_queue[i];
            end
        end
    end

endmodule
