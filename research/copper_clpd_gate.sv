`timescale 1ns/1ps

// COPPER-CLPD: Compressed Line-Provenance Directory.
//
// This block models the retained source-proof representation used to avoid a
// graph-scan proof-ledger capacity cliff. Each directory entry stores one
// source cache-line tag, a source-line epoch, a token/domain, and a per-word
// proof mask. It does not implement a DMP predictor or MMU; it answers whether
// a candidate DMP source word has retained committed source authority.
//
// Invariant:
//   allow iff the source line entry matches, the current line epoch matches,
//   the word bit is proven, the token/domain matches, and translation and
//   permission checks pass. Any source-line write/fill/invalidate clears the
//   retained line proof.

module copper_clpd_gate #(
    parameter int LINE_TAG_W = 12,
    parameter int WORDS_PER_LINE = 16,
    parameter int WORD_OFF_W = 4,
    parameter int TOKEN_W = 8,
    parameter int EPOCH_W = 4,
    parameter int ENTRIES = 64,
    parameter int ENTRY_IDX_W = 6
) (
    input  logic clk,
    input  logic rst_n,

    input  logic commit_ptr_valid,
    input  logic [LINE_TAG_W-1:0] commit_line_tag,
    input  logic [WORD_OFF_W-1:0] commit_word,
    input  logic [TOKEN_W-1:0] commit_token,
    input  logic [EPOCH_W-1:0] commit_line_epoch,

    input  logic source_write_valid,
    input  logic [LINE_TAG_W-1:0] source_write_line_tag,

    input  logic line_fill_valid,
    input  logic [LINE_TAG_W-1:0] line_fill_tag,

    input  logic invalidate_valid,
    input  logic [LINE_TAG_W-1:0] invalidate_line_tag,

    input  logic dmp_seed_valid,
    input  logic [LINE_TAG_W-1:0] dmp_line_tag,
    input  logic [WORD_OFF_W-1:0] dmp_word,
    input  logic [TOKEN_W-1:0] dmp_src_token,
    input  logic [TOKEN_W-1:0] dmp_target_token,
    input  logic [EPOCH_W-1:0] dmp_line_epoch,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    output logic source_line_hit,
    output logic source_word_proven,
    output logic source_authorized,
    output logic dmp_seed_allow,
    output logic dmp_seed_block,

    output logic block_no_entry,
    output logic block_word_unproven,
    output logic block_stale_epoch,
    output logic block_token_mismatch,
    output logic block_fault_or_perm
);

    logic entry_valid [ENTRIES];
    logic [LINE_TAG_W-1:0] entry_tag [ENTRIES];
    logic [TOKEN_W-1:0] entry_token [ENTRIES];
    logic [EPOCH_W-1:0] entry_epoch [ENTRIES];
    logic [WORDS_PER_LINE-1:0] entry_mask [ENTRIES];

    function automatic logic [ENTRY_IDX_W-1:0] dir_idx(
        input logic [LINE_TAG_W-1:0] tag
    );
        dir_idx = tag[ENTRY_IDX_W-1:0];
    endfunction

    logic [ENTRY_IDX_W-1:0] dmp_idx;
    logic [ENTRY_IDX_W-1:0] commit_idx;
    logic [ENTRY_IDX_W-1:0] write_idx;
    logic [ENTRY_IDX_W-1:0] fill_idx;
    logic [ENTRY_IDX_W-1:0] inval_idx;
    logic token_match;
    logic epoch_match;

    always_comb begin
        dmp_idx = dir_idx(dmp_line_tag);
        commit_idx = dir_idx(commit_line_tag);
        write_idx = dir_idx(source_write_line_tag);
        fill_idx = dir_idx(line_fill_tag);
        inval_idx = dir_idx(invalidate_line_tag);

        source_line_hit =
            entry_valid[dmp_idx]
            && (entry_tag[dmp_idx] == dmp_line_tag);

        epoch_match =
            source_line_hit
            && (entry_epoch[dmp_idx] == dmp_line_epoch);

        token_match =
            source_line_hit
            && (entry_token[dmp_idx] == dmp_src_token)
            && (dmp_src_token == dmp_target_token);

        source_word_proven =
            source_line_hit
            && epoch_match
            && entry_mask[dmp_idx][dmp_word];

        source_authorized =
            source_word_proven
            && token_match;

        dmp_seed_allow =
            dmp_seed_valid
            && source_authorized
            && dmp_translation_ok
            && dmp_permission_ok;

        dmp_seed_block = dmp_seed_valid && !dmp_seed_allow;

        block_no_entry =
            dmp_seed_valid
            && !source_line_hit;

        block_word_unproven =
            dmp_seed_valid
            && source_line_hit
            && epoch_match
            && !entry_mask[dmp_idx][dmp_word];

        block_stale_epoch =
            dmp_seed_valid
            && source_line_hit
            && !epoch_match;

        block_token_mismatch =
            dmp_seed_valid
            && source_line_hit
            && epoch_match
            && entry_mask[dmp_idx][dmp_word]
            && !token_match;

        block_fault_or_perm =
            dmp_seed_valid
            && source_authorized
            && !(dmp_translation_ok && dmp_permission_ok);
    end

    task automatic clear_if_match(input logic [LINE_TAG_W-1:0] tag);
        logic [ENTRY_IDX_W-1:0] idx;
        begin
            idx = dir_idx(tag);
            if (entry_valid[idx] && entry_tag[idx] == tag) begin
                entry_valid[idx] <= 1'b0;
                entry_mask[idx] <= '0;
            end
        end
    endtask

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < ENTRIES; i++) begin
                entry_valid[i] <= 1'b0;
                entry_tag[i] <= '0;
                entry_token[i] <= '0;
                entry_epoch[i] <= '0;
                entry_mask[i] <= '0;
            end
        end else begin
            if (source_write_valid) begin
                clear_if_match(source_write_line_tag);
            end

            if (line_fill_valid) begin
                clear_if_match(line_fill_tag);
            end

            if (invalidate_valid) begin
                clear_if_match(invalidate_line_tag);
            end

            if (commit_ptr_valid) begin
                if (
                    entry_valid[commit_idx]
                    && entry_tag[commit_idx] == commit_line_tag
                    && entry_token[commit_idx] == commit_token
                    && entry_epoch[commit_idx] == commit_line_epoch
                ) begin
                    entry_mask[commit_idx][commit_word] <= 1'b1;
                end else begin
                    entry_valid[commit_idx] <= 1'b1;
                    entry_tag[commit_idx] <= commit_line_tag;
                    entry_token[commit_idx] <= commit_token;
                    entry_epoch[commit_idx] <= commit_line_epoch;
                    entry_mask[commit_idx] <= '0;
                    entry_mask[commit_idx][commit_word] <= 1'b1;
                end
            end
        end
    end

endmodule
