`timescale 1ns/1ps

// COPPER SARI-RQ: ring-queued SoC Authority Revocation Interface.
//
// SARI-RQ preserves SARI's external authority contract while avoiding the
// timing cost of shifting every queued source revocation each cycle. Source
// revocations are admitted through a ready/hold front door into a circular
// queue; one queued source line is cleared per cycle. If a source event arrives
// when the queue cannot accept the full DMA/CHI/I/O burst, overflow_sticky
// forces a conservative global DMP hold.

module copper_sari_ring_revoker #(
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

    output logic source_clear_valid,
    output logic [SRC_LINE_W-1:0] source_clear_line_tag,
    output logic source_events_ready,

    output logic ctlw_remap_valid,
    output logic [TGT_LINE_W-1:0] ctlw_remap_vline,
    output logic [TOKEN_W-1:0] ctlw_remap_token,
    output logic ctlw_tlbi_token_valid,
    output logic [TOKEN_W-1:0] ctlw_tlbi_token,
    output logic ctlw_tlbi_all_valid,

    output logic dmp_revocation_hold,
    output logic overflow_sticky,
    output logic [COUNT_W-1:0] queued_count
);

    localparam int PTR_W = (DEPTH <= 2) ? 1 : $clog2(DEPTH);

    logic [SRC_LINE_W-1:0] queue [DEPTH];
    logic [PTR_W-1:0] head;
    logic [PTR_W-1:0] tail;
    logic [PTR_W-1:0] next_head;
    logic [PTR_W-1:0] next_tail;
    logic [PTR_W-1:0] tail1;
    logic [PTR_W-1:0] tail2;
    logic [PTR_W-1:0] tail3;
    logic [COUNT_W-1:0] count;
    logic [COUNT_W-1:0] next_count;
    logic [COUNT_W:0] space_after_dequeue;

    logic source_event_dma;
    logic source_event_chi;
    logic source_event_io;
    logic incoming_source_event;
    logic incoming_target_event;
    logic next_overflow;

    logic wr0_valid;
    logic wr1_valid;
    logic wr2_valid;
    logic [SRC_LINE_W-1:0] wr0_line;
    logic [SRC_LINE_W-1:0] wr1_line;
    logic [SRC_LINE_W-1:0] wr2_line;
    logic [1:0] wr_count;

    function automatic logic [PTR_W-1:0] bump(
        input logic [PTR_W-1:0] ptr
    );
        if (ptr == PTR_W'(DEPTH - 1)) begin
            bump = '0;
        end else begin
            bump = ptr + {{(PTR_W-1){1'b0}}, 1'b1};
        end
    endfunction

    assign source_event_dma = dma_write_valid;
    assign source_event_chi = chi_snoop_valid && (chi_snoop_write || chi_snoop_invalidate);
    assign source_event_io = io_write_valid;
    assign incoming_source_event = source_event_dma || source_event_chi || source_event_io;
    assign incoming_target_event = target_remap_valid || tlbi_token_valid || tlbi_all_valid;

    assign source_clear_valid = count != '0;
    assign source_clear_line_tag = source_clear_valid ? queue[head] : '0;
    assign queued_count = count;

    assign space_after_dequeue =
        {1'b0, COUNT_W'(DEPTH)}
        - {1'b0, count}
        + ((count != '0) ? {{COUNT_W{1'b0}}, 1'b1} : '0);
    assign source_events_ready = space_after_dequeue >= (COUNT_W+1)'(3);

    assign ctlw_remap_valid = target_remap_valid;
    assign ctlw_remap_vline = target_remap_vline;
    assign ctlw_remap_token = target_remap_token;
    assign ctlw_tlbi_token_valid = tlbi_token_valid;
    assign ctlw_tlbi_token = tlbi_token;
    assign ctlw_tlbi_all_valid = tlbi_all_valid;

    assign dmp_revocation_hold =
        overflow_sticky
        || (count != '0)
        || incoming_source_event
        || incoming_target_event;

    assign tail1 = bump(tail);
    assign tail2 = bump(tail1);
    assign tail3 = bump(tail2);

    always_comb begin
        wr0_valid = 1'b0;
        wr1_valid = 1'b0;
        wr2_valid = 1'b0;
        wr0_line = '0;
        wr1_line = '0;
        wr2_line = '0;
        wr_count = '0;

        if (source_events_ready) begin
            unique case ({source_event_dma, source_event_chi, source_event_io})
                3'b100: begin
                    wr0_valid = 1'b1;
                    wr0_line = dma_line_tag;
                    wr_count = 2'd1;
                end
                3'b010: begin
                    wr0_valid = 1'b1;
                    wr0_line = chi_line_tag;
                    wr_count = 2'd1;
                end
                3'b001: begin
                    wr0_valid = 1'b1;
                    wr0_line = io_line_tag;
                    wr_count = 2'd1;
                end
                3'b110: begin
                    wr0_valid = 1'b1;
                    wr1_valid = 1'b1;
                    wr0_line = dma_line_tag;
                    wr1_line = chi_line_tag;
                    wr_count = 2'd2;
                end
                3'b101: begin
                    wr0_valid = 1'b1;
                    wr1_valid = 1'b1;
                    wr0_line = dma_line_tag;
                    wr1_line = io_line_tag;
                    wr_count = 2'd2;
                end
                3'b011: begin
                    wr0_valid = 1'b1;
                    wr1_valid = 1'b1;
                    wr0_line = chi_line_tag;
                    wr1_line = io_line_tag;
                    wr_count = 2'd2;
                end
                3'b111: begin
                    wr0_valid = 1'b1;
                    wr1_valid = 1'b1;
                    wr2_valid = 1'b1;
                    wr0_line = dma_line_tag;
                    wr1_line = chi_line_tag;
                    wr2_line = io_line_tag;
                    wr_count = 2'd3;
                end
                default: begin
                    wr_count = '0;
                end
            endcase
        end
    end

    always_comb begin
        next_head = head;
        next_tail = tail;
        next_count = count;
        next_overflow = overflow_sticky;

        if (count != '0) begin
            next_head = bump(head);
            next_count = count - COUNT_W'(1);
        end

        if (incoming_source_event && !source_events_ready) begin
            next_overflow = 1'b1;
        end

        unique case (wr_count)
            2'd1: begin
                next_tail = tail1;
                next_count = next_count + COUNT_W'(1);
            end
            2'd2: begin
                next_tail = tail2;
                next_count = next_count + COUNT_W'(2);
            end
            2'd3: begin
                next_tail = tail3;
                next_count = next_count + COUNT_W'(3);
            end
            default: begin
                next_tail = tail;
            end
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            head <= '0;
            tail <= '0;
            count <= '0;
            overflow_sticky <= 1'b0;
            for (int i = 0; i < DEPTH; i++) begin
                queue[i] <= '0;
            end
        end else begin
            head <= next_head;
            tail <= next_tail;
            count <= next_count;
            overflow_sticky <= next_overflow;
            if (wr0_valid) begin
                queue[tail] <= wr0_line;
            end
            if (wr1_valid) begin
                queue[tail1] <= wr1_line;
            end
            if (wr2_valid) begin
                queue[tail2] <= wr2_line;
            end
        end
    end

endmodule
