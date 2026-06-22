`timescale 1ns/1ps

module copper_ropl_lsq_retire_guard_tb;

    localparam int REPLAY_GEN_W = 4;
    localparam int SQUASH_EPOCH_W = 4;
    localparam int ALIAS_GEN_W = 4;
    localparam int TRIALS = 20000;

    logic clk;

    logic src_tag_valid;
    logic src_executed;
    logic src_retired;
    logic src_exception;
    logic src_older_than_dep;
    logic tag_live;
    logic tag_stale;
    logic [REPLAY_GEN_W-1:0] tag_replay_gen;
    logic [REPLAY_GEN_W-1:0] dep_replay_gen;
    logic [SQUASH_EPOCH_W-1:0] tag_squash_epoch;
    logic [SQUASH_EPOCH_W-1:0] current_squash_epoch;
    logic [ALIAS_GEN_W-1:0] tag_alias_gen;
    logic [ALIAS_GEN_W-1:0] current_alias_gen;
    logic dep_execute_valid;
    logic dep_retire_valid;
    logic dep_is_memory;
    logic dep_exception;
    logic dep_squashed;
    logic memory_order_violation;
    logic target_translation_ok;
    logic target_permission_ok;

    logic proof_valid;
    logic blocked_execute_stage;
    logic blocked_not_retire;
    logic blocked_not_memory;
    logic blocked_no_live_tag;
    logic blocked_source_not_clean;
    logic blocked_exception_or_squash;
    logic blocked_replay_or_squash_epoch;
    logic blocked_alias_or_order;
    logic blocked_translation_or_permission;

    logic exp_retire_memory_attempt;
    logic exp_tag_ok;
    logic exp_source_ok;
    logic exp_exception_ok;
    logic exp_replay_ok;
    logic exp_squash_epoch_ok;
    logic exp_alias_ok;
    logic exp_order_ok;
    logic exp_target_ok;
    logic exp_gen_ok;
    logic exp_backend_hazard_ok;
    logic exp_proof;
    logic exp_block_execute_stage;
    logic exp_block_not_retire;
    logic exp_block_not_memory;
    logic exp_block_no_live_tag;
    logic exp_block_source_not_clean;
    logic exp_block_exception_or_squash;
    logic exp_block_replay_or_squash_epoch;
    logic exp_block_alias_or_order;
    logic exp_block_translation_or_permission;

    int errors;
    int legal_proof_seen;
    int execute_stage_block_seen;
    int not_retire_seen;
    int not_memory_seen;
    int no_live_tag_seen;
    int source_not_clean_seen;
    int exception_squash_seen;
    int replay_squash_seen;
    int alias_order_seen;
    int translation_perm_seen;
    int random_proof_seen;
    int random_block_seen;

    copper_ropl_lsq_retire_guard #(
        .REPLAY_GEN_W(REPLAY_GEN_W),
        .SQUASH_EPOCH_W(SQUASH_EPOCH_W),
        .ALIAS_GEN_W(ALIAS_GEN_W)
    ) dut (
        .src_tag_valid(src_tag_valid),
        .src_executed(src_executed),
        .src_retired(src_retired),
        .src_exception(src_exception),
        .src_older_than_dep(src_older_than_dep),
        .tag_live(tag_live),
        .tag_stale(tag_stale),
        .tag_replay_gen(tag_replay_gen),
        .dep_replay_gen(dep_replay_gen),
        .tag_squash_epoch(tag_squash_epoch),
        .current_squash_epoch(current_squash_epoch),
        .tag_alias_gen(tag_alias_gen),
        .current_alias_gen(current_alias_gen),
        .dep_execute_valid(dep_execute_valid),
        .dep_retire_valid(dep_retire_valid),
        .dep_is_memory(dep_is_memory),
        .dep_exception(dep_exception),
        .dep_squashed(dep_squashed),
        .memory_order_violation(memory_order_violation),
        .target_translation_ok(target_translation_ok),
        .target_permission_ok(target_permission_ok),
        .proof_valid(proof_valid),
        .blocked_execute_stage(blocked_execute_stage),
        .blocked_not_retire(blocked_not_retire),
        .blocked_not_memory(blocked_not_memory),
        .blocked_no_live_tag(blocked_no_live_tag),
        .blocked_source_not_clean(blocked_source_not_clean),
        .blocked_exception_or_squash(blocked_exception_or_squash),
        .blocked_replay_or_squash_epoch(blocked_replay_or_squash_epoch),
        .blocked_alias_or_order(blocked_alias_or_order),
        .blocked_translation_or_permission(blocked_translation_or_permission)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    always_comb begin
        exp_retire_memory_attempt = dep_retire_valid && dep_is_memory;
        exp_tag_ok = src_tag_valid && tag_live && !tag_stale;
        exp_source_ok = src_executed && src_retired && !src_exception && src_older_than_dep;
        exp_exception_ok = !dep_exception && !dep_squashed;
        exp_replay_ok = tag_replay_gen == dep_replay_gen;
        exp_squash_epoch_ok = tag_squash_epoch == current_squash_epoch;
        exp_alias_ok = tag_alias_gen == current_alias_gen;
        exp_order_ok = !memory_order_violation;
        exp_target_ok = target_translation_ok && target_permission_ok;
        exp_gen_ok = exp_replay_ok && exp_squash_epoch_ok;
        exp_backend_hazard_ok = exp_alias_ok && exp_order_ok;

        exp_proof =
            exp_retire_memory_attempt
            && exp_tag_ok
            && exp_source_ok
            && exp_exception_ok
            && exp_gen_ok
            && exp_backend_hazard_ok
            && exp_target_ok;

        exp_block_execute_stage = dep_execute_valid && !dep_retire_valid && src_tag_valid;
        exp_block_not_retire = src_tag_valid && dep_is_memory && !dep_retire_valid;
        exp_block_not_memory = src_tag_valid && dep_retire_valid && !dep_is_memory;
        exp_block_no_live_tag = exp_retire_memory_attempt && !exp_tag_ok;
        exp_block_source_not_clean = exp_retire_memory_attempt && exp_tag_ok && !exp_source_ok;
        exp_block_exception_or_squash =
            exp_retire_memory_attempt && exp_tag_ok && exp_source_ok && !exp_exception_ok;
        exp_block_replay_or_squash_epoch =
            exp_retire_memory_attempt
            && exp_tag_ok
            && exp_source_ok
            && exp_exception_ok
            && !exp_gen_ok;
        exp_block_alias_or_order =
            exp_retire_memory_attempt
            && exp_tag_ok
            && exp_source_ok
            && exp_exception_ok
            && exp_gen_ok
            && !exp_backend_hazard_ok;
        exp_block_translation_or_permission =
            exp_retire_memory_attempt
            && exp_tag_ok
            && exp_source_ok
            && exp_exception_ok
            && exp_gen_ok
            && exp_backend_hazard_ok
            && !exp_target_ok;
    end

    task automatic set_legal;
        begin
            src_tag_valid = 1'b1;
            src_executed = 1'b1;
            src_retired = 1'b1;
            src_exception = 1'b0;
            src_older_than_dep = 1'b1;
            tag_live = 1'b1;
            tag_stale = 1'b0;
            tag_replay_gen = 4'h3;
            dep_replay_gen = 4'h3;
            tag_squash_epoch = 4'h5;
            current_squash_epoch = 4'h5;
            tag_alias_gen = 4'h6;
            current_alias_gen = 4'h6;
            dep_execute_valid = 1'b1;
            dep_retire_valid = 1'b1;
            dep_is_memory = 1'b1;
            dep_exception = 1'b0;
            dep_squashed = 1'b0;
            memory_order_violation = 1'b0;
            target_translation_ok = 1'b1;
            target_permission_ok = 1'b1;
        end
    endtask

    task automatic check_now(input string label, input bit is_random);
        begin
            #1;
            if (proof_valid !== exp_proof) begin
                $error("%s: proof expected %0b got %0b", label, exp_proof, proof_valid);
                errors++;
            end
            if (blocked_execute_stage !== exp_block_execute_stage) begin
                $error("%s: blocked_execute_stage expected %0b got %0b", label, exp_block_execute_stage, blocked_execute_stage);
                errors++;
            end
            if (blocked_not_retire !== exp_block_not_retire) begin
                $error("%s: blocked_not_retire expected %0b got %0b", label, exp_block_not_retire, blocked_not_retire);
                errors++;
            end
            if (blocked_not_memory !== exp_block_not_memory) begin
                $error("%s: blocked_not_memory expected %0b got %0b", label, exp_block_not_memory, blocked_not_memory);
                errors++;
            end
            if (blocked_no_live_tag !== exp_block_no_live_tag) begin
                $error("%s: blocked_no_live_tag expected %0b got %0b", label, exp_block_no_live_tag, blocked_no_live_tag);
                errors++;
            end
            if (blocked_source_not_clean !== exp_block_source_not_clean) begin
                $error("%s: blocked_source_not_clean expected %0b got %0b", label, exp_block_source_not_clean, blocked_source_not_clean);
                errors++;
            end
            if (blocked_exception_or_squash !== exp_block_exception_or_squash) begin
                $error("%s: blocked_exception_or_squash expected %0b got %0b", label, exp_block_exception_or_squash, blocked_exception_or_squash);
                errors++;
            end
            if (blocked_replay_or_squash_epoch !== exp_block_replay_or_squash_epoch) begin
                $error("%s: blocked_replay_or_squash_epoch expected %0b got %0b", label, exp_block_replay_or_squash_epoch, blocked_replay_or_squash_epoch);
                errors++;
            end
            if (blocked_alias_or_order !== exp_block_alias_or_order) begin
                $error("%s: blocked_alias_or_order expected %0b got %0b", label, exp_block_alias_or_order, blocked_alias_or_order);
                errors++;
            end
            if (blocked_translation_or_permission !== exp_block_translation_or_permission) begin
                $error("%s: blocked_translation_or_permission expected %0b got %0b", label, exp_block_translation_or_permission, blocked_translation_or_permission);
                errors++;
            end
            if (proof_valid && (
                !dep_retire_valid
                || !dep_is_memory
                || !src_tag_valid
                || !src_executed
                || !src_retired
                || src_exception
                || !src_older_than_dep
                || !tag_live
                || tag_stale
                || tag_replay_gen != dep_replay_gen
                || tag_squash_epoch != current_squash_epoch
                || tag_alias_gen != current_alias_gen
                || dep_exception
                || dep_squashed
                || memory_order_violation
                || !target_translation_ok
                || !target_permission_ok
            )) begin
                $error("%s: soundness guard allowed an unsafe proof", label);
                errors++;
            end

            if (proof_valid) legal_proof_seen++;
            if (blocked_execute_stage) execute_stage_block_seen++;
            if (blocked_not_retire) not_retire_seen++;
            if (blocked_not_memory) not_memory_seen++;
            if (blocked_no_live_tag) no_live_tag_seen++;
            if (blocked_source_not_clean) source_not_clean_seen++;
            if (blocked_exception_or_squash) exception_squash_seen++;
            if (blocked_replay_or_squash_epoch) replay_squash_seen++;
            if (blocked_alias_or_order) alias_order_seen++;
            if (blocked_translation_or_permission) translation_perm_seen++;
            if (is_random && proof_valid) random_proof_seen++;
            if (is_random && (
                blocked_execute_stage
                || blocked_not_retire
                || blocked_not_memory
                || blocked_no_live_tag
                || blocked_source_not_clean
                || blocked_exception_or_squash
                || blocked_replay_or_squash_epoch
                || blocked_alias_or_order
                || blocked_translation_or_permission
            )) begin
                random_block_seen++;
            end
            @(posedge clk);
        end
    endtask

    task automatic directed_tests;
        begin
            @(negedge clk);
            set_legal();
            check_now("legal retire proof", 1'b0);

            @(negedge clk);
            set_legal();
            dep_retire_valid = 1'b0;
            check_now("execute stage cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            dep_is_memory = 1'b0;
            check_now("non-memory retire cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            src_tag_valid = 1'b0;
            check_now("missing source tag cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            tag_live = 1'b0;
            check_now("dead tag cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            tag_stale = 1'b1;
            check_now("stale tag cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            src_executed = 1'b0;
            check_now("source not executed cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            src_retired = 1'b0;
            check_now("source not retired cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            src_exception = 1'b1;
            check_now("source exception cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            src_older_than_dep = 1'b0;
            check_now("younger source cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            dep_exception = 1'b1;
            check_now("dependent exception cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            dep_squashed = 1'b1;
            check_now("dependent squash cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            dep_replay_gen = 4'h4;
            check_now("replay generation mismatch cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            current_squash_epoch = 4'h7;
            check_now("squash epoch mismatch cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            current_alias_gen = 4'h9;
            check_now("same-line alias generation mismatch cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            memory_order_violation = 1'b1;
            check_now("memory-order violation cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            target_translation_ok = 1'b0;
            check_now("translation failure cannot prove", 1'b0);

            @(negedge clk);
            set_legal();
            target_permission_ok = 1'b0;
            check_now("permission failure cannot prove", 1'b0);
        end
    endtask

    task automatic random_cycle(input int trial);
        int r;
        begin
            @(negedge clk);
            r = $urandom();
            set_legal();
            src_tag_valid = (r[0] || (trial % 13 != 0));
            src_executed = (r[1] || (trial % 17 != 0));
            src_retired = (r[2] || (trial % 19 != 0));
            src_exception = (trial % 23) == 0;
            src_older_than_dep = (r[3] || (trial % 29 != 0));
            tag_live = (r[4] || (trial % 31 != 0));
            tag_stale = (trial % 37) == 0;
            tag_replay_gen = $urandom_range(0, (1 << REPLAY_GEN_W) - 1);
            dep_replay_gen = (trial % 11 == 0) ? (tag_replay_gen ^ 4'h1) : tag_replay_gen;
            tag_squash_epoch = $urandom_range(0, (1 << SQUASH_EPOCH_W) - 1);
            current_squash_epoch = (trial % 7 == 0) ? (tag_squash_epoch ^ 4'h1) : tag_squash_epoch;
            tag_alias_gen = $urandom_range(0, (1 << ALIAS_GEN_W) - 1);
            current_alias_gen = (trial % 5 == 0) ? (tag_alias_gen ^ 4'h1) : tag_alias_gen;
            dep_execute_valid = (r[5] || (trial % 3 != 0));
            dep_retire_valid = (r[6] || (trial % 41 != 0));
            dep_is_memory = (r[7] || (trial % 43 != 0));
            dep_exception = (trial % 47) == 0;
            dep_squashed = (trial % 53) == 0;
            memory_order_violation = (trial % 59) == 0;
            target_translation_ok = (r[8] || (trial % 61 != 0));
            target_permission_ok = (r[9] || (trial % 67 != 0));
            check_now($sformatf("random_%0d", trial), 1'b1);
        end
    endtask

    initial begin
        errors = 0;
        legal_proof_seen = 0;
        execute_stage_block_seen = 0;
        not_retire_seen = 0;
        not_memory_seen = 0;
        no_live_tag_seen = 0;
        source_not_clean_seen = 0;
        exception_squash_seen = 0;
        replay_squash_seen = 0;
        alias_order_seen = 0;
        translation_perm_seen = 0;
        random_proof_seen = 0;
        random_block_seen = 0;

        set_legal();
        repeat (3) @(posedge clk);

        directed_tests();
        for (int trial = 0; trial < TRIALS; trial++) begin
            random_cycle(trial);
        end

        if (
            errors != 0
            || legal_proof_seen == 0
            || execute_stage_block_seen == 0
            || not_retire_seen == 0
            || not_memory_seen == 0
            || no_live_tag_seen == 0
            || source_not_clean_seen == 0
            || exception_squash_seen == 0
            || replay_squash_seen == 0
            || alias_order_seen == 0
            || translation_perm_seen == 0
            || random_proof_seen == 0
            || random_block_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER ROPL-LSQ retire guard coverage failed: errors=%0d legal=%0d execute_stage=%0d not_retire=%0d not_memory=%0d no_live_tag=%0d source=%0d exception=%0d replay_squash=%0d alias_order=%0d translation_perm=%0d random_proof=%0d random_block=%0d",
                errors,
                legal_proof_seen,
                execute_stage_block_seen,
                not_retire_seen,
                not_memory_seen,
                no_live_tag_seen,
                source_not_clean_seen,
                exception_squash_seen,
                replay_squash_seen,
                alias_order_seen,
                translation_perm_seen,
                random_proof_seen,
                random_block_seen
            );
        end

        $display(
            "COPPER ROPL-LSQ retire guard completed: directed=18 random=%0d legal=%0d execute_stage=%0d not_retire=%0d not_memory=%0d no_live_tag=%0d source=%0d exception=%0d replay_squash=%0d alias_order=%0d translation_perm=%0d random_proof=%0d random_block=%0d errors=%0d",
            TRIALS,
            legal_proof_seen,
            execute_stage_block_seen,
            not_retire_seen,
            not_memory_seen,
            no_live_tag_seen,
            source_not_clean_seen,
            exception_squash_seen,
            replay_squash_seen,
            alias_order_seen,
            translation_perm_seen,
            random_proof_seen,
            random_block_seen,
            errors
        );
        $finish;
    end

endmodule
