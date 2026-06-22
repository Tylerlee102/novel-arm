`timescale 1ns/1ps

// Assertion-focused harness for the COPPER full authority gate.
//
// The ordinary randomized testbench checks the gate against a scoreboard. This
// harness states the paper invariant as SystemVerilog properties: any allowed
// DMP seed must have exact committed source proof, token binding, non-terminal
// source status, target authority, and permission success. It also asserts the
// public block-reason outputs are equivalent to the named unsafe classes.

module copper_full_authority_sva_tb;

    localparam int VALUE_W = 12;
    localparam int EPOCH_W = 4;
    localparam int TOKEN_W = 4;
    localparam int LINE_W = 12;
    localparam int TRIALS = 10000;

    logic clk;
    logic started;

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
    logic witness_valid;
    logic [LINE_W-1:0] witness_target_line;
    logic [TOKEN_W-1:0] witness_token;

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

    logic exp_proof_exact;
    logic exp_token_match;
    logic exp_source_authorized;
    logic exp_witness_exact;
    logic exp_target_authorized;
    logic exp_allow;
    logic exp_block;
    logic exp_no_source_proof;
    logic exp_stale_source;
    logic exp_token_mismatch;
    logic exp_terminal_source;
    logic exp_no_target_authority;
    logic exp_fault_or_perm;

    int allowed_seen;
    int blocked_seen;
    int no_source_seen;
    int unsound_seen;
    int stale_value_seen;
    int stale_epoch_seen;
    int token_seen;
    int terminal_seen;
    int missing_witness_seen;
    int wrong_witness_seen;
    int stale_witness_seen;
    int perm_seen;
    int same_page_allow_seen;
    int cross_page_allow_seen;

    copper_full_authority_gate #(
        .VALUE_W(VALUE_W),
        .EPOCH_W(EPOCH_W),
        .TOKEN_W(TOKEN_W),
        .LINE_W(LINE_W)
    ) dut (
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
        .witness_valid(witness_valid),
        .witness_target_line(witness_target_line),
        .witness_token(witness_token),
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
        exp_proof_exact =
            proof_valid
            && proof_sound
            && (proof_value == source_value)
            && (proof_epoch == source_epoch);

        exp_token_match = proof_valid && (proof_token == current_token);

        exp_source_authorized =
            source_valid
            && source_clean
            && exp_proof_exact
            && exp_token_match;

        exp_witness_exact =
            witness_valid
            && (witness_target_line == candidate_target_line)
            && (witness_token == current_token);

        exp_target_authorized = target_same_page
            ? same_page_translation_ok
            : exp_witness_exact;

        exp_allow =
            dmp_seed_valid
            && exp_source_authorized
            && !terminal_source
            && exp_target_authorized
            && target_permission_ok;

        exp_block = dmp_seed_valid && !exp_allow;

        exp_no_source_proof =
            dmp_seed_valid
            && !(source_valid && source_clean && proof_valid && proof_sound);

        exp_stale_source =
            dmp_seed_valid
            && source_valid
            && source_clean
            && proof_valid
            && proof_sound
            && ((proof_value != source_value) || (proof_epoch != source_epoch));

        exp_token_mismatch =
            dmp_seed_valid
            && source_valid
            && source_clean
            && proof_valid
            && proof_sound
            && (proof_value == source_value)
            && (proof_epoch == source_epoch)
            && (proof_token != current_token);

        exp_terminal_source =
            dmp_seed_valid
            && exp_source_authorized
            && terminal_source;

        exp_no_target_authority =
            dmp_seed_valid
            && exp_source_authorized
            && !terminal_source
            && !exp_target_authorized;

        exp_fault_or_perm =
            dmp_seed_valid
            && exp_source_authorized
            && !terminal_source
            && exp_target_authorized
            && !target_permission_ok;
    end

    a_source_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            source_authorized == exp_source_authorized);

    a_target_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            target_authorized == exp_target_authorized);

    a_allow_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            dmp_seed_allow == exp_allow);

    a_block_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            dmp_seed_block == exp_block);

    a_allow_requires_exact_committed_source:
        assert property (@(posedge clk) disable iff (!started)
            dmp_seed_allow |-> (source_valid && source_clean && proof_valid && proof_sound
                && (proof_value == source_value)
                && (proof_epoch == source_epoch)));

    a_allow_requires_pasb_token:
        assert property (@(posedge clk) disable iff (!started)
            dmp_seed_allow |-> (proof_token == current_token));

    a_allow_requires_nonterminal_source:
        assert property (@(posedge clk) disable iff (!started)
            dmp_seed_allow |-> !terminal_source);

    a_allow_requires_target_authority:
        assert property (@(posedge clk) disable iff (!started)
            dmp_seed_allow |-> (target_same_page
                ? same_page_translation_ok
                : (witness_valid
                    && (witness_target_line == candidate_target_line)
                    && (witness_token == current_token))));

    a_allow_requires_permission:
        assert property (@(posedge clk) disable iff (!started)
            dmp_seed_allow |-> target_permission_ok);

    a_no_source_reason_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            block_no_source_proof == exp_no_source_proof);

    a_stale_reason_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            block_stale_source == exp_stale_source);

    a_token_reason_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            block_token_mismatch == exp_token_mismatch);

    a_terminal_reason_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            block_terminal_source == exp_terminal_source);

    a_target_reason_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            block_no_target_authority == exp_no_target_authority);

    a_perm_reason_equivalence:
        assert property (@(posedge clk) disable iff (!started)
            block_fault_or_perm == exp_fault_or_perm);

    task automatic set_clean_allow_case;
        begin
            dmp_seed_valid = 1'b1;
            source_valid = 1'b1;
            source_clean = 1'b1;
            source_value = 12'h123;
            source_epoch = 4'h5;
            current_token = 4'h7;
            proof_valid = 1'b1;
            proof_sound = 1'b1;
            proof_value = 12'h123;
            proof_epoch = 4'h5;
            proof_token = 4'h7;
            target_same_page = 1'b1;
            same_page_translation_ok = 1'b1;
            target_permission_ok = 1'b1;
            terminal_source = 1'b0;
            candidate_target_line = 12'habc;
            witness_valid = 1'b0;
            witness_target_line = 12'h000;
            witness_token = 4'h0;
        end
    endtask

    task automatic sample_case(input string name);
        begin
            @(posedge clk);
            #1;
            if (exp_allow) allowed_seen++;
            if (exp_block) blocked_seen++;
            if (exp_no_source_proof) no_source_seen++;
            if (dmp_seed_valid && source_valid && source_clean && proof_valid && !proof_sound) unsound_seen++;
            if (exp_stale_source && (proof_value != source_value)) stale_value_seen++;
            if (exp_stale_source && (proof_epoch != source_epoch)) stale_epoch_seen++;
            if (exp_token_mismatch) token_seen++;
            if (exp_terminal_source) terminal_seen++;
            if (exp_no_target_authority && !target_same_page && !witness_valid) missing_witness_seen++;
            if (exp_no_target_authority && !target_same_page && witness_valid
                    && (witness_token == current_token)
                    && (witness_target_line != candidate_target_line)) wrong_witness_seen++;
            if (exp_no_target_authority && !target_same_page && witness_valid
                    && (witness_target_line == candidate_target_line)
                    && (witness_token != current_token)) stale_witness_seen++;
            if (exp_fault_or_perm) perm_seen++;
            if (exp_allow && target_same_page) same_page_allow_seen++;
            if (exp_allow && !target_same_page) cross_page_allow_seen++;
        end
    endtask

    task automatic drive_random(input int trial);
        int r;
        begin
            r = $urandom();
            dmp_seed_valid = (r[3:0] != 0);
            source_valid = (r[7:4] < 14);
            source_clean = (r[11:8] < 13);
            proof_valid = (r[15:12] < 13);
            proof_sound = (r[19:16] < 12);
            target_same_page = r[20];
            same_page_translation_ok = (r[24:21] < 13);
            target_permission_ok = (r[28:25] < 13);
            terminal_source = (trial % 17) == 0;

            source_value = $urandom_range(0, (1 << VALUE_W) - 1);
            source_epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            current_token = $urandom_range(0, (1 << TOKEN_W) - 1);

            proof_value = ((trial % 5) == 0)
                ? (source_value ^ {{(VALUE_W-1){1'b0}}, 1'b1})
                : source_value;
            proof_epoch = ((trial % 7) == 0)
                ? (source_epoch + 1'b1)
                : source_epoch;
            proof_token = ((trial % 11) == 0)
                ? (current_token + 1'b1)
                : current_token;

            candidate_target_line = $urandom_range(0, (1 << LINE_W) - 1);
            witness_valid = (r[31:29] != 0);
            witness_target_line = ((trial % 13) == 0)
                ? (candidate_target_line + 1'b1)
                : candidate_target_line;
            witness_token = ((trial % 19) == 0)
                ? (current_token + 1'b1)
                : current_token;

            if ((trial % 23) == 0) begin
                set_clean_allow_case();
                target_same_page = 1'b0;
                witness_valid = 1'b1;
                witness_target_line = candidate_target_line;
                witness_token = current_token;
            end

            sample_case($sformatf("random_%0d", trial));
        end
    endtask

    initial begin
        started = 1'b0;
        allowed_seen = 0;
        blocked_seen = 0;
        no_source_seen = 0;
        unsound_seen = 0;
        stale_value_seen = 0;
        stale_epoch_seen = 0;
        token_seen = 0;
        terminal_seen = 0;
        missing_witness_seen = 0;
        wrong_witness_seen = 0;
        stale_witness_seen = 0;
        perm_seen = 0;
        same_page_allow_seen = 0;
        cross_page_allow_seen = 0;

        set_clean_allow_case();
        started = 1'b1;
        sample_case("same_page_allow");

        set_clean_allow_case();
        proof_valid = 1'b0;
        sample_case("no_proof_blocks");

        set_clean_allow_case();
        proof_sound = 1'b0;
        sample_case("unsound_proof_blocks");

        set_clean_allow_case();
        proof_epoch = source_epoch + 1'b1;
        sample_case("stale_epoch_blocks");

        set_clean_allow_case();
        proof_value = source_value ^ 12'h001;
        sample_case("stale_value_blocks");

        set_clean_allow_case();
        proof_token = current_token + 1'b1;
        sample_case("pasb_token_blocks");

        set_clean_allow_case();
        terminal_source = 1'b1;
        sample_case("terminal_source_blocks");

        set_clean_allow_case();
        target_same_page = 1'b0;
        witness_valid = 1'b0;
        sample_case("cross_page_without_witness_blocks");

        set_clean_allow_case();
        target_same_page = 1'b0;
        witness_valid = 1'b1;
        witness_target_line = candidate_target_line + 1'b1;
        witness_token = current_token;
        sample_case("wrong_line_witness_blocks");

        set_clean_allow_case();
        target_same_page = 1'b0;
        witness_valid = 1'b1;
        witness_target_line = candidate_target_line;
        witness_token = current_token + 1'b1;
        sample_case("stale_witness_token_blocks");

        set_clean_allow_case();
        target_same_page = 1'b0;
        witness_valid = 1'b1;
        witness_target_line = candidate_target_line;
        witness_token = current_token;
        sample_case("cross_page_exact_witness_allows");

        set_clean_allow_case();
        target_permission_ok = 1'b0;
        sample_case("permission_blocks");

        for (int trial = 0; trial < TRIALS; trial++) begin
            drive_random(trial);
        end

        if (
            allowed_seen == 0
            || blocked_seen == 0
            || no_source_seen == 0
            || unsound_seen == 0
            || stale_value_seen == 0
            || stale_epoch_seen == 0
            || token_seen == 0
            || terminal_seen == 0
            || missing_witness_seen == 0
            || wrong_witness_seen == 0
            || stale_witness_seen == 0
            || perm_seen == 0
            || same_page_allow_seen == 0
            || cross_page_allow_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER authority SVA coverage failed: allowed=%0d blocked=%0d no_source=%0d unsound=%0d stale_value=%0d stale_epoch=%0d token=%0d terminal=%0d missing_witness=%0d wrong_witness=%0d stale_witness=%0d perm=%0d same_allow=%0d cross_allow=%0d",
                allowed_seen,
                blocked_seen,
                no_source_seen,
                unsound_seen,
                stale_value_seen,
                stale_epoch_seen,
                token_seen,
                terminal_seen,
                missing_witness_seen,
                wrong_witness_seen,
                stale_witness_seen,
                perm_seen,
                same_page_allow_seen,
                cross_page_allow_seen
            );
        end

        $display(
            "COPPER full authority SVA completed: directed=12 random=%0d allowed=%0d blocked=%0d no_source=%0d unsound=%0d stale_value=%0d stale_epoch=%0d token=%0d terminal=%0d missing_witness=%0d wrong_witness=%0d stale_witness=%0d perm=%0d same_allow=%0d cross_allow=%0d",
            TRIALS,
            allowed_seen,
            blocked_seen,
            no_source_seen,
            unsound_seen,
            stale_value_seen,
            stale_epoch_seen,
            token_seen,
            terminal_seen,
            missing_witness_seen,
            wrong_witness_seen,
            stale_witness_seen,
            perm_seen,
            same_page_allow_seen,
            cross_page_allow_seen
        );
        $finish;
    end

endmodule
