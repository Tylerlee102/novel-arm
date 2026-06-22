`timescale 1ns/1ps

// COPPER-PEB: Provenance Epoch Boundary.
//
// This block gives COPPER an O(1) boundary mechanism for context, ROI, VM, or
// security-domain transitions. A boundary increments a small per-domain epoch
// that is mixed into the stored proof token. Existing CLPD/proof entries then
// fail the epoch/token comparison without sweeping the directory. If an epoch
// would wrap, the block raises a flush-required condition and blocks that
// domain until external logic purges the matching proof entries.

module copper_provenance_epoch_boundary #(
    parameter int DOMAIN_W = 4,
    parameter int EPOCH_W = 8,
    parameter int TOKEN_W = 16
) (
    input  logic clk,
    input  logic rst_n,

    input  logic boundary_valid,
    input  logic [DOMAIN_W-1:0] boundary_domain,
    output logic boundary_ack,
    output logic wrap_flush_required,

    input  logic wrap_clear_valid,
    input  logic [DOMAIN_W-1:0] wrap_clear_domain,
    output logic wrap_clear_ack,

    input  logic commit_valid,
    input  logic [DOMAIN_W-1:0] commit_domain,
    input  logic [TOKEN_W-1:0] commit_base_token,
    output logic [EPOCH_W-1:0] commit_epoch,
    output logic [TOKEN_W-1:0] commit_epoch_token,
    output logic commit_domain_blocked,

    input  logic dmp_valid,
    input  logic [DOMAIN_W-1:0] dmp_domain,
    input  logic [TOKEN_W-1:0] dmp_base_token,
    output logic [EPOCH_W-1:0] dmp_epoch,
    output logic [TOKEN_W-1:0] dmp_epoch_token,
    output logic dmp_domain_blocked,

    input  logic stored_valid,
    input  logic [EPOCH_W-1:0] stored_epoch,
    input  logic [TOKEN_W-1:0] stored_epoch_token,
    output logic proof_epoch_match,
    output logic proof_token_match,
    output logic proof_current
);

    localparam int DOMAINS = 1 << DOMAIN_W;

    logic [EPOCH_W-1:0] domain_epoch [DOMAINS];
    logic wrap_pending [DOMAINS];

    function automatic logic [TOKEN_W-1:0] mix_token(
        input logic [TOKEN_W-1:0] base_token,
        input logic [EPOCH_W-1:0] epoch,
        input logic [DOMAIN_W-1:0] domain
    );
        logic [TOKEN_W-1:0] mixed;
        int i;
        begin
            mixed = base_token;
            for (i = 0; i < TOKEN_W; i++) begin
                mixed[i] = base_token[i]
                    ^ epoch[i % EPOCH_W]
                    ^ domain[i % DOMAIN_W]
                    ^ epoch[(i + DOMAIN_W) % EPOCH_W];
            end
            mix_token = mixed;
        end
    endfunction

    always_comb begin
        commit_epoch = domain_epoch[commit_domain];
        dmp_epoch = domain_epoch[dmp_domain];
        commit_epoch_token =
            mix_token(commit_base_token, commit_epoch, commit_domain);
        dmp_epoch_token = mix_token(dmp_base_token, dmp_epoch, dmp_domain);

        commit_domain_blocked = commit_valid && wrap_pending[commit_domain];
        dmp_domain_blocked = dmp_valid && wrap_pending[dmp_domain];

        proof_epoch_match =
            stored_valid
            && !dmp_domain_blocked
            && stored_epoch == dmp_epoch;
        proof_token_match =
            proof_epoch_match
            && stored_epoch_token == dmp_epoch_token;
        proof_current =
            dmp_valid
            && stored_valid
            && !dmp_domain_blocked
            && proof_epoch_match
            && proof_token_match;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            boundary_ack <= 1'b0;
            wrap_flush_required <= 1'b0;
            wrap_clear_ack <= 1'b0;
            for (int i = 0; i < DOMAINS; i++) begin
                domain_epoch[i] <= '0;
                wrap_pending[i] <= 1'b0;
            end
        end else begin
            boundary_ack <= 1'b0;
            wrap_flush_required <= 1'b0;
            wrap_clear_ack <= 1'b0;

            if (wrap_clear_valid) begin
                domain_epoch[wrap_clear_domain] <= '0;
                wrap_pending[wrap_clear_domain] <= 1'b0;
                wrap_clear_ack <= 1'b1;
            end

            if (boundary_valid && !wrap_pending[boundary_domain]) begin
                if (domain_epoch[boundary_domain] == {EPOCH_W{1'b1}}) begin
                    wrap_pending[boundary_domain] <= 1'b1;
                    wrap_flush_required <= 1'b1;
                end else begin
                    domain_epoch[boundary_domain] <=
                        domain_epoch[boundary_domain] + 1'b1;
                    boundary_ack <= 1'b1;
                end
            end else if (boundary_valid) begin
                wrap_flush_required <= 1'b1;
            end
        end
    end

endmodule
