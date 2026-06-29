`timescale 1ns/1ps

module picorv32_tiny_soc_memory #(
    parameter int MEM_WORDS = 64
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        mem_valid,
    input  logic        mem_instr,
    input  logic [31:0] mem_addr,
    input  logic [31:0] mem_wdata,
    input  logic [3:0]  mem_wstrb,
    output logic        mem_ready,
    output logic [31:0] mem_rdata,
    output logic [31:0] activity_word,
    output logic [15:0] instr_count,
    output logic [15:0] load_count,
    output logic [15:0] store_count
);
    localparam int INDEX_W = $clog2(MEM_WORDS);

    logic [31:0] data_mem [0:MEM_WORDS-1];
    logic [INDEX_W-1:0] word_index;

    assign word_index = mem_addr[INDEX_W+1:2];

    function automatic logic [31:0] boot_word(input logic [31:0] addr);
        unique case (addr[7:2])
            6'h00: boot_word = 32'h0000_0093; // addi x1, x0, 0
            6'h01: boot_word = 32'h1000_0113; // addi x2, x0, 256
            6'h02: boot_word = 32'h0001_2183; // lw   x3, 0(x2)
            6'h03: boot_word = 32'h0011_8193; // addi x3, x3, 1
            6'h04: boot_word = 32'h0031_2023; // sw   x3, 0(x2)
            6'h05: boot_word = 32'h0041_2203; // lw   x4, 4(x2)
            6'h06: boot_word = 32'h0022_0213; // addi x4, x4, 2
            6'h07: boot_word = 32'h0041_2223; // sw   x4, 4(x2)
            default: boot_word = 32'h0000_0013; // nop
        endcase
    endfunction

    always_comb begin
        mem_ready = mem_valid;
        if (mem_instr || mem_addr[31:8] == 24'h0) begin
            mem_rdata = boot_word(mem_addr);
        end else begin
            mem_rdata = data_mem[word_index];
        end
        activity_word = mem_addr ^ mem_wdata ^ mem_rdata ^ {28'b0, mem_wstrb};
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            instr_count <= '0;
            load_count <= '0;
            store_count <= '0;
            for (int i = 0; i < MEM_WORDS; i++) begin
                data_mem[i] <= 32'h1000_0000 ^ i;
            end
        end else if (mem_valid && mem_ready) begin
            if (mem_instr) begin
                instr_count <= instr_count + 16'd1;
            end else if (mem_wstrb == 4'b0000) begin
                load_count <= load_count + 16'd1;
            end else begin
                store_count <= store_count + 16'd1;
                if (mem_wstrb[0]) data_mem[word_index][7:0] <= mem_wdata[7:0];
                if (mem_wstrb[1]) data_mem[word_index][15:8] <= mem_wdata[15:8];
                if (mem_wstrb[2]) data_mem[word_index][23:16] <= mem_wdata[23:16];
                if (mem_wstrb[3]) data_mem[word_index][31:24] <= mem_wdata[31:24];
            end
        end
    end
endmodule

module picorv32_full_core_shell #(
    parameter int MEM_WORDS = 64
) (
    input  logic        clk,
    input  logic        rst_n,
    output logic        trap,
    output logic        mem_valid,
    output logic        mem_ready,
    output logic        mem_instr,
    output logic [31:0] mem_addr,
    output logic [31:0] mem_wdata,
    output logic [3:0]  mem_wstrb,
    output logic        mem_la_read,
    output logic        mem_la_write,
    output logic [31:0] mem_la_addr,
    output logic [31:0] activity_word,
    output logic [15:0] instr_count,
    output logic [15:0] load_count,
    output logic [15:0] store_count
);
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

    picorv32_tiny_soc_memory #(
        .MEM_WORDS(MEM_WORDS)
    ) u_mem (
        .clk(clk),
        .rst_n(rst_n),
        .mem_valid(mem_valid),
        .mem_instr(mem_instr),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_ready(mem_ready),
        .mem_rdata(mem_rdata),
        .activity_word(activity_word),
        .instr_count(instr_count),
        .load_count(load_count),
        .store_count(store_count)
    );
endmodule

module full_core_baseline #(
    parameter int MEM_WORDS = 64
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        enable,
    output logic        trap,
    output logic [31:0] core_status
);
    logic        mem_valid;
    logic        mem_ready;
    logic        mem_instr;
    logic [31:0] mem_addr;
    logic [31:0] mem_wdata;
    logic [3:0]  mem_wstrb;
    logic        mem_la_read;
    logic        mem_la_write;
    logic [31:0] mem_la_addr;
    logic [31:0] activity_word;
    logic [15:0] instr_count;
    logic [15:0] load_count;
    logic [15:0] store_count;

    picorv32_full_core_shell #(
        .MEM_WORDS(MEM_WORDS)
    ) u_shell (
        .clk(clk),
        .rst_n(rst_n),
        .trap(trap),
        .mem_valid(mem_valid),
        .mem_ready(mem_ready),
        .mem_instr(mem_instr),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_la_read(mem_la_read),
        .mem_la_write(mem_la_write),
        .mem_la_addr(mem_la_addr),
        .activity_word(activity_word),
        .instr_count(instr_count),
        .load_count(load_count),
        .store_count(store_count)
    );

    always_comb begin
        core_status = activity_word ^ {instr_count, load_count} ^ {store_count, 12'b0, enable, mem_ready, mem_instr, mem_valid};
    end
endmodule

module full_core_plus_copper #(
    parameter int MEM_WORDS = 64,
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
    logic        mem_ready;
    logic        mem_instr;
    logic [31:0] mem_addr;
    logic [31:0] mem_wdata;
    logic [3:0]  mem_wstrb;
    logic        mem_la_read;
    logic        mem_la_write;
    logic [31:0] mem_la_addr;
    logic [31:0] activity_word;
    logic [15:0] instr_count;
    logic [15:0] load_count;
    logic [15:0] store_count;
    logic [15:0] token;
    logic        queue_full;
    logic        blocked_unproven;
    logic        blocked_disabled;
    logic        blocked_permission;
    logic        architectural_state_mutated;
    logic [3:0]  queue_count;

    picorv32_full_core_shell #(
        .MEM_WORDS(MEM_WORDS)
    ) u_shell (
        .clk(clk),
        .rst_n(rst_n),
        .trap(trap),
        .mem_valid(mem_valid),
        .mem_ready(mem_ready),
        .mem_instr(mem_instr),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_la_read(mem_la_read),
        .mem_la_write(mem_la_write),
        .mem_la_addr(mem_la_addr),
        .activity_word(activity_word),
        .instr_count(instr_count),
        .load_count(load_count),
        .store_count(store_count)
    );

    assign token = mem_la_addr[17:2] ^ instr_count ^ load_count ^ store_count;

    copper_prefetch_unit_open #(
        .ADDR_W(48),
        .TOKEN_W(16),
        .ENTRIES(ENTRIES),
        .QUEUE_DEPTH(QUEUE_DEPTH)
    ) u_prefetch (
        .clk(clk),
        .rst_n(rst_n),
        .copper_enable(enable),
        .commit_valid(mem_valid && mem_ready),
        .commit_speculative(1'b0),
        .commit_src_addr({16'b0, mem_addr}),
        .commit_value_token(token),
        .demand_valid(mem_la_read || (mem_valid && mem_ready && !mem_instr && mem_wstrb == 4'b0000)),
        .demand_src_addr({16'b0, mem_la_read ? mem_la_addr : mem_addr}),
        .demand_value_token(token),
        .demand_translation_ok(1'b1),
        .demand_permission_ok(1'b1),
        .queue_pop(mem_valid && mem_ready && !mem_instr),
        .prefetch_valid(prefetch_valid),
        .queue_full(queue_full),
        .blocked_unproven(blocked_unproven),
        .blocked_disabled(blocked_disabled),
        .blocked_permission(blocked_permission),
        .architectural_state_mutated(architectural_state_mutated),
        .queue_count(queue_count)
    );

    always_comb begin
        core_status = activity_word ^ {instr_count, load_count} ^ {
            6'b0,
            store_count[7:0],
            prefetch_valid,
            queue_full,
            blocked_unproven,
            blocked_disabled,
            blocked_permission,
            architectural_state_mutated,
            queue_count,
            token[7:0]
        };
    end
endmodule
