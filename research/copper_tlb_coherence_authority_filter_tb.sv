`timescale 1ns/1ps

// Testbench for the COPPER TLB/coherence authority filter.
//
// The directed cases mirror the Python contract counterexamples: same-cycle
// and queued source revocation, target remap/TLBI, permission downgrade,
// page-level witness overreach, source-only authority, unrelated-event
// precision, and overflow fallback.

module copper_tlb_coherence_authority_filter_tb;

    localparam int SRC_LINE_W = 6;
    localparam int TGT_LINE_W = 8;
    localparam int TOKEN_W = 4;
    localparam int SOURCE_Q_DEPTH = 4;
    localparam int TARGET_Q_DEPTH = 4;
    localparam int COUNT_W = 3;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;

    logic candidate_valid;
    logic [SRC_LINE_W-1:0] candidate_src_line;
    logic [TGT_LINE_W-1:0] candidate_tgt_line;
    logic [TOKEN_W-1:0] candidate_token;
    logic source_proof_valid;
    logic target_witness_valid;
    logic target_exact_match;
    logic target_permission_ok;
    logic source_revoke_valid;
    logic [SRC_LINE_W-1:0] source_revoke_line;
    logic target_remap_valid;
    logic [TGT_LINE_W-1:0] target_remap_line;
    logic [TOKEN_W-1:0] target_remap_token;
    logic tlbi_token_valid;
    logic [TOKEN_W-1:0] tlbi_token;
    logic tlbi_all_valid;
    logic permission_downgrade_valid;
    logic [TGT_LINE_W-1:0] permission_line;
    logic [TOKEN_W-1:0] permission_token;
    logic source_drain_enable;
    logic target_drain_enable;

    logic dmp_allow;
    logic dmp_block;
    logic conflict_hold;
    logic block_no_source_proof;
    logic block_no_target_witness;
    logic block_permission;
    logic block_revocation;
    logic block_overflow;
    logic source_clear_valid;
    logic [SRC_LINE_W-1:0] source_clear_line;
    logic target_clear_valid;
    logic target_clear_is_remap;
    logic target_clear_is_token;
    logic target_clear_is_global;
    logic [TGT_LINE_W-1:0] target_clear_line;
    logic [TOKEN_W-1:0] target_clear_token;
    logic source_events_ready;
    logic target_events_ready;
    logic overflow_sticky;
    logic [COUNT_W-1:0] source_queued_count;
    logic [COUNT_W-1:0] target_queued_count;

    int errors;
    int directed_checks;
    int random_checks;
    int baseline_allow_seen;
    int no_source_block_seen;
    int no_target_block_seen;
    int permission_block_seen;
    int source_same_cycle_block_seen;
    int source_queued_block_seen;
    int target_remap_block_seen;
    int target_queued_block_seen;
    int tlbi_token_block_seen;
    int tlbi_all_block_seen;
    int unrelated_allow_seen;
    int overflow_block_seen;
    int random_allow_seen;
    int random_block_seen;

    copper_tlb_coherence_authority_filter #(
        .SRC_LINE_W(SRC_LINE_W),
        .TGT_LINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .SOURCE_Q_DEPTH(SOURCE_Q_DEPTH),
        .TARGET_Q_DEPTH(TARGET_Q_DEPTH),
        .COUNT_W(COUNT_W)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .candidate_valid(candidate_valid),
        .candidate_src_line(candidate_src_line),
        .candidate_tgt_line(candidate_tgt_line),
        .candidate_token(candidate_token),
        .source_proof_valid(source_proof_valid),
        .target_witness_valid(target_witness_valid),
        .target_exact_match(target_exact_match),
        .target_permission_ok(target_permission_ok),
        .source_revoke_valid(source_revoke_valid),
        .source_revoke_line(source_revoke_line),
        .target_remap_valid(target_remap_valid),
        .target_remap_line(target_remap_line),
        .target_remap_token(target_remap_token),
        .tlbi_token_valid(tlbi_token_valid),
        .tlbi_token(tlbi_token),
        .tlbi_all_valid(tlbi_all_valid),
        .permission_downgrade_valid(permission_downgrade_valid),
        .permission_line(permission_line),
        .permission_token(permission_token),
        .source_drain_enable(source_drain_enable),
        .target_drain_enable(target_drain_enable),
        .dmp_allow(dmp_allow),
        .dmp_block(dmp_block),
        .conflict_hold(conflict_hold),
        .block_no_source_proof(block_no_source_proof),
        .block_no_target_witness(block_no_target_witness),
        .block_permission(block_permission),
        .block_revocation(block_revocation),
        .block_overflow(block_overflow),
        .source_clear_valid(source_clear_valid),
        .source_clear_line(source_clear_line),
        .target_clear_valid(target_clear_valid),
        .target_clear_is_remap(target_clear_is_remap),
        .target_clear_is_token(target_clear_is_token),
        .target_clear_is_global(target_clear_is_global),
        .target_clear_line(target_clear_line),
        .target_clear_token(target_clear_token),
        .source_events_ready(source_events_ready),
        .target_events_ready(target_events_ready),
        .overflow_sticky(overflow_sticky),
        .source_queued_count(source_queued_count),
        .target_queued_count(target_queued_count)
    );

    always #5 clk = ~clk;

    task automatic clear_inputs;
        begin
            candidate_valid = 1'b0;
            candidate_src_line = SRC_LINE_W'(6'd3);
            candidate_tgt_line = TGT_LINE_W'(8'h44);
            candidate_token = TOKEN_W'(4'h5);
            source_proof_valid = 1'b1;
            target_witness_valid = 1'b1;
            target_exact_match = 1'b1;
            target_permission_ok = 1'b1;
            source_revoke_valid = 1'b0;
            source_revoke_line = '0;
            target_remap_valid = 1'b0;
            target_remap_line = '0;
            target_remap_token = '0;
            tlbi_token_valid = 1'b0;
            tlbi_token = '0;
            tlbi_all_valid = 1'b0;
            permission_downgrade_valid = 1'b0;
            permission_line = '0;
            permission_token = '0;
            source_drain_enable = 1'b1;
            target_drain_enable = 1'b1;
        end
    endtask

    task automatic reset_dut;
        begin
            rst_n = 1'b0;
            clear_inputs();
            repeat (4) @(posedge clk);
            rst_n = 1'b1;
            repeat (2) @(posedge clk);
        end
    endtask

    task automatic check(input string name, input logic condition);
        begin
            directed_checks++;
            if (!condition) begin
                errors++;
                $display("ERROR %s at t=%0t", name, $time);
            end
        end
    endtask

    task automatic tick;
        begin
            @(posedge clk);
            #1;
        end
    endtask

    task automatic expect_clean_allow(input string name);
        begin
            candidate_valid = 1'b1;
            #1;
            check(name, dmp_allow && !dmp_block && !conflict_hold);
            baseline_allow_seen++;
            clear_inputs();
            tick();
        end
    endtask

    task automatic push_source_revoke(input logic [SRC_LINE_W-1:0] line);
        begin
            clear_inputs();
            source_revoke_valid = 1'b1;
            source_revoke_line = line;
            tick();
            clear_inputs();
            #1;
        end
    endtask

    task automatic push_target_remap(
        input logic [TGT_LINE_W-1:0] line,
        input logic [TOKEN_W-1:0] token
    );
        begin
            clear_inputs();
            target_remap_valid = 1'b1;
            target_remap_line = line;
            target_remap_token = token;
            tick();
            clear_inputs();
            #1;
        end
    endtask

    task automatic directed_suite;
        begin
            reset_dut();

            clear_inputs();
            expect_clean_allow("baseline allow");

            candidate_valid = 1'b1;
            source_proof_valid = 1'b0;
            #1;
            check("missing source proof blocks", dmp_block && block_no_source_proof && !dmp_allow);
            no_source_block_seen++;

            clear_inputs();
            candidate_valid = 1'b1;
            target_witness_valid = 1'b1;
            target_exact_match = 1'b0;
            #1;
            check("page-level/non-exact witness blocks", dmp_block && block_no_target_witness && !dmp_allow);
            no_target_block_seen++;

            clear_inputs();
            candidate_valid = 1'b1;
            target_witness_valid = 1'b0;
            target_exact_match = 1'b0;
            #1;
            check("source-only authority blocks", dmp_block && block_no_target_witness && !dmp_allow);
            no_target_block_seen++;

            clear_inputs();
            candidate_valid = 1'b1;
            target_permission_ok = 1'b0;
            #1;
            check("permission gate blocks", dmp_block && block_permission && !dmp_allow);
            permission_block_seen++;

            clear_inputs();
            candidate_valid = 1'b1;
            source_revoke_valid = 1'b1;
            source_revoke_line = candidate_src_line;
            #1;
            check("same-cycle source revoke blocks", dmp_block && block_revocation && conflict_hold && !dmp_allow);
            source_same_cycle_block_seen++;

            clear_inputs();
            candidate_valid = 1'b1;
            source_revoke_valid = 1'b1;
            source_revoke_line = candidate_src_line ^ SRC_LINE_W'(6'd1);
            #1;
            check("unrelated source revoke allows", dmp_allow && !conflict_hold);
            unrelated_allow_seen++;

            reset_dut();
            push_source_revoke(SRC_LINE_W'(6'd3));
            candidate_valid = 1'b1;
            #1;
            check("queued source revoke blocks", dmp_block && block_revocation && source_clear_valid && !dmp_allow);
            source_queued_block_seen++;

            reset_dut();
            clear_inputs();
            candidate_valid = 1'b1;
            target_remap_valid = 1'b1;
            target_remap_line = candidate_tgt_line;
            target_remap_token = candidate_token;
            #1;
            check("same-cycle target remap blocks", dmp_block && block_revocation && conflict_hold && !dmp_allow);
            target_remap_block_seen++;

            reset_dut();
            push_target_remap(TGT_LINE_W'(8'h44), TOKEN_W'(4'h5));
            candidate_valid = 1'b1;
            #1;
            check("queued target remap blocks", dmp_block && block_revocation && target_clear_valid && !dmp_allow);
            target_queued_block_seen++;

            reset_dut();
            clear_inputs();
            candidate_valid = 1'b1;
            target_remap_valid = 1'b1;
            target_remap_line = candidate_tgt_line ^ TGT_LINE_W'(8'h01);
            target_remap_token = candidate_token ^ TOKEN_W'(4'h1);
            #1;
            check("unrelated target remap allows", dmp_allow && !conflict_hold);
            unrelated_allow_seen++;

            clear_inputs();
            candidate_valid = 1'b1;
            tlbi_token_valid = 1'b1;
            tlbi_token = candidate_token;
            #1;
            check("token TLBI blocks", dmp_block && block_revocation && conflict_hold && !dmp_allow);
            tlbi_token_block_seen++;

            clear_inputs();
            candidate_valid = 1'b1;
            tlbi_all_valid = 1'b1;
            #1;
            check("global TLBI blocks", dmp_block && block_revocation && conflict_hold && !dmp_allow);
            tlbi_all_block_seen++;

            clear_inputs();
            candidate_valid = 1'b1;
            permission_downgrade_valid = 1'b1;
            permission_line = candidate_tgt_line;
            permission_token = candidate_token;
            #1;
            check("permission downgrade blocks", dmp_block && block_permission && conflict_hold && !dmp_allow);
            permission_block_seen++;

            reset_dut();
            clear_inputs();
            source_drain_enable = 1'b0;
            for (int i = 0; i < SOURCE_Q_DEPTH; i++) begin
                source_revoke_valid = 1'b1;
                source_revoke_line = SRC_LINE_W'(i);
                tick();
            end
            source_revoke_valid = 1'b1;
            source_revoke_line = SRC_LINE_W'(6'd22);
            tick();
            clear_inputs();
            candidate_valid = 1'b1;
            #1;
            check("overflow fallback blocks", overflow_sticky && dmp_block && block_overflow && !dmp_allow);
            overflow_block_seen++;
        end
    endtask

    task automatic random_suite;
        logic obvious_block;
        begin
            reset_dut();
            for (int i = 0; i < TRIALS; i++) begin
                clear_inputs();
                candidate_valid = $urandom_range(0, 3) != 0;
                candidate_src_line = SRC_LINE_W'($urandom());
                candidate_tgt_line = TGT_LINE_W'($urandom());
                candidate_token = TOKEN_W'($urandom());
                source_proof_valid = $urandom_range(0, 7) != 0;
                target_witness_valid = $urandom_range(0, 7) != 0;
                target_exact_match = $urandom_range(0, 5) != 0;
                target_permission_ok = $urandom_range(0, 7) != 0;
                source_drain_enable = $urandom_range(0, 9) != 0;
                target_drain_enable = $urandom_range(0, 9) != 0;

                source_revoke_valid = $urandom_range(0, 9) == 0;
                source_revoke_line = ($urandom_range(0, 3) == 0)
                    ? candidate_src_line
                    : SRC_LINE_W'($urandom());

                target_remap_valid = $urandom_range(0, 12) == 0;
                target_remap_line = ($urandom_range(0, 3) == 0)
                    ? candidate_tgt_line
                    : TGT_LINE_W'($urandom());
                target_remap_token = ($urandom_range(0, 3) == 0)
                    ? candidate_token
                    : TOKEN_W'($urandom());

                tlbi_token_valid = $urandom_range(0, 19) == 0;
                tlbi_token = ($urandom_range(0, 2) == 0)
                    ? candidate_token
                    : TOKEN_W'($urandom());
                tlbi_all_valid = $urandom_range(0, 63) == 0;

                permission_downgrade_valid = $urandom_range(0, 19) == 0;
                permission_line = ($urandom_range(0, 2) == 0)
                    ? candidate_tgt_line
                    : TGT_LINE_W'($urandom());
                permission_token = ($urandom_range(0, 2) == 0)
                    ? candidate_token
                    : TOKEN_W'($urandom());

                #1;
                obvious_block =
                    candidate_valid
                    && ((!source_proof_valid)
                        || (!target_witness_valid)
                        || (!target_exact_match)
                        || (!target_permission_ok)
                        || (source_revoke_valid && source_revoke_line == candidate_src_line)
                        || (target_remap_valid
                            && target_remap_line == candidate_tgt_line
                            && target_remap_token == candidate_token)
                        || (tlbi_token_valid && tlbi_token == candidate_token)
                        || tlbi_all_valid
                        || (permission_downgrade_valid
                            && permission_line == candidate_tgt_line
                            && permission_token == candidate_token)
                        || overflow_sticky);

                random_checks++;
                if (dmp_allow && (block_no_source_proof || block_no_target_witness
                    || block_permission || block_revocation || block_overflow)) begin
                    errors++;
                    $display("ERROR random allow with block flag at trial %0d", i);
                end
                if (dmp_allow && obvious_block) begin
                    errors++;
                    $display("ERROR random allow despite obvious block at trial %0d", i);
                end
                if (dmp_allow) begin
                    random_allow_seen++;
                end
                if (dmp_block) begin
                    random_block_seen++;
                end

                tick();
            end
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        errors = 0;
        directed_checks = 0;
        random_checks = 0;
        baseline_allow_seen = 0;
        no_source_block_seen = 0;
        no_target_block_seen = 0;
        permission_block_seen = 0;
        source_same_cycle_block_seen = 0;
        source_queued_block_seen = 0;
        target_remap_block_seen = 0;
        target_queued_block_seen = 0;
        tlbi_token_block_seen = 0;
        tlbi_all_block_seen = 0;
        unrelated_allow_seen = 0;
        overflow_block_seen = 0;
        random_allow_seen = 0;
        random_block_seen = 0;
        clear_inputs();

        directed_suite();
        random_suite();

        check("baseline seen", baseline_allow_seen > 0);
        check("no-source block seen", no_source_block_seen > 0);
        check("no-target block seen", no_target_block_seen > 0);
        check("permission block seen", permission_block_seen > 0);
        check("same-cycle source block seen", source_same_cycle_block_seen > 0);
        check("queued source block seen", source_queued_block_seen > 0);
        check("target remap block seen", target_remap_block_seen > 0);
        check("queued target block seen", target_queued_block_seen > 0);
        check("tlbi token block seen", tlbi_token_block_seen > 0);
        check("tlbi all block seen", tlbi_all_block_seen > 0);
        check("unrelated allow seen", unrelated_allow_seen > 0);
        check("overflow block seen", overflow_block_seen > 0);

        $display("COPPER TLB-coherence authority filter completed directed=%0d random=%0d baseline_allow=%0d no_source=%0d no_target=%0d permission=%0d source_same=%0d source_queued=%0d target_remap=%0d target_queued=%0d tlbi_token=%0d tlbi_all=%0d unrelated_allow=%0d overflow=%0d random_allow=%0d random_block=%0d errors=%0d",
            directed_checks,
            random_checks,
            baseline_allow_seen,
            no_source_block_seen,
            no_target_block_seen,
            permission_block_seen,
            source_same_cycle_block_seen,
            source_queued_block_seen,
            target_remap_block_seen,
            target_queued_block_seen,
            tlbi_token_block_seen,
            tlbi_all_block_seen,
            unrelated_allow_seen,
            overflow_block_seen,
            random_allow_seen,
            random_block_seen,
            errors);

        if (errors != 0) begin
            $fatal(1, "COPPER TLB-coherence authority filter failed");
        end
        $finish;
    end

endmodule
