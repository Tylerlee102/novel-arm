`timescale 1ns/1ps

module baseline_core_stub_with_prefetch_interface #(
    parameter int ADDR_W = 48
) (
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    output logic prefetch_valid,
    output logic [ADDR_W-1:0] prefetch_addr,
    output logic [15:0] retire_count
);
    (* keep *) logic [ADDR_W-1:0] demand_addr;
    (* keep *) logic demand_valid;

    baseline_prefetch_unit #(
        .ADDR_W(ADDR_W)
    ) u_baseline_prefetch (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .demand_valid(demand_valid),
        .demand_addr(demand_addr),
        .prefetch_valid(prefetch_valid),
        .prefetch_addr(prefetch_addr)
    );

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            demand_addr <= '0;
            demand_valid <= 1'b0;
            retire_count <= '0;
        end else begin
            demand_valid <= 1'b1;
            demand_addr <= demand_addr + {{(ADDR_W-7){1'b0}}, 7'd64};
            retire_count <= retire_count + 16'd1;
        end
    end
endmodule

module nearcore_stub_baseline #(
    parameter int ADDR_W = 48
) (
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    output logic prefetch_valid,
    output logic [ADDR_W-1:0] prefetch_addr,
    output logic [15:0] retire_count
);
    baseline_core_stub_with_prefetch_interface #(
        .ADDR_W(ADDR_W)
    ) u_nearcore_baseline (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .prefetch_valid(prefetch_valid),
        .prefetch_addr(prefetch_addr),
        .retire_count(retire_count)
    );
endmodule

module nearcore_stub_plus_copper #(
    parameter int ADDR_W = 48,
    parameter int TOKEN_W = 16,
    parameter int ENTRIES = 8,
    parameter int QUEUE_DEPTH = 4
) (
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    output logic prefetch_valid,
    output logic [15:0] retire_count,
    output logic [7:0] core_status
);
    core_stub_plus_copper #(
        .ADDR_W(ADDR_W),
        .TOKEN_W(TOKEN_W),
        .ENTRIES(ENTRIES),
        .QUEUE_DEPTH(QUEUE_DEPTH)
    ) u_nearcore_copper (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .prefetch_valid(prefetch_valid),
        .retire_count(retire_count),
        .core_status(core_status)
    );
endmodule

module core_stub_plus_copper #(
    parameter int ADDR_W = 48,
    parameter int TOKEN_W = 16,
    parameter int ENTRIES = 8,
    parameter int QUEUE_DEPTH = 4
) (
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    output logic prefetch_valid,
    output logic [15:0] retire_count,
    output logic [7:0] core_status
);
    (* keep *) logic [ADDR_W-1:0] demand_addr;
    (* keep *) logic [ADDR_W-1:0] committed_addr;
    (* keep *) logic [TOKEN_W-1:0] token;
    (* keep *) logic queue_pop;
    logic queue_full;
    logic blocked_unproven;
    logic blocked_disabled;
    logic blocked_permission;
    logic architectural_state_mutated;
    logic [3:0] queue_count;

    copper_prefetch_unit_open #(
        .ADDR_W(ADDR_W),
        .TOKEN_W(TOKEN_W),
        .ENTRIES(ENTRIES),
        .QUEUE_DEPTH(QUEUE_DEPTH)
    ) u_copper_prefetch (
        .clk(clk),
        .rst_n(rst_n),
        .copper_enable(enable),
        .commit_valid(1'b1),
        .commit_speculative(1'b0),
        .commit_src_addr(committed_addr),
        .commit_value_token(token),
        .demand_valid(1'b1),
        .demand_src_addr(demand_addr),
        .demand_value_token(token),
        .demand_translation_ok(1'b1),
        .demand_permission_ok(1'b1),
        .queue_pop(queue_pop),
        .prefetch_valid(prefetch_valid),
        .queue_full(queue_full),
        .blocked_unproven(blocked_unproven),
        .blocked_disabled(blocked_disabled),
        .blocked_permission(blocked_permission),
        .architectural_state_mutated(architectural_state_mutated),
        .queue_count(queue_count)
    );

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            demand_addr <= '0;
            committed_addr <= '0;
            token <= '0;
            retire_count <= '0;
            queue_pop <= 1'b0;
            core_status <= '0;
        end else begin
            committed_addr <= demand_addr;
            demand_addr <= demand_addr + {{(ADDR_W-7){1'b0}}, 7'd64};
            token <= token + 16'd1;
            retire_count <= retire_count + 16'd1;
            queue_pop <= retire_count[0];
            core_status <= {
                prefetch_valid,
                queue_full,
                blocked_unproven,
                blocked_disabled,
                blocked_permission,
                architectural_state_mutated,
                queue_count[1:0]
            };
        end
    end
endmodule
