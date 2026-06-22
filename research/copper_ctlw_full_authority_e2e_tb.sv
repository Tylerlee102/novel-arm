`timescale 1ns/1ps

// CTLW witness directory -> full-authority gate integration harness.
//
// The standalone CTLW directory proves exact witness lookup and invalidation.
// The full-authority gate proves the final allow predicate. This harness wires
// them together so cross-page DMP issue is opened only by a live exact CTLW
// directory hit for the current token.

module copper_ctlw_full_authority_e2e_tb;

    localparam int VALUE_W = 12;
    localparam int EPOCH_W = 4;
    localparam int TOKEN_W = 4;
    localparam int LINE_W = 12;
    localparam int ENTRIES = 16;
    localparam int IDX_W = 4;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;
    logic started;

    logic record_valid;
    logic [LINE_W-1:0] record_vline;
    logic [LINE_W-1:0] record_pline;
    logic [TOKEN_W-1:0] record_token;
    logic remap_valid;
    logic [LINE_W-1:0] remap_vline;
    logic [TOKEN_W-1:0] remap_token;
    logic tlbi_token_valid;
    logic [TOKEN_W-1:0] tlbi_token;
    logic tlbi_all_valid;

    logic dmp_seed_valid;
    logic source_valid;
    logic source_clean;
    logic [VALUE_W-1:0] source_value;
    logic [EPOCH_W-1:0] source_epoch;
    logic [TOKEN_W-1:0] current_token;
    logic proof_valid;
    logic proof_sound;
    logic [VALUE_W-1:0] proof_value;
    logic [EPOCH_W-1:0] proof_epoch;
    logic [TOKEN_W-1:0] proof_token;
    logic target_same_page;
    logic same_page_translation_ok;
    logic target_permission_ok;
    logic terminal_source;
    logic [LINE_W-1:0] candidate_target_line;

    logic ctlw_query_valid;
    logic ctlw_witness_valid;
    logic [LINE_W-1:0] ctlw_witness_pline;
    logic ctlw_query_miss;
    logic ctlw_token_mismatch_seen;
    logic ctlw_line_mismatch_seen;
    logic ctlw_remap_clear_hit;
    logic ctlw_tlbi_clear_hit;
    logic ctlw_collision_evict;

    logic source_authorized;
    logic target_authorized;
    logic dmp_seed_allow;
    logic dmp_seed_block;
    logic block_no_source_proof;
    logic block_stale_source;
    logic block_token_mismatch;
    logic block_terminal_source;
    logic block_no_target_authority;
    logic block_fault_or_perm;

    logic exp_source_authorized;
    logic exp_target_authorized;
    logic exp_allow;
    logic exp_block;

    int errors;
    int exact_cross_allow_seen;
    int no_witness_block_seen;
    int token_mismatch_block_seen;
    int line_mismatch_block_seen;
    int stale_after_remap_block_seen;
    int stale_after_tlbi_block_seen;
    int terminal_block_seen;
    int permission_block_seen;
    int stale_source_block_seen;
    int same_page_allow_seen;
    int random_allow_seen;
    int random_block_seen;
    int collision_seen;

    assign ctlw_query_valid = dmp_seed_valid && !target_same_page;

    copper_ctlw_witness_dir #(
        .VLINE_W(LINE_W),
        .PLINE_W(LINE_W),
        .TOKEN_W(TOKEN_W),
        .ENTRIES(ENTRIES),
        .IDX_W(IDX_W)
    ) ctlw_dir (
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
        .query_valid(ctlw_query_valid),
        .query_vline(candidate_target_line),
        .query_token(current_token),
        .witness_valid(ctlw_witness_valid),
        .witness_pline(ctlw_witness_pline),
        .query_miss(ctlw_query_miss),
        .token_mismatch_seen(ctlw_token_mismatch_seen),
        .line_mismatch_seen(ctlw_line_mismatch_seen),
        .remap_clear_hit(ctlw_remap_clear_hit),
        .tlbi_clear_hit(ctlw_tlbi_clear_hit),
        .collision_evict(ctlw_collision_evict)
    );

    copper_full_authority_gate #(
        .VALUE_W(VALUE_W),
        .EPOCH_W(EPOCH_W),
        .TOKEN_W(TOKEN_W),
        .LINE_W(LINE_W)
    ) authority_gate (
        .dmp_seed_valid(dmp_seed_valid),
        .source_valid(source_valid),
        .source_clean(source_clean),
        .source_value(source_value),
        .source_epoch(source_epoch),
        .current_token(current_token),
        .proof_valid(proof_valid),
        .proof_sound(proof_sound),
        .proof_value(proof_value),
        .proof_epoch(proof_epoch),
        .proof_token(proof_token),
        .target_same_page(target_same_page),
        .same_page_translation_ok(same_page_translation_ok),
        .target_permission_ok(target_permission_ok),
        .terminal_source(terminal_source),
        .candidate_target_line(candidate_target_line),
        .witness_valid(ctlw_witness_valid),
        .witness_target_line(ctlw_witness_valid ? candidate_target_line : '0),
        .witness_token(current_token),
        .source_authorized(source_authorized),
        .target_authorized(target_authorized),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block(dmp_seed_block),
        .block_no_source_proof(block_no_source_proof),
        .block_stale_source(block_stale_source),
        .block_token_mismatch(block_token_mismatch),
        .block_terminal_source(block_terminal_source),
        .block_no_target_authority(block_no_target_authority),
        .block_fault_or_perm(block_fault_or_perm)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    always_comb begin
        exp_source_authorized =
            source_valid
            && source_clean
            && proof_valid
            && proof_sound
            && (proof_value == source_value)
            && (proof_epoch == source_epoch)
            && (proof_token == current_token);

        exp_target_authorized = target_same_page
            ? same_page_translation_ok
            : ctlw_witness_valid;

        exp_allow =
            dmp_seed_valid
            && exp_source_authorized
            && !terminal_source
            && exp_target_authorized
            && target_permission_ok;

        exp_block = dmp_seed_valid && !exp_allow;
    end

    a_allow_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_allow == exp_allow);

    a_block_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_block == exp_block);

    a_cross_page_requires_ctlw_hit:
        assert property (@(negedge clk) disable iff (!started)
            (dmp_seed_allow && !target_same_page) |-> ctlw_witness_valid);

    a_ctlw_miss_blocks_target:
        assert property (@(negedge clk) disable iff (!started)
            (dmp_seed_valid && !target_same_page && exp_source_authorized && !terminal_source
             && !ctlw_witness_valid) |-> block_no_target_authority);

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

            dmp_seed_valid = 1'b0;
            source_valid = 1'b1;
            source_clean = 1'b1;
            source_value = 12'h123;
            source_epoch = 4'h5;
            current_token = 4'h1;
            proof_valid = 1'b1;
            proof_sound = 1'b1;
            proof_value = 12'h123;
            proof_epoch = 4'h5;
            proof_token = 4'h1;
            target_same_page = 1'b0;
            same_page_translation_ok = 1'b1;
            target_permission_ok = 1'b1;
            terminal_source = 1'b0;
            candidate_target_line = 12'h234;
        end
    endtask

    task automatic set_source_token(input [TOKEN_W-1:0] token);
        begin
            current_token = token;
            proof_token = token;
        end
    endtask

    task automatic record_witness(
        input [LINE_W-1:0] vline_i,
        input [LINE_W-1:0] pline_i,
        input [TOKEN_W-1:0] token_i
    );
        begin
            clear_inputs();
            record_valid = 1'b1;
            record_vline = vline_i;
            record_pline = pline_i;
            record_token = token_i;
            #1;
            if (ctlw_collision_evict) collision_seen++;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic apply_remap(input [LINE_W-1:0] vline_i, input [TOKEN_W-1:0] token_i);
        begin
            clear_inputs();
            remap_valid = 1'b1;
            remap_vline = vline_i;
            remap_token = token_i;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic apply_tlbi_token(input [TOKEN_W-1:0] token_i);
        begin
            clear_inputs();
            tlbi_token_valid = 1'b1;
            tlbi_token = token_i;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic sample_case(input string label);
        begin
            #1;
            if (dmp_seed_allow !== exp_allow) begin
                $error("%s: allow expected %0b got %0b", label, exp_allow, dmp_seed_allow);
                errors++;
            end
            if (dmp_seed_block !== exp_block) begin
                $error("%s: block expected %0b got %0b", label, exp_block, dmp_seed_block);
                errors++;
            end
            if (dmp_seed_allow && !target_same_page && ctlw_witness_valid) begin
                exact_cross_allow_seen++;
            end
            if (dmp_seed_allow && target_same_page) same_page_allow_seen++;
            if (dmp_seed_block && !ctlw_witness_valid && block_no_target_authority) no_witness_block_seen++;
            if (dmp_seed_block && ctlw_token_mismatch_seen && block_no_target_authority) token_mismatch_block_seen++;
            if (dmp_seed_block && ctlw_line_mismatch_seen && block_no_target_authority) line_mismatch_block_seen++;
            if (dmp_seed_block && terminal_source && block_terminal_source) terminal_block_seen++;
            if (dmp_seed_block && !target_permission_ok && block_fault_or_perm) permission_block_seen++;
            if (dmp_seed_block && block_stale_source) stale_source_block_seen++;
            if (dmp_seed_allow) random_allow_seen++;
            if (dmp_seed_block) random_block_seen++;
            if (ctlw_collision_evict) collision_seen++;
            @(posedge clk);
            #1;
        end
    endtask

    task automatic query_cross(
        input [LINE_W-1:0] vline_i,
        input [TOKEN_W-1:0] token_i
    );
        begin
            clear_inputs();
            dmp_seed_valid = 1'b1;
            target_same_page = 1'b0;
            candidate_target_line = vline_i;
            set_source_token(token_i);
        end
    endtask

    task automatic directed_tests;
        begin
            query_cross(12'h234, 4'h1);
            sample_case("cross-page without CTLW witness blocks");

            record_witness(12'h234, 12'ha34, 4'h1);
            query_cross(12'h234, 4'h1);
            sample_case("exact CTLW witness opens cross-page full-authority gate");

            query_cross(12'h234, 4'h2);
            sample_case("stale token CTLW witness blocks full-authority gate");

            query_cross(12'h244, 4'h1);
            sample_case("same-index wrong-line witness blocks full-authority gate");

            query_cross(12'h234, 4'h1);
            terminal_source = 1'b1;
            sample_case("terminal source still blocks exact witness");

            query_cross(12'h234, 4'h1);
            target_permission_ok = 1'b0;
            sample_case("permission failure still blocks exact witness");

            query_cross(12'h234, 4'h1);
            proof_epoch = source_epoch + 1'b1;
            sample_case("stale source proof still blocks exact witness");

            apply_remap(12'h234, 4'h1);
            query_cross(12'h234, 4'h1);
            sample_case("remap-cleared CTLW witness blocks full-authority gate");
            if (dmp_seed_block) stale_after_remap_block_seen++;

            record_witness(12'h345, 12'hb45, 4'h3);
            query_cross(12'h345, 4'h3);
            sample_case("setup token TLBI exact witness");

            apply_tlbi_token(4'h3);
            query_cross(12'h345, 4'h3);
            sample_case("token-TLBI-cleared CTLW witness blocks full-authority gate");
            if (dmp_seed_block) stale_after_tlbi_block_seen++;

            record_witness(12'h456, 12'hc56, 4'h4);
            clear_inputs();
            dmp_seed_valid = 1'b1;
            target_same_page = 1'b1;
            same_page_translation_ok = 1'b1;
            set_source_token(4'h4);
            sample_case("same-page path does not need CTLW witness");

            record_witness(12'h567, 12'h111, 4'h5);
            record_witness(12'h577, 12'h222, 4'h5);
            query_cross(12'h567, 4'h5);
            sample_case("collision evicts old CTLW witness and blocks");
        end
    endtask

    task automatic drive_random(input int trial);
        int r;
        begin
            clear_inputs();
            r = $urandom();
            record_valid = (r[3:0] < 5);
            record_vline = $urandom_range(0, (1 << LINE_W) - 1);
            record_pline = $urandom_range(0, (1 << LINE_W) - 1);
            record_token = $urandom_range(0, (1 << TOKEN_W) - 1);
            remap_valid = (trial % 97) == 0;
            remap_vline = record_vline;
            remap_token = record_token;
            tlbi_token_valid = (trial % 151) == 0;
            tlbi_token = record_token;
            tlbi_all_valid = (trial % 503) == 0;

            dmp_seed_valid = (r[7:4] < 13);
            target_same_page = (trial % 17) == 0;
            candidate_target_line = ((trial % 3) == 0)
                ? record_vline
                : $urandom_range(0, (1 << LINE_W) - 1);
            current_token = ((trial % 11) == 0)
                ? (record_token + 1'b1)
                : record_token;
            proof_token = current_token;
            target_permission_ok = (r[11:8] < 13);
            terminal_source = (trial % 29) == 0;
            if ((trial % 31) == 0) begin
                proof_epoch = source_epoch + 1'b1;
            end

            sample_case($sformatf("random_%0d", trial));
        end
    endtask

    initial begin
        errors = 0;
        exact_cross_allow_seen = 0;
        no_witness_block_seen = 0;
        token_mismatch_block_seen = 0;
        line_mismatch_block_seen = 0;
        stale_after_remap_block_seen = 0;
        stale_after_tlbi_block_seen = 0;
        terminal_block_seen = 0;
        permission_block_seen = 0;
        stale_source_block_seen = 0;
        same_page_allow_seen = 0;
        random_allow_seen = 0;
        random_block_seen = 0;
        collision_seen = 0;

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
            || exact_cross_allow_seen == 0
            || no_witness_block_seen == 0
            || token_mismatch_block_seen == 0
            || line_mismatch_block_seen == 0
            || stale_after_remap_block_seen == 0
            || stale_after_tlbi_block_seen == 0
            || terminal_block_seen == 0
            || permission_block_seen == 0
            || stale_source_block_seen == 0
            || same_page_allow_seen == 0
            || random_allow_seen == 0
            || random_block_seen == 0
            || collision_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER CTLW full-authority E2E coverage failed: errors=%0d exact=%0d no_witness=%0d token=%0d line=%0d remap=%0d tlbi=%0d terminal=%0d perm=%0d stale=%0d same=%0d allow=%0d block=%0d collision=%0d",
                errors,
                exact_cross_allow_seen,
                no_witness_block_seen,
                token_mismatch_block_seen,
                line_mismatch_block_seen,
                stale_after_remap_block_seen,
                stale_after_tlbi_block_seen,
                terminal_block_seen,
                permission_block_seen,
                stale_source_block_seen,
                same_page_allow_seen,
                random_allow_seen,
                random_block_seen,
                collision_seen
            );
        end

        $display(
            "COPPER CTLW full-authority E2E tests completed: directed=12 random=%0d exact_cross_allow=%0d no_witness_block=%0d token_mismatch_block=%0d line_mismatch_block=%0d stale_after_remap_block=%0d stale_after_tlbi_block=%0d terminal_block=%0d permission_block=%0d stale_source_block=%0d same_page_allow=%0d random_allow=%0d random_block=%0d collision=%0d errors=%0d",
            TRIALS,
            exact_cross_allow_seen,
            no_witness_block_seen,
            token_mismatch_block_seen,
            line_mismatch_block_seen,
            stale_after_remap_block_seen,
            stale_after_tlbi_block_seen,
            terminal_block_seen,
            permission_block_seen,
            stale_source_block_seen,
            same_page_allow_seen,
            random_allow_seen,
            random_block_seen,
            collision_seen,
            errors
        );
        $finish;
    end

endmodule
