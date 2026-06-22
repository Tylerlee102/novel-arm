`timescale 1ns/1ps

module copper_full_authority_gate_tb;

    localparam int VALUE_W = 12;
    localparam int EPOCH_W = 4;
    localparam int TOKEN_W = 4;
    localparam int LINE_W = 12;
    localparam int TRIALS = 5000;

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

    int errors;
    int allowed_seen;
    int blocked_seen;
    int stale_seen;
    int stale_value_seen;
    int stale_epoch_seen;
    int token_seen;
    int target_seen;
    int no_source_seen;
    int unsound_seen;
    int same_page_allow_seen;
    int cross_page_allow_seen;
    int missing_witness_seen;
    int wrong_line_witness_seen;
    int stale_witness_seen;
    int terminal_seen;
    int perm_seen;

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

    function automatic logic exp_source_authorized;
        exp_source_authorized =
            source_valid
            && source_clean
            && proof_valid
            && proof_sound
            && (proof_value == source_value)
            && (proof_epoch == source_epoch)
            && (proof_token == current_token);
    endfunction

    function automatic logic exp_target_authorized;
        exp_target_authorized = target_same_page
            ? same_page_translation_ok
            : (witness_valid
                && (witness_target_line == candidate_target_line)
                && (witness_token == current_token));
    endfunction

    function automatic logic exp_allow;
        exp_allow =
            dmp_seed_valid
            && exp_source_authorized()
            && !terminal_source
            && exp_target_authorized()
            && target_permission_ok;
    endfunction

    task automatic check_case(input string name);
        logic exp_src;
        logic exp_tgt;
        logic exp_a;
        logic exp_b;
        logic exp_no_src;
        logic exp_stale;
        logic exp_token;
        logic exp_terminal;
        logic exp_target;
        logic exp_perm;
        logic exp_unsound;
        logic exp_stale_value;
        logic exp_stale_epoch;
        logic exp_missing_witness;
        logic exp_wrong_line_witness;
        logic exp_stale_witness;
        begin
            #1;
            exp_src = exp_source_authorized();
            exp_tgt = exp_target_authorized();
            exp_a = exp_allow();
            exp_b = dmp_seed_valid && !exp_a;
            exp_no_src =
                dmp_seed_valid
                && !(source_valid && source_clean && proof_valid && proof_sound);
            exp_stale =
                dmp_seed_valid
                && source_valid
                && source_clean
                && proof_valid
                && proof_sound
                && ((proof_value != source_value) || (proof_epoch != source_epoch));
            exp_token =
                dmp_seed_valid
                && source_valid
                && source_clean
                && proof_valid
                && proof_sound
                && (proof_value == source_value)
                && (proof_epoch == source_epoch)
                && (proof_token != current_token);
            exp_terminal =
                dmp_seed_valid
                && exp_src
                && terminal_source;
            exp_target =
                dmp_seed_valid
                && exp_src
                && !terminal_source
                && !exp_tgt;
            exp_perm =
                dmp_seed_valid
                && exp_src
                && !terminal_source
                && exp_tgt
                && !target_permission_ok;
            exp_unsound =
                dmp_seed_valid
                && source_valid
                && source_clean
                && proof_valid
                && !proof_sound;
            exp_stale_value =
                exp_stale
                && (proof_value != source_value);
            exp_stale_epoch =
                exp_stale
                && (proof_epoch != source_epoch);
            exp_missing_witness =
                dmp_seed_valid
                && exp_src
                && !terminal_source
                && !target_same_page
                && !witness_valid;
            exp_wrong_line_witness =
                dmp_seed_valid
                && exp_src
                && !terminal_source
                && !target_same_page
                && witness_valid
                && (witness_token == current_token)
                && (witness_target_line != candidate_target_line);
            exp_stale_witness =
                dmp_seed_valid
                && exp_src
                && !terminal_source
                && !target_same_page
                && witness_valid
                && (witness_target_line == candidate_target_line)
                && (witness_token != current_token);

            if (source_authorized !== exp_src) begin
                $error("%s: source_authorized expected %0b got %0b", name, exp_src, source_authorized);
                errors++;
            end
            if (target_authorized !== exp_tgt) begin
                $error("%s: target_authorized expected %0b got %0b", name, exp_tgt, target_authorized);
                errors++;
            end
            if (dmp_seed_allow !== exp_a) begin
                $error("%s: allow expected %0b got %0b", name, exp_a, dmp_seed_allow);
                errors++;
            end
            if (dmp_seed_block !== exp_b) begin
                $error("%s: block expected %0b got %0b", name, exp_b, dmp_seed_block);
                errors++;
            end
            if (block_no_source_proof !== exp_no_src) begin
                $error("%s: no_source expected %0b got %0b", name, exp_no_src, block_no_source_proof);
                errors++;
            end
            if (block_stale_source !== exp_stale) begin
                $error("%s: stale expected %0b got %0b", name, exp_stale, block_stale_source);
                errors++;
            end
            if (block_token_mismatch !== exp_token) begin
                $error("%s: token expected %0b got %0b", name, exp_token, block_token_mismatch);
                errors++;
            end
            if (block_terminal_source !== exp_terminal) begin
                $error("%s: terminal expected %0b got %0b", name, exp_terminal, block_terminal_source);
                errors++;
            end
            if (block_no_target_authority !== exp_target) begin
                $error("%s: target expected %0b got %0b", name, exp_target, block_no_target_authority);
                errors++;
            end
            if (block_fault_or_perm !== exp_perm) begin
                $error("%s: perm expected %0b got %0b", name, exp_perm, block_fault_or_perm);
                errors++;
            end

            if (exp_a) allowed_seen++;
            if (exp_b) blocked_seen++;
            if (exp_stale) stale_seen++;
            if (exp_stale_value) stale_value_seen++;
            if (exp_stale_epoch) stale_epoch_seen++;
            if (exp_token) token_seen++;
            if (exp_target) target_seen++;
            if (exp_no_src) no_source_seen++;
            if (exp_unsound) unsound_seen++;
            if (exp_a && target_same_page) same_page_allow_seen++;
            if (exp_a && !target_same_page) cross_page_allow_seen++;
            if (exp_missing_witness) missing_witness_seen++;
            if (exp_wrong_line_witness) wrong_line_witness_seen++;
            if (exp_stale_witness) stale_witness_seen++;
            if (exp_terminal) terminal_seen++;
            if (exp_perm) perm_seen++;
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

            check_case($sformatf("random_%0d", trial));
        end
    endtask

    initial begin
        errors = 0;
        allowed_seen = 0;
        blocked_seen = 0;
        stale_seen = 0;
        stale_value_seen = 0;
        stale_epoch_seen = 0;
        token_seen = 0;
        target_seen = 0;
        no_source_seen = 0;
        unsound_seen = 0;
        same_page_allow_seen = 0;
        cross_page_allow_seen = 0;
        missing_witness_seen = 0;
        wrong_line_witness_seen = 0;
        stale_witness_seen = 0;
        terminal_seen = 0;
        perm_seen = 0;

        set_clean_allow_case();
        check_case("same_page_allow");

        set_clean_allow_case();
        proof_valid = 1'b0;
        check_case("no_proof_blocks");

        set_clean_allow_case();
        proof_sound = 1'b0;
        check_case("unsound_proof_blocks");

        set_clean_allow_case();
        proof_epoch = source_epoch + 1'b1;
        check_case("stale_epoch_blocks");

        set_clean_allow_case();
        proof_value = source_value ^ 12'h001;
        check_case("stale_value_blocks");

        set_clean_allow_case();
        proof_token = current_token + 1'b1;
        check_case("pasb_token_blocks");

        set_clean_allow_case();
        terminal_source = 1'b1;
        check_case("terminal_source_blocks");

        set_clean_allow_case();
        target_same_page = 1'b0;
        witness_valid = 1'b0;
        check_case("cross_page_without_witness_blocks");

        set_clean_allow_case();
        target_same_page = 1'b0;
        witness_valid = 1'b1;
        witness_target_line = candidate_target_line + 1'b1;
        witness_token = current_token;
        check_case("page_level_wrong_line_witness_blocks");

        set_clean_allow_case();
        target_same_page = 1'b0;
        witness_valid = 1'b1;
        witness_target_line = candidate_target_line;
        witness_token = current_token + 1'b1;
        check_case("stale_witness_token_blocks");

        set_clean_allow_case();
        target_same_page = 1'b0;
        witness_valid = 1'b1;
        witness_target_line = candidate_target_line;
        witness_token = current_token;
        check_case("cross_page_exact_witness_allows");

        set_clean_allow_case();
        target_permission_ok = 1'b0;
        check_case("permission_blocks");

        for (int trial = 0; trial < TRIALS; trial++) begin
            drive_random(trial);
        end

        if (allowed_seen == 0) begin
            $error("no allowed candidates observed");
            errors++;
        end
        if (blocked_seen == 0) begin
            $error("no blocked candidates observed");
            errors++;
        end
        if (
            stale_seen == 0
            || stale_value_seen == 0
            || stale_epoch_seen == 0
            || token_seen == 0
            || target_seen == 0
            || no_source_seen == 0
            || unsound_seen == 0
            || same_page_allow_seen == 0
            || cross_page_allow_seen == 0
            || missing_witness_seen == 0
            || wrong_line_witness_seen == 0
            || stale_witness_seen == 0
            || terminal_seen == 0
            || perm_seen == 0
        ) begin
            $error(
                "insufficient coverage no_source=%0d unsound=%0d stale=%0d stale_value=%0d stale_epoch=%0d token=%0d target=%0d same_allow=%0d cross_allow=%0d missing_witness=%0d wrong_line_witness=%0d stale_witness=%0d terminal=%0d perm=%0d",
                no_source_seen,
                unsound_seen,
                stale_seen,
                stale_value_seen,
                stale_epoch_seen,
                token_seen,
                target_seen,
                same_page_allow_seen,
                cross_page_allow_seen,
                missing_witness_seen,
                wrong_line_witness_seen,
                stale_witness_seen,
                terminal_seen,
                perm_seen
            );
            errors++;
        end
        if (errors != 0) begin
            $fatal(1, "COPPER full authority gate tests failed: errors=%0d", errors);
        end

        $display(
            "COPPER full authority gate tests completed: directed=12 random=%0d allowed=%0d blocked=%0d stale=%0d token=%0d target=%0d terminal=%0d perm=%0d errors=%0d",
            TRIALS,
            allowed_seen,
            blocked_seen,
            stale_seen,
            token_seen,
            target_seen,
            terminal_seen,
            perm_seen,
            errors
        );
        $display(
            "COPPER full authority named coverage: no_source=%0d unsound=%0d stale_value=%0d stale_epoch=%0d pasb_token=%0d same_page_allow=%0d cross_page_allow=%0d missing_witness=%0d wrong_line_witness=%0d stale_witness=%0d terminal=%0d permission=%0d",
            no_source_seen,
            unsound_seen,
            stale_value_seen,
            stale_epoch_seen,
            token_seen,
            same_page_allow_seen,
            cross_page_allow_seen,
            missing_witness_seen,
            wrong_line_witness_seen,
            stale_witness_seen,
            terminal_seen,
            perm_seen
        );
        $finish;
    end

endmodule
