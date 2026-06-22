`timescale 1ns/1ps

module copper_amba_sari_frontdoor_tb;

    localparam int SRC_LINE_W = 8;
    localparam int TGT_LINE_W = 12;
    localparam int TOKEN_W = 4;
    localparam int CHI_KIND_W = 3;
    localparam int DVM_KIND_W = 2;
    localparam int TRIALS = 10000;

    localparam logic [CHI_KIND_W-1:0] CHI_READ_SHARED       = CHI_KIND_W'(3'd0);
    localparam logic [CHI_KIND_W-1:0] CHI_READ_UNIQUE       = CHI_KIND_W'(3'd1);
    localparam logic [CHI_KIND_W-1:0] CHI_CLEAN_INVALIDATE  = CHI_KIND_W'(3'd2);
    localparam logic [CHI_KIND_W-1:0] CHI_MAKE_INVALID      = CHI_KIND_W'(3'd3);
    localparam logic [CHI_KIND_W-1:0] CHI_WRITEBACK_DIRTY   = CHI_KIND_W'(3'd4);
    localparam logic [CHI_KIND_W-1:0] CHI_DVM               = CHI_KIND_W'(3'd5);

    localparam logic [DVM_KIND_W-1:0] DVM_NONE       = DVM_KIND_W'(2'd0);
    localparam logic [DVM_KIND_W-1:0] DVM_TLBI_TOKEN = DVM_KIND_W'(2'd1);
    localparam logic [DVM_KIND_W-1:0] DVM_TLBI_ALL   = DVM_KIND_W'(2'd2);

    logic sari_source_events_ready;
    logic dma_write_valid;
    logic [SRC_LINE_W-1:0] dma_line_tag;
    logic chi_event_valid;
    logic [CHI_KIND_W-1:0] chi_event_kind;
    logic [SRC_LINE_W-1:0] chi_line_tag;
    logic io_write_valid;
    logic [SRC_LINE_W-1:0] io_line_tag;
    logic target_remap_valid;
    logic [TGT_LINE_W-1:0] target_remap_vline;
    logic [TOKEN_W-1:0] target_remap_token;
    logic dvm_valid;
    logic [DVM_KIND_W-1:0] dvm_kind;
    logic [TOKEN_W-1:0] dvm_token;

    logic sari_dma_write_valid;
    logic [SRC_LINE_W-1:0] sari_dma_line_tag;
    logic sari_chi_snoop_valid;
    logic sari_chi_snoop_write;
    logic sari_chi_snoop_invalidate;
    logic [SRC_LINE_W-1:0] sari_chi_line_tag;
    logic sari_io_write_valid;
    logic [SRC_LINE_W-1:0] sari_io_line_tag;
    logic sari_target_remap_valid;
    logic [TGT_LINE_W-1:0] sari_target_remap_vline;
    logic [TOKEN_W-1:0] sari_target_remap_token;
    logic sari_tlbi_token_valid;
    logic [TOKEN_W-1:0] sari_tlbi_token;
    logic sari_tlbi_all_valid;
    logic frontdoor_ready;
    logic dmp_frontdoor_hold;
    logic decoded_source_event;
    logic decoded_target_event;
    logic source_backpressure;

    logic exp_chi_write;
    logic exp_chi_invalidate;
    logic exp_chi_source_event;
    logic exp_tlbi_token;
    logic exp_tlbi_all;
    logic exp_source_event;
    logic exp_target_event;
    logic exp_backpressure;

    int errors;
    int read_only_seen;
    int read_unique_seen;
    int clean_inv_seen;
    int make_inv_seen;
    int writeback_seen;
    int dma_seen;
    int io_seen;
    int triple_accept_seen;
    int remap_seen;
    int dvm_token_seen;
    int dvm_all_seen;
    int backpressure_seen;
    int hold_seen;
    int random_source_seen;
    int random_target_seen;

    copper_amba_sari_frontdoor #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .CHI_KIND_W(CHI_KIND_W),
        .DVM_KIND_W(DVM_KIND_W)
    ) dut (
        .sari_source_events_ready(sari_source_events_ready),
        .dma_write_valid(dma_write_valid),
        .dma_line_tag(dma_line_tag),
        .chi_event_valid(chi_event_valid),
        .chi_event_kind(chi_event_kind),
        .chi_line_tag(chi_line_tag),
        .io_write_valid(io_write_valid),
        .io_line_tag(io_line_tag),
        .target_remap_valid(target_remap_valid),
        .target_remap_vline(target_remap_vline),
        .target_remap_token(target_remap_token),
        .dvm_valid(dvm_valid),
        .dvm_kind(dvm_kind),
        .dvm_token(dvm_token),
        .sari_dma_write_valid(sari_dma_write_valid),
        .sari_dma_line_tag(sari_dma_line_tag),
        .sari_chi_snoop_valid(sari_chi_snoop_valid),
        .sari_chi_snoop_write(sari_chi_snoop_write),
        .sari_chi_snoop_invalidate(sari_chi_snoop_invalidate),
        .sari_chi_line_tag(sari_chi_line_tag),
        .sari_io_write_valid(sari_io_write_valid),
        .sari_io_line_tag(sari_io_line_tag),
        .sari_target_remap_valid(sari_target_remap_valid),
        .sari_target_remap_vline(sari_target_remap_vline),
        .sari_target_remap_token(sari_target_remap_token),
        .sari_tlbi_token_valid(sari_tlbi_token_valid),
        .sari_tlbi_token(sari_tlbi_token),
        .sari_tlbi_all_valid(sari_tlbi_all_valid),
        .frontdoor_ready(frontdoor_ready),
        .dmp_frontdoor_hold(dmp_frontdoor_hold),
        .decoded_source_event(decoded_source_event),
        .decoded_target_event(decoded_target_event),
        .source_backpressure(source_backpressure)
    );

    always_comb begin
        exp_chi_write = 1'b0;
        exp_chi_invalidate = 1'b0;
        unique case (chi_event_kind)
            CHI_READ_SHARED: begin
                exp_chi_write = 1'b0;
                exp_chi_invalidate = 1'b0;
            end
            CHI_READ_UNIQUE: begin
                exp_chi_write = 1'b1;
                exp_chi_invalidate = 1'b0;
            end
            CHI_CLEAN_INVALIDATE: begin
                exp_chi_write = 1'b0;
                exp_chi_invalidate = 1'b1;
            end
            CHI_MAKE_INVALID: begin
                exp_chi_write = 1'b0;
                exp_chi_invalidate = 1'b1;
            end
            CHI_WRITEBACK_DIRTY: begin
                exp_chi_write = 1'b1;
                exp_chi_invalidate = 1'b0;
            end
            default: begin
                exp_chi_write = 1'b0;
                exp_chi_invalidate = 1'b0;
            end
        endcase

        exp_chi_source_event =
            chi_event_valid
            && (exp_chi_write || exp_chi_invalidate);
        exp_tlbi_token =
            dvm_valid
            && (
                (dvm_kind == DVM_TLBI_TOKEN)
                || (chi_event_valid && (chi_event_kind == CHI_DVM) && (dvm_kind == DVM_TLBI_TOKEN))
            );
        exp_tlbi_all =
            dvm_valid
            && (
                (dvm_kind == DVM_TLBI_ALL)
                || (chi_event_valid && (chi_event_kind == CHI_DVM) && (dvm_kind == DVM_TLBI_ALL))
            );
        exp_source_event =
            dma_write_valid
            || exp_chi_source_event
            || io_write_valid;
        exp_target_event =
            target_remap_valid
            || exp_tlbi_token
            || exp_tlbi_all;
        exp_backpressure =
            exp_source_event
            && !sari_source_events_ready;
    end

    task automatic clear_inputs;
        begin
            sari_source_events_ready = 1'b1;
            dma_write_valid = 1'b0;
            dma_line_tag = '0;
            chi_event_valid = 1'b0;
            chi_event_kind = '0;
            chi_line_tag = '0;
            io_write_valid = 1'b0;
            io_line_tag = '0;
            target_remap_valid = 1'b0;
            target_remap_vline = '0;
            target_remap_token = '0;
            dvm_valid = 1'b0;
            dvm_kind = '0;
            dvm_token = '0;
        end
    endtask

    task automatic check_outputs(input string label, input bit is_random);
        begin
            #1;
            if (decoded_source_event !== exp_source_event) begin
                $error("%s: decoded_source expected %0b got %0b", label, exp_source_event, decoded_source_event);
                errors++;
            end
            if (decoded_target_event !== exp_target_event) begin
                $error("%s: decoded_target expected %0b got %0b", label, exp_target_event, decoded_target_event);
                errors++;
            end
            if (source_backpressure !== exp_backpressure) begin
                $error("%s: backpressure expected %0b got %0b", label, exp_backpressure, source_backpressure);
                errors++;
            end
            if (frontdoor_ready !== !exp_backpressure) begin
                $error("%s: ready expected %0b got %0b", label, !exp_backpressure, frontdoor_ready);
                errors++;
            end
            if (dmp_frontdoor_hold !== (exp_source_event || exp_target_event)) begin
                $error("%s: hold expected %0b got %0b", label, exp_source_event || exp_target_event, dmp_frontdoor_hold);
                errors++;
            end
            if (sari_dma_write_valid !== (dma_write_valid && sari_source_events_ready)) begin
                $error("%s: dma valid mismatch", label);
                errors++;
            end
            if (sari_dma_line_tag !== dma_line_tag) begin
                $error("%s: dma tag mismatch", label);
                errors++;
            end
            if (sari_chi_snoop_valid !== (exp_chi_source_event && sari_source_events_ready)) begin
                $error("%s: chi valid mismatch", label);
                errors++;
            end
            if (sari_chi_snoop_write !== exp_chi_write) begin
                $error("%s: chi write mismatch", label);
                errors++;
            end
            if (sari_chi_snoop_invalidate !== exp_chi_invalidate) begin
                $error("%s: chi invalidate mismatch", label);
                errors++;
            end
            if (sari_chi_line_tag !== chi_line_tag) begin
                $error("%s: chi tag mismatch", label);
                errors++;
            end
            if (sari_io_write_valid !== (io_write_valid && sari_source_events_ready)) begin
                $error("%s: io valid mismatch", label);
                errors++;
            end
            if (sari_io_line_tag !== io_line_tag) begin
                $error("%s: io tag mismatch", label);
                errors++;
            end
            if (sari_target_remap_valid !== target_remap_valid
                || sari_target_remap_vline !== target_remap_vline
                || sari_target_remap_token !== target_remap_token) begin
                $error("%s: remap mismatch", label);
                errors++;
            end
            if (sari_tlbi_token_valid !== exp_tlbi_token || sari_tlbi_token !== dvm_token) begin
                $error("%s: dvm token mismatch", label);
                errors++;
            end
            if (sari_tlbi_all_valid !== exp_tlbi_all) begin
                $error("%s: dvm all mismatch", label);
                errors++;
            end

            if (chi_event_valid && chi_event_kind == CHI_READ_SHARED && !decoded_source_event && !decoded_target_event) read_only_seen++;
            if (chi_event_valid && chi_event_kind == CHI_READ_UNIQUE && decoded_source_event) read_unique_seen++;
            if (chi_event_valid && chi_event_kind == CHI_CLEAN_INVALIDATE && decoded_source_event) clean_inv_seen++;
            if (chi_event_valid && chi_event_kind == CHI_MAKE_INVALID && decoded_source_event) make_inv_seen++;
            if (chi_event_valid && chi_event_kind == CHI_WRITEBACK_DIRTY && decoded_source_event) writeback_seen++;
            if (dma_write_valid && sari_dma_write_valid) dma_seen++;
            if (io_write_valid && sari_io_write_valid) io_seen++;
            if (dma_write_valid && exp_chi_source_event && io_write_valid && sari_source_events_ready
                && sari_dma_write_valid && sari_chi_snoop_valid && sari_io_write_valid) triple_accept_seen++;
            if (target_remap_valid && sari_target_remap_valid) remap_seen++;
            if (exp_tlbi_token && sari_tlbi_token_valid) dvm_token_seen++;
            if (exp_tlbi_all && sari_tlbi_all_valid) dvm_all_seen++;
            if (source_backpressure) backpressure_seen++;
            if (dmp_frontdoor_hold) hold_seen++;
            if (is_random && decoded_source_event) random_source_seen++;
            if (is_random && decoded_target_event) random_target_seen++;
        end
    endtask

    task automatic directed_tests;
        begin
            clear_inputs();
            chi_event_valid = 1'b1;
            chi_event_kind = CHI_READ_SHARED;
            chi_line_tag = 8'h11;
            check_outputs("read-only chi no revocation", 1'b0);

            clear_inputs();
            chi_event_valid = 1'b1;
            chi_event_kind = CHI_READ_UNIQUE;
            chi_line_tag = 8'h12;
            check_outputs("read-unique chi source write", 1'b0);

            clear_inputs();
            chi_event_valid = 1'b1;
            chi_event_kind = CHI_CLEAN_INVALIDATE;
            chi_line_tag = 8'h13;
            check_outputs("clean-invalidate chi source invalidate", 1'b0);

            clear_inputs();
            chi_event_valid = 1'b1;
            chi_event_kind = CHI_MAKE_INVALID;
            chi_line_tag = 8'h14;
            check_outputs("make-invalid chi source invalidate", 1'b0);

            clear_inputs();
            chi_event_valid = 1'b1;
            chi_event_kind = CHI_WRITEBACK_DIRTY;
            chi_line_tag = 8'h15;
            check_outputs("dirty writeback chi source write", 1'b0);

            clear_inputs();
            dma_write_valid = 1'b1;
            dma_line_tag = 8'h22;
            chi_event_valid = 1'b1;
            chi_event_kind = CHI_CLEAN_INVALIDATE;
            chi_line_tag = 8'h23;
            io_write_valid = 1'b1;
            io_line_tag = 8'h24;
            check_outputs("three source lanes accepted", 1'b0);

            clear_inputs();
            sari_source_events_ready = 1'b0;
            dma_write_valid = 1'b1;
            dma_line_tag = 8'h32;
            check_outputs("source backpressure holds without output", 1'b0);

            clear_inputs();
            target_remap_valid = 1'b1;
            target_remap_vline = 12'h456;
            target_remap_token = 4'ha;
            check_outputs("target remap pass-through", 1'b0);

            clear_inputs();
            dvm_valid = 1'b1;
            dvm_kind = DVM_TLBI_TOKEN;
            dvm_token = 4'hb;
            check_outputs("dvm token tlbi pass-through", 1'b0);

            clear_inputs();
            chi_event_valid = 1'b1;
            chi_event_kind = CHI_DVM;
            dvm_valid = 1'b1;
            dvm_kind = DVM_TLBI_ALL;
            dvm_token = 4'hc;
            check_outputs("chi-carried dvm all tlbi pass-through", 1'b0);
        end
    endtask

    task automatic random_test(input int trial);
        int r;
        begin
            clear_inputs();
            r = $urandom();
            sari_source_events_ready = (trial % 11) != 0;
            dma_write_valid = (r[3:0] < 4);
            dma_line_tag = $urandom_range(0, (1 << SRC_LINE_W) - 1);
            chi_event_valid = (r[7:4] < 8);
            chi_event_kind = $urandom_range(0, 6);
            chi_line_tag = $urandom_range(0, (1 << SRC_LINE_W) - 1);
            io_write_valid = (r[11:8] < 4);
            io_line_tag = $urandom_range(0, (1 << SRC_LINE_W) - 1);
            target_remap_valid = (trial % 17) == 0;
            target_remap_vline = $urandom_range(0, (1 << TGT_LINE_W) - 1);
            target_remap_token = $urandom_range(0, (1 << TOKEN_W) - 1);
            dvm_valid = (trial % 19) == 0;
            dvm_kind = $urandom_range(0, 2);
            dvm_token = $urandom_range(0, (1 << TOKEN_W) - 1);
            check_outputs($sformatf("random_%0d", trial), 1'b1);
        end
    endtask

    initial begin
        errors = 0;
        read_only_seen = 0;
        read_unique_seen = 0;
        clean_inv_seen = 0;
        make_inv_seen = 0;
        writeback_seen = 0;
        dma_seen = 0;
        io_seen = 0;
        triple_accept_seen = 0;
        remap_seen = 0;
        dvm_token_seen = 0;
        dvm_all_seen = 0;
        backpressure_seen = 0;
        hold_seen = 0;
        random_source_seen = 0;
        random_target_seen = 0;

        directed_tests();
        for (int trial = 0; trial < TRIALS; trial++) begin
            random_test(trial);
        end

        if (
            errors != 0
            || read_only_seen == 0
            || read_unique_seen == 0
            || clean_inv_seen == 0
            || make_inv_seen == 0
            || writeback_seen == 0
            || dma_seen == 0
            || io_seen == 0
            || triple_accept_seen == 0
            || remap_seen == 0
            || dvm_token_seen == 0
            || dvm_all_seen == 0
            || backpressure_seen == 0
            || hold_seen == 0
            || random_source_seen == 0
            || random_target_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER AMBA-SARI frontdoor coverage failed: errors=%0d read_only=%0d read_unique=%0d clean_inv=%0d make_inv=%0d writeback=%0d dma=%0d io=%0d triple=%0d remap=%0d dvm_token=%0d dvm_all=%0d backpressure=%0d hold=%0d random_source=%0d random_target=%0d",
                errors,
                read_only_seen,
                read_unique_seen,
                clean_inv_seen,
                make_inv_seen,
                writeback_seen,
                dma_seen,
                io_seen,
                triple_accept_seen,
                remap_seen,
                dvm_token_seen,
                dvm_all_seen,
                backpressure_seen,
                hold_seen,
                random_source_seen,
                random_target_seen
            );
        end

        $display(
            "COPPER AMBA-SARI frontdoor completed: directed=10 random=%0d read_only=%0d read_unique=%0d clean_inv=%0d make_inv=%0d writeback=%0d dma=%0d io=%0d triple=%0d remap=%0d dvm_token=%0d dvm_all=%0d backpressure=%0d hold=%0d random_source=%0d random_target=%0d errors=%0d",
            TRIALS,
            read_only_seen,
            read_unique_seen,
            clean_inv_seen,
            make_inv_seen,
            writeback_seen,
            dma_seen,
            io_seen,
            triple_accept_seen,
            remap_seen,
            dvm_token_seen,
            dvm_all_seen,
            backpressure_seen,
            hold_seen,
            random_source_seen,
            random_target_seen,
            errors
        );
        $finish;
    end

endmodule
