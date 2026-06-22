`timescale 1ns/1ps

// End-to-end COPPER CEPF -> line-provenance integration harness.
//
// This testbench connects the commit-epoch proof bridge directly to the
// line-resident DMP gate. It checks the multi-cycle contract that a committed,
// non-faulting, address-dependent memory operation can create source proof,
// while stale/faulted/squashed/unproven commits cannot; writes, fills, and
// invalidations then clear that proof before the DMP gate can use it.

module copper_cepf_line_e2e_sva_tb;

    localparam int LINE_IDX_W = 4;
    localparam int WORDS_PER_LINE = 4;
    localparam int WORD_OFF_W = 2;
    localparam int DOMAIN_W = 4;
    localparam int EPOCH_W = 4;
    localparam int LINES = 16;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;
    logic started;

    logic commit_valid;
    logic commit_is_memory;
    logic commit_addr_dep_valid;
    logic commit_exception;
    logic commit_squashed;
    logic commit_translation_ok;
    logic commit_permission_ok;
    logic [LINE_IDX_W-1:0] commit_src_line_idx;
    logic [WORD_OFF_W-1:0] commit_src_word;
    logic [DOMAIN_W-1:0] commit_src_domain;
    logic [EPOCH_W-1:0] commit_src_epoch;
    logic [EPOCH_W-1:0] source_current_epoch;

    logic proof_valid;
    logic [LINE_IDX_W-1:0] proof_line_idx;
    logic [WORD_OFF_W-1:0] proof_word;
    logic [DOMAIN_W-1:0] proof_domain;
    logic blocked_not_commit;
    logic blocked_no_source;
    logic blocked_fault_or_perm;
    logic blocked_epoch_mismatch;

    logic write_valid;
    logic [LINE_IDX_W-1:0] write_line_idx;
    logic [WORD_OFF_W-1:0] write_word;
    logic line_fill_valid;
    logic [LINE_IDX_W-1:0] line_fill_idx;
    logic invalidate_valid;
    logic [LINE_IDX_W-1:0] invalidate_line_idx;

    logic dmp_seed_valid;
    logic [LINE_IDX_W-1:0] dmp_line_idx;
    logic [WORD_OFF_W-1:0] dmp_word;
    logic [DOMAIN_W-1:0] dmp_src_domain;
    logic [DOMAIN_W-1:0] dmp_target_domain;
    logic dmp_translation_ok;
    logic dmp_permission_ok;
    logic dmp_seed_allow;
    logic dmp_seed_block;
    logic source_proven_clean;

    logic [WORDS_PER_LINE-1:0] shadow_proof_bits [LINES];
    logic [DOMAIN_W-1:0] shadow_domain [LINES];
    logic shadow_source_clean;
    logic exp_dmp_allow;
    logic exp_dmp_block;

    int errors;
    int valid_commit_seen;
    int proof_to_allow_seen;
    int unproven_block_seen;
    int stale_epoch_block_seen;
    int no_source_block_seen;
    int fault_perm_block_seen;
    int not_commit_block_seen;
    int write_clear_seen;
    int fill_clear_seen;
    int invalidate_clear_seen;
    int domain_block_seen;
    int translation_block_seen;
    int permission_block_seen;
    int random_allow_seen;
    int random_block_seen;

    copper_commit_epoch_proof_bridge #(
        .LINE_IDX_W(LINE_IDX_W),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .EPOCH_W(EPOCH_W)
    ) bridge (
        .commit_valid(commit_valid),
        .commit_is_memory(commit_is_memory),
        .commit_addr_dep_valid(commit_addr_dep_valid),
        .commit_exception(commit_exception),
        .commit_squashed(commit_squashed),
        .commit_translation_ok(commit_translation_ok),
        .commit_permission_ok(commit_permission_ok),
        .commit_src_line_idx(commit_src_line_idx),
        .commit_src_word(commit_src_word),
        .commit_src_domain(commit_src_domain),
        .commit_src_epoch(commit_src_epoch),
        .source_current_epoch(source_current_epoch),
        .proof_valid(proof_valid),
        .proof_line_idx(proof_line_idx),
        .proof_word(proof_word),
        .proof_domain(proof_domain),
        .blocked_not_commit(blocked_not_commit),
        .blocked_no_source(blocked_no_source),
        .blocked_fault_or_perm(blocked_fault_or_perm),
        .blocked_epoch_mismatch(blocked_epoch_mismatch)
    );

    copper_line_provenance_gate #(
        .LINE_IDX_W(LINE_IDX_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .LINES(LINES)
    ) line_gate (
        .clk(clk),
        .rst_n(rst_n),
        .commit_ptr_valid(proof_valid),
        .commit_line_idx(proof_line_idx),
        .commit_word(proof_word),
        .commit_domain(proof_domain),
        .write_valid(write_valid),
        .write_line_idx(write_line_idx),
        .write_word(write_word),
        .line_fill_valid(line_fill_valid),
        .line_fill_idx(line_fill_idx),
        .invalidate_valid(invalidate_valid),
        .invalidate_line_idx(invalidate_line_idx),
        .dmp_seed_valid(dmp_seed_valid),
        .dmp_line_idx(dmp_line_idx),
        .dmp_word(dmp_word),
        .dmp_src_domain(dmp_src_domain),
        .dmp_target_domain(dmp_target_domain),
        .dmp_translation_ok(dmp_translation_ok),
        .dmp_permission_ok(dmp_permission_ok),
        .dmp_seed_allow(dmp_seed_allow),
        .dmp_seed_block(dmp_seed_block),
        .source_proven_clean(source_proven_clean)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    always_comb begin
        shadow_source_clean =
            shadow_proof_bits[dmp_line_idx][dmp_word]
            && (shadow_domain[dmp_line_idx] == dmp_src_domain);

        exp_dmp_allow =
            dmp_seed_valid
            && shadow_source_clean
            && (dmp_src_domain == dmp_target_domain)
            && dmp_translation_ok
            && dmp_permission_ok;

        exp_dmp_block = dmp_seed_valid && !exp_dmp_allow;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < LINES; i++) begin
                shadow_proof_bits[i] <= '0;
                shadow_domain[i] <= '0;
            end
        end else begin
            if (line_fill_valid) begin
                shadow_proof_bits[line_fill_idx] <= '0;
                shadow_domain[line_fill_idx] <= '0;
            end
            if (invalidate_valid) begin
                shadow_proof_bits[invalidate_line_idx] <= '0;
                shadow_domain[invalidate_line_idx] <= '0;
            end
            if (write_valid) begin
                shadow_proof_bits[write_line_idx][write_word] <= 1'b0;
            end
            if (proof_valid) begin
                shadow_proof_bits[proof_line_idx][proof_word] <= 1'b1;
                shadow_domain[proof_line_idx] <= proof_domain;
            end
        end
    end

    a_e2e_allow_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_allow == exp_dmp_allow);

    a_e2e_block_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_block == exp_dmp_block);

    a_no_unproven_dmp_seed_allow:
        assert property (@(negedge clk) disable iff (!started)
            (dmp_seed_valid && !shadow_source_clean) |-> !dmp_seed_allow);

    a_domain_translation_permission_required:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_allow |-> ((dmp_src_domain == dmp_target_domain)
                && dmp_translation_ok
                && dmp_permission_ok));

    task automatic clear_cycle_inputs;
        begin
            commit_valid = 1'b0;
            commit_is_memory = 1'b1;
            commit_addr_dep_valid = 1'b1;
            commit_exception = 1'b0;
            commit_squashed = 1'b0;
            commit_translation_ok = 1'b1;
            commit_permission_ok = 1'b1;
            commit_src_line_idx = '0;
            commit_src_word = '0;
            commit_src_domain = '0;
            commit_src_epoch = '0;
            source_current_epoch = '0;

            write_valid = 1'b0;
            write_line_idx = '0;
            write_word = '0;
            line_fill_valid = 1'b0;
            line_fill_idx = '0;
            invalidate_valid = 1'b0;
            invalidate_line_idx = '0;

            dmp_seed_valid = 1'b0;
            dmp_line_idx = '0;
            dmp_word = '0;
            dmp_src_domain = '0;
            dmp_target_domain = '0;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
        end
    endtask

    task automatic set_valid_commit(
        input [LINE_IDX_W-1:0] line_idx,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] domain,
        input [EPOCH_W-1:0] epoch
    );
        begin
            commit_valid = 1'b1;
            commit_is_memory = 1'b1;
            commit_addr_dep_valid = 1'b1;
            commit_exception = 1'b0;
            commit_squashed = 1'b0;
            commit_translation_ok = 1'b1;
            commit_permission_ok = 1'b1;
            commit_src_line_idx = line_idx;
            commit_src_word = word;
            commit_src_domain = domain;
            commit_src_epoch = epoch;
            source_current_epoch = epoch;
        end
    endtask

    task automatic set_dmp_query(
        input [LINE_IDX_W-1:0] line_idx,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] src_domain,
        input [DOMAIN_W-1:0] target_domain,
        input logic translation_ok,
        input logic permission_ok
    );
        begin
            dmp_seed_valid = 1'b1;
            dmp_line_idx = line_idx;
            dmp_word = word;
            dmp_src_domain = src_domain;
            dmp_target_domain = target_domain;
            dmp_translation_ok = translation_ok;
            dmp_permission_ok = permission_ok;
        end
    endtask

    task automatic step_and_check(input string label);
        begin
            @(posedge clk);
            #1;
            if (dmp_seed_allow !== exp_dmp_allow) begin
                $error("%s: allow expected %0b got %0b", label, exp_dmp_allow, dmp_seed_allow);
                errors++;
            end
            if (dmp_seed_block !== exp_dmp_block) begin
                $error("%s: block expected %0b got %0b", label, exp_dmp_block, dmp_seed_block);
                errors++;
            end

            if (proof_valid) valid_commit_seen++;
            if (dmp_seed_allow) begin
                proof_to_allow_seen++;
                random_allow_seen++;
            end
            if (dmp_seed_block) random_block_seen++;
            if (dmp_seed_valid && !shadow_source_clean && dmp_seed_block) unproven_block_seen++;
            if (blocked_epoch_mismatch) stale_epoch_block_seen++;
            if (blocked_no_source) no_source_block_seen++;
            if (blocked_fault_or_perm) fault_perm_block_seen++;
            if (blocked_not_commit) not_commit_block_seen++;
            if (dmp_seed_valid && shadow_source_clean && (dmp_src_domain != dmp_target_domain) && dmp_seed_block) domain_block_seen++;
            if (dmp_seed_valid && shadow_source_clean && (dmp_src_domain == dmp_target_domain) && !dmp_translation_ok && dmp_seed_block) translation_block_seen++;
            if (dmp_seed_valid && shadow_source_clean && (dmp_src_domain == dmp_target_domain) && dmp_translation_ok && !dmp_permission_ok && dmp_seed_block) permission_block_seen++;
        end
    endtask

    task automatic directed_valid_commit_allows;
        begin
            clear_cycle_inputs();
            set_valid_commit(4'h3, 2'h1, 4'h5, 4'h9);
            set_dmp_query(4'h3, 2'h1, 4'h5, 4'h5, 1'b1, 1'b1);
            step_and_check("valid CEPF proof reaches line gate and allows DMP");
        end
    endtask

    task automatic directed_bad_commit_blocks;
        begin
            clear_cycle_inputs();
            set_valid_commit(4'h4, 2'h2, 4'h6, 4'h8);
            commit_src_epoch = 4'h8;
            source_current_epoch = 4'h9;
            set_dmp_query(4'h4, 2'h2, 4'h6, 4'h6, 1'b1, 1'b1);
            step_and_check("stale CEPF epoch cannot create line proof");

            clear_cycle_inputs();
            set_valid_commit(4'h5, 2'h0, 4'h7, 4'h3);
            commit_addr_dep_valid = 1'b0;
            set_dmp_query(4'h5, 2'h0, 4'h7, 4'h7, 1'b1, 1'b1);
            step_and_check("missing source tag cannot create line proof");

            clear_cycle_inputs();
            set_valid_commit(4'h5, 2'h1, 4'h7, 4'h3);
            commit_exception = 1'b1;
            set_dmp_query(4'h5, 2'h1, 4'h7, 4'h7, 1'b1, 1'b1);
            step_and_check("faulted commit cannot create line proof");

            clear_cycle_inputs();
            set_valid_commit(4'h5, 2'h2, 4'h7, 4'h3);
            commit_squashed = 1'b1;
            set_dmp_query(4'h5, 2'h2, 4'h7, 4'h7, 1'b1, 1'b1);
            step_and_check("squashed commit cannot create line proof");
        end
    endtask

    task automatic directed_clears_and_gates;
        begin
            clear_cycle_inputs();
            set_valid_commit(4'h6, 2'h1, 4'h2, 4'h1);
            set_dmp_query(4'h6, 2'h1, 4'h2, 4'h2, 1'b1, 1'b1);
            step_and_check("setup proof for clear tests");

            clear_cycle_inputs();
            set_dmp_query(4'h6, 2'h1, 4'h2, 4'h3, 1'b1, 1'b1);
            step_and_check("target domain mismatch blocks proven source");

            clear_cycle_inputs();
            set_dmp_query(4'h6, 2'h1, 4'h2, 4'h2, 1'b0, 1'b1);
            step_and_check("DMP translation failure blocks proven source");

            clear_cycle_inputs();
            set_dmp_query(4'h6, 2'h1, 4'h2, 4'h2, 1'b1, 1'b0);
            step_and_check("DMP permission failure blocks proven source");

            clear_cycle_inputs();
            write_valid = 1'b1;
            write_line_idx = 4'h6;
            write_word = 2'h1;
            set_dmp_query(4'h6, 2'h1, 4'h2, 4'h2, 1'b1, 1'b1);
            step_and_check("write clears CEPF-created line proof");
            if (dmp_seed_block) write_clear_seen++;

            clear_cycle_inputs();
            set_valid_commit(4'h7, 2'h0, 4'h4, 4'h2);
            set_dmp_query(4'h7, 2'h0, 4'h4, 4'h4, 1'b1, 1'b1);
            step_and_check("setup proof for fill clear");

            clear_cycle_inputs();
            line_fill_valid = 1'b1;
            line_fill_idx = 4'h7;
            set_dmp_query(4'h7, 2'h0, 4'h4, 4'h4, 1'b1, 1'b1);
            step_and_check("line fill clears CEPF-created proof");
            if (dmp_seed_block) fill_clear_seen++;

            clear_cycle_inputs();
            set_valid_commit(4'h8, 2'h3, 4'ha, 4'h2);
            set_dmp_query(4'h8, 2'h3, 4'ha, 4'ha, 1'b1, 1'b1);
            step_and_check("setup proof for invalidate clear");

            clear_cycle_inputs();
            invalidate_valid = 1'b1;
            invalidate_line_idx = 4'h8;
            set_dmp_query(4'h8, 2'h3, 4'ha, 4'ha, 1'b1, 1'b1);
            step_and_check("invalidate clears CEPF-created proof");
            if (dmp_seed_block) invalidate_clear_seen++;
        end
    endtask

    task automatic drive_random(input int trial);
        int r;
        begin
            clear_cycle_inputs();
            r = $urandom();

            commit_valid = (r[3:0] < 10);
            commit_is_memory = (r[7:4] < 13);
            commit_addr_dep_valid = (r[11:8] < 12);
            commit_exception = (trial % 29) == 0;
            commit_squashed = (trial % 31) == 0;
            commit_translation_ok = (r[15:12] < 13);
            commit_permission_ok = (r[19:16] < 13);
            commit_src_line_idx = $urandom_range(0, LINES - 1);
            commit_src_word = $urandom_range(0, WORDS_PER_LINE - 1);
            commit_src_domain = $urandom_range(0, (1 << DOMAIN_W) - 1);
            commit_src_epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            source_current_epoch = ((trial % 17) == 0) ? (commit_src_epoch + 1'b1) : commit_src_epoch;

            write_valid = (trial % 23) == 0;
            write_line_idx = commit_src_line_idx;
            write_word = commit_src_word;
            line_fill_valid = (trial % 101) == 0;
            line_fill_idx = commit_src_line_idx;
            invalidate_valid = (trial % 137) == 0;
            invalidate_line_idx = commit_src_line_idx;

            dmp_seed_valid = (r[23:20] < 14);
            dmp_line_idx = ((trial % 3) == 0) ? commit_src_line_idx : $urandom_range(0, LINES - 1);
            dmp_word = ((trial % 3) == 0) ? commit_src_word : $urandom_range(0, WORDS_PER_LINE - 1);
            dmp_src_domain = ((trial % 3) == 0) ? commit_src_domain : $urandom_range(0, (1 << DOMAIN_W) - 1);
            dmp_target_domain = ((trial % 11) == 0) ? (dmp_src_domain + 1'b1) : dmp_src_domain;
            dmp_translation_ok = (r[27:24] < 13);
            dmp_permission_ok = (r[31:28] < 13);

            step_and_check($sformatf("random_%0d", trial));
        end
    endtask

    initial begin
        errors = 0;
        valid_commit_seen = 0;
        proof_to_allow_seen = 0;
        unproven_block_seen = 0;
        stale_epoch_block_seen = 0;
        no_source_block_seen = 0;
        fault_perm_block_seen = 0;
        not_commit_block_seen = 0;
        write_clear_seen = 0;
        fill_clear_seen = 0;
        invalidate_clear_seen = 0;
        domain_block_seen = 0;
        translation_block_seen = 0;
        permission_block_seen = 0;
        random_allow_seen = 0;
        random_block_seen = 0;

        started = 1'b0;
        clear_cycle_inputs();
        rst_n = 1'b0;
        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
        started = 1'b1;

        clear_cycle_inputs();
        set_dmp_query(4'h1, 2'h0, 4'h1, 4'h1, 1'b1, 1'b1);
        step_and_check("unproven reset state blocks DMP");

        directed_valid_commit_allows();
        directed_bad_commit_blocks();
        directed_clears_and_gates();

        for (int trial = 0; trial < TRIALS; trial++) begin
            drive_random(trial);
        end

        if (
            errors != 0
            || valid_commit_seen == 0
            || proof_to_allow_seen == 0
            || unproven_block_seen == 0
            || stale_epoch_block_seen == 0
            || no_source_block_seen == 0
            || fault_perm_block_seen == 0
            || not_commit_block_seen == 0
            || write_clear_seen == 0
            || fill_clear_seen == 0
            || invalidate_clear_seen == 0
            || domain_block_seen == 0
            || translation_block_seen == 0
            || permission_block_seen == 0
            || random_allow_seen == 0
            || random_block_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER CEPF-line E2E coverage failed: errors=%0d valid_commit=%0d proof_to_allow=%0d unproven=%0d stale_epoch=%0d no_source=%0d fault_perm=%0d not_commit=%0d write_clear=%0d fill_clear=%0d invalidate_clear=%0d domain=%0d translation=%0d permission=%0d random_allow=%0d random_block=%0d",
                errors,
                valid_commit_seen,
                proof_to_allow_seen,
                unproven_block_seen,
                stale_epoch_block_seen,
                no_source_block_seen,
                fault_perm_block_seen,
                not_commit_block_seen,
                write_clear_seen,
                fill_clear_seen,
                invalidate_clear_seen,
                domain_block_seen,
                translation_block_seen,
                permission_block_seen,
                random_allow_seen,
                random_block_seen
            );
        end

        $display(
            "COPPER CEPF-line E2E SVA completed: directed=12 random=%0d valid_commit=%0d proof_to_allow=%0d unproven_block=%0d stale_epoch_block=%0d no_source_block=%0d fault_perm_block=%0d not_commit_block=%0d write_clear=%0d fill_clear=%0d invalidate_clear=%0d domain_block=%0d translation_block=%0d permission_block=%0d random_allow=%0d random_block=%0d errors=%0d",
            TRIALS,
            valid_commit_seen,
            proof_to_allow_seen,
            unproven_block_seen,
            stale_epoch_block_seen,
            no_source_block_seen,
            fault_perm_block_seen,
            not_commit_block_seen,
            write_clear_seen,
            fill_clear_seen,
            invalidate_clear_seen,
            domain_block_seen,
            translation_block_seen,
            permission_block_seen,
            random_allow_seen,
            random_block_seen,
            errors
        );
        $finish;
    end

endmodule
