`timescale 1ns/1ps

// COPPER-CLPD SRAM Directory
//
// This is the scalable storage form of the COPPER compressed line-provenance
// directory. Unlike copper_clpd_gate, which is a compact combinational gate,
// this block models the implementation form a cache-adjacent prefetch filter
// would use: banked SRAM-style entries, a synchronous one-cycle query path, and
// a serialized read-modify-write update path for line masks.
//
// Core safety invariant:
//   A DMP seed is allowed only when the delayed source-line proof entry matches
//   the queried line tag, token domain, line epoch, and word mask, and when
//   translation/permission checks pass. If an update for the same directory
//   location is accepted or being written, the query is conservatively blocked
//   to close stale-proof timing windows.
//
// Update policy:
//   COMMIT merges a proven word into the line mask when tag/token/epoch match;
//   otherwise it replaces the line entry. PURGE clears the indexed entry
//   conservatively. A purge for an aliasing tag may evict a different line's
//   proof, which is safe and measurable as a false-negative/capacity cost.

module copper_clpd_sram_dir #(
    parameter int LINE_TAG_W = 32,
    parameter int WORDS_PER_LINE = 16,
    parameter int WORD_OFF_W = 4,
    parameter int TOKEN_W = 8,
    parameter int EPOCH_W = 8,
    parameter int BANKS = 8,
    parameter int BANK_IDX_W = 3,
    parameter int SETS_PER_BANK = 512,
    parameter int SET_IDX_W = 9
) (
    input  logic clk,
    input  logic rst_n,

    input  logic update_valid,
    input  logic [1:0] update_op,
    input  logic [LINE_TAG_W-1:0] update_line_tag,
    input  logic [WORD_OFF_W-1:0] update_word,
    input  logic [TOKEN_W-1:0] update_token,
    input  logic [EPOCH_W-1:0] update_line_epoch,
    output logic update_ready,
    output logic update_commit_merged,
    output logic update_commit_replaced,
    output logic update_purge_match,
    output logic update_purge_alias,

    input  logic dmp_seed_valid,
    input  logic [LINE_TAG_W-1:0] dmp_line_tag,
    input  logic [WORD_OFF_W-1:0] dmp_word,
    input  logic [TOKEN_W-1:0] dmp_src_token,
    input  logic [TOKEN_W-1:0] dmp_target_token,
    input  logic [EPOCH_W-1:0] dmp_line_epoch,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    output logic init_done,
    output logic dmp_resp_valid,
    output logic source_line_hit,
    output logic source_word_proven,
    output logic source_authorized,
    output logic dmp_seed_allow,
    output logic dmp_seed_block,

    output logic block_no_entry,
    output logic block_word_unproven,
    output logic block_stale_epoch,
    output logic block_token_mismatch,
    output logic block_fault_or_perm,
    output logic block_pending_update
);

    localparam logic [1:0] CLPD_OP_COMMIT = 2'd0;
    localparam logic [1:0] CLPD_OP_PURGE = 2'd1;
    localparam int ENTRY_W = 1 + LINE_TAG_W + TOKEN_W + EPOCH_W + WORDS_PER_LINE;
    localparam int TOTAL_ENTRIES = BANKS * SETS_PER_BANK;
    localparam int TOTAL_IDX_W = BANK_IDX_W + SET_IDX_W;
    localparam logic [TOTAL_IDX_W-1:0] LAST_ADDR = TOTAL_ENTRIES - 1;

    (* ram_style = "block" *)
    logic [ENTRY_W-1:0] entry_mem [0:TOTAL_ENTRIES-1];

    logic init_active;
    logic [TOTAL_IDX_W-1:0] init_addr;

    logic upd_stage_valid;
    logic [1:0] upd_op_r;
    logic [LINE_TAG_W-1:0] upd_tag_r;
    logic [WORD_OFF_W-1:0] upd_word_r;
    logic [TOKEN_W-1:0] upd_token_r;
    logic [EPOCH_W-1:0] upd_epoch_r;
    logic [TOTAL_IDX_W-1:0] upd_idx_r;
    logic [ENTRY_W-1:0] upd_entry_r;

    logic q_valid_r;
    logic q_hazard_r;
    logic [LINE_TAG_W-1:0] q_tag_r;
    logic [WORD_OFF_W-1:0] q_word_r;
    logic [TOKEN_W-1:0] q_src_token_r;
    logic [TOKEN_W-1:0] q_target_token_r;
    logic [EPOCH_W-1:0] q_epoch_r;
    logic q_translation_ok_r;
    logic q_permission_ok_r;
    logic [ENTRY_W-1:0] q_entry_r;

    function automatic logic [LINE_TAG_W-1:0] fold_tag(
        input logic [LINE_TAG_W-1:0] tag
    );
        fold_tag = tag ^ (tag >> SET_IDX_W) ^ (tag >> (SET_IDX_W + BANK_IDX_W));
    endfunction

    function automatic logic [BANK_IDX_W-1:0] bank_idx(
        input logic [LINE_TAG_W-1:0] tag
    );
        logic [LINE_TAG_W-1:0] folded;
        folded = fold_tag(tag);
        bank_idx = folded[BANK_IDX_W-1:0];
    endfunction

    function automatic logic [SET_IDX_W-1:0] set_idx(
        input logic [LINE_TAG_W-1:0] tag
    );
        logic [LINE_TAG_W-1:0] folded;
        folded = fold_tag(tag);
        set_idx = folded[BANK_IDX_W +: SET_IDX_W];
    endfunction

    function automatic logic [TOTAL_IDX_W-1:0] dir_idx(
        input logic [LINE_TAG_W-1:0] tag
    );
        dir_idx = {bank_idx(tag), set_idx(tag)};
    endfunction

    function automatic logic [ENTRY_W-1:0] pack_entry(
        input logic valid,
        input logic [LINE_TAG_W-1:0] tag,
        input logic [TOKEN_W-1:0] token,
        input logic [EPOCH_W-1:0] epoch,
        input logic [WORDS_PER_LINE-1:0] mask
    );
        pack_entry = {valid, tag, token, epoch, mask};
    endfunction

    function automatic logic entry_valid(input logic [ENTRY_W-1:0] entry);
        entry_valid = entry[ENTRY_W-1];
    endfunction

    function automatic logic [LINE_TAG_W-1:0] entry_tag(input logic [ENTRY_W-1:0] entry);
        entry_tag = entry[ENTRY_W-2 -: LINE_TAG_W];
    endfunction

    function automatic logic [TOKEN_W-1:0] entry_token(input logic [ENTRY_W-1:0] entry);
        entry_token = entry[WORDS_PER_LINE + EPOCH_W + TOKEN_W - 1 -: TOKEN_W];
    endfunction

    function automatic logic [EPOCH_W-1:0] entry_epoch(input logic [ENTRY_W-1:0] entry);
        entry_epoch = entry[WORDS_PER_LINE + EPOCH_W - 1 -: EPOCH_W];
    endfunction

    function automatic logic [WORDS_PER_LINE-1:0] entry_mask(input logic [ENTRY_W-1:0] entry);
        entry_mask = entry[WORDS_PER_LINE-1:0];
    endfunction

    logic [TOTAL_IDX_W-1:0] dmp_idx;
    logic [TOTAL_IDX_W-1:0] update_idx;
    logic accept_update;

    always_comb begin
        dmp_idx = dir_idx(dmp_line_tag);
        update_idx = dir_idx(update_line_tag);
        update_ready = !init_active && !upd_stage_valid;
        accept_update = update_valid && update_ready;
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            init_active <= 1'b1;
            init_addr <= '0;
            upd_stage_valid <= 1'b0;
            upd_op_r <= '0;
            upd_tag_r <= '0;
            upd_word_r <= '0;
            upd_token_r <= '0;
            upd_epoch_r <= '0;
            upd_idx_r <= '0;
            upd_entry_r <= '0;
            q_valid_r <= 1'b0;
            q_hazard_r <= 1'b0;
            q_tag_r <= '0;
            q_word_r <= '0;
            q_src_token_r <= '0;
            q_target_token_r <= '0;
            q_epoch_r <= '0;
            q_translation_ok_r <= 1'b0;
            q_permission_ok_r <= 1'b0;
            q_entry_r <= '0;
            update_commit_merged <= 1'b0;
            update_commit_replaced <= 1'b0;
            update_purge_match <= 1'b0;
            update_purge_alias <= 1'b0;
        end else begin
            update_commit_merged <= 1'b0;
            update_commit_replaced <= 1'b0;
            update_purge_match <= 1'b0;
            update_purge_alias <= 1'b0;

            if (init_active) begin
                entry_mem[init_addr] <= '0;
                q_valid_r <= 1'b0;
                q_hazard_r <= 1'b0;
                upd_stage_valid <= 1'b0;

                if (init_addr == LAST_ADDR) begin
                    init_addr <= '0;
                    init_active <= 1'b0;
                end else begin
                    init_addr <= init_addr + 1'b1;
                end
            end else begin
                q_valid_r <= dmp_seed_valid;
                q_hazard_r <= dmp_seed_valid
                    && (
                        (accept_update && dmp_idx == update_idx)
                        || (upd_stage_valid && dmp_idx == upd_idx_r)
                    );
                q_tag_r <= dmp_line_tag;
                q_word_r <= dmp_word;
                q_src_token_r <= dmp_src_token;
                q_target_token_r <= dmp_target_token;
                q_epoch_r <= dmp_line_epoch;
                q_translation_ok_r <= dmp_translation_ok;
                q_permission_ok_r <= dmp_permission_ok;
                q_entry_r <= entry_mem[dmp_idx];

                if (upd_stage_valid) begin
                    logic old_valid;
                    logic old_match;
                    logic old_same_domain;
                    logic old_same_epoch;
                    logic [WORDS_PER_LINE-1:0] next_mask;

                    old_valid = entry_valid(upd_entry_r);
                    old_match = old_valid && entry_tag(upd_entry_r) == upd_tag_r;
                    old_same_domain = old_match && entry_token(upd_entry_r) == upd_token_r;
                    old_same_epoch = old_match && entry_epoch(upd_entry_r) == upd_epoch_r;
                    next_mask = entry_mask(upd_entry_r);
                    next_mask[upd_word_r] = 1'b1;

                    if (upd_op_r == CLPD_OP_COMMIT) begin
                        if (old_same_domain && old_same_epoch) begin
                            entry_mem[upd_idx_r] <= pack_entry(
                                1'b1,
                                upd_tag_r,
                                upd_token_r,
                                upd_epoch_r,
                                next_mask
                            );
                            update_commit_merged <= 1'b1;
                        end else begin
                            logic [WORDS_PER_LINE-1:0] single_mask;
                            single_mask = '0;
                            single_mask[upd_word_r] = 1'b1;
                            entry_mem[upd_idx_r] <= pack_entry(
                                1'b1,
                                upd_tag_r,
                                upd_token_r,
                                upd_epoch_r,
                                single_mask
                            );
                            update_commit_replaced <= 1'b1;
                        end
                    end else if (upd_op_r == CLPD_OP_PURGE) begin
                        entry_mem[upd_idx_r] <= '0;
                        update_purge_match <= old_match;
                        update_purge_alias <= old_valid && !old_match;
                    end else begin
                        entry_mem[upd_idx_r] <= '0;
                    end

                    upd_stage_valid <= 1'b0;
                end else if (accept_update) begin
                    upd_stage_valid <= 1'b1;
                    upd_op_r <= update_op;
                    upd_tag_r <= update_line_tag;
                    upd_word_r <= update_word;
                    upd_token_r <= update_token;
                    upd_epoch_r <= update_line_epoch;
                    upd_idx_r <= update_idx;
                    upd_entry_r <= entry_mem[update_idx];
                end
            end
        end
    end

    always_comb begin
        dmp_resp_valid = q_valid_r;
        source_line_hit = 1'b0;
        source_word_proven = 1'b0;
        source_authorized = 1'b0;
        dmp_seed_allow = 1'b0;
        dmp_seed_block = q_valid_r;
        block_no_entry = 1'b0;
        block_word_unproven = 1'b0;
        block_stale_epoch = 1'b0;
        block_token_mismatch = 1'b0;
        block_fault_or_perm = 1'b0;
        block_pending_update = 1'b0;

        if (q_valid_r) begin
            if (q_hazard_r) begin
                block_pending_update = 1'b1;
            end else begin
                logic epoch_match;
                logic token_match;
                logic [WORDS_PER_LINE-1:0] q_mask;

                q_mask = entry_mask(q_entry_r);

                source_line_hit =
                    entry_valid(q_entry_r)
                    && entry_tag(q_entry_r) == q_tag_r;

                epoch_match =
                    source_line_hit
                    && entry_epoch(q_entry_r) == q_epoch_r;

                token_match =
                    source_line_hit
                    && entry_token(q_entry_r) == q_src_token_r
                    && q_src_token_r == q_target_token_r;

                source_word_proven =
                    source_line_hit
                    && epoch_match
                    && q_mask[q_word_r];

                source_authorized = source_word_proven && token_match;

                dmp_seed_allow =
                    source_authorized
                    && q_translation_ok_r
                    && q_permission_ok_r;

                dmp_seed_block = !dmp_seed_allow;

                block_no_entry = !source_line_hit;
                block_word_unproven =
                    source_line_hit
                    && epoch_match
                    && !q_mask[q_word_r];
                block_stale_epoch = source_line_hit && !epoch_match;
                block_token_mismatch =
                    source_line_hit
                    && epoch_match
                    && q_mask[q_word_r]
                    && !token_match;
                block_fault_or_perm =
                    source_authorized
                    && !(q_translation_ok_r && q_permission_ok_r);
            end
        end
    end

    assign init_done = !init_active;

endmodule
