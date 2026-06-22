`timescale 1ns/1ps

module copper_ctlw_witness_dir_tb;

    localparam int VLINE_W = 12;
    localparam int PLINE_W = 12;
    localparam int TOKEN_W = 4;
    localparam int ENTRIES = 16;
    localparam int IDX_W = 4;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;
    logic started;

    logic record_valid;
    logic [VLINE_W-1:0] record_vline;
    logic [PLINE_W-1:0] record_pline;
    logic [TOKEN_W-1:0] record_token;
    logic remap_valid;
    logic [VLINE_W-1:0] remap_vline;
    logic [TOKEN_W-1:0] remap_token;
    logic tlbi_token_valid;
    logic [TOKEN_W-1:0] tlbi_token;
    logic tlbi_all_valid;
    logic query_valid;
    logic [VLINE_W-1:0] query_vline;
    logic [TOKEN_W-1:0] query_token;

    logic witness_valid;
    logic [PLINE_W-1:0] witness_pline;
    logic query_miss;
    logic token_mismatch_seen;
    logic line_mismatch_seen;
    logic remap_clear_hit;
    logic tlbi_clear_hit;
    logic collision_evict;

    logic shadow_valid [ENTRIES];
    logic [VLINE_W-1:0] shadow_vline [ENTRIES];
    logic [PLINE_W-1:0] shadow_pline [ENTRIES];
    logic [TOKEN_W-1:0] shadow_token [ENTRIES];

    logic exp_witness_valid;
    logic [PLINE_W-1:0] exp_witness_pline;
    logic exp_query_miss;
    logic exp_token_mismatch_seen;
    logic exp_line_mismatch_seen;
    logic exp_remap_clear_hit;
    logic exp_tlbi_clear_hit;
    logic exp_collision_evict;

    int errors;
    int exact_hit_seen;
    int miss_seen;
    int token_mismatch_seen_count;
    int line_mismatch_seen_count;
    int remap_clear_seen;
    int tlbi_token_clear_seen;
    int tlbi_all_clear_seen;
    int collision_seen;
    int stale_after_remap_block_seen;
    int stale_after_tlbi_block_seen;

    copper_ctlw_witness_dir #(
        .VLINE_W(VLINE_W),
        .PLINE_W(PLINE_W),
        .TOKEN_W(TOKEN_W),
        .ENTRIES(ENTRIES),
        .IDX_W(IDX_W)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .record_valid(record_valid),
        .record_vline(record_vline),
        .record_pline(record_pline),
        .record_token(record_token),
        .remap_valid(remap_valid),
        .remap_vline(remap_vline),
        .remap_token(remap_token),
        .tlbi_token_valid(tlbi_token_valid),
        .tlbi_token(tlbi_token),
        .tlbi_all_valid(tlbi_all_valid),
        .query_valid(query_valid),
        .query_vline(query_vline),
        .query_token(query_token),
        .witness_valid(witness_valid),
        .witness_pline(witness_pline),
        .query_miss(query_miss),
        .token_mismatch_seen(token_mismatch_seen),
        .line_mismatch_seen(line_mismatch_seen),
        .remap_clear_hit(remap_clear_hit),
        .tlbi_clear_hit(tlbi_clear_hit),
        .collision_evict(collision_evict)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    always_comb begin
        exp_witness_valid =
            query_valid
            && shadow_valid[query_vline[IDX_W-1:0]]
            && (shadow_vline[query_vline[IDX_W-1:0]] == query_vline)
            && (shadow_token[query_vline[IDX_W-1:0]] == query_token);

        exp_witness_pline = exp_witness_valid
            ? shadow_pline[query_vline[IDX_W-1:0]]
            : '0;

        exp_query_miss = query_valid && !exp_witness_valid;

        exp_token_mismatch_seen =
            query_valid
            && shadow_valid[query_vline[IDX_W-1:0]]
            && (shadow_vline[query_vline[IDX_W-1:0]] == query_vline)
            && (shadow_token[query_vline[IDX_W-1:0]] != query_token);

        exp_line_mismatch_seen =
            query_valid
            && shadow_valid[query_vline[IDX_W-1:0]]
            && (shadow_vline[query_vline[IDX_W-1:0]] != query_vline);

        exp_remap_clear_hit =
            remap_valid
            && shadow_valid[remap_vline[IDX_W-1:0]]
            && (shadow_vline[remap_vline[IDX_W-1:0]] == remap_vline)
            && (shadow_token[remap_vline[IDX_W-1:0]] == remap_token);

        exp_tlbi_clear_hit = 1'b0;
        for (int i = 0; i < ENTRIES; i++) begin
            if (shadow_valid[i] && (tlbi_all_valid || (tlbi_token_valid && shadow_token[i] == tlbi_token))) begin
                exp_tlbi_clear_hit = 1'b1;
            end
        end

        exp_collision_evict =
            record_valid
            && shadow_valid[record_vline[IDX_W-1:0]]
            && ((shadow_vline[record_vline[IDX_W-1:0]] != record_vline)
                || (shadow_token[record_vline[IDX_W-1:0]] != record_token));
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < ENTRIES; i++) begin
                shadow_valid[i] <= 1'b0;
                shadow_vline[i] <= '0;
                shadow_pline[i] <= '0;
                shadow_token[i] <= '0;
            end
        end else begin
            if (tlbi_all_valid) begin
                for (int i = 0; i < ENTRIES; i++) begin
                    shadow_valid[i] <= 1'b0;
                end
            end else begin
                if (tlbi_token_valid) begin
                    for (int i = 0; i < ENTRIES; i++) begin
                        if (shadow_valid[i] && shadow_token[i] == tlbi_token) begin
                            shadow_valid[i] <= 1'b0;
                        end
                    end
                end
                if (remap_valid
                    && shadow_valid[remap_vline[IDX_W-1:0]]
                    && (shadow_vline[remap_vline[IDX_W-1:0]] == remap_vline)
                    && (shadow_token[remap_vline[IDX_W-1:0]] == remap_token)) begin
                    shadow_valid[remap_vline[IDX_W-1:0]] <= 1'b0;
                end
                if (record_valid) begin
                    shadow_valid[record_vline[IDX_W-1:0]] <= 1'b1;
                    shadow_vline[record_vline[IDX_W-1:0]] <= record_vline;
                    shadow_pline[record_vline[IDX_W-1:0]] <= record_pline;
                    shadow_token[record_vline[IDX_W-1:0]] <= record_token;
                end
            end
        end
    end

    a_witness_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            witness_valid == exp_witness_valid);

    a_pline_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            witness_pline == exp_witness_pline);

    a_query_miss_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            query_miss == exp_query_miss);

    a_no_token_mismatch_hit:
        assert property (@(negedge clk) disable iff (!started)
            (query_valid && exp_token_mismatch_seen) |-> !witness_valid);

    a_no_line_mismatch_hit:
        assert property (@(negedge clk) disable iff (!started)
            (query_valid && exp_line_mismatch_seen) |-> !witness_valid);

    task automatic clear_inputs;
        begin
            record_valid = 1'b0;
            record_vline = '0;
            record_pline = '0;
            record_token = '0;
            remap_valid = 1'b0;
            remap_vline = '0;
            remap_token = '0;
            tlbi_token_valid = 1'b0;
            tlbi_token = '0;
            tlbi_all_valid = 1'b0;
            query_valid = 1'b0;
            query_vline = '0;
            query_token = '0;
        end
    endtask

    task automatic record_witness(
        input [VLINE_W-1:0] vline_i,
        input [PLINE_W-1:0] pline_i,
        input [TOKEN_W-1:0] token_i
    );
        begin
            clear_inputs();
            record_valid = 1'b1;
            record_vline = vline_i;
            record_pline = pline_i;
            record_token = token_i;
        end
    endtask

    task automatic query_witness(
        input [VLINE_W-1:0] vline_i,
        input [TOKEN_W-1:0] token_i
    );
        begin
            query_valid = 1'b1;
            query_vline = vline_i;
            query_token = token_i;
        end
    endtask

    task automatic step_and_check(input string label);
        begin
            #1;
            if (remap_clear_hit !== exp_remap_clear_hit) begin
                $error("%s: remap_clear_hit expected %0b got %0b", label, exp_remap_clear_hit, remap_clear_hit);
                errors++;
            end
            if (tlbi_clear_hit !== exp_tlbi_clear_hit) begin
                $error("%s: tlbi_clear_hit expected %0b got %0b", label, exp_tlbi_clear_hit, tlbi_clear_hit);
                errors++;
            end
            if (collision_evict !== exp_collision_evict) begin
                $error("%s: collision_evict expected %0b got %0b", label, exp_collision_evict, collision_evict);
                errors++;
            end
            if (remap_clear_hit) remap_clear_seen++;
            if (tlbi_clear_hit && tlbi_token_valid) tlbi_token_clear_seen++;
            if (tlbi_clear_hit && tlbi_all_valid) tlbi_all_clear_seen++;
            if (collision_evict) collision_seen++;

            @(posedge clk);
            #1;
            if (witness_valid !== exp_witness_valid) begin
                $error("%s: witness_valid expected %0b got %0b", label, exp_witness_valid, witness_valid);
                errors++;
            end
            if (witness_pline !== exp_witness_pline) begin
                $error("%s: witness_pline expected %0h got %0h", label, exp_witness_pline, witness_pline);
                errors++;
            end
            if (query_miss !== exp_query_miss) begin
                $error("%s: query_miss expected %0b got %0b", label, exp_query_miss, query_miss);
                errors++;
            end
            if (token_mismatch_seen !== exp_token_mismatch_seen) begin
                $error("%s: token mismatch expected %0b got %0b", label, exp_token_mismatch_seen, token_mismatch_seen);
                errors++;
            end
            if (line_mismatch_seen !== exp_line_mismatch_seen) begin
                $error("%s: line mismatch expected %0b got %0b", label, exp_line_mismatch_seen, line_mismatch_seen);
                errors++;
            end

            if (witness_valid) exact_hit_seen++;
            if (query_miss) miss_seen++;
            if (token_mismatch_seen) token_mismatch_seen_count++;
            if (line_mismatch_seen) line_mismatch_seen_count++;
        end
    endtask

    task automatic directed_tests;
        begin
            clear_inputs();
            query_witness(12'h123, 4'h1);
            step_and_check("unrecorded witness misses");

            record_witness(12'h123, 12'habc, 4'h1);
            query_witness(12'h123, 4'h1);
            step_and_check("exact witness allows");

            clear_inputs();
            query_witness(12'h123, 4'h2);
            step_and_check("token mismatch blocks");

            clear_inputs();
            query_witness(12'h133, 4'h1);
            step_and_check("same-index line mismatch blocks");

            clear_inputs();
            remap_valid = 1'b1;
            remap_vline = 12'h123;
            remap_token = 4'h1;
            query_witness(12'h123, 4'h1);
            step_and_check("remap clears exact witness");
            if (query_miss) stale_after_remap_block_seen++;

            record_witness(12'h234, 12'hbcd, 4'h4);
            query_witness(12'h234, 4'h4);
            step_and_check("setup token TLBI witness");

            clear_inputs();
            tlbi_token_valid = 1'b1;
            tlbi_token = 4'h4;
            query_witness(12'h234, 4'h4);
            step_and_check("token TLBI clears witness");
            if (query_miss) stale_after_tlbi_block_seen++;

            record_witness(12'h345, 12'hcde, 4'h5);
            query_witness(12'h345, 4'h5);
            step_and_check("setup TLBI all witness");

            clear_inputs();
            tlbi_all_valid = 1'b1;
            query_witness(12'h345, 4'h5);
            step_and_check("TLBI all clears witness");

            record_witness(12'h456, 12'h111, 4'h6);
            query_witness(12'h456, 4'h6);
            step_and_check("setup collision witness");

            record_witness(12'h466, 12'h222, 4'h6);
            query_witness(12'h456, 4'h6);
            step_and_check("direct-mapped collision evicts old witness");
        end
    endtask

    task automatic drive_random(input int trial);
        int r;
        logic [VLINE_W-1:0] base_vline;
        logic [TOKEN_W-1:0] base_token;
        begin
            clear_inputs();
            r = $urandom();
            base_vline = $urandom_range(0, (1 << VLINE_W) - 1);
            base_token = $urandom_range(0, (1 << TOKEN_W) - 1);

            record_valid = (r[3:0] < 7);
            record_vline = base_vline;
            record_pline = $urandom_range(0, (1 << PLINE_W) - 1);
            record_token = base_token;

            remap_valid = (trial % 31) == 0;
            remap_vline = (trial % 2) ? base_vline : query_vline;
            remap_token = base_token;

            tlbi_token_valid = (trial % 47) == 0;
            tlbi_token = base_token;
            tlbi_all_valid = (trial % 211) == 0;

            query_valid = (r[7:4] < 13);
            query_vline = (trial % 3) == 0
                ? base_vline
                : $urandom_range(0, (1 << VLINE_W) - 1);
            query_token = (trial % 11) == 0
                ? (base_token + 1'b1)
                : base_token;

            if ((trial % 19) == 0) begin
                record_valid = 1'b1;
                record_vline = 12'h5a5;
                record_pline = 12'h155;
                record_token = 4'h9;
                query_valid = 1'b1;
                query_vline = 12'h5a5;
                query_token = 4'h9;
            end

            step_and_check($sformatf("random_%0d", trial));
        end
    endtask

    initial begin
        errors = 0;
        exact_hit_seen = 0;
        miss_seen = 0;
        token_mismatch_seen_count = 0;
        line_mismatch_seen_count = 0;
        remap_clear_seen = 0;
        tlbi_token_clear_seen = 0;
        tlbi_all_clear_seen = 0;
        collision_seen = 0;
        stale_after_remap_block_seen = 0;
        stale_after_tlbi_block_seen = 0;

        started = 1'b0;
        clear_inputs();
        rst_n = 1'b0;
        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
        started = 1'b1;

        directed_tests();
        for (int trial = 0; trial < TRIALS; trial++) begin
            drive_random(trial);
        end

        if (
            errors != 0
            || exact_hit_seen == 0
            || miss_seen == 0
            || token_mismatch_seen_count == 0
            || line_mismatch_seen_count == 0
            || remap_clear_seen == 0
            || tlbi_token_clear_seen == 0
            || tlbi_all_clear_seen == 0
            || collision_seen == 0
            || stale_after_remap_block_seen == 0
            || stale_after_tlbi_block_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER CTLW witness directory coverage failed: errors=%0d exact=%0d miss=%0d token=%0d line=%0d remap=%0d tlbi_token=%0d tlbi_all=%0d collision=%0d stale_remap=%0d stale_tlbi=%0d",
                errors,
                exact_hit_seen,
                miss_seen,
                token_mismatch_seen_count,
                line_mismatch_seen_count,
                remap_clear_seen,
                tlbi_token_clear_seen,
                tlbi_all_clear_seen,
                collision_seen,
                stale_after_remap_block_seen,
                stale_after_tlbi_block_seen
            );
        end

        $display(
            "COPPER CTLW witness directory tests completed: directed=10 random=%0d exact_hit=%0d miss=%0d token_mismatch=%0d line_mismatch=%0d remap_clear=%0d tlbi_token_clear=%0d tlbi_all_clear=%0d collision=%0d stale_after_remap_block=%0d stale_after_tlbi_block=%0d errors=%0d",
            TRIALS,
            exact_hit_seen,
            miss_seen,
            token_mismatch_seen_count,
            line_mismatch_seen_count,
            remap_clear_seen,
            tlbi_token_clear_seen,
            tlbi_all_clear_seen,
            collision_seen,
            stale_after_remap_block_seen,
            stale_after_tlbi_block_seen,
            errors
        );
        $finish;
    end

endmodule
