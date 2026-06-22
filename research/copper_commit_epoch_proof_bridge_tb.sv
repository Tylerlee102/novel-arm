`timescale 1ns/1ps

module copper_commit_epoch_proof_bridge_tb;

    localparam int LINE_IDX_W = 4;
    localparam int WORD_OFF_W = 3;
    localparam int DOMAIN_W = 4;
    localparam int EPOCH_W = 4;

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

    copper_commit_epoch_proof_bridge #(
        .LINE_IDX_W(LINE_IDX_W),
        .WORD_OFF_W(WORD_OFF_W),
        .DOMAIN_W(DOMAIN_W),
        .EPOCH_W(EPOCH_W)
    ) dut (
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

    task automatic drive_default;
        begin
            commit_valid = 1'b1;
            commit_is_memory = 1'b1;
            commit_addr_dep_valid = 1'b1;
            commit_exception = 1'b0;
            commit_squashed = 1'b0;
            commit_translation_ok = 1'b1;
            commit_permission_ok = 1'b1;
            commit_src_line_idx = 4'h7;
            commit_src_word = 3'h3;
            commit_src_domain = 4'h5;
            commit_src_epoch = 4'h9;
            source_current_epoch = 4'h9;
            #1;
        end
    endtask

    task automatic check(
        input string label,
        input logic exp_proof,
        input logic exp_not_commit,
        input logic exp_no_source,
        input logic exp_fault_perm,
        input logic exp_epoch
    );
        begin
            if (proof_valid !== exp_proof) begin
                $error("%s: proof_valid expected %0b got %0b", label, exp_proof, proof_valid);
            end
            if (blocked_not_commit !== exp_not_commit) begin
                $error("%s: blocked_not_commit expected %0b got %0b", label, exp_not_commit, blocked_not_commit);
            end
            if (blocked_no_source !== exp_no_source) begin
                $error("%s: blocked_no_source expected %0b got %0b", label, exp_no_source, blocked_no_source);
            end
            if (blocked_fault_or_perm !== exp_fault_perm) begin
                $error("%s: blocked_fault_or_perm expected %0b got %0b", label, exp_fault_perm, blocked_fault_or_perm);
            end
            if (blocked_epoch_mismatch !== exp_epoch) begin
                $error("%s: blocked_epoch_mismatch expected %0b got %0b", label, exp_epoch, blocked_epoch_mismatch);
            end
        end
    endtask

    initial begin
        drive_default();
        check("clean committed dependent memory op allows proof", 1'b1, 1'b0, 1'b0, 1'b0, 1'b0);
        if (proof_line_idx !== 4'h7 || proof_word !== 3'h3 || proof_domain !== 4'h5) begin
            $error("proof identity output mismatch");
        end

        drive_default();
        commit_valid = 1'b0;
        #1;
        check("invalid commit does not report a block", 1'b0, 1'b0, 1'b0, 1'b0, 1'b0);

        drive_default();
        commit_is_memory = 1'b0;
        #1;
        check("non-memory commit blocks proof creation", 1'b0, 1'b1, 1'b0, 1'b0, 1'b0);

        drive_default();
        commit_squashed = 1'b1;
        #1;
        check("squashed op blocks proof creation", 1'b0, 1'b1, 1'b0, 1'b0, 1'b0);

        drive_default();
        commit_addr_dep_valid = 1'b0;
        #1;
        check("missing source tag blocks proof creation", 1'b0, 1'b0, 1'b1, 1'b0, 1'b0);

        drive_default();
        commit_exception = 1'b1;
        #1;
        check("architectural exception blocks proof creation", 1'b0, 1'b0, 1'b0, 1'b1, 1'b0);

        drive_default();
        commit_translation_ok = 1'b0;
        #1;
        check("translation failure blocks proof creation", 1'b0, 1'b0, 1'b0, 1'b1, 1'b0);

        drive_default();
        commit_permission_ok = 1'b0;
        #1;
        check("permission failure blocks proof creation", 1'b0, 1'b0, 1'b0, 1'b1, 1'b0);

        drive_default();
        source_current_epoch = 4'ha;
        #1;
        check("stale source epoch blocks proof creation", 1'b0, 1'b0, 1'b0, 1'b0, 1'b1);

        $display("COPPER commit-epoch proof bridge directed tests completed");
        $finish;
    end

endmodule
