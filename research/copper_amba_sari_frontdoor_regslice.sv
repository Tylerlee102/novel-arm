`timescale 1ns/1ps

// Registered timing slice for the COPPER AMBA-style SARI front door.
//
// The frontdoor itself is combinational. This wrapper registers its inputs and
// outputs so Vivado can report a real clk-to-clk decode path for implementation
// evidence. It is an optional boundary slice, not a required extra cycle in a
// production integration.

module copper_amba_sari_frontdoor_regslice #(
    parameter int SRC_LINE_W = 12,
    parameter int TGT_LINE_W = 16,
    parameter int TOKEN_W = 8,
    parameter int CHI_KIND_W = 3,
    parameter int DVM_KIND_W = 2
) (
    input  logic clk,
    input  logic rst_n,

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

    logic r_sari_source_events_ready;
    logic r_dma_write_valid;
    logic [SRC_LINE_W-1:0] r_dma_line_tag;
    logic r_chi_event_valid;
    logic [CHI_KIND_W-1:0] r_chi_event_kind;
    logic [SRC_LINE_W-1:0] r_chi_line_tag;
    logic r_io_write_valid;
    logic [SRC_LINE_W-1:0] r_io_line_tag;
    logic r_target_remap_valid;
    logic [TGT_LINE_W-1:0] r_target_remap_vline;
    logic [TOKEN_W-1:0] r_target_remap_token;
    logic r_dvm_valid;
    logic [DVM_KIND_W-1:0] r_dvm_kind;
    logic [TOKEN_W-1:0] r_dvm_token;

    logic w_sari_dma_write_valid;
    logic [SRC_LINE_W-1:0] w_sari_dma_line_tag;
    logic w_sari_chi_snoop_valid;
    logic w_sari_chi_snoop_write;
    logic w_sari_chi_snoop_invalidate;
    logic [SRC_LINE_W-1:0] w_sari_chi_line_tag;
    logic w_sari_io_write_valid;
    logic [SRC_LINE_W-1:0] w_sari_io_line_tag;
    logic w_sari_target_remap_valid;
    logic [TGT_LINE_W-1:0] w_sari_target_remap_vline;
    logic [TOKEN_W-1:0] w_sari_target_remap_token;
    logic w_sari_tlbi_token_valid;
    logic [TOKEN_W-1:0] w_sari_tlbi_token;
    logic w_sari_tlbi_all_valid;
    logic w_frontdoor_ready;
    logic w_dmp_frontdoor_hold;
    logic w_decoded_source_event;
    logic w_decoded_target_event;
    logic w_source_backpressure;

    copper_amba_sari_frontdoor #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .CHI_KIND_W(CHI_KIND_W),
        .DVM_KIND_W(DVM_KIND_W)
    ) frontdoor (
        .sari_source_events_ready(r_sari_source_events_ready),
        .dma_write_valid(r_dma_write_valid),
        .dma_line_tag(r_dma_line_tag),
        .chi_event_valid(r_chi_event_valid),
        .chi_event_kind(r_chi_event_kind),
        .chi_line_tag(r_chi_line_tag),
        .io_write_valid(r_io_write_valid),
        .io_line_tag(r_io_line_tag),
        .target_remap_valid(r_target_remap_valid),
        .target_remap_vline(r_target_remap_vline),
        .target_remap_token(r_target_remap_token),
        .dvm_valid(r_dvm_valid),
        .dvm_kind(r_dvm_kind),
        .dvm_token(r_dvm_token),
        .sari_dma_write_valid(w_sari_dma_write_valid),
        .sari_dma_line_tag(w_sari_dma_line_tag),
        .sari_chi_snoop_valid(w_sari_chi_snoop_valid),
        .sari_chi_snoop_write(w_sari_chi_snoop_write),
        .sari_chi_snoop_invalidate(w_sari_chi_snoop_invalidate),
        .sari_chi_line_tag(w_sari_chi_line_tag),
        .sari_io_write_valid(w_sari_io_write_valid),
        .sari_io_line_tag(w_sari_io_line_tag),
        .sari_target_remap_valid(w_sari_target_remap_valid),
        .sari_target_remap_vline(w_sari_target_remap_vline),
        .sari_target_remap_token(w_sari_target_remap_token),
        .sari_tlbi_token_valid(w_sari_tlbi_token_valid),
        .sari_tlbi_token(w_sari_tlbi_token),
        .sari_tlbi_all_valid(w_sari_tlbi_all_valid),
        .frontdoor_ready(w_frontdoor_ready),
        .dmp_frontdoor_hold(w_dmp_frontdoor_hold),
        .decoded_source_event(w_decoded_source_event),
        .decoded_target_event(w_decoded_target_event),
        .source_backpressure(w_source_backpressure)
    );

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r_sari_source_events_ready <= 1'b0;
            r_dma_write_valid <= 1'b0;
            r_dma_line_tag <= '0;
            r_chi_event_valid <= 1'b0;
            r_chi_event_kind <= '0;
            r_chi_line_tag <= '0;
            r_io_write_valid <= 1'b0;
            r_io_line_tag <= '0;
            r_target_remap_valid <= 1'b0;
            r_target_remap_vline <= '0;
            r_target_remap_token <= '0;
            r_dvm_valid <= 1'b0;
            r_dvm_kind <= '0;
            r_dvm_token <= '0;

            sari_dma_write_valid <= 1'b0;
            sari_dma_line_tag <= '0;
            sari_chi_snoop_valid <= 1'b0;
            sari_chi_snoop_write <= 1'b0;
            sari_chi_snoop_invalidate <= 1'b0;
            sari_chi_line_tag <= '0;
            sari_io_write_valid <= 1'b0;
            sari_io_line_tag <= '0;
            sari_target_remap_valid <= 1'b0;
            sari_target_remap_vline <= '0;
            sari_target_remap_token <= '0;
            sari_tlbi_token_valid <= 1'b0;
            sari_tlbi_token <= '0;
            sari_tlbi_all_valid <= 1'b0;
            frontdoor_ready <= 1'b0;
            dmp_frontdoor_hold <= 1'b0;
            decoded_source_event <= 1'b0;
            decoded_target_event <= 1'b0;
            source_backpressure <= 1'b0;
        end else begin
            r_sari_source_events_ready <= sari_source_events_ready;
            r_dma_write_valid <= dma_write_valid;
            r_dma_line_tag <= dma_line_tag;
            r_chi_event_valid <= chi_event_valid;
            r_chi_event_kind <= chi_event_kind;
            r_chi_line_tag <= chi_line_tag;
            r_io_write_valid <= io_write_valid;
            r_io_line_tag <= io_line_tag;
            r_target_remap_valid <= target_remap_valid;
            r_target_remap_vline <= target_remap_vline;
            r_target_remap_token <= target_remap_token;
            r_dvm_valid <= dvm_valid;
            r_dvm_kind <= dvm_kind;
            r_dvm_token <= dvm_token;

            sari_dma_write_valid <= w_sari_dma_write_valid;
            sari_dma_line_tag <= w_sari_dma_line_tag;
            sari_chi_snoop_valid <= w_sari_chi_snoop_valid;
            sari_chi_snoop_write <= w_sari_chi_snoop_write;
            sari_chi_snoop_invalidate <= w_sari_chi_snoop_invalidate;
            sari_chi_line_tag <= w_sari_chi_line_tag;
            sari_io_write_valid <= w_sari_io_write_valid;
            sari_io_line_tag <= w_sari_io_line_tag;
            sari_target_remap_valid <= w_sari_target_remap_valid;
            sari_target_remap_vline <= w_sari_target_remap_vline;
            sari_target_remap_token <= w_sari_target_remap_token;
            sari_tlbi_token_valid <= w_sari_tlbi_token_valid;
            sari_tlbi_token <= w_sari_tlbi_token;
            sari_tlbi_all_valid <= w_sari_tlbi_all_valid;
            frontdoor_ready <= w_frontdoor_ready;
            dmp_frontdoor_hold <= w_dmp_frontdoor_hold;
            decoded_source_event <= w_decoded_source_event;
            decoded_target_event <= w_decoded_target_event;
            source_backpressure <= w_source_backpressure;
        end
    end

endmodule
