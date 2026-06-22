`timescale 1ns/1ps

// COPPER-STREAM: stream-certified, dirty-source-gated prefetch permission.
//
// This sketch targets the limitations found in the value-token design:
// 1. No short value token is needed.
// 2. A trained pointer-producing stream can cover many source lines.
// 3. Source writes/coherence updates mark entries dirty; dirty or overflow
//    state fails safe by blocking stream prefetches.

module copper_stream_gate #(
    parameter int LINE_TAG_W = 40,
    parameter int WORD_OFF_W = 4,
    parameter int DOMAIN_W = 16,
    parameter int DIRTY_ENTRIES = 32,
    parameter int TRAIN_THRESHOLD = 32
) (
    input  logic clk,
    input  logic rst_n,

    input  logic epoch_advance,

    // Commit path: a source word produced a committed demand address.
    input  logic commit_ptr_valid,
    input  logic [LINE_TAG_W-1:0] commit_src_line,
    input  logic [WORD_OFF_W-1:0] commit_src_word,
    input  logic [DOMAIN_W-1:0] commit_domain,

    // Source word was overwritten or invalidated.
    input  logic source_dirty_valid,
    input  logic [LINE_TAG_W-1:0] source_dirty_line,
    input  logic [WORD_OFF_W-1:0] source_dirty_word,
    input  logic [DOMAIN_W-1:0] source_dirty_domain,

    // DMP candidate from a trained pointer-producing stream.
    input  logic dmp_seed_valid,
    input  logic [LINE_TAG_W-1:0] dmp_src_line,
    input  logic [WORD_OFF_W-1:0] dmp_src_word,
    input  logic [DOMAIN_W-1:0] dmp_src_domain,
    input  logic [DOMAIN_W-1:0] dmp_target_domain,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    output logic dmp_seed_allow,
    output logic dmp_seed_block,
    output logic stream_trained,
    output logic dirty_overflow
);

    typedef struct packed {
        logic valid;
        logic [LINE_TAG_W-1:0] line;
        logic [WORD_OFF_W-1:0] word;
        logic [DOMAIN_W-1:0] domain;
    } dirty_entry_t;

    dirty_entry_t dirty_cam [DIRTY_ENTRIES];

    localparam int COUNT_W = $clog2(TRAIN_THRESHOLD + 2);
    localparam logic [COUNT_W-1:0] TRAIN_LIMIT = TRAIN_THRESHOLD;
    logic [COUNT_W-1:0] committed_count;
    logic dirty_hit;
    logic dirty_existing_hit;
    logic free_found;
    logic [$clog2(DIRTY_ENTRIES)-1:0] free_idx;

    always_comb begin
        dirty_hit = 1'b0;
        dirty_existing_hit = 1'b0;
        free_found = 1'b0;
        free_idx = '0;

        for (int i = 0; i < DIRTY_ENTRIES; i++) begin
            if (dirty_cam[i].valid
                && dirty_cam[i].line == dmp_src_line
                && dirty_cam[i].word == dmp_src_word
                && dirty_cam[i].domain == dmp_src_domain) begin
                dirty_hit = 1'b1;
            end

            if (dirty_cam[i].valid
                && dirty_cam[i].line == source_dirty_line
                && dirty_cam[i].word == source_dirty_word
                && dirty_cam[i].domain == source_dirty_domain) begin
                dirty_existing_hit = 1'b1;
            end

            if (!dirty_cam[i].valid && !free_found) begin
                free_found = 1'b1;
                free_idx = i[$clog2(DIRTY_ENTRIES)-1:0];
            end
        end

        dmp_seed_allow = dmp_seed_valid
            && stream_trained
            && !dirty_hit
            && !dirty_overflow
            && dmp_src_domain == dmp_target_domain
            && dmp_translation_ok
            && dmp_permission_ok;

        dmp_seed_block = dmp_seed_valid && !dmp_seed_allow;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stream_trained <= 1'b0;
            dirty_overflow <= 1'b0;
            committed_count <= '0;
            for (int i = 0; i < DIRTY_ENTRIES; i++) begin
                dirty_cam[i].valid <= 1'b0;
                dirty_cam[i].line <= '0;
                dirty_cam[i].word <= '0;
                dirty_cam[i].domain <= '0;
            end
        end else begin
            if (commit_ptr_valid) begin
                if (committed_count < TRAIN_LIMIT) begin
                    committed_count <= committed_count + 1'b1;
                end

                for (int i = 0; i < DIRTY_ENTRIES; i++) begin
                    if (dirty_cam[i].valid
                        && dirty_cam[i].line == commit_src_line
                        && dirty_cam[i].word == commit_src_word
                        && dirty_cam[i].domain == commit_domain) begin
                        dirty_cam[i].valid <= 1'b0;
                    end
                end
            end

            if (epoch_advance && committed_count >= TRAIN_LIMIT) begin
                stream_trained <= 1'b1;
            end

            if (source_dirty_valid && !dirty_existing_hit) begin
                if (free_found) begin
                    dirty_cam[free_idx].valid <= 1'b1;
                    dirty_cam[free_idx].line <= source_dirty_line;
                    dirty_cam[free_idx].word <= source_dirty_word;
                    dirty_cam[free_idx].domain <= source_dirty_domain;
                end else begin
                    dirty_overflow <= 1'b1;
                end
            end
        end
    end

endmodule
