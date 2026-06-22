`timescale 1ns/1ps

module copper_lsq_source_tag_tracker_tb;

    localparam int TAG_ENTRIES = 8;
    localparam int TAG_W = 3;
    localparam int LINE_IDX_W = 4;
    localparam int WORD_OFF_W = 2;
    localparam int DOMAIN_W = 4;
    localparam int EPOCH_W = 4;
    localparam int VALUE_W = 12;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;

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
    logic proof_valid;
    logic [LINE_IDX_W-1:0] proof_line_idx;
    logic [WORD_OFF_W-1:0] proof_word;
    logic [DOMAIN_W-1:0] proof_domain;
    logic [EPOCH_W-1:0] proof_epoch;
    logic [VALUE_W-1:0] proof_value_hash;
    logic blocked_not_commit;
    logic blocked_no_tag;
    logic blocked_fault_or_perm;
    logic blocked_tag_stale;
    logic blocked_epoch_value_mismatch;

    logic sh_valid [TAG_ENTRIES];
    logic sh_stale [TAG_ENTRIES];
    logic [LINE_IDX_W-1:0] sh_line [TAG_ENTRIES];
    logic [WORD_OFF_W-1:0] sh_word [TAG_ENTRIES];
    logic [DOMAIN_W-1:0] sh_domain [TAG_ENTRIES];
    logic [EPOCH_W-1:0] sh_epoch [TAG_ENTRIES];
    logic [VALUE_W-1:0] sh_value [TAG_ENTRIES];

    logic exp_proof;
    logic exp_not_commit;
    logic exp_no_tag;
    logic exp_fault_perm;
    logic exp_tag_stale;
    logic exp_epoch_value;
    logic exp_same_cycle_kill;
    logic exp_tag_live;
    logic exp_base_ok;
    logic exp_fault_ok;
    logic exp_epoch_value_ok;

    int errors;
    int clean_proof_seen;
    int capture_no_proof_seen;
    int no_tag_seen;
    int stale_seen;
    int same_cycle_kill_seen;
    int epoch_mismatch_seen;
    int value_mismatch_seen;
    int fault_perm_seen;
    int not_commit_seen;
    int flush_seen;
    int clear_seen;
    int random_proof_seen;
    int random_block_seen;

    copper_lsq_source_tag_tracker #(
        .TAG_ENTRIES(TAG_ENTRIES),
        .TAG_W(TAG_W),
        .LINE_IDX_W(LINE_IDX_W),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .EPOCH_W(EPOCH_W),
        .VALUE_W(VALUE_W)
    ) dut (
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
        .proof_valid(proof_valid),
        .proof_line_idx(proof_line_idx),
        .proof_word(proof_word),
        .proof_domain(proof_domain),
        .proof_epoch(proof_epoch),
        .proof_value_hash(proof_value_hash),
        .blocked_not_commit(blocked_not_commit),
        .blocked_no_tag(blocked_no_tag),
        .blocked_fault_or_perm(blocked_fault_or_perm),
        .blocked_tag_stale(blocked_tag_stale),
        .blocked_epoch_value_mismatch(blocked_epoch_value_mismatch)
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

        exp_proof =
            exp_base_ok
            && exp_tag_live
            && exp_fault_ok
            && !sh_stale[commit_dep_tag]
            && !exp_same_cycle_kill
            && exp_epoch_value_ok;

        exp_not_commit = commit_valid && (!commit_is_memory || commit_squashed);
        exp_no_tag = exp_base_ok && !exp_tag_live;
        exp_fault_perm = exp_base_ok && exp_tag_live && !exp_fault_ok;
        exp_tag_stale =
            exp_base_ok
            && exp_tag_live
            && exp_fault_ok
            && (sh_stale[commit_dep_tag] || exp_same_cycle_kill);
        exp_epoch_value =
            exp_base_ok
            && exp_tag_live
            && exp_fault_ok
            && !sh_stale[commit_dep_tag]
            && !exp_same_cycle_kill
            && !exp_epoch_value_ok;
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
        end
    end

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
        end
    endtask

    task automatic do_capture(
        input [TAG_W-1:0] tag,
        input [LINE_IDX_W-1:0] line,
        input [WORD_OFF_W-1:0] word,
        input [DOMAIN_W-1:0] domain,
        input [EPOCH_W-1:0] epoch,
        input [VALUE_W-1:0] value_hash
    );
        begin
            capture_valid = 1'b1;
            capture_tag = tag;
            capture_src_line_idx = line;
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

    task automatic check_then_step(input string label, input bit is_random);
        begin
            #1;
            if (proof_valid !== exp_proof) begin
                $error("%s: proof expected %0b got %0b", label, exp_proof, proof_valid);
                errors++;
            end
            if (blocked_not_commit !== exp_not_commit) begin
                $error("%s: blocked_not_commit expected %0b got %0b", label, exp_not_commit, blocked_not_commit);
                errors++;
            end
            if (blocked_no_tag !== exp_no_tag) begin
                $error("%s: blocked_no_tag expected %0b got %0b", label, exp_no_tag, blocked_no_tag);
                errors++;
            end
            if (blocked_fault_or_perm !== exp_fault_perm) begin
                $error("%s: blocked_fault_or_perm expected %0b got %0b", label, exp_fault_perm, blocked_fault_or_perm);
                errors++;
            end
            if (blocked_tag_stale !== exp_tag_stale) begin
                $error("%s: blocked_tag_stale expected %0b got %0b", label, exp_tag_stale, blocked_tag_stale);
                errors++;
            end
            if (blocked_epoch_value_mismatch !== exp_epoch_value) begin
                $error("%s: blocked_epoch_value_mismatch expected %0b got %0b", label, exp_epoch_value, blocked_epoch_value_mismatch);
                errors++;
            end
            if (proof_valid) begin
                if (
                    proof_line_idx !== sh_line[commit_dep_tag]
                    || proof_word !== sh_word[commit_dep_tag]
                    || proof_domain !== sh_domain[commit_dep_tag]
                    || proof_epoch !== sh_epoch[commit_dep_tag]
                    || proof_value_hash !== sh_value[commit_dep_tag]
                ) begin
                    $error("%s: proof identity mismatch", label);
                    errors++;
                end
                clean_proof_seen++;
            end
            if (capture_valid && !commit_valid && !proof_valid) capture_no_proof_seen++;
            if (blocked_no_tag) no_tag_seen++;
            if (blocked_tag_stale && !exp_same_cycle_kill) stale_seen++;
            if (blocked_tag_stale && exp_same_cycle_kill) same_cycle_kill_seen++;
            if (blocked_epoch_value_mismatch && (sh_epoch[commit_dep_tag] != commit_src_current_epoch)) epoch_mismatch_seen++;
            if (blocked_epoch_value_mismatch && (sh_value[commit_dep_tag] != commit_src_current_value_hash)) value_mismatch_seen++;
            if (blocked_fault_or_perm) fault_perm_seen++;
            if (blocked_not_commit) not_commit_seen++;
            if (flush_valid) flush_seen++;
            if (clear_tag_valid) clear_seen++;
            if (proof_valid && is_random) random_proof_seen++;
            if ((blocked_no_tag || blocked_fault_or_perm || blocked_tag_stale || blocked_epoch_value_mismatch || blocked_not_commit) && is_random) random_block_seen++;
            @(posedge clk);
            #1;
        end
    endtask

    task automatic directed_tests;
        begin
            @(negedge clk);
            clear_inputs();
            commit_valid = 1'b1;
            commit_is_memory = 1'b1;
            commit_dep_tag_valid = 1'b0;
            check_then_step("direct no source tag blocks", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd2, 4'h4, 2'h1, 4'ha, 4'h3, 12'habc);
            check_then_step("capture alone creates no proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd2, 4'h3, 12'habc);
            check_then_step("clean dependent commit creates proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd3, 4'h5, 2'h2, 4'hb, 4'h4, 12'h123);
            check_then_step("capture stale-test tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            source_write_valid = 1'b1;
            source_write_line_idx = 4'h5;
            source_write_word = 2'h2;
            do_commit(3'd3, 4'h4, 12'h123);
            check_then_step("same cycle source write kills commit proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd3, 4'h4, 12'h123);
            check_then_step("prior cycle source write keeps tag stale", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd4, 4'h6, 2'h0, 4'hc, 4'h8, 12'h321);
            check_then_step("capture epoch mismatch tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h9, 12'h321);
            check_then_step("epoch mismatch blocks proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h322);
            check_then_step("value mismatch blocks proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h321);
            commit_translation_ok = 1'b0;
            check_then_step("translation failure blocks proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h321);
            commit_permission_ok = 1'b0;
            check_then_step("permission failure blocks proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h321);
            commit_exception = 1'b1;
            check_then_step("exception blocks proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd4, 4'h8, 12'h321);
            commit_squashed = 1'b1;
            check_then_step("squash blocks proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            flush_valid = 1'b1;
            do_commit(3'd4, 4'h8, 12'h321);
            check_then_step("flush same cycle blocks proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd5, 4'h7, 2'h3, 4'hd, 4'h2, 12'h777);
            check_then_step("capture clear-test tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            clear_tag_valid = 1'b1;
            clear_tag = 3'd5;
            do_commit(3'd5, 4'h2, 12'h777);
            check_then_step("clear retires tag after current-cycle proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd5, 4'h2, 12'h777);
            check_then_step("cleared tag blocks later commit", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd6, 4'h8, 2'h1, 4'he, 4'h5, 12'h888);
            check_then_step("capture fill-test tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            line_fill_valid = 1'b1;
            line_fill_idx = 4'h8;
            do_commit(3'd6, 4'h5, 12'h888);
            check_then_step("same cycle fill kills proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd6, 4'h5, 12'h888);
            check_then_step("prior cycle line fill keeps tag stale", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_capture(3'd7, 4'h9, 2'h1, 4'he, 4'h5, 12'h999);
            check_then_step("capture invalidate-test tag", 1'b0);

            @(negedge clk);
            clear_inputs();
            invalidate_valid = 1'b1;
            invalidate_line_idx = 4'h9;
            do_commit(3'd7, 4'h5, 12'h999);
            check_then_step("same cycle invalidate kills proof", 1'b0);

            @(negedge clk);
            clear_inputs();
            do_commit(3'd7, 4'h5, 12'h999);
            check_then_step("prior cycle invalidate keeps tag stale", 1'b0);
        end
    endtask

    task automatic random_cycle(input int trial);
        int r;
        logic [TAG_W-1:0] tag;
        begin
            @(negedge clk);
            clear_inputs();
            r = $urandom();
            tag = $urandom_range(0, TAG_ENTRIES - 1);

            capture_valid = (r[3:0] < 6);
            capture_tag = tag;
            capture_src_line_idx = $urandom_range(0, (1 << LINE_IDX_W) - 1);
            capture_src_word = $urandom_range(0, (1 << WORD_OFF_W) - 1);
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

            check_then_step($sformatf("random_%0d", trial), 1'b1);
        end
    endtask

    initial begin
        errors = 0;
        clean_proof_seen = 0;
        capture_no_proof_seen = 0;
        no_tag_seen = 0;
        stale_seen = 0;
        same_cycle_kill_seen = 0;
        epoch_mismatch_seen = 0;
        value_mismatch_seen = 0;
        fault_perm_seen = 0;
        not_commit_seen = 0;
        flush_seen = 0;
        clear_seen = 0;
        random_proof_seen = 0;
        random_block_seen = 0;

        clear_inputs();
        rst_n = 1'b0;
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
        repeat (2) @(posedge clk);

        directed_tests();
        for (int trial = 0; trial < TRIALS; trial++) begin
            random_cycle(trial);
        end

        if (
            errors != 0
            || clean_proof_seen == 0
            || capture_no_proof_seen == 0
            || no_tag_seen == 0
            || stale_seen == 0
            || same_cycle_kill_seen == 0
            || epoch_mismatch_seen == 0
            || value_mismatch_seen == 0
            || fault_perm_seen == 0
            || not_commit_seen == 0
            || flush_seen == 0
            || clear_seen == 0
            || random_proof_seen == 0
            || random_block_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER LSQ source-tag tracker coverage failed: errors=%0d clean=%0d capture_only=%0d no_tag=%0d stale=%0d same_cycle_kill=%0d epoch_mismatch=%0d value_mismatch=%0d fault_perm=%0d not_commit=%0d flush=%0d clear=%0d random_proof=%0d random_block=%0d",
                errors,
                clean_proof_seen,
                capture_no_proof_seen,
                no_tag_seen,
                stale_seen,
                same_cycle_kill_seen,
                epoch_mismatch_seen,
                value_mismatch_seen,
                fault_perm_seen,
                not_commit_seen,
                flush_seen,
                clear_seen,
                random_proof_seen,
                random_block_seen
            );
        end

        $display(
            "COPPER LSQ source-tag tracker completed: directed=21 random=%0d clean_proof=%0d capture_no_proof=%0d no_tag=%0d stale=%0d same_cycle_kill=%0d epoch_mismatch=%0d value_mismatch=%0d fault_perm=%0d not_commit=%0d flush=%0d clear=%0d random_proof=%0d random_block=%0d errors=%0d",
            TRIALS,
            clean_proof_seen,
            capture_no_proof_seen,
            no_tag_seen,
            stale_seen,
            same_cycle_kill_seen,
            epoch_mismatch_seen,
            value_mismatch_seen,
            fault_perm_seen,
            not_commit_seen,
            flush_seen,
            clear_seen,
            random_proof_seen,
            random_block_seen,
            errors
        );
        $finish;
    end

endmodule
