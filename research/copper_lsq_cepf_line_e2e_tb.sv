`timescale 1ns/1ps

// COPPER backend-to-cache end-to-end harness.
//
// This connects the LSQ-style source-tag tracker to the commit-epoch proof
// bridge and then to the line-resident provenance gate. The checked contract is
// intentionally narrow: a dependent memory operation may materialize DMP
// authority only after a clean commit whose source tag is live, unstale, and
// epoch/value-current. The resulting cache-line proof is then consumed by the
// DMP gate on later cycles and cleared by writes, fills, and invalidations.

module copper_lsq_cepf_line_e2e_tb;

    localparam int TAG_ENTRIES = 8;
    localparam int TAG_W = 3;
    localparam int LINE_IDX_W = 4;
    localparam int WORDS_PER_LINE = 4;
    localparam int WORD_OFF_W = 2;
    localparam int DOMAIN_W = 4;
    localparam int EPOCH_W = 4;
    localparam int VALUE_W = 12;
    localparam int LINES = 16;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;
    logic started;

    logic flush_valid;
    logic capture_valid;
    logic [TAG_W-1:0] capture_tag;
    logic [LINE_IDX_W-1:0] capture_src_line_idx;
    logic [WORD_OFF_W-1:0] capture_src_word;
    logic [DOMAIN_W-1:0] capture_src_domain;
    logic [EPOCH_W-1:0] capture_src_epoch;
    logic [VALUE_W-1:0] capture_src_value_hash;
    logic clear_tag_valid;
    logic [TAG_W-1:0] clear_tag;
    logic source_write_valid;
    logic [LINE_IDX_W-1:0] source_write_line_idx;
    logic [WORD_OFF_W-1:0] source_write_word;
    logic line_fill_valid;
    logic [LINE_IDX_W-1:0] line_fill_idx;
    logic invalidate_valid;
    logic [LINE_IDX_W-1:0] invalidate_line_idx;

    logic commit_valid;
    logic commit_is_memory;
    logic commit_dep_tag_valid;
    logic [TAG_W-1:0] commit_dep_tag;
    logic commit_exception;
    logic commit_squashed;
    logic commit_translation_ok;
    logic commit_permission_ok;
    logic [EPOCH_W-1:0] commit_src_current_epoch;
    logic [VALUE_W-1:0] commit_src_current_value_hash;

    logic lsq_proof_valid;
    logic [LINE_IDX_W-1:0] lsq_proof_line_idx;
    logic [WORD_OFF_W-1:0] lsq_proof_word;
    logic [DOMAIN_W-1:0] lsq_proof_domain;
    logic [EPOCH_W-1:0] lsq_proof_epoch;
    logic [VALUE_W-1:0] lsq_proof_value_hash;
    logic lsq_blocked_not_commit;
    logic lsq_blocked_no_tag;
    logic lsq_blocked_fault_or_perm;
    logic lsq_blocked_tag_stale;
    logic lsq_blocked_epoch_value_mismatch;

    logic bridge_proof_valid;
    logic [LINE_IDX_W-1:0] bridge_proof_line_idx;
    logic [WORD_OFF_W-1:0] bridge_proof_word;
    logic [DOMAIN_W-1:0] bridge_proof_domain;
    logic bridge_blocked_not_commit;
    logic bridge_blocked_no_source;
    logic bridge_blocked_fault_or_perm;
    logic bridge_blocked_epoch_mismatch;

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

    logic sh_valid [TAG_ENTRIES];
    logic sh_stale [TAG_ENTRIES];
    logic [LINE_IDX_W-1:0] sh_line [TAG_ENTRIES];
    logic [WORD_OFF_W-1:0] sh_word [TAG_ENTRIES];
    logic [DOMAIN_W-1:0] sh_domain [TAG_ENTRIES];
    logic [EPOCH_W-1:0] sh_epoch [TAG_ENTRIES];
    logic [VALUE_W-1:0] sh_value [TAG_ENTRIES];
    logic [WORDS_PER_LINE-1:0] sh_line_proof_bits [LINES];
    logic [DOMAIN_W-1:0] sh_line_domain [LINES];

    logic exp_tag_live;
    logic exp_base_ok;
    logic exp_fault_ok;
    logic exp_epoch_value_ok;
    logic exp_same_cycle_kill;
    logic exp_lsq_proof;
    logic exp_lsq_not_commit;
    logic exp_lsq_no_tag;
    logic exp_lsq_fault_perm;
    logic exp_lsq_stale;
    logic exp_lsq_epoch_value;
    logic exp_bridge_proof;
    logic exp_source_clean;
    logic exp_dmp_allow;
    logic exp_dmp_block;

    int errors;
    int bridge_proof_seen;
    int materialized_allow_seen;
    int same_cycle_dmp_block_seen;
    int no_tag_seen;
    int stale_seen;
    int same_cycle_kill_seen;
    int epoch_mismatch_seen;
    int value_mismatch_seen;
    int fault_perm_seen;
    int not_commit_seen;
    int flush_seen;
    int clear_seen;
    int write_clear_seen;
    int fill_clear_seen;
    int invalidate_clear_seen;
    int domain_block_seen;
    int translation_block_seen;
    int permission_block_seen;
    int random_allow_seen;
    int random_block_seen;

    copper_lsq_source_tag_tracker #(
        .TAG_ENTRIES(TAG_ENTRIES),
        .TAG_W(TAG_W),
        .LINE_IDX_W(LINE_IDX_W),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .EPOCH_W(EPOCH_W),
        .VALUE_W(VALUE_W)
    ) tracker (
        .clk(clk),
        .rst_n(rst_n),
        .flush_valid(flush_valid),
        .capture_valid(capture_valid),
        .capture_tag(capture_tag),
        .capture_src_line_idx(capture_src_line_idx),
        .capture_src_word(capture_src_word),
        .capture_src_domain(capture_src_domain),
        .capture_src_epoch(capture_src_epoch),
        .capture_src_value_hash(capture_src_value_hash),
        .clear_tag_valid(clear_tag_valid),
        .clear_tag(clear_tag),
        .source_write_valid(source_write_valid),
        .source_write_line_idx(source_write_line_idx),
        .source_write_word(source_write_word),
        .line_fill_valid(line_fill_valid),
        .line_fill_idx(line_fill_idx),
        .invalidate_valid(invalidate_valid),
        .invalidate_line_idx(invalidate_line_idx),
        .commit_valid(commit_valid),
        .commit_is_memory(commit_is_memory),
        .commit_dep_tag_valid(commit_dep_tag_valid),
        .commit_dep_tag(commit_dep_tag),
        .commit_exception(commit_exception),
        .commit_squashed(commit_squashed),
        .commit_translation_ok(commit_translation_ok),
        .commit_permission_ok(commit_permission_ok),
        .commit_src_current_epoch(commit_src_current_epoch),
        .commit_src_current_value_hash(commit_src_current_value_hash),
        .proof_valid(lsq_proof_valid),
        .proof_line_idx(lsq_proof_line_idx),
        .proof_word(lsq_proof_word),
        .proof_domain(lsq_proof_domain),
        .proof_epoch(lsq_proof_epoch),
        .proof_value_hash(lsq_proof_value_hash),
        .blocked_not_commit(lsq_blocked_not_commit),
        .blocked_no_tag(lsq_blocked_no_tag),
        .blocked_fault_or_perm(lsq_blocked_fault_or_perm),
        .blocked_tag_stale(lsq_blocked_tag_stale),
        .blocked_epoch_value_mismatch(lsq_blocked_epoch_value_mismatch)
    );

    copper_commit_epoch_proof_bridge #(
        .LINE_IDX_W(LINE_IDX_W),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .EPOCH_W(EPOCH_W)
    ) bridge (
        .commit_valid(commit_valid),
        .commit_is_memory(commit_is_memory),
        .commit_addr_dep_valid(lsq_proof_valid),
        .commit_exception(commit_exception),
        .commit_squashed(commit_squashed),
        .commit_translation_ok(commit_translation_ok),
        .commit_permission_ok(commit_permission_ok),
        .commit_src_line_idx(lsq_proof_line_idx),
        .commit_src_word(lsq_proof_word),
        .commit_src_domain(lsq_proof_domain),
        .commit_src_epoch(lsq_proof_epoch),
        .source_current_epoch(commit_src_current_epoch),
        .proof_valid(bridge_proof_valid),
        .proof_line_idx(bridge_proof_line_idx),
        .proof_word(bridge_proof_word),
        .proof_domain(bridge_proof_domain),
        .blocked_not_commit(bridge_blocked_not_commit),
        .blocked_no_source(bridge_blocked_no_source),
        .blocked_fault_or_perm(bridge_blocked_fault_or_perm),
        .blocked_epoch_mismatch(bridge_blocked_epoch_mismatch)
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
        .commit_ptr_valid(bridge_proof_valid),
        .commit_line_idx(bridge_proof_line_idx),
        .commit_word(bridge_proof_word),
        .commit_domain(bridge_proof_domain),
        .write_valid(source_write_valid),
        .write_line_idx(source_write_line_idx),
        .write_word(source_write_word),
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
        exp_tag_live = commit_dep_tag_valid && sh_valid[commit_dep_tag];
        exp_base_ok = commit_valid && commit_is_memory && !commit_squashed;
        exp_fault_ok = !commit_exception && commit_translation_ok && commit_permission_ok;
        exp_epoch_value_ok =
            exp_tag_live
            && (sh_epoch[commit_dep_tag] == commit_src_current_epoch)
            && (sh_value[commit_dep_tag] == commit_src_current_value_hash);
        exp_same_cycle_kill =
            flush_valid
            || (
                exp_tag_live
                && source_write_valid
                && (source_write_line_idx == sh_line[commit_dep_tag])
                && (source_write_word == sh_word[commit_dep_tag])
            )
            || (
                exp_tag_live
                && line_fill_valid
                && (line_fill_idx == sh_line[commit_dep_tag])
            )
            || (
                exp_tag_live
                && invalidate_valid
                && (invalidate_line_idx == sh_line[commit_dep_tag])
            );

        exp_lsq_proof =
            exp_base_ok
            && exp_tag_live
            && exp_fault_ok
            && !sh_stale[commit_dep_tag]
            && !exp_same_cycle_kill
            && exp_epoch_value_ok;

        exp_lsq_not_commit = commit_valid && (!commit_is_memory || commit_squashed);
        exp_lsq_no_tag = exp_base_ok && !exp_tag_live;
        exp_lsq_fault_perm = exp_base_ok && exp_tag_live && !exp_fault_ok;
        exp_lsq_stale =
            exp_base_ok
            && exp_tag_live
            && exp_fault_ok
            && (sh_stale[commit_dep_tag] || exp_same_cycle_kill);
        exp_lsq_epoch_value =
            exp_base_ok
            && exp_tag_live
            && exp_fault_ok
            && !sh_stale[commit_dep_tag]
            && !exp_same_cycle_kill
            && !exp_epoch_value_ok;

        exp_bridge_proof = exp_lsq_proof;

        exp_source_clean =
            sh_line_proof_bits[dmp_line_idx][dmp_word]
            && (sh_line_domain[dmp_line_idx] == dmp_src_domain);
        exp_dmp_allow =
            dmp_seed_valid
            && exp_source_clean
            && (dmp_src_domain == dmp_target_domain)
            && dmp_translation_ok
            && dmp_permission_ok;
        exp_dmp_block = dmp_seed_valid && !exp_dmp_allow;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < TAG_ENTRIES; i++) begin
                sh_valid[i] <= 1'b0;
                sh_stale[i] <= 1'b0;
                sh_line[i] <= '0;
                sh_word[i] <= '0;
                sh_domain[i] <= '0;
                sh_epoch[i] <= '0;
                sh_value[i] <= '0;
            end
            for (int line = 0; line < LINES; line++) begin
                sh_line_proof_bits[line] <= '0;
                sh_line_domain[line] <= '0;
            end
        end else begin
            if (flush_valid) begin
                for (int i = 0; i < TAG_ENTRIES; i++) begin
                    sh_valid[i] <= 1'b0;
                    sh_stale[i] <= 1'b1;
                end
            end
            for (int i = 0; i < TAG_ENTRIES; i++) begin
                if (sh_valid[i]) begin
                    if (
                        source_write_valid
                        && (source_write_line_idx == sh_line[i])
                        && (source_write_word == sh_word[i])
                    ) begin
                        sh_stale[i] <= 1'b1;
                    end
                    if (line_fill_valid && (line_fill_idx == sh_line[i])) begin
                        sh_stale[i] <= 1'b1;
                    end
                    if (invalidate_valid && (invalidate_line_idx == sh_line[i])) begin
                        sh_stale[i] <= 1'b1;
                    end
                end
            end
            if (capture_valid) begin
                sh_valid[capture_tag] <= 1'b1;
                sh_stale[capture_tag] <= 1'b0;
                sh_line[capture_tag] <= capture_src_line_idx;
                sh_word[capture_tag] <= capture_src_word;
                sh_domain[capture_tag] <= capture_src_domain;
                sh_epoch[capture_tag] <= capture_src_epoch;
                sh_value[capture_tag] <= capture_src_value_hash;
            end
            if (clear_tag_valid) begin
                sh_valid[clear_tag] <= 1'b0;
                sh_stale[clear_tag] <= 1'b0;
            end

            if (line_fill_valid) begin
                sh_line_proof_bits[line_fill_idx] <= '0;
                sh_line_domain[line_fill_idx] <= '0;
            end
            if (invalidate_valid) begin
                sh_line_proof_bits[invalidate_line_idx] <= '0;
                sh_line_domain[invalidate_line_idx] <= '0;
            end
            if (source_write_valid) begin
                sh_line_proof_bits[source_write_line_idx][source_write_word] <= 1'b0;
            end
            if (exp_bridge_proof) begin
                sh_line_proof_bits[sh_line[commit_dep_tag]][sh_word[commit_dep_tag]] <= 1'b1;
                sh_line_domain[sh_line[commit_dep_tag]] <= sh_domain[commit_dep_tag];
            end
        end
    end

    a_bridge_requires_lsq_proof:
        assert property (@(negedge clk) disable iff (!started)
            bridge_proof_valid |-> lsq_proof_valid);

    a_no_same_cycle_materialization:
        assert property (@(negedge clk) disable iff (!started)
            (bridge_proof_valid && dmp_seed_valid
             && (dmp_line_idx == bridge_proof_line_idx)
             && (dmp_word == bridge_proof_word)
             && !exp_source_clean) |-> !dmp_seed_allow);

    a_no_unproven_dmp_allow:
        assert property (@(negedge clk) disable iff (!started)
            (dmp_seed_valid && !exp_source_clean) |-> !dmp_seed_allow);

    a_domain_translation_permission_required:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_allow |-> ((dmp_src_domain == dmp_target_domain)
                && dmp_translation_ok
                && dmp_permission_ok));

    task automatic clear_inputs;
        begin
            flush_valid = 1'b0;
            capture_valid = 1'b0;
            capture_tag = '0;
            capture_src_line_idx = '0;
            capture_src_word = '0;
            capture_src_domain = '0;
            capture_src_epoch = '0;
            capture_src_value_hash = '0;
            clear_tag_valid = 1'b0;
            clear_tag = '0;
            source_write_valid = 1'b0;
            source_write_line_idx = '0;
            source_write_word = '0;
            line_fill_valid = 1'b0;
            line_fill_idx = '0;
            invalidate_valid = 1'b0;
            invalidate_line_idx = '0;
            commit_valid = 1'b0;
            commit_is_memory = 1'b1;
            commit_dep_tag_valid = 1'b0;
            commit_dep_tag = '0;
            commit_exception = 1'b0;
            commit_squashed = 1'b0;
            commit_translation_ok = 1'b1;
            commit_permission_ok = 1'b1;
            commit_src_current_epoch = '0;
            commit_src_current_value_hash = '0;
            dmp_seed_valid = 1'b0;
            dmp_line_idx = '0;
            dmp_word = '0;
            dmp_src_domain = '0;
            dmp_target_domain = '0;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
        end
    endtask

    task automatic do_capture(
        input [TAG_W-1:0] tag,
        input [LINE_IDX_W-1:0] line_idx,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] domain,
        input [EPOCH_W-1:0] epoch,
        input [VALUE_W-1:0] value_hash
    );
        begin
            capture_valid = 1'b1;
            capture_tag = tag;
            capture_src_line_idx = line_idx;
            capture_src_word = word;
            capture_src_domain = domain;
            capture_src_epoch = epoch;
            capture_src_value_hash = value_hash;
        end
    endtask

    task automatic do_commit(
        input [TAG_W-1:0] tag,
        input [EPOCH_W-1:0] current_epoch,
        input [VALUE_W-1:0] current_value_hash
    );
        begin
            commit_valid = 1'b1;
            commit_is_memory = 1'b1;
            commit_dep_tag_valid = 1'b1;
            commit_dep_tag = tag;
            commit_src_current_epoch = current_epoch;
            commit_src_current_value_hash = current_value_hash;
        end
    endtask

    task automatic do_seed(
        input [LINE_IDX_W-1:0] line_idx,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] src_domain,
        input [DOMAIN_W-1:0] target_domain
    );
        begin
            dmp_seed_valid = 1'b1;
            dmp_line_idx = line_idx;
            dmp_word = word;
            dmp_src_domain = src_domain;
            dmp_target_domain = target_domain;
            dmp_translation_ok = 1'b1;
            dmp_permission_ok = 1'b1;
        end
    endtask

    task automatic check_then_step(input string label, input bit is_random);
        begin
            #1;
            if (lsq_proof_valid !== exp_lsq_proof) begin
                $error("%s: LSQ proof expected %0b got %0b", label, exp_lsq_proof, lsq_proof_valid);
                errors++;
            end
            if (bridge_proof_valid !== exp_bridge_proof) begin
                $error("%s: bridge proof expected %0b got %0b", label, exp_bridge_proof, bridge_proof_valid);
                errors++;
            end
            if (lsq_blocked_not_commit !== exp_lsq_not_commit) begin
                $error("%s: LSQ not-commit block expected %0b got %0b", label, exp_lsq_not_commit, lsq_blocked_not_commit);
                errors++;
            end
            if (lsq_blocked_no_tag !== exp_lsq_no_tag) begin
                $error("%s: LSQ no-tag block expected %0b got %0b", label, exp_lsq_no_tag, lsq_blocked_no_tag);
                errors++;
            end
            if (lsq_blocked_fault_or_perm !== exp_lsq_fault_perm) begin
                $error("%s: LSQ fault/perm block expected %0b got %0b", label, exp_lsq_fault_perm, lsq_blocked_fault_or_perm);
                errors++;
            end
            if (lsq_blocked_tag_stale !== exp_lsq_stale) begin
                $error("%s: LSQ stale block expected %0b got %0b", label, exp_lsq_stale, lsq_blocked_tag_stale);
                errors++;
            end
            if (lsq_blocked_epoch_value_mismatch !== exp_lsq_epoch_value) begin
                $error("%s: LSQ epoch/value block expected %0b got %0b", label, exp_lsq_epoch_value, lsq_blocked_epoch_value_mismatch);
                errors++;
            end
            if (dmp_seed_allow !== exp_dmp_allow) begin
                $error("%s: DMP allow expected %0b got %0b", label, exp_dmp_allow, dmp_seed_allow);
                errors++;
            end
            if (dmp_seed_block !== exp_dmp_block) begin
                $error("%s: DMP block expected %0b got %0b", label, exp_dmp_block, dmp_seed_block);
                errors++;
            end
            if (exp_bridge_proof && dmp_seed_valid && !exp_dmp_allow) same_cycle_dmp_block_seen++;
            if (bridge_proof_valid) bridge_proof_seen++;
            if (dmp_seed_allow) materialized_allow_seen++;
            if (lsq_blocked_no_tag) no_tag_seen++;
            if (lsq_blocked_tag_stale && !exp_same_cycle_kill) stale_seen++;
            if (lsq_blocked_tag_stale && exp_same_cycle_kill) same_cycle_kill_seen++;
            if (lsq_blocked_epoch_value_mismatch && (sh_epoch[commit_dep_tag] != commit_src_current_epoch)) epoch_mismatch_seen++;
            if (lsq_blocked_epoch_value_mismatch && (sh_value[commit_dep_tag] != commit_src_current_value_hash)) value_mismatch_seen++;
            if (lsq_blocked_fault_or_perm) fault_perm_seen++;
            if (lsq_blocked_not_commit) not_commit_seen++;
            if (flush_valid) flush_seen++;
            if (clear_tag_valid) clear_seen++;
            if (dmp_seed_block && exp_source_clean && (dmp_src_domain != dmp_target_domain)) domain_block_seen++;
            if (dmp_seed_block && exp_source_clean && !dmp_translation_ok) translation_block_seen++;
            if (dmp_seed_block && exp_source_clean && !dmp_permission_ok) permission_block_seen++;
            if (is_random && dmp_seed_allow) random_allow_seen++;
            if (is_random && dmp_seed_block) random_block_seen++;
            @(posedge clk);
            #1;
        end
    endtask

    task automatic directed_tests;
        begin
            @(negedge clk);
            clear_inputs();
            do_capture(3'd2, 4'h4, 2'h1, 4'ha, 4'h3, 12'habc);
            check_then_step("capture source tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd2, 4'h3, 12'habc);
            do_seed(4'h4, 2'h1, 4'ha, 4'ha);
            check_then_step("commit proof cannot authorize same-cycle DMP", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_seed(4'h4, 2'h1, 4'ha, 4'ha);
            check_then_step("materialized proof authorizes next-cycle DMP", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_seed(4'h4, 2'h1, 4'ha, 4'hb);
            check_then_step("domain mismatch blocks proven source", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_seed(4'h4, 2'h1, 4'ha, 4'ha);
            dmp_translation_ok = 1'b0;
            check_then_step("translation failure blocks proven source", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_seed(4'h4, 2'h1, 4'ha, 4'ha);
            dmp_permission_ok = 1'b0;
            check_then_step("permission failure blocks proven source", 1'b0);

            @(negedge clk);
            clear_inputs();
            source_write_valid = 1'b1;
            source_write_line_idx = 4'h4;
            source_write_word = 2'h1;
            check_then_step("write clears materialized proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_seed(4'h4, 2'h1, 4'ha, 4'ha);
            check_then_step("written proof blocks later DMP", 1'b0);
            write_clear_seen++;

            @(negedge clk);
            clear_inputs();
            do_capture(3'd3, 4'h5, 2'h2, 4'hb, 4'h4, 12'h123);
            check_then_step("capture same-cycle-kill tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            source_write_valid = 1'b1;
            source_write_line_idx = 4'h5;
            source_write_word = 2'h2;
            do_commit(3'd3, 4'h4, 12'h123);
            check_then_step("same-cycle source write prevents proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd3, 4'h4, 12'h123);
            check_then_step("prior source write leaves tag stale", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd4, 4'h6, 2'h0, 4'hc, 4'h8, 12'h321);
            check_then_step("capture mismatch tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h9, 12'h321);
            check_then_step("epoch mismatch prevents proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h322);
            check_then_step("value mismatch prevents proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h321);
            commit_exception = 1'b1;
            check_then_step("exception prevents proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h321);
            commit_translation_ok = 1'b0;
            check_then_step("commit translation failure prevents proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h321);
            commit_permission_ok = 1'b0;
            check_then_step("commit permission failure prevents proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h321);
            commit_squashed = 1'b1;
            check_then_step("squash prevents proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            commit_valid = 1'b1;
            commit_is_memory = 1'b1;
            commit_dep_tag_valid = 1'b0;
            check_then_step("no source tag prevents proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd5, 4'h7, 2'h3, 4'hd, 4'h2, 12'h777);
            check_then_step("capture clear-test tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            clear_tag_valid = 1'b1;
            clear_tag = 3'd5;
            check_then_step("clear retires source tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd5, 4'h2, 12'h777);
            check_then_step("cleared tag cannot prove", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd6, 4'h8, 2'h1, 4'he, 4'h5, 12'h888);
            check_then_step("capture line-fill-test tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd6, 4'h5, 12'h888);
            check_then_step("create proof before fill", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_seed(4'h8, 2'h1, 4'he, 4'he);
            check_then_step("proof before fill authorizes", 1'b0);

            @(negedge clk);
            clear_inputs();
            line_fill_valid = 1'b1;
            line_fill_idx = 4'h8;
            check_then_step("line fill clears proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_seed(4'h8, 2'h1, 4'he, 4'he);
            check_then_step("filled line blocks later DMP", 1'b0);
            fill_clear_seen++;

            @(negedge clk);
            clear_inputs();
            do_capture(3'd7, 4'h9, 2'h1, 4'he, 4'h5, 12'h999);
            check_then_step("capture invalidate-test tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd7, 4'h5, 12'h999);
            check_then_step("create proof before invalidate", 1'b0);

            @(negedge clk);
            clear_inputs();
            invalidate_valid = 1'b1;
            invalidate_line_idx = 4'h9;
            check_then_step("invalidate clears proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_seed(4'h9, 2'h1, 4'he, 4'he);
            check_then_step("invalidated line blocks later DMP", 1'b0);
            invalidate_clear_seen++;

            @(negedge clk);
            clear_inputs();
            do_capture(3'd1, 4'ha, 2'h0, 4'h2, 4'h6, 12'haaa);
            check_then_step("capture flush-test tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            flush_valid = 1'b1;
            do_commit(3'd1, 4'h6, 12'haaa);
            check_then_step("flush prevents proof", 1'b0);
        end
    endtask

    task automatic random_cycle(input int trial);
        int r;
        int found_line;
        int found_word;
        logic found;
        logic [DOMAIN_W-1:0] found_domain;
        logic [TAG_W-1:0] tag;
        begin
            @(negedge clk);
            clear_inputs();
            r = $urandom();
            tag = $urandom_range(0, TAG_ENTRIES - 1);

            capture_valid = (r[3:0] < 5);
            capture_tag = tag;
            capture_src_line_idx = $urandom_range(0, LINES - 1);
            capture_src_word = $urandom_range(0, WORDS_PER_LINE - 1);
            capture_src_domain = $urandom_range(0, (1 << DOMAIN_W) - 1);
            capture_src_epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            capture_src_value_hash = $urandom_range(0, (1 << VALUE_W) - 1);

            commit_valid = (r[7:4] < 10);
            commit_is_memory = (r[11:8] < 13);
            commit_dep_tag_valid = (r[15:12] < 13);
            commit_dep_tag = (trial % 2 == 0) ? tag : $urandom_range(0, TAG_ENTRIES - 1);
            commit_exception = (trial % 29) == 0;
            commit_squashed = (trial % 31) == 0;
            commit_translation_ok = (r[19:16] < 13);
            commit_permission_ok = (r[23:20] < 13);
            if (sh_valid[commit_dep_tag] && (trial % 5 != 0)) begin
                commit_src_current_epoch = sh_epoch[commit_dep_tag];
                commit_src_current_value_hash = sh_value[commit_dep_tag];
            end else begin
                commit_src_current_epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
                commit_src_current_value_hash = $urandom_range(0, (1 << VALUE_W) - 1);
            end

            flush_valid = (trial % 997) == 0;
            clear_tag_valid = (trial % 149) == 0;
            clear_tag = commit_dep_tag;
            source_write_valid = (trial % 37) == 0;
            source_write_line_idx = sh_valid[commit_dep_tag] ? sh_line[commit_dep_tag] : capture_src_line_idx;
            source_write_word = sh_valid[commit_dep_tag] ? sh_word[commit_dep_tag] : capture_src_word;
            line_fill_valid = (trial % 211) == 0;
            line_fill_idx = sh_valid[commit_dep_tag] ? sh_line[commit_dep_tag] : capture_src_line_idx;
            invalidate_valid = (trial % 257) == 0;
            invalidate_line_idx = sh_valid[commit_dep_tag] ? sh_line[commit_dep_tag] : capture_src_line_idx;

            found = 1'b0;
            found_line = 0;
            found_word = 0;
            found_domain = '0;
            for (int line = 0; line < LINES; line++) begin
                for (int word = 0; word < WORDS_PER_LINE; word++) begin
                    if (!found && sh_line_proof_bits[line][word]) begin
                        found = 1'b1;
                        found_line = line;
                        found_word = word;
                        found_domain = sh_line_domain[line];
                    end
                end
            end

            dmp_seed_valid = (r[27:24] < 11);
            if (found && (trial % 3 != 0)) begin
                dmp_line_idx = found_line[LINE_IDX_W-1:0];
                dmp_word = found_word[WORD_OFF_W-1:0];
                dmp_src_domain = found_domain;
                dmp_target_domain = (trial % 7 == 0) ? found_domain + 1'b1 : found_domain;
            end else begin
                dmp_line_idx = $urandom_range(0, LINES - 1);
                dmp_word = $urandom_range(0, WORDS_PER_LINE - 1);
                dmp_src_domain = $urandom_range(0, (1 << DOMAIN_W) - 1);
                dmp_target_domain = (trial % 5 == 0) ? dmp_src_domain + 1'b1 : dmp_src_domain;
            end
            dmp_translation_ok = (trial % 17) != 0;
            dmp_permission_ok = (trial % 19) != 0;

            check_then_step($sformatf("random_%0d", trial), 1'b1);
        end
    endtask

    initial begin
        errors = 0;
        bridge_proof_seen = 0;
        materialized_allow_seen = 0;
        same_cycle_dmp_block_seen = 0;
        no_tag_seen = 0;
        stale_seen = 0;
        same_cycle_kill_seen = 0;
        epoch_mismatch_seen = 0;
        value_mismatch_seen = 0;
        fault_perm_seen = 0;
        not_commit_seen = 0;
        flush_seen = 0;
        clear_seen = 0;
        write_clear_seen = 0;
        fill_clear_seen = 0;
        invalidate_clear_seen = 0;
        domain_block_seen = 0;
        translation_block_seen = 0;
        permission_block_seen = 0;
        random_allow_seen = 0;
        random_block_seen = 0;
        started = 1'b0;

        clear_inputs();
        rst_n = 1'b0;
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
        repeat (2) @(posedge clk);
        started = 1'b1;

        directed_tests();
        for (int trial = 0; trial < TRIALS; trial++) begin
            random_cycle(trial);
        end

        if (
            errors != 0
            || bridge_proof_seen == 0
            || materialized_allow_seen == 0
            || same_cycle_dmp_block_seen == 0
            || no_tag_seen == 0
            || stale_seen == 0
            || same_cycle_kill_seen == 0
            || epoch_mismatch_seen == 0
            || value_mismatch_seen == 0
            || fault_perm_seen == 0
            || not_commit_seen == 0
            || flush_seen == 0
            || clear_seen == 0
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
                "COPPER LSQ-CEPF-line E2E coverage failed: errors=%0d bridge_proof=%0d allow=%0d same_cycle_dmp_block=%0d no_tag=%0d stale=%0d same_cycle_kill=%0d epoch_mismatch=%0d value_mismatch=%0d fault_perm=%0d not_commit=%0d flush=%0d clear=%0d write_clear=%0d fill_clear=%0d invalidate_clear=%0d domain_block=%0d translation_block=%0d permission_block=%0d random_allow=%0d random_block=%0d",
                errors,
                bridge_proof_seen,
                materialized_allow_seen,
                same_cycle_dmp_block_seen,
                no_tag_seen,
                stale_seen,
                same_cycle_kill_seen,
                epoch_mismatch_seen,
                value_mismatch_seen,
                fault_perm_seen,
                not_commit_seen,
                flush_seen,
                clear_seen,
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
            "COPPER LSQ-CEPF-line E2E completed: directed=33 random=%0d bridge_proof=%0d materialized_allow=%0d same_cycle_dmp_block=%0d no_tag=%0d stale=%0d same_cycle_kill=%0d epoch_mismatch=%0d value_mismatch=%0d fault_perm=%0d not_commit=%0d flush=%0d clear=%0d write_clear=%0d fill_clear=%0d invalidate_clear=%0d domain_block=%0d translation_block=%0d permission_block=%0d random_allow=%0d random_block=%0d errors=%0d",
            TRIALS,
            bridge_proof_seen,
            materialized_allow_seen,
            same_cycle_dmp_block_seen,
            no_tag_seen,
            stale_seen,
            same_cycle_kill_seen,
            epoch_mismatch_seen,
            value_mismatch_seen,
            fault_perm_seen,
            not_commit_seen,
            flush_seen,
            clear_seen,
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
