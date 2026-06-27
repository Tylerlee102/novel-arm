`timescale 1ns/1ps

module copper_prefetch_unit_open #(
    parameter int ADDR_W = 48,
    parameter int TOKEN_W = 16,
    parameter int ENTRIES = 4,
    parameter int QUEUE_DEPTH = 2
) (
    input  logic clk,
    input  logic rst_n,
    input  logic copper_enable,

    input  logic commit_valid,
    input  logic commit_speculative,
    input  logic [ADDR_W-1:0] commit_src_addr,
    input  logic [TOKEN_W-1:0] commit_value_token,

    input  logic demand_valid,
    input  logic [ADDR_W-1:0] demand_src_addr,
    input  logic [TOKEN_W-1:0] demand_value_token,
    input  logic demand_translation_ok,
    input  logic demand_permission_ok,

    input  logic queue_pop,

    output logic prefetch_valid,
    output logic queue_full,
    output logic blocked_unproven,
    output logic blocked_disabled,
    output logic blocked_permission,
    output logic architectural_state_mutated,
    output logic [3:0] queue_count
);
    logic [ADDR_W-1:0] src_table [ENTRIES];
    logic [TOKEN_W-1:0] token_table [ENTRIES];
    logic valid_table [ENTRIES];
    logic [$clog2(ENTRIES)-1:0] insert_ptr;
    logic [ENTRIES-1:0] match_vec;
    logic hit;
    localparam logic [3:0] QUEUE_DEPTH_LIMIT = QUEUE_DEPTH;

    generate
        for (genvar gi = 0; gi < ENTRIES; gi++) begin : gen_match
            assign match_vec[gi] = valid_table[gi]
                && src_table[gi] == demand_src_addr
                && token_table[gi] == demand_value_token;
        end
    endgenerate

    assign hit = |match_vec;

    assign queue_full = queue_count >= QUEUE_DEPTH_LIMIT;
    assign blocked_disabled = demand_valid && !copper_enable;
    assign blocked_permission = demand_valid && copper_enable && hit
        && (!demand_translation_ok || !demand_permission_ok);
    assign blocked_unproven = demand_valid && copper_enable && !hit;
    assign prefetch_valid = demand_valid && copper_enable && hit
        && demand_translation_ok && demand_permission_ok && !queue_full;
    assign architectural_state_mutated = 1'b0;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            insert_ptr <= '0;
            queue_count <= '0;
            for (int i = 0; i < ENTRIES; i++) begin
                valid_table[i] <= 1'b0;
                src_table[i] <= '0;
                token_table[i] <= '0;
            end
        end else begin
            if (commit_valid && !commit_speculative) begin
                valid_table[insert_ptr] <= 1'b1;
                src_table[insert_ptr] <= commit_src_addr;
                token_table[insert_ptr] <= commit_value_token;
                insert_ptr <= insert_ptr + 1'b1;
            end

            if (prefetch_valid) begin
                queue_count <= queue_count + 1'b1;
            end else if (queue_pop && queue_count != 0) begin
                queue_count <= queue_count - 1'b1;
            end
        end
    end
endmodule
