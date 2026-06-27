`timescale 1ns/1ps

module baseline_prefetch_unit #(
    parameter int ADDR_W = 48
) (
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    input  logic demand_valid,
    input  logic [ADDR_W-1:0] demand_addr,
    output logic prefetch_valid,
    output logic [ADDR_W-1:0] prefetch_addr
);
    always_comb begin
        prefetch_valid = enable && demand_valid;
        prefetch_addr = demand_addr + {{(ADDR_W-7){1'b0}}, 7'd64};
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
        end
    end
endmodule
