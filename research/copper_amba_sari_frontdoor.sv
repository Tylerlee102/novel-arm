`timescale 1ns/1ps

// COPPER AMBA-style SARI front door.
//
// This module is not an ARM CHI/ACE implementation. It is a public, generic
// AMBA-style event decoder for COPPER's SoC Authority Revocation Interface
// (SARI). It maps coherence/DMA/I/O/MMU event classes into the abstract SARI
// source-line and target-witness revocation signals.
//
// Front-door invariant:
//   Any authority-changing source event either enters SARI in the same cycle
//   or deasserts frontdoor_ready while asserting dmp_frontdoor_hold. Target
//   remap/TLBI/DVM events are passed through immediately and also hold DMP.

module copper_amba_sari_frontdoor #(
    parameter int SRC_LINE_W = 12,
    parameter int TGT_LINE_W = 16,
    parameter int TOKEN_W = 8,
    parameter int CHI_KIND_W = 3,
    parameter int DVM_KIND_W = 2
) (
    input  logic sari_source_events_ready,

    input  logic dma_write_valid,
    input  logic [SRC_LINE_W-1:0] dma_line_tag,

    input  logic chi_event_valid,
    input  logic [CHI_KIND_W-1:0] chi_event_kind,
    input  logic [SRC_LINE_W-1:0] chi_line_tag,

    input  logic io_write_valid,
    input  logic [SRC_LINE_W-1:0] io_line_tag,

    input  logic target_remap_valid,
    input  logic [TGT_LINE_W-1:0] target_remap_vline,
    input  logic [TOKEN_W-1:0] target_remap_token,

    input  logic dvm_valid,
    input  logic [DVM_KIND_W-1:0] dvm_kind,
    input  logic [TOKEN_W-1:0] dvm_token,

    output logic sari_dma_write_valid,
    output logic [SRC_LINE_W-1:0] sari_dma_line_tag,
    output logic sari_chi_snoop_valid,
    output logic sari_chi_snoop_write,
    output logic sari_chi_snoop_invalidate,
    output logic [SRC_LINE_W-1:0] sari_chi_line_tag,
    output logic sari_io_write_valid,
    output logic [SRC_LINE_W-1:0] sari_io_line_tag,

    output logic sari_target_remap_valid,
    output logic [TGT_LINE_W-1:0] sari_target_remap_vline,
    output logic [TOKEN_W-1:0] sari_target_remap_token,
    output logic sari_tlbi_token_valid,
    output logic [TOKEN_W-1:0] sari_tlbi_token,
    output logic sari_tlbi_all_valid,

    output logic frontdoor_ready,
    output logic dmp_frontdoor_hold,
    output logic decoded_source_event,
    output logic decoded_target_event,
    output logic source_backpressure
);

    localparam logic [CHI_KIND_W-1:0] CHI_READ_SHARED       = CHI_KIND_W'(3'd0);
    localparam logic [CHI_KIND_W-1:0] CHI_READ_UNIQUE       = CHI_KIND_W'(3'd1);
    localparam logic [CHI_KIND_W-1:0] CHI_CLEAN_INVALIDATE  = CHI_KIND_W'(3'd2);
    localparam logic [CHI_KIND_W-1:0] CHI_MAKE_INVALID      = CHI_KIND_W'(3'd3);
    localparam logic [CHI_KIND_W-1:0] CHI_WRITEBACK_DIRTY   = CHI_KIND_W'(3'd4);
    localparam logic [CHI_KIND_W-1:0] CHI_DVM               = CHI_KIND_W'(3'd5);

    localparam logic [DVM_KIND_W-1:0] DVM_NONE       = DVM_KIND_W'(2'd0);
    localparam logic [DVM_KIND_W-1:0] DVM_TLBI_TOKEN = DVM_KIND_W'(2'd1);
    localparam logic [DVM_KIND_W-1:0] DVM_TLBI_ALL   = DVM_KIND_W'(2'd2);

    logic chi_source_write;
    logic chi_source_invalidate;
    logic chi_source_event;
    logic dvm_tlbi_token;
    logic dvm_tlbi_all;

    always_comb begin
        chi_source_write = 1'b0;
        chi_source_invalidate = 1'b0;

        unique case (chi_event_kind)
            CHI_READ_SHARED: begin
                chi_source_write = 1'b0;
                chi_source_invalidate = 1'b0;
            end
            CHI_READ_UNIQUE: begin
                chi_source_write = 1'b1;
                chi_source_invalidate = 1'b0;
            end
            CHI_CLEAN_INVALIDATE: begin
                chi_source_write = 1'b0;
                chi_source_invalidate = 1'b1;
            end
            CHI_MAKE_INVALID: begin
                chi_source_write = 1'b0;
                chi_source_invalidate = 1'b1;
            end
            CHI_WRITEBACK_DIRTY: begin
                chi_source_write = 1'b1;
                chi_source_invalidate = 1'b0;
            end
            default: begin
                chi_source_write = 1'b0;
                chi_source_invalidate = 1'b0;
            end
        endcase

        chi_source_event =
            chi_event_valid
            && (chi_source_write || chi_source_invalidate);

        dvm_tlbi_token =
            dvm_valid
            && (
                (dvm_kind == DVM_TLBI_TOKEN)
                || (chi_event_valid && (chi_event_kind == CHI_DVM) && (dvm_kind == DVM_TLBI_TOKEN))
            );

        dvm_tlbi_all =
            dvm_valid
            && (
                (dvm_kind == DVM_TLBI_ALL)
                || (chi_event_valid && (chi_event_kind == CHI_DVM) && (dvm_kind == DVM_TLBI_ALL))
            );

        decoded_source_event =
            dma_write_valid
            || chi_source_event
            || io_write_valid;

        decoded_target_event =
            target_remap_valid
            || dvm_tlbi_token
            || dvm_tlbi_all;

        source_backpressure =
            decoded_source_event
            && !sari_source_events_ready;

        frontdoor_ready =
            !source_backpressure;

        dmp_frontdoor_hold =
            decoded_source_event
            || decoded_target_event;

        sari_dma_write_valid =
            dma_write_valid
            && sari_source_events_ready;
        sari_dma_line_tag = dma_line_tag;

        sari_chi_snoop_valid =
            chi_source_event
            && sari_source_events_ready;
        sari_chi_snoop_write = chi_source_write;
        sari_chi_snoop_invalidate = chi_source_invalidate;
        sari_chi_line_tag = chi_line_tag;

        sari_io_write_valid =
            io_write_valid
            && sari_source_events_ready;
        sari_io_line_tag = io_line_tag;

        sari_target_remap_valid = target_remap_valid;
        sari_target_remap_vline = target_remap_vline;
        sari_target_remap_token = target_remap_token;
        sari_tlbi_token_valid = dvm_tlbi_token;
        sari_tlbi_token = dvm_token;
        sari_tlbi_all_valid = dvm_tlbi_all;
    end

endmodule
