`timescale 1ns/1ps

// CLPD source-proof directory -> CTLW target-witness directory -> full authority
// gate integration harness.
//
// The CLPD block supplies compressed source-word authority. The CTLW directory
// supplies exact target-line authority. This harness checks that the final DMP
// issue predicate opens only when both live authorities are present, unless the
// target is same-page translated, and that source-side destructive events plus
// target-side remap/TLBI events revoke the combined authority.

module copper_clpd_ctlw_authority_e2e_tb;

    localparam int SRC_LINE_W = 8;
    localparam int WORDS_PER_LINE = 16;
    localparam int WORD_OFF_W = 4;
    localparam int VALUE_W = 12;
    localparam int EPOCH_W = 4;
    localparam int TOKEN_W = 4;
    localparam int CLPD_ENTRIES = 8;
    localparam int CLPD_IDX_W = 3;
    localparam int TGT_LINE_W = 12;
    localparam int CTLW_ENTRIES = 16;
    localparam int CTLW_IDX_W = 4;
    localparam int TRIALS = 10000;

    logic clk;
    logic rst_n;
    logic started;

    logic commit_ptr_valid;
    logic [SRC_LINE_W-1:0] commit_line_tag;
    logic [WORD_OFF_W-1:0] commit_word;
    logic [TOKEN_W-1:0] commit_token;
    logic [EPOCH_W-1:0] commit_line_epoch;
    logic source_write_valid;
    logic [SRC_LINE_W-1:0] source_write_line_tag;
    logic line_fill_valid;
    logic [SRC_LINE_W-1:0] line_fill_tag;
    logic invalidate_valid;
    logic [SRC_LINE_W-1:0] invalidate_line_tag;

    logic dmp_seed_valid;
    logic [SRC_LINE_W-1:0] dmp_line_tag;
    logic [WORD_OFF_W-1:0] dmp_word;
    logic [TOKEN_W-1:0] current_token;
    logic [EPOCH_W-1:0] dmp_line_epoch;
    logic clpd_translation_ok;
    logic clpd_permission_ok;

    logic clpd_source_line_hit;
    logic clpd_source_word_proven;
    logic clpd_source_authorized;
    logic clpd_seed_allow;
    logic clpd_seed_block;
    logic clpd_block_no_entry;
    logic clpd_block_word_unproven;
    logic clpd_block_stale_epoch;
    logic clpd_block_token_mismatch;
    logic clpd_block_fault_or_perm;

    logic record_valid;
    logic [TGT_LINE_W-1:0] record_vline;
    logic [TGT_LINE_W-1:0] record_pline;
    logic [TOKEN_W-1:0] record_token;
    logic remap_valid;
    logic [TGT_LINE_W-1:0] remap_vline;
    logic [TOKEN_W-1:0] remap_token;
    logic tlbi_token_valid;
    logic [TOKEN_W-1:0] tlbi_token;
    logic tlbi_all_valid;
    logic ctlw_query_valid;
    logic [TGT_LINE_W-1:0] candidate_target_line;
    logic ctlw_witness_valid;
    logic [TGT_LINE_W-1:0] ctlw_witness_pline;
    logic ctlw_query_miss;
    logic ctlw_token_mismatch_seen;
    logic ctlw_line_mismatch_seen;
    logic ctlw_remap_clear_hit;
    logic ctlw_tlbi_clear_hit;
    logic ctlw_collision_evict;

    logic target_same_page;
    logic same_page_translation_ok;
    logic target_permission_ok;
    logic terminal_source;

    logic source_valid;
    logic source_clean;
    logic [VALUE_W-1:0] source_value;
    logic [EPOCH_W-1:0] source_epoch;
    logic proof_valid;
    logic proof_sound;
    logic [VALUE_W-1:0] proof_value;
    logic [EPOCH_W-1:0] proof_epoch;
    logic [TOKEN_W-1:0] proof_token;

    logic gate_source_authorized;
    logic gate_target_authorized;
    logic dmp_seed_allow;
    logic dmp_seed_block;
    logic block_no_source_proof;
    logic block_stale_source;
    logic block_token_mismatch;
    logic block_terminal_source;
    logic block_no_target_authority;
    logic block_fault_or_perm;

    logic exp_target_authorized;
    logic exp_allow;
    logic exp_block;

    int errors;
    int joint_cross_allow_seen;
    int same_page_allow_seen;
    int no_source_block_seen;
    int word_unproven_block_seen;
    int stale_epoch_block_seen;
    int source_token_block_seen;
    int target_no_witness_block_seen;
    int target_line_alias_block_seen;
    int remap_block_seen;
    int tlbi_block_seen;
    int write_clear_block_seen;
    int fill_clear_block_seen;
    int invalidate_clear_block_seen;
    int terminal_block_seen;
    int permission_block_seen;
    int clpd_collision_seen;
    int ctlw_collision_seen;
    int random_allow_seen;
    int random_block_seen;

    copper_clpd_gate #(
        .LINE_TAG_W(SRC_LINE_W),
        .WORDS_PER_LINE(WORDS_PER_LINE),
        .WORD_OFF_W(WORD_OFF_W),
        .TOKEN_W(TOKEN_W),
        .EPOCH_W(EPOCH_W),
        .ENTRIES(CLPD_ENTRIES),
        .ENTRY_IDX_W(CLPD_IDX_W)
    ) clpd (
        .clk(clk),
        .rst_n(rst_n),
        .commit_ptr_valid(commit_ptr_valid),
        .commit_line_tag(commit_line_tag),
        .commit_word(commit_word),
        .commit_token(commit_token),
        .commit_line_epoch(commit_line_epoch),
        .source_write_valid(source_write_valid),
        .source_write_line_tag(source_write_line_tag),
        .line_fill_valid(line_fill_valid),
        .line_fill_tag(line_fill_tag),
        .invalidate_valid(invalidate_valid),
        .invalidate_line_tag(invalidate_line_tag),
        .dmp_seed_valid(dmp_seed_valid),
        .dmp_line_tag(dmp_line_tag),
        .dmp_word(dmp_word),
        .dmp_src_token(current_token),
        .dmp_target_token(current_token),
        .dmp_line_epoch(dmp_line_epoch),
        .dmp_translation_ok(clpd_translation_ok),
        .dmp_permission_ok(clpd_permission_ok),
        .source_line_hit(clpd_source_line_hit),
        .source_word_proven(clpd_source_word_proven),
        .source_authorized(clpd_source_authorized),
        .dmp_seed_allow(clpd_seed_allow),
        .dmp_seed_block(clpd_seed_block),
        .block_no_entry(clpd_block_no_entry),
        .block_word_unproven(clpd_block_word_unproven),
        .block_stale_epoch(clpd_block_stale_epoch),
        .block_token_mismatch(clpd_block_token_mismatch),
        .block_fault_or_perm(clpd_block_fault_or_perm)
    );

    assign ctlw_query_valid = dmp_seed_valid && !target_same_page;

    copper_ctlw_witness_dir #(
        .VLINE_W(TGT_LINE_W),
        .PLINE_W(TGT_LINE_W),
        .TOKEN_W(TOKEN_W),
        .ENTRIES(CTLW_ENTRIES),
        .IDX_W(CTLW_IDX_W)
    ) ctlw (
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

    assign source_value = {dmp_line_tag, dmp_word};
    assign source_epoch = dmp_line_epoch;
    assign source_valid = 1'b1;
    assign source_clean = 1'b1;

    assign proof_valid = clpd_source_authorized;
    assign proof_sound = clpd_source_authorized;
    assign proof_value = source_value;
    assign proof_epoch = source_epoch;
    assign proof_token = current_token;

    copper_full_authority_gate #(
        .VALUE_W(VALUE_W),
        .EPOCH_W(EPOCH_W),
        .TOKEN_W(TOKEN_W),
        .LINE_W(TGT_LINE_W)
    ) authority (
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
        .source_authorized(gate_source_authorized),
        .target_authorized(gate_target_authorized),
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
        exp_target_authorized = target_same_page
            ? same_page_translation_ok
            : ctlw_witness_valid;

        exp_allow =
            dmp_seed_valid
            && clpd_source_authorized
            && !terminal_source
            && exp_target_authorized
            && target_permission_ok;

        exp_block = dmp_seed_valid && !exp_allow;
    end

    a_joint_allow_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_allow == exp_allow);

    a_joint_block_equivalence:
        assert property (@(negedge clk) disable iff (!started)
            dmp_seed_block == exp_block);

    a_cross_page_requires_both_authorities:
        assert property (@(negedge clk) disable iff (!started)
            (dmp_seed_allow && !target_same_page)
            |-> (clpd_source_authorized && ctlw_witness_valid));

    a_missing_clpd_blocks_source:
        assert property (@(negedge clk) disable iff (!started)
            (dmp_seed_valid && !clpd_source_authorized)
            |-> block_no_source_proof);

    a_missing_ctlw_blocks_target:
        assert property (@(negedge clk) disable iff (!started)
            (dmp_seed_valid && clpd_source_authorized && !target_same_page
             && !ctlw_witness_valid && !terminal_source)
            |-> block_no_target_authority);

    task automatic clear_inputs;
        begin
            commit_ptr_valid = 1'b0;
            commit_line_tag = '0;
            commit_word = '0;
            commit_token = '0;
            commit_line_epoch = '0;
            source_write_valid = 1'b0;
            source_write_line_tag = '0;
            line_fill_valid = 1'b0;
            line_fill_tag = '0;
            invalidate_valid = 1'b0;
            invalidate_line_tag = '0;

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
            dmp_line_tag = 8'h35;
            dmp_word = 4'h3;
            current_token = 4'h2;
            dmp_line_epoch = 4'h1;
            clpd_translation_ok = 1'b1;
            clpd_permission_ok = 1'b1;
            target_same_page = 1'b0;
            same_page_translation_ok = 1'b1;
            target_permission_ok = 1'b1;
            terminal_source = 1'b0;
            candidate_target_line = 12'h234;
        end
    endtask

    task automatic commit_source(
        input [SRC_LINE_W-1:0] tag,
        input [WORD_OFF_W-1:0] word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch
    );
        begin
            clear_inputs();
            if (started && clpd_source_line_hit && dmp_line_tag[CLPD_IDX_W-1:0] == tag[CLPD_IDX_W-1:0]
                && dmp_line_tag != tag) begin
                clpd_collision_seen++;
            end
            commit_ptr_valid = 1'b1;
            commit_line_tag = tag;
            commit_word = word;
            commit_token = token;
            commit_line_epoch = epoch;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic source_write(input [SRC_LINE_W-1:0] tag);
        begin
            clear_inputs();
            source_write_valid = 1'b1;
            source_write_line_tag = tag;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic source_fill(input [SRC_LINE_W-1:0] tag);
        begin
            clear_inputs();
            line_fill_valid = 1'b1;
            line_fill_tag = tag;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic source_invalidate(input [SRC_LINE_W-1:0] tag);
        begin
            clear_inputs();
            invalidate_valid = 1'b1;
            invalidate_line_tag = tag;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic record_target(
        input [TGT_LINE_W-1:0] vline,
        input [TOKEN_W-1:0] token
    );
        begin
            clear_inputs();
            record_valid = 1'b1;
            record_vline = vline;
            record_pline = vline ^ 12'h800;
            record_token = token;
            #1;
            if (ctlw_collision_evict) ctlw_collision_seen++;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic remap_target(input [TGT_LINE_W-1:0] vline, input [TOKEN_W-1:0] token);
        begin
            clear_inputs();
            remap_valid = 1'b1;
            remap_vline = vline;
            remap_token = token;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic tlbi_target_token(input [TOKEN_W-1:0] token);
        begin
            clear_inputs();
            tlbi_token_valid = 1'b1;
            tlbi_token = token;
            @(posedge clk);
            #1;
            clear_inputs();
        end
    endtask

    task automatic query_cross(
        input [SRC_LINE_W-1:0] src_tag,
        input [WORD_OFF_W-1:0] src_word,
        input [TOKEN_W-1:0] token,
        input [EPOCH_W-1:0] epoch,
        input [TGT_LINE_W-1:0] target_line
    );
        begin
            clear_inputs();
            dmp_seed_valid = 1'b1;
            dmp_line_tag = src_tag;
            dmp_word = src_word;
            current_token = token;
            dmp_line_epoch = epoch;
            target_same_page = 1'b0;
            candidate_target_line = target_line;
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
            if (dmp_seed_allow && !target_same_page && clpd_source_authorized && ctlw_witness_valid) joint_cross_allow_seen++;
            if (dmp_seed_allow && target_same_page && clpd_source_authorized) same_page_allow_seen++;
            if (dmp_seed_block && !clpd_source_authorized && block_no_source_proof) no_source_block_seen++;
            if (dmp_seed_block && clpd_block_word_unproven) word_unproven_block_seen++;
            if (dmp_seed_block && clpd_block_stale_epoch) stale_epoch_block_seen++;
            if (dmp_seed_block && clpd_block_token_mismatch) source_token_block_seen++;
            if (dmp_seed_block && clpd_source_authorized && !ctlw_witness_valid && block_no_target_authority) target_no_witness_block_seen++;
            if (dmp_seed_block && ctlw_line_mismatch_seen && block_no_target_authority) target_line_alias_block_seen++;
            if (dmp_seed_block && terminal_source && block_terminal_source) terminal_block_seen++;
            if (dmp_seed_block && !target_permission_ok && block_fault_or_perm) permission_block_seen++;
            if (dmp_seed_allow) random_allow_seen++;
            if (dmp_seed_block) random_block_seen++;
            if (ctlw_collision_evict) ctlw_collision_seen++;
            @(posedge clk);
            #1;
        end
    endtask

    task automatic directed_tests;
        begin
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("no CLPD source proof blocks before target use");

            commit_source(8'h35, 4'h3, 4'h2, 4'h1);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("source proof without CTLW target witness blocks");

            record_target(12'h234, 4'h2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("CLPD source plus CTLW target allows cross-page");

            query_cross(8'h35, 4'h4, 4'h2, 4'h1, 12'h234);
            sample_case("unproven source word blocks even with CTLW");

            query_cross(8'h35, 4'h3, 4'h2, 4'h2, 12'h234);
            sample_case("stale source-line epoch blocks even with CTLW");

            query_cross(8'h35, 4'h3, 4'h3, 4'h1, 12'h234);
            sample_case("source token mismatch blocks even with target witness");

            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h244);
            sample_case("same-index wrong target line blocks");

            remap_target(12'h234, 4'h2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h234);
            sample_case("target remap clears CTLW and blocks");
            if (dmp_seed_block) remap_block_seen++;

            record_target(12'h345, 4'h2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            sample_case("setup target for TLBI");
            tlbi_target_token(4'h2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h345);
            sample_case("target TLBI clears CTLW and blocks");
            if (dmp_seed_block) tlbi_block_seen++;

            record_target(12'h456, 4'h2);
            source_write(8'h35);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            sample_case("source write clears CLPD and blocks");
            if (dmp_seed_block) write_clear_block_seen++;

            commit_source(8'h35, 4'h3, 4'h2, 4'h1);
            source_fill(8'h35);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            sample_case("source fill clears CLPD and blocks");
            if (dmp_seed_block) fill_clear_block_seen++;

            commit_source(8'h35, 4'h3, 4'h2, 4'h1);
            source_invalidate(8'h35);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            sample_case("source invalidate clears CLPD and blocks");
            if (dmp_seed_block) invalidate_clear_block_seen++;

            commit_source(8'h35, 4'h3, 4'h2, 4'h1);
            record_target(12'h456, 4'h2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            terminal_source = 1'b1;
            sample_case("terminal source blocks combined authorities");

            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            target_permission_ok = 1'b0;
            sample_case("permission failure blocks combined authorities");

            clear_inputs();
            dmp_seed_valid = 1'b1;
            dmp_line_tag = 8'h35;
            dmp_word = 4'h3;
            current_token = 4'h2;
            dmp_line_epoch = 4'h1;
            target_same_page = 1'b1;
            same_page_translation_ok = 1'b1;
            sample_case("same-page target allows without CTLW when CLPD source holds");

            commit_source(8'h3d, 4'h7, 4'h2, 4'h1);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h456);
            sample_case("CLPD collision evicts old source proof and blocks");

            commit_source(8'h35, 4'h3, 4'h2, 4'h1);
            record_target(12'h567, 4'h2);
            record_target(12'h577, 4'h2);
            query_cross(8'h35, 4'h3, 4'h2, 4'h1, 12'h567);
            sample_case("CTLW collision evicts old target witness and blocks");
        end
    endtask

    task automatic drive_random(input int trial);
        logic [SRC_LINE_W-1:0] src_tag;
        logic [WORD_OFF_W-1:0] src_word;
        logic [TOKEN_W-1:0] token;
        logic [EPOCH_W-1:0] epoch;
        logic [TGT_LINE_W-1:0] tgt;
        begin
            src_tag = $urandom_range(0, 255);
            src_word = $urandom_range(0, WORDS_PER_LINE - 1);
            token = $urandom_range(0, (1 << TOKEN_W) - 1);
            epoch = $urandom_range(0, (1 << EPOCH_W) - 1);
            tgt = $urandom_range(0, (1 << TGT_LINE_W) - 1);

            if ((trial % 5) == 0) commit_source(src_tag, src_word, token, epoch);
            if ((trial % 7) == 0) record_target(tgt, token);
            if ((trial % 97) == 0) source_write(src_tag);
            if ((trial % 131) == 0) source_fill(src_tag);
            if ((trial % 173) == 0) source_invalidate(src_tag);
            if ((trial % 211) == 0) remap_target(tgt, token);
            if ((trial % 307) == 0) tlbi_target_token(token);

            query_cross(src_tag, src_word, token, epoch, tgt);
            if ((trial % 11) == 0) dmp_word = src_word + 1'b1;
            if ((trial % 13) == 0) dmp_line_epoch = epoch + 1'b1;
            if ((trial % 17) == 0) current_token = token + 1'b1;
            if ((trial % 19) == 0) candidate_target_line = tgt + 12'h010;
            if ((trial % 23) == 0) target_same_page = 1'b1;
            if ((trial % 29) == 0) terminal_source = 1'b1;
            if ((trial % 31) == 0) target_permission_ok = 1'b0;
            sample_case($sformatf("random_%0d", trial));
        end
    endtask

    initial begin
        errors = 0;
        joint_cross_allow_seen = 0;
        same_page_allow_seen = 0;
        no_source_block_seen = 0;
        word_unproven_block_seen = 0;
        stale_epoch_block_seen = 0;
        source_token_block_seen = 0;
        target_no_witness_block_seen = 0;
        target_line_alias_block_seen = 0;
        remap_block_seen = 0;
        tlbi_block_seen = 0;
        write_clear_block_seen = 0;
        fill_clear_block_seen = 0;
        invalidate_clear_block_seen = 0;
        terminal_block_seen = 0;
        permission_block_seen = 0;
        clpd_collision_seen = 0;
        ctlw_collision_seen = 0;
        random_allow_seen = 0;
        random_block_seen = 0;

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
            || joint_cross_allow_seen == 0
            || same_page_allow_seen == 0
            || no_source_block_seen == 0
            || word_unproven_block_seen == 0
            || stale_epoch_block_seen == 0
            || source_token_block_seen == 0
            || target_no_witness_block_seen == 0
            || target_line_alias_block_seen == 0
            || remap_block_seen == 0
            || tlbi_block_seen == 0
            || write_clear_block_seen == 0
            || fill_clear_block_seen == 0
            || invalidate_clear_block_seen == 0
            || terminal_block_seen == 0
            || permission_block_seen == 0
            || clpd_collision_seen == 0
            || ctlw_collision_seen == 0
            || random_allow_seen == 0
            || random_block_seen == 0
        ) begin
            $fatal(
                1,
                "COPPER CLPD-CTLW authority E2E coverage failed: errors=%0d joint=%0d same=%0d no_src=%0d word=%0d stale=%0d src_token=%0d no_tgt=%0d alias=%0d remap=%0d tlbi=%0d write=%0d fill=%0d inval=%0d terminal=%0d perm=%0d clpd_col=%0d ctlw_col=%0d allow=%0d block=%0d",
                errors,
                joint_cross_allow_seen,
                same_page_allow_seen,
                no_source_block_seen,
                word_unproven_block_seen,
                stale_epoch_block_seen,
                source_token_block_seen,
                target_no_witness_block_seen,
                target_line_alias_block_seen,
                remap_block_seen,
                tlbi_block_seen,
                write_clear_block_seen,
                fill_clear_block_seen,
                invalidate_clear_block_seen,
                terminal_block_seen,
                permission_block_seen,
                clpd_collision_seen,
                ctlw_collision_seen,
                random_allow_seen,
                random_block_seen
            );
        end

        $display(
            "COPPER CLPD-CTLW authority E2E tests completed: directed=18 random=%0d joint_cross_allow=%0d same_page_allow=%0d no_source_block=%0d word_unproven_block=%0d stale_epoch_block=%0d source_token_block=%0d target_no_witness_block=%0d target_line_alias_block=%0d remap_block=%0d tlbi_block=%0d write_clear_block=%0d fill_clear_block=%0d invalidate_clear_block=%0d terminal_block=%0d permission_block=%0d clpd_collision=%0d ctlw_collision=%0d random_allow=%0d random_block=%0d errors=%0d",
            TRIALS,
            joint_cross_allow_seen,
            same_page_allow_seen,
            no_source_block_seen,
            word_unproven_block_seen,
            stale_epoch_block_seen,
            source_token_block_seen,
            target_no_witness_block_seen,
            target_line_alias_block_seen,
            remap_block_seen,
            tlbi_block_seen,
            write_clear_block_seen,
            fill_clear_block_seen,
            invalidate_clear_block_seen,
            terminal_block_seen,
            permission_block_seen,
            clpd_collision_seen,
            ctlw_collision_seen,
            random_allow_seen,
            random_block_seen,
            errors
        );
        $finish;
    end

endmodule
