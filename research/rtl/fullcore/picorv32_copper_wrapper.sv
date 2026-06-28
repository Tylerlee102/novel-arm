`timescale 1ns/1ps

module picorv32_memory_tieoff (
    input  logic        mem_valid,
    input  logic [31:0] mem_addr,
    input  logic [31:0] mem_wdata,
    input  logic [3:0]  mem_wstrb,
    output logic        mem_ready,
    output logic [31:0] mem_rdata,
    output logic [31:0] activity_word
);
    always_comb begin
        mem_ready = mem_valid;
        mem_rdata = 32'h0000_0013; // RISC-V NOP: addi x0, x0, 0
        activity_word = mem_addr ^ mem_wdata ^ {28'b0, mem_wstrb};
    end
endmodule

module picorv32_core_shell (
    input  logic        clk,
    input  logic        rst_n,
    output logic        trap,
    output logic        mem_valid,
    output logic        mem_instr,
    output logic [31:0] mem_addr,
    output logic [31:0] mem_wdata,
    output logic [3:0]  mem_wstrb,
    output logic        mem_la_read,
    output logic        mem_la_write,
    output logic [31:0] mem_la_addr,
    output logic [31:0] activity_word
);
    logic        mem_ready;
    logic [31:0] mem_rdata;
    logic [31:0] mem_la_wdata;
    logic [3:0]  mem_la_wstrb;
    logic        pcpi_valid;
    logic [31:0] pcpi_insn;
    logic [31:0] pcpi_rs1;
    logic [31:0] pcpi_rs2;
    logic [31:0] eoi;

    picorv32 #(
        .ENABLE_COUNTERS(0),
        .ENABLE_COUNTERS64(0),
        .ENABLE_REGS_16_31(1),
        .ENABLE_REGS_DUALPORT(1),
        .TWO_STAGE_SHIFT(1),
        .BARREL_SHIFTER(0),
        .ENABLE_MUL(0),
        .ENABLE_DIV(0),
        .ENABLE_IRQ(0),
        .ENABLE_TRACE(0),
        .REGS_INIT_ZERO(1)
    ) u_core (
        .clk(clk),
        .resetn(rst_n),
        .trap(trap),
        .mem_valid(mem_valid),
        .mem_instr(mem_instr),
        .mem_ready(mem_ready),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_rdata(mem_rdata),
        .mem_la_read(mem_la_read),
        .mem_la_write(mem_la_write),
        .mem_la_addr(mem_la_addr),
        .mem_la_wdata(mem_la_wdata),
        .mem_la_wstrb(mem_la_wstrb),
        .pcpi_valid(pcpi_valid),
        .pcpi_insn(pcpi_insn),
        .pcpi_rs1(pcpi_rs1),
        .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(1'b0),
        .pcpi_rd(32'b0),
        .pcpi_wait(1'b0),
        .pcpi_ready(1'b0),
        .irq(32'b0),
        .eoi(eoi)
    );

    picorv32_memory_tieoff u_mem (
        .mem_valid(mem_valid),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_ready(mem_ready),
        .mem_rdata(mem_rdata),
        .activity_word(activity_word)
    );
endmodule

module baseline_core_wrapper (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        enable,
    output logic        trap,
    output logic [31:0] core_status
);
    logic        mem_valid;
    logic        mem_instr;
    logic [31:0] mem_addr;
    logic [31:0] mem_wdata;
    logic [3:0]  mem_wstrb;
    logic        mem_la_read;
    logic        mem_la_write;
    logic [31:0] mem_la_addr;
    logic [31:0] activity_word;

    picorv32_core_shell u_shell (
        .clk(clk),
        .rst_n(rst_n),
        .trap(trap),
        .mem_valid(mem_valid),
        .mem_instr(mem_instr),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_la_read(mem_la_read),
        .mem_la_write(mem_la_write),
        .mem_la_addr(mem_la_addr),
        .activity_word(activity_word)
    );

    always_comb begin
        core_status = activity_word ^ {28'b0, enable, mem_instr, mem_la_write, mem_la_read};
    end
endmodule

module core_wrapper_plus_baseline_prefetch (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        enable,
    output logic        trap,
    output logic        prefetch_valid,
    output logic [31:0] core_status
);
    logic        mem_valid;
    logic        mem_instr;
    logic [31:0] mem_addr;
    logic [31:0] mem_wdata;
    logic [3:0]  mem_wstrb;
    logic        mem_la_read;
    logic        mem_la_write;
    logic [31:0] mem_la_addr;
    logic [31:0] activity_word;
    logic [47:0] prefetch_addr;

    picorv32_core_shell u_shell (
        .clk(clk),
        .rst_n(rst_n),
        .trap(trap),
        .mem_valid(mem_valid),
        .mem_instr(mem_instr),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_la_read(mem_la_read),
        .mem_la_write(mem_la_write),
        .mem_la_addr(mem_la_addr),
        .activity_word(activity_word)
    );

    baseline_prefetch_unit #(
        .ADDR_W(48)
    ) u_prefetch (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .demand_valid(mem_la_read || (mem_valid && !mem_instr && mem_wstrb == 4'b0000)),
        .demand_addr({16'b0, mem_la_read ? mem_la_addr : mem_addr}),
        .prefetch_valid(prefetch_valid),
        .prefetch_addr(prefetch_addr)
    );

    always_comb begin
        core_status = activity_word ^ prefetch_addr[31:0] ^ {31'b0, prefetch_valid};
    end
endmodule

module core_wrapper_plus_copper #(
    parameter int ENTRIES = 8,
    parameter int QUEUE_DEPTH = 4
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        enable,
    output logic        trap,
    output logic        prefetch_valid,
    output logic [31:0] core_status
);
    logic        mem_valid;
    logic        mem_instr;
    logic [31:0] mem_addr;
    logic [31:0] mem_wdata;
    logic [3:0]  mem_wstrb;
    logic        mem_la_read;
    logic        mem_la_write;
    logic [31:0] mem_la_addr;
    logic [31:0] activity_word;
    logic [15:0] token;
    logic        queue_pop;
    logic        queue_full;
    logic        blocked_unproven;
    logic        blocked_disabled;
    logic        blocked_permission;
    logic        architectural_state_mutated;
    logic [3:0]  queue_count;

    picorv32_core_shell u_shell (
        .clk(clk),
        .rst_n(rst_n),
        .trap(trap),
        .mem_valid(mem_valid),
        .mem_instr(mem_instr),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_la_read(mem_la_read),
        .mem_la_write(mem_la_write),
        .mem_la_addr(mem_la_addr),
        .activity_word(activity_word)
    );

    assign token = mem_la_addr[17:2] ^ {12'b0, mem_wstrb};
    assign queue_pop = mem_valid && mem_ready_like(mem_addr);

    copper_prefetch_unit_open #(
        .ADDR_W(48),
        .TOKEN_W(16),
        .ENTRIES(ENTRIES),
        .QUEUE_DEPTH(QUEUE_DEPTH)
    ) u_prefetch (
        .clk(clk),
        .rst_n(rst_n),
        .copper_enable(enable),
        .commit_valid(mem_la_read || mem_valid),
        .commit_speculative(1'b0),
        .commit_src_addr({16'b0, mem_la_read ? mem_la_addr : mem_addr}),
        .commit_value_token(token),
        .demand_valid(mem_la_read || (mem_valid && !mem_instr && mem_wstrb == 4'b0000)),
        .demand_src_addr({16'b0, mem_la_read ? mem_la_addr : mem_addr}),
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

    always_comb begin
        core_status = activity_word ^ {
            20'b0,
            prefetch_valid,
            queue_full,
            blocked_unproven,
            blocked_disabled,
            blocked_permission,
            architectural_state_mutated,
            queue_count,
            token[1:0]
        };
    end

    function automatic logic mem_ready_like(input logic [31:0] addr);
        mem_ready_like = ^addr[7:2];
    endfunction
endmodule
