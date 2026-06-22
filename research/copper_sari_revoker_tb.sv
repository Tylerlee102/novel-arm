`timescale 1ns/1ps

module copper_sari_revoker_tb;

    localparam int SRC_LINE_W = 8;
    localparam int TGT_LINE_W = 12;
    localparam int TOKEN_W = 4;
    localparam int DEPTH = 8;
    localparam int COUNT_W = 4;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;

    logic dma_write_valid;
    logic [SRC_LINE_W-1:0] dma_line_tag;
    logic chi_snoop_valid;
    logic chi_snoop_write;
    logic chi_snoop_invalidate;
    logic [SRC_LINE_W-1:0] chi_line_tag;
    logic io_write_valid;
    logic [SRC_LINE_W-1:0] io_line_tag;
    logic target_remap_valid;
    logic [TGT_LINE_W-1:0] target_remap_vline;
    logic [TOKEN_W-1:0] target_remap_token;
    logic tlbi_token_valid;
    logic [TOKEN_W-1:0] tlbi_token;
    logic tlbi_all_valid;

    logic source_clear_valid;
    logic [SRC_LINE_W-1:0] source_clear_line_tag;
    logic source_events_ready;
    logic ctlw_remap_valid;
    logic [TGT_LINE_W-1:0] ctlw_remap_vline;
    logic [TOKEN_W-1:0] ctlw_remap_token;
    logic ctlw_tlbi_token_valid;
    logic [TOKEN_W-1:0] ctlw_tlbi_token;
    logic ctlw_tlbi_all_valid;
    logic dmp_revocation_hold;
    logic overflow_sticky;
    logic [COUNT_W-1:0] queued_count;

    logic [SRC_LINE_W-1:0] sb_queue [DEPTH];
    int sb_count;
    logic sb_overflow;

    int errors;
    int dma_seen;
    int chi_seen;
    int io_seen;
    int triple_burst_seen;
    int hold_seen;
    int remap_seen;
    int tlbi_token_seen;
    int tlbi_all_seen;
    int ready_low_seen;
    int overflow_seen;
    int random_cycles;

    copper_sari_revoker #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .DEPTH(DEPTH),
        .COUNT_W(COUNT_W)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .dma_write_valid(dma_write_valid),
        .dma_line_tag(dma_line_tag),
        .chi_snoop_valid(chi_snoop_valid),
        .chi_snoop_write(chi_snoop_write),
        .chi_snoop_invalidate(chi_snoop_invalidate),
        .chi_line_tag(chi_line_tag),
        .io_write_valid(io_write_valid),
        .io_line_tag(io_line_tag),
        .target_remap_valid(target_remap_valid),
        .target_remap_vline(target_remap_vline),
        .target_remap_token(target_remap_token),
        .tlbi_token_valid(tlbi_token_valid),
        .tlbi_token(tlbi_token),
        .tlbi_all_valid(tlbi_all_valid),
        .source_clear_valid(source_clear_valid),
        .source_clear_line_tag(source_clear_line_tag),
        .source_events_ready(source_events_ready),
        .ctlw_remap_valid(ctlw_remap_valid),
        .ctlw_remap_vline(ctlw_remap_vline),
        .ctlw_remap_token(ctlw_remap_token),
        .ctlw_tlbi_token_valid(ctlw_tlbi_token_valid),
        .ctlw_tlbi_token(ctlw_tlbi_token),
        .ctlw_tlbi_all_valid(ctlw_tlbi_all_valid),
        .dmp_revocation_hold(dmp_revocation_hold),
        .overflow_sticky(overflow_sticky),
        .queued_count(queued_count)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    function automatic logic source_event_chi;
        source_event_chi = chi_snoop_valid && (chi_snoop_write || chi_snoop_invalidate);
    endfunction

    function automatic logic incoming_source_event;
        incoming_source_event = dma_write_valid || source_event_chi() || io_write_valid;
    endfunction

    function automatic logic incoming_target_event;
        incoming_target_event = target_remap_valid || tlbi_token_valid || tlbi_all_valid;
    endfunction

    task automatic clear_inputs;
        begin
            dma_write_valid = 1'b0;
            dma_line_tag = '0;
            chi_snoop_valid = 1'b0;
            chi_snoop_write = 1'b0;
            chi_snoop_invalidate = 1'b0;
            chi_line_tag = '0;
            io_write_valid = 1'b0;
            io_line_tag = '0;
            target_remap_valid = 1'b0;
            target_remap_vline = '0;
            target_remap_token = '0;
            tlbi_token_valid = 1'b0;
            tlbi_token = '0;
            tlbi_all_valid = 1'b0;
        end
    endtask

    task automatic sb_reset;
        begin
            sb_count = 0;
            sb_overflow = 1'b0;
            for (int i = 0; i < DEPTH; i++) begin
                sb_queue[i] = '0;
            end
        end
    endtask

    task automatic sb_push(input logic [SRC_LINE_W-1:0] tag);
        begin
            if (sb_count < DEPTH) begin
                sb_queue[sb_count] = tag;
                sb_count++;
            end else begin
                sb_overflow = 1'b1;
            end
        end
    endtask

    task automatic sb_update;
        begin
            if (sb_count > 0) begin
                for (int i = 0; i < DEPTH - 1; i++) begin
                    sb_queue[i] = sb_queue[i + 1];
                end
                sb_queue[DEPTH - 1] = '0;
                sb_count--;
            end
            if (dma_write_valid) sb_push(dma_line_tag);
            if (source_event_chi()) sb_push(chi_line_tag);
            if (io_write_valid) sb_push(io_line_tag);
        end
    endtask

    task automatic check_outputs(input string label);
        logic exp_clear_valid;
        logic [SRC_LINE_W-1:0] exp_clear_tag;
        logic exp_ready;
        logic exp_hold;
        int exp_space;
        begin
            #1;
            exp_clear_valid = sb_count != 0;
            exp_clear_tag = exp_clear_valid ? sb_queue[0] : '0;
            exp_space = DEPTH - sb_count + ((sb_count != 0) ? 1 : 0);
            exp_ready = exp_space >= 3;
            exp_hold = sb_overflow || (sb_count != 0) || incoming_source_event() || incoming_target_event();

            if (source_clear_valid !== exp_clear_valid) begin
                $error("%s: clear_valid expected %0b got %0b", label, exp_clear_valid, source_clear_valid);
                errors++;
            end
            if (source_clear_line_tag !== exp_clear_tag) begin
                $error("%s: clear_tag expected %0h got %0h", label, exp_clear_tag, source_clear_line_tag);
                errors++;
            end
            if (source_events_ready !== exp_ready) begin
                $error("%s: ready expected %0b got %0b", label, exp_ready, source_events_ready);
                errors++;
            end
            if (dmp_revocation_hold !== exp_hold) begin
                $error("%s: hold expected %0b got %0b", label, exp_hold, dmp_revocation_hold);
                errors++;
            end
            if (queued_count !== COUNT_W'(sb_count)) begin
                $error("%s: count expected %0d got %0d", label, sb_count, queued_count);
                errors++;
            end
            if (overflow_sticky !== sb_overflow) begin
                $error("%s: overflow expected %0b got %0b", label, sb_overflow, overflow_sticky);
                errors++;
            end
            if (ctlw_remap_valid !== target_remap_valid
                || ctlw_remap_vline !== target_remap_vline
                || ctlw_remap_token !== target_remap_token) begin
                $error("%s: remap pass-through mismatch", label);
                errors++;
            end
            if (ctlw_tlbi_token_valid !== tlbi_token_valid || ctlw_tlbi_token !== tlbi_token) begin
                $error("%s: TLBI token pass-through mismatch", label);
                errors++;
            end
            if (ctlw_tlbi_all_valid !== tlbi_all_valid) begin
                $error("%s: TLBI-all pass-through mismatch", label);
                errors++;
            end

            if (dmp_revocation_hold) hold_seen++;
            if (!source_events_ready) ready_low_seen++;
            if (overflow_sticky) overflow_seen++;
        end
    endtask

    task automatic step_cycle(input string label);
        begin
            check_outputs(label);
            @(posedge clk);
            sb_update();
            #1;
        end
    endtask

    task automatic drain_queue(input string label);
        begin
            clear_inputs();
            while (sb_count != 0) begin
                step_cycle(label);
            end
            step_cycle({label, "_empty"});
        end
    endtask

    task automatic reset_dut;
        begin
            clear_inputs();
            sb_reset();
            rst_n = 1'b0;
            repeat (3) @(posedge clk);
            rst_n = 1'b1;
            @(posedge clk);
            #1;
        end
    endtask

    task automatic directed_tests;
        begin
            dma_write_valid = 1'b1;
            dma_line_tag = 8'h12;
            step_cycle("dma immediate hold");
            dma_seen++;
            drain_queue("dma drain");

            chi_snoop_valid = 1'b1;
            chi_snoop_write = 1'b1;
            chi_line_tag = 8'h34;
            step_cycle("chi write immediate hold");
            chi_seen++;
            drain_queue("chi drain");

            io_write_valid = 1'b1;
            io_line_tag = 8'h56;
            step_cycle("io write immediate hold");
            io_seen++;
            drain_queue("io drain");

            dma_write_valid = 1'b1;
            dma_line_tag = 8'ha1;
            chi_snoop_valid = 1'b1;
            chi_snoop_invalidate = 1'b1;
            chi_line_tag = 8'ha2;
            io_write_valid = 1'b1;
            io_line_tag = 8'ha3;
            step_cycle("triple source burst");
            triple_burst_seen++;
            drain_queue("triple drain");

            target_remap_valid = 1'b1;
            target_remap_vline = 12'h234;
            target_remap_token = 4'h5;
            step_cycle("target remap pass through");
            remap_seen++;
            clear_inputs();
            step_cycle("target remap clear");

            tlbi_token_valid = 1'b1;
            tlbi_token = 4'h7;
            step_cycle("tlbi token pass through");
            tlbi_token_seen++;
            clear_inputs();
            step_cycle("tlbi token clear");

            tlbi_all_valid = 1'b1;
            step_cycle("tlbi all pass through");
            tlbi_all_seen++;
            clear_inputs();
            step_cycle("tlbi all clear");

            for (int i = 0; i < 6; i++) begin
                dma_write_valid = 1'b1;
                dma_line_tag = 8'h80 + i[7:0];
                chi_snoop_valid = 1'b1;
                chi_snoop_write = 1'b1;
                chi_line_tag = 8'h90 + i[7:0];
                io_write_valid = 1'b1;
                io_line_tag = 8'ha0 + i[7:0];
                step_cycle($sformatf("overflow fill %0d", i));
            end
            clear_inputs();
            step_cycle("overflow sticky visible");
            if (!overflow_sticky) begin
                $error("overflow scenario did not assert overflow_sticky");
                errors++;
            end
            overflow_seen++;
            reset_dut();
        end
    endtask

    task automatic random_tests;
        begin
            for (int trial = 0; trial < TRIALS; trial++) begin
                clear_inputs();
                dma_write_valid = ($urandom_range(0, 99) < 18);
                dma_line_tag = $urandom_range(0, 255);
                chi_snoop_valid = ($urandom_range(0, 99) < 22);
                chi_snoop_write = ($urandom_range(0, 1) == 0);
                chi_snoop_invalidate = ($urandom_range(0, 3) == 0);
                chi_line_tag = $urandom_range(0, 255);
                io_write_valid = ($urandom_range(0, 99) < 12);
                io_line_tag = $urandom_range(0, 255);
                target_remap_valid = ($urandom_range(0, 199) == 0);
                target_remap_vline = $urandom_range(0, 4095);
                target_remap_token = $urandom_range(0, 15);
                tlbi_token_valid = ($urandom_range(0, 251) == 0);
                tlbi_token = $urandom_range(0, 15);
                tlbi_all_valid = ($urandom_range(0, 503) == 0);
                step_cycle($sformatf("random_%0d", trial));
                random_cycles++;
            end
        end
    endtask

    initial begin
        errors = 0;
        dma_seen = 0;
        chi_seen = 0;
        io_seen = 0;
        triple_burst_seen = 0;
        hold_seen = 0;
        remap_seen = 0;
        tlbi_token_seen = 0;
        tlbi_all_seen = 0;
        ready_low_seen = 0;
        overflow_seen = 0;
        random_cycles = 0;

        reset_dut();
        directed_tests();
        random_tests();

        if (
            errors != 0
            || dma_seen == 0
            || chi_seen == 0
            || io_seen == 0
            || triple_burst_seen == 0
            || hold_seen == 0
            || remap_seen == 0
            || tlbi_token_seen == 0
            || tlbi_all_seen == 0
            || ready_low_seen == 0
            || overflow_seen == 0
            || random_cycles != TRIALS
        ) begin
            $fatal(
                1,
                "COPPER SARI coverage failed: errors=%0d dma=%0d chi=%0d io=%0d triple=%0d hold=%0d remap=%0d tlbi_token=%0d tlbi_all=%0d ready_low=%0d overflow=%0d random=%0d",
                errors,
                dma_seen,
                chi_seen,
                io_seen,
                triple_burst_seen,
                hold_seen,
                remap_seen,
                tlbi_token_seen,
                tlbi_all_seen,
                ready_low_seen,
                overflow_seen,
                random_cycles
            );
        end

        $display(
            "COPPER SARI revoker tests completed: directed=8 random=%0d dma=%0d chi=%0d io=%0d triple_burst=%0d hold=%0d remap=%0d tlbi_token=%0d tlbi_all=%0d ready_low=%0d overflow=%0d final_queue=%0d errors=%0d",
            TRIALS,
            dma_seen,
            chi_seen,
            io_seen,
            triple_burst_seen,
            hold_seen,
            remap_seen,
            tlbi_token_seen,
            tlbi_all_seen,
            ready_low_seen,
            overflow_seen,
            queued_count,
            errors
        );
        $finish;
    end

endmodule
