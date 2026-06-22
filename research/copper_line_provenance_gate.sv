`timescale 1ns/1ps

// COPPER-LINE: line-resident clean committed-pointer provenance.
//
// This block models the metadata that would sit beside cache-line state. It
// does not implement a DMP. It answers only one question: may the DMP use this
// source word as authority for a dereference prefetch?
//
// Invariant:
//   allow iff the source word has a clean committed-pointer proof in the
//   source domain, the target domain matches, and translation/permission pass.

module copper_line_provenance_gate #(
    parameter int LINE_IDX_W = 6,
    parameter int WORDS_PER_LINE = 8,
    parameter int WORD_OFF_W = 3,
    parameter int DOMAIN_W = 8,
    parameter int LINES = 64
) (
    input  logic clk,
    input  logic rst_n,

    input  logic commit_ptr_valid,
    input  logic [LINE_IDX_W-1:0] commit_line_idx,
    input  logic [WORD_OFF_W-1:0] commit_word,
    input  logic [DOMAIN_W-1:0] commit_domain,

    input  logic write_valid,
    input  logic [LINE_IDX_W-1:0] write_line_idx,
    input  logic [WORD_OFF_W-1:0] write_word,

    input  logic line_fill_valid,
    input  logic [LINE_IDX_W-1:0] line_fill_idx,

    input  logic invalidate_valid,
    input  logic [LINE_IDX_W-1:0] invalidate_line_idx,

    input  logic dmp_seed_valid,
    input  logic [LINE_IDX_W-1:0] dmp_line_idx,
    input  logic [WORD_OFF_W-1:0] dmp_word,
    input  logic [DOMAIN_W-1:0] dmp_src_domain,
    input  logic [DOMAIN_W-1:0] dmp_target_domain,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    output logic dmp_seed_allow,
    output logic dmp_seed_block,
    output logic source_proven_clean
);

    logic [WORDS_PER_LINE-1:0] proof_bits [LINES];
    logic [DOMAIN_W-1:0] line_domain [LINES];

    always_comb begin
        source_proven_clean =
            proof_bits[dmp_line_idx][dmp_word]
            && line_domain[dmp_line_idx] == dmp_src_domain;

        dmp_seed_allow =
            dmp_seed_valid
            && source_proven_clean
            && dmp_src_domain == dmp_target_domain
            && dmp_translation_ok
            && dmp_permission_ok;

        dmp_seed_block = dmp_seed_valid && !dmp_seed_allow;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < LINES; i++) begin
                proof_bits[i] <= '0;
                line_domain[i] <= '0;
            end
        end else begin
            if (line_fill_valid) begin
                proof_bits[line_fill_idx] <= '0;
                line_domain[line_fill_idx] <= '0;
            end

            if (invalidate_valid) begin
                proof_bits[invalidate_line_idx] <= '0;
                line_domain[invalidate_line_idx] <= '0;
            end

            if (write_valid) begin
                proof_bits[write_line_idx][write_word] <= 1'b0;
            end

            if (commit_ptr_valid) begin
                proof_bits[commit_line_idx][commit_word] <= 1'b1;
                line_domain[commit_line_idx] <= commit_domain;
            end
        end
    end

endmodule
