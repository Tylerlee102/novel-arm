`timescale 1ns/1ps

module copper_provenance_epoch_boundary_tb;
    localparam int DOMAIN_W = 2;
    localparam int EPOCH_W = 3;
    localparam int TOKEN_W = 12;

    logic clk;
    logic rst_n;

    logic boundary_valid;
    logic [DOMAIN_W-1:0] boundary_domain;
    logic boundary_ack;
    logic wrap_flush_required;

    logic wrap_clear_valid;
    logic [DOMAIN_W-1:0] wrap_clear_domain;
    logic wrap_clear_ack;

    logic commit_valid;
    logic [DOMAIN_W-1:0] commit_domain;
    logic [TOKEN_W-1:0] commit_base_token;
    logic [EPOCH_W-1:0] commit_epoch;
    logic [TOKEN_W-1:0] commit_epoch_token;
    logic commit_domain_blocked;

    logic dmp_valid;
    logic [DOMAIN_W-1:0] dmp_domain;
    logic [TOKEN_W-1:0] dmp_base_token;
    logic [EPOCH_W-1:0] dmp_epoch;
    logic [TOKEN_W-1:0] dmp_epoch_token;
    logic dmp_domain_blocked;

    logic stored_valid;
    logic [EPOCH_W-1:0] stored_epoch;
    logic [TOKEN_W-1:0] stored_epoch_token;
    logic proof_epoch_match;
    logic proof_token_match;
    logic proof_current;

    int errors;
    int directed;
    int boundaries;
    int stale_blocks;
    int domain_isolation_hits;
    int wrap_blocks;

    copper_provenance_epoch_boundary #(
        .DOMAIN_W(DOMAIN_W),
        .EPOCH_W(EPOCH_W),
        .TOKEN_W(TOKEN_W)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .boundary_valid(boundary_valid),
        .boundary_domain(boundary_domain),
        .boundary_ack(boundary_ack),
        .wrap_flush_required(wrap_flush_required),
        .wrap_clear_valid(wrap_clear_valid),
        .wrap_clear_domain(wrap_clear_domain),
        .wrap_clear_ack(wrap_clear_ack),
        .commit_valid(commit_valid),
        .commit_domain(commit_domain),
        .commit_base_token(commit_base_token),
        .commit_epoch(commit_epoch),
        .commit_epoch_token(commit_epoch_token),
        .commit_domain_blocked(commit_domain_blocked),
        .dmp_valid(dmp_valid),
        .dmp_domain(dmp_domain),
        .dmp_base_token(dmp_base_token),
        .dmp_epoch(dmp_epoch),
        .dmp_epoch_token(dmp_epoch_token),
        .dmp_domain_blocked(dmp_domain_blocked),
        .stored_valid(stored_valid),
        .stored_epoch(stored_epoch),
        .stored_epoch_token(stored_epoch_token),
        .proof_epoch_match(proof_epoch_match),
        .proof_token_match(proof_token_match),
        .proof_current(proof_current)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic fail(input string msg);
        begin
            $error("%s", msg);
            errors++;
        end
    endtask

    task automatic reset_dut();
        begin
            rst_n = 1'b0;
            boundary_valid = 1'b0;
            boundary_domain = '0;
            wrap_clear_valid = 1'b0;
            wrap_clear_domain = '0;
            commit_valid = 1'b0;
            commit_domain = '0;
            commit_base_token = '0;
            dmp_valid = 1'b0;
            dmp_domain = '0;
            dmp_base_token = '0;
            stored_valid = 1'b0;
            stored_epoch = '0;
            stored_epoch_token = '0;
            repeat (3) @(posedge clk);
            rst_n = 1'b1;
            @(posedge clk);
        end
    endtask

    task automatic capture_proof(
        input logic [DOMAIN_W-1:0] domain,
        input logic [TOKEN_W-1:0] token
    );
        begin
            commit_valid = 1'b1;
            commit_domain = domain;
            commit_base_token = token;
            #1;
            stored_valid = 1'b1;
            stored_epoch = commit_epoch;
            stored_epoch_token = commit_epoch_token;
            commit_valid = 1'b0;
            directed++;
        end
    endtask

    task automatic query_expect(
        input string name,
        input logic [DOMAIN_W-1:0] domain,
        input logic [TOKEN_W-1:0] token,
        input logic expect_current
    );
        begin
            dmp_valid = 1'b1;
            dmp_domain = domain;
            dmp_base_token = token;
            #1;
            if (proof_current !== expect_current) begin
                fail($sformatf(
                    "%s: proof_current expected %0b got %0b",
                    name, expect_current, proof_current));
            end
            if (!expect_current && stored_valid && stored_epoch != dmp_epoch) begin
                stale_blocks++;
            end
            if (expect_current) begin
                domain_isolation_hits++;
            end
            dmp_valid = 1'b0;
            directed++;
        end
    endtask

    task automatic boundary_step(input logic [DOMAIN_W-1:0] domain);
        begin
            boundary_valid = 1'b1;
            boundary_domain = domain;
            @(posedge clk);
            #1;
            if (!boundary_ack) begin
                fail("boundary did not acknowledge before wrap");
            end
            if (wrap_flush_required) begin
                fail("boundary unexpectedly requested wrap flush");
            end
            boundary_valid = 1'b0;
            boundaries++;
            @(posedge clk);
        end
    endtask

    task automatic boundary_until_wrap(input logic [DOMAIN_W-1:0] domain);
        begin
            while (wrap_flush_required !== 1'b1) begin
                boundary_valid = 1'b1;
                boundary_domain = domain;
                @(posedge clk);
                #1;
                if (boundary_ack) begin
                    boundaries++;
                end
                if (boundary_ack && dmp_epoch == {EPOCH_W{1'b1}}) begin
                    fail("boundary acknowledged past max epoch");
                end
            end
            boundary_valid = 1'b0;
            wrap_blocks++;
            @(posedge clk);
        end
    endtask

    initial begin
        errors = 0;
        directed = 0;
        boundaries = 0;
        stale_blocks = 0;
        domain_isolation_hits = 0;
        wrap_blocks = 0;

        reset_dut();

        capture_proof(2'd0, 12'h5a5);
        query_expect("same epoch/domain allows", 2'd0, 12'h5a5, 1'b1);
        query_expect("wrong token blocks", 2'd0, 12'h123, 1'b0);

        boundary_step(2'd0);
        query_expect("boundary makes old domain0 proof stale", 2'd0, 12'h5a5, 1'b0);

        capture_proof(2'd0, 12'h5a5);
        query_expect("new domain0 proof allows", 2'd0, 12'h5a5, 1'b1);

        capture_proof(2'd1, 12'h777);
        boundary_step(2'd0);
        query_expect("domain1 survives domain0 boundary", 2'd1, 12'h777, 1'b1);

        capture_proof(2'd2, 12'hab4);
        boundary_until_wrap(2'd2);
        dmp_valid = 1'b1;
        dmp_domain = 2'd2;
        dmp_base_token = 12'hab4;
        #1;
        if (!dmp_domain_blocked || proof_current) begin
            fail("wrap-pending domain must block queries");
        end
        dmp_valid = 1'b0;

        commit_valid = 1'b1;
        commit_domain = 2'd2;
        commit_base_token = 12'hab4;
        #1;
        if (!commit_domain_blocked) begin
            fail("wrap-pending domain must block commits");
        end
        commit_valid = 1'b0;

        wrap_clear_valid = 1'b1;
        wrap_clear_domain = 2'd2;
        @(posedge clk);
        #1;
        if (!wrap_clear_ack) begin
            fail("wrap clear did not acknowledge");
        end
        wrap_clear_valid = 1'b0;
        @(posedge clk);

        capture_proof(2'd2, 12'hab4);
        query_expect("post-clear domain2 proof allows", 2'd2, 12'hab4, 1'b1);

        if (errors != 0 || boundaries < 3 || stale_blocks < 1 ||
            domain_isolation_hits < 4 || wrap_blocks < 1) begin
            $fatal(1,
                "COPPER PEB coverage failed: errors=%0d boundaries=%0d stale=%0d isolation=%0d wrap=%0d",
                errors, boundaries, stale_blocks, domain_isolation_hits,
                wrap_blocks);
        end

        $display(
            "COPPER PEB tests completed: directed=%0d boundaries=%0d stale_blocks=%0d domain_isolation_hits=%0d wrap_blocks=%0d errors=%0d",
            directed, boundaries, stale_blocks, domain_isolation_hits,
            wrap_blocks, errors);
        $finish;
    end
endmodule
