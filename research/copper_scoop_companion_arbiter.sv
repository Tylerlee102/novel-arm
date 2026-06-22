`timescale 1ns/1ps

module copper_scoop_companion_arbiter #(
    parameter int unsigned ID_W = 4
) (
    input  logic              primary_valid,
    input  logic [ID_W-1:0]   primary_id,
    input  logic              companion_valid,
    input  logic [ID_W-1:0]   companion_id,
    input  logic              sink_ready,
    output logic              primary_ready,
    output logic              companion_ready,
    output logic              issue_valid,
    output logic              issue_is_companion,
    output logic [ID_W-1:0]   issue_id,
    output logic              companion_blocked_by_primary
);

    always_comb begin
        issue_valid = primary_valid || companion_valid;
        issue_is_companion = 1'b0;
        issue_id = primary_id;
        primary_ready = 1'b0;
        companion_ready = 1'b0;
        companion_blocked_by_primary = primary_valid && companion_valid;

        if (primary_valid) begin
            primary_ready = sink_ready;
            issue_is_companion = 1'b0;
            issue_id = primary_id;
        end else if (companion_valid) begin
            companion_ready = sink_ready;
            issue_is_companion = 1'b1;
            issue_id = companion_id;
        end else begin
            issue_valid = 1'b0;
            issue_id = '0;
        end
    end

endmodule
