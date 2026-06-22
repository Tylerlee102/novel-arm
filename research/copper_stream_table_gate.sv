`timescale 1ns/1ps

// COPPER stream-table gate.
//
// More realistic than copper_stream_gate.sv:
// - multiple load-stream IDs,
// - per-stream training counters,
// - per-stream domain binding,
// - dirty-source CAM,
// - fail-safe dirty overflow.

module copper_stream_table_gate #(
    parameter int STREAM_ID_W = 8,
    parameter int LINE_TAG_W = 40,
    parameter int WORD_OFF_W = 4,
    parameter int DOMAIN_W = 16,
    parameter int STREAM_ENTRIES = 8,
    parameter int DIRTY_ENTRIES = 32,
    parameter int TRAIN_THRESHOLD = 32
) (
    input  logic clk,
    input  logic rst_n,
    input  logic epoch_advance,

    input  logic commit_ptr_valid,
    input  logic [STREAM_ID_W-1:0] commit_stream_id,
    input  logic [LINE_TAG_W-1:0] commit_src_line,
    input  logic [WORD_OFF_W-1:0] commit_src_word,
    input  logic [DOMAIN_W-1:0] commit_domain,

    input  logic source_dirty_valid,
    input  logic [LINE_TAG_W-1:0] source_dirty_line,
    input  logic [WORD_OFF_W-1:0] source_dirty_word,
    input  logic [DOMAIN_W-1:0] source_dirty_domain,

    input  logic dmp_seed_valid,
    input  logic [STREAM_ID_W-1:0] dmp_stream_id,
    input  logic [LINE_TAG_W-1:0] dmp_src_line,
    input  logic [WORD_OFF_W-1:0] dmp_src_word,
    input  logic [DOMAIN_W-1:0] dmp_src_domain,
    input  logic [DOMAIN_W-1:0] dmp_target_domain,
    input  logic dmp_translation_ok,
    input  logic dmp_permission_ok,

    output logic dmp_seed_allow,
    output logic dmp_seed_block,
    output logic dirty_overflow
);

    localparam int STREAM_IDX_W = $clog2(STREAM_ENTRIES);
    localparam int DIRTY_IDX_W = $clog2(DIRTY_ENTRIES);
    localparam int COUNT_W = $clog2(TRAIN_THRESHOLD + 2);
    localparam logic [COUNT_W-1:0] TRAIN_LIMIT = TRAIN_THRESHOLD;

    typedef struct packed {
        logic valid;
        logic trained;
        logic [STREAM_ID_W-1:0] stream_id;
        logic [DOMAIN_W-1:0] domain;
        logic [COUNT_W-1:0] count;
    } stream_entry_t;

    typedef struct packed {
        logic valid;
        logic [LINE_TAG_W-1:0] line;
        logic [WORD_OFF_W-1:0] word;
        logic [DOMAIN_W-1:0] domain;
    } dirty_entry_t;

    stream_entry_t stream_tab [STREAM_ENTRIES];
    dirty_entry_t dirty_cam [DIRTY_ENTRIES];

    logic stream_hit;
    logic stream_trained_hit;
    logic stream_domain_hit;
    logic dirty_hit;
    logic commit_stream_hit;
    logic stream_free_found;
    logic [STREAM_IDX_W-1:0] commit_stream_idx;
    logic [STREAM_IDX_W-1:0] stream_free_idx;
    logic dirty_existing_hit;
    logic dirty_free_found;
    logic [DIRTY_IDX_W-1:0] dirty_free_idx;

    always_comb begin
        stream_hit = 1'b0;
        stream_trained_hit = 1'b0;
        stream_domain_hit = 1'b0;
        commit_stream_hit = 1'b0;
        stream_free_found = 1'b0;
        commit_stream_idx = '0;
        stream_free_idx = '0;

        for (int i = 0; i < STREAM_ENTRIES; i++) begin
            if (stream_tab[i].valid && stream_tab[i].stream_id == dmp_stream_id) begin
                stream_hit = 1'b1;
                stream_trained_hit = stream_tab[i].trained;
                stream_domain_hit = stream_tab[i].domain == dmp_src_domain;
            end

            if (stream_tab[i].valid && stream_tab[i].stream_id == commit_stream_id) begin
                commit_stream_hit = 1'b1;
                commit_stream_idx = i[STREAM_IDX_W-1:0];
            end

            if (!stream_tab[i].valid && !stream_free_found) begin
                stream_free_found = 1'b1;
                stream_free_idx = i[STREAM_IDX_W-1:0];
            end
        end

        dirty_hit = 1'b0;
        dirty_existing_hit = 1'b0;
        dirty_free_found = 1'b0;
        dirty_free_idx = '0;

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

            if (!dirty_cam[i].valid && !dirty_free_found) begin
                dirty_free_found = 1'b1;
                dirty_free_idx = i[DIRTY_IDX_W-1:0];
            end
        end

        dmp_seed_allow = dmp_seed_valid
            && stream_hit
            && stream_trained_hit
            && stream_domain_hit
            && !dirty_hit
            && !dirty_overflow
            && dmp_src_domain == dmp_target_domain
            && dmp_translation_ok
            && dmp_permission_ok;

        dmp_seed_block = dmp_seed_valid && !dmp_seed_allow;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dirty_overflow <= 1'b0;
            for (int i = 0; i < STREAM_ENTRIES; i++) begin
                stream_tab[i].valid <= 1'b0;
                stream_tab[i].trained <= 1'b0;
                stream_tab[i].stream_id <= '0;
                stream_tab[i].domain <= '0;
                stream_tab[i].count <= '0;
            end
            for (int i = 0; i < DIRTY_ENTRIES; i++) begin
                dirty_cam[i].valid <= 1'b0;
                dirty_cam[i].line <= '0;
                dirty_cam[i].word <= '0;
                dirty_cam[i].domain <= '0;
            end
        end else begin
            if (commit_ptr_valid) begin
                if (commit_stream_hit) begin
                    if (stream_tab[commit_stream_idx].count < TRAIN_LIMIT) begin
                        stream_tab[commit_stream_idx].count <= stream_tab[commit_stream_idx].count + 1'b1;
                    end
                    stream_tab[commit_stream_idx].domain <= commit_domain;
                end else if (stream_free_found) begin
                    stream_tab[stream_free_idx].valid <= 1'b1;
                    stream_tab[stream_free_idx].trained <= 1'b0;
                    stream_tab[stream_free_idx].stream_id <= commit_stream_id;
                    stream_tab[stream_free_idx].domain <= commit_domain;
                    stream_tab[stream_free_idx].count <= 1;
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

            if (epoch_advance) begin
                for (int i = 0; i < STREAM_ENTRIES; i++) begin
                    if (stream_tab[i].valid && stream_tab[i].count >= TRAIN_LIMIT) begin
                        stream_tab[i].trained <= 1'b1;
                    end
                end
            end

            if (source_dirty_valid && !dirty_existing_hit) begin
                if (dirty_free_found) begin
                    dirty_cam[dirty_free_idx].valid <= 1'b1;
                    dirty_cam[dirty_free_idx].line <= source_dirty_line;
                    dirty_cam[dirty_free_idx].word <= source_dirty_word;
                    dirty_cam[dirty_free_idx].domain <= source_dirty_domain;
                end else begin
                    dirty_overflow <= 1'b1;
                end
            end
        end
    end

endmodule
