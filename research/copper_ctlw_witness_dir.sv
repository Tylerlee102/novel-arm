`timescale 1ns/1ps

// COPPER CTLW: Committed Target-Line Witness directory.
//
// This block models the small table behind Committed Target-Line Witnessing.
// A demand access may record an exact virtual target-line -> physical line
// witness for the current address-space token. A recursive cross-page DMP
// candidate may use only an exact live witness for the same virtual line and
// token; page-level matches and stale token matches are not authority.

module copper_ctlw_witness_dir #(
    parameter int VLINE_W = 16,
    parameter int PLINE_W = 16,
    parameter int TOKEN_W = 8,
    parameter int ENTRIES = 16,
    parameter int IDX_W = 4
) (
    input  logic clk,
    input  logic rst_n,

    input  logic record_valid,
    input  logic [VLINE_W-1:0] record_vline,
    input  logic [PLINE_W-1:0] record_pline,
    input  logic [TOKEN_W-1:0] record_token,

    input  logic remap_valid,
    input  logic [VLINE_W-1:0] remap_vline,
    input  logic [TOKEN_W-1:0] remap_token,

    input  logic tlbi_token_valid,
    input  logic [TOKEN_W-1:0] tlbi_token,

    input  logic tlbi_all_valid,

    input  logic query_valid,
    input  logic [VLINE_W-1:0] query_vline,
    input  logic [TOKEN_W-1:0] query_token,

    output logic witness_valid,
    output logic [PLINE_W-1:0] witness_pline,
    output logic query_miss,
    output logic token_mismatch_seen,
    output logic line_mismatch_seen,
    output logic remap_clear_hit,
    output logic tlbi_clear_hit,
    output logic collision_evict
);

    logic valid [ENTRIES];
    logic [VLINE_W-1:0] vline [ENTRIES];
    logic [PLINE_W-1:0] pline [ENTRIES];
    logic [TOKEN_W-1:0] token [ENTRIES];

    logic [IDX_W-1:0] record_idx;
    logic [IDX_W-1:0] remap_idx;
    logic [IDX_W-1:0] query_idx;
    logic query_slot_valid;

    assign record_idx = record_vline[IDX_W-1:0];
    assign remap_idx = remap_vline[IDX_W-1:0];
    assign query_idx = query_vline[IDX_W-1:0];

    always_comb begin
        query_slot_valid = valid[query_idx];

        witness_valid =
            query_valid
            && query_slot_valid
            && (vline[query_idx] == query_vline)
            && (token[query_idx] == query_token);

        witness_pline = witness_valid ? pline[query_idx] : '0;

        token_mismatch_seen =
            query_valid
            && query_slot_valid
            && (vline[query_idx] == query_vline)
            && (token[query_idx] != query_token);

        line_mismatch_seen =
            query_valid
            && query_slot_valid
            && (vline[query_idx] != query_vline);

        query_miss = query_valid && !witness_valid;

        remap_clear_hit =
            remap_valid
            && valid[remap_idx]
            && (vline[remap_idx] == remap_vline)
            && (token[remap_idx] == remap_token);

        tlbi_clear_hit = 1'b0;
        for (int i = 0; i < ENTRIES; i++) begin
            if (valid[i] && (tlbi_all_valid || (tlbi_token_valid && token[i] == tlbi_token))) begin
                tlbi_clear_hit = 1'b1;
            end
        end

        collision_evict =
            record_valid
            && valid[record_idx]
            && ((vline[record_idx] != record_vline)
                || (token[record_idx] != record_token));
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < ENTRIES; i++) begin
                valid[i] <= 1'b0;
                vline[i] <= '0;
                pline[i] <= '0;
                token[i] <= '0;
            end
        end else begin
            if (tlbi_all_valid) begin
                for (int i = 0; i < ENTRIES; i++) begin
                    valid[i] <= 1'b0;
                end
            end else begin
                if (tlbi_token_valid) begin
                    for (int i = 0; i < ENTRIES; i++) begin
                        if (valid[i] && token[i] == tlbi_token) begin
                            valid[i] <= 1'b0;
                        end
                    end
                end

                if (remap_valid
                    && valid[remap_idx]
                    && (vline[remap_idx] == remap_vline)
                    && (token[remap_idx] == remap_token)) begin
                    valid[remap_idx] <= 1'b0;
                end

                if (record_valid) begin
                    valid[record_idx] <= 1'b1;
                    vline[record_idx] <= record_vline;
                    pline[record_idx] <= record_pline;
                    token[record_idx] <= record_token;
                end
            end
        end
    end

endmodule
