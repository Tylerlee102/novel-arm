`timescale 1ns/1ps

// COPPER: value-bound committed pointer-provenance gate.
//
// This is an RTL sketch, not production-ready RTL. It shows the placement and
// state carried by the mechanism: a commit-side recorder and a DMP-side gate.

module copper_prefetch_gate #(
    parameter int LINE_TAG_W = 40,
    parameter int WORD_OFF_W = 4,
    // Use enough bits to make false aliasing architecturally negligible.
    // A short hash is unsafe; the Python validation shows collision-induced
    // stale-value prefetches when the token is truncated.
    parameter int VALUE_TOKEN_W = 48,
    parameter int DOMAIN_W = 16,
    parameter int ENTRIES = 512
) (
    input  logic clk,
    input  logic rst_n,

    // Commit path: asserted when a demand memory operation commits and its
    // effective address came from a known source cache word.
    input  logic commit_ptr_valid,
    input  logic [LINE_TAG_W-1:0] commit_src_line,
    input  logic [WORD_OFF_W-1:0] commit_src_word,
    input  logic [VALUE_TOKEN_W-1:0] commit_value_token,
    input  logic [DOMAIN_W-1:0] commit_domain,

    // Coherence path: source-line updates invalidate stale provenance.
    input  logic coh_update_valid,
    input  logic [LINE_TAG_W-1:0] coh_update_line,

    // DMP path: candidate derived from memory content.
    input  logic dmp_seed_valid,
    input  logic [LINE_TAG_W-1:0] dmp_src_line,
    input  logic [WORD_OFF_W-1:0] dmp_src_word,
    input  logic [VALUE_TOKEN_W-1:0] dmp_value_token,
    input  logic [DOMAIN_W-1:0] dmp_domain,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    output logic dmp_seed_allow,
    output logic dmp_seed_block_stale
);

    typedef struct packed {
        logic valid;
        logic [LINE_TAG_W-1:0] src_line;
        logic [WORD_OFF_W-1:0] src_word;
        logic [VALUE_TOKEN_W-1:0] value_token;
        logic [DOMAIN_W-1:0] domain;
    } copper_entry_t;

    copper_entry_t prov_table [ENTRIES];

    logic [$clog2(ENTRIES)-1:0] insert_ptr;
    logic hit;

    always_comb begin
        hit = 1'b0;
        for (int i = 0; i < ENTRIES; i++) begin
            hit |= prov_table[i].valid
                && prov_table[i].src_line == dmp_src_line
                && prov_table[i].src_word == dmp_src_word
                && prov_table[i].value_token == dmp_value_token
                && prov_table[i].domain == dmp_domain;
        end

        dmp_seed_allow = dmp_seed_valid
            && hit
            && dmp_translation_ok
            && dmp_permission_ok;

        dmp_seed_block_stale = dmp_seed_valid && !dmp_seed_allow;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            insert_ptr <= '0;
            for (int i = 0; i < ENTRIES; i++) begin
                prov_table[i].valid <= 1'b0;
                prov_table[i].src_line <= '0;
                prov_table[i].src_word <= '0;
                prov_table[i].value_token <= '0;
                prov_table[i].domain <= '0;
            end
        end else begin
            if (coh_update_valid) begin
                for (int i = 0; i < ENTRIES; i++) begin
                    if (prov_table[i].valid && prov_table[i].src_line == coh_update_line) begin
                        prov_table[i].valid <= 1'b0;
                    end
                end
            end

            if (commit_ptr_valid) begin
                prov_table[insert_ptr].valid <= 1'b1;
                prov_table[insert_ptr].src_line <= commit_src_line;
                prov_table[insert_ptr].src_word <= commit_src_word;
                prov_table[insert_ptr].value_token <= commit_value_token;
                prov_table[insert_ptr].domain <= commit_domain;
                insert_ptr <= insert_ptr + 1'b1;
            end
        end
    end

endmodule
