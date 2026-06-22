#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "yyjson.h"

typedef struct {
    char *data;
    size_t len;
    size_t cap;
} strbuf_t;

static uint64_t checksum_acc = 0x6a09e667f3bcc909ull;

static uint64_t
mix64(uint64_t x)
{
    x += 0x9e3779b97f4a7c15ull;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ull;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebull;
    return x ^ (x >> 31);
}

static void
fold(uint64_t value)
{
    checksum_acc ^= mix64(value + checksum_acc);
    checksum_acc = (checksum_acc << 23) | (checksum_acc >> 41);
}

static int
is_power_of_two(uint32_t x)
{
    return x && ((x & (x - 1)) == 0);
}

static uint32_t
permute_index(uint32_t i, uint32_t mask, uint32_t seed)
{
    return (uint32_t)(((uint64_t)i * 2654435761u) + ((uint64_t)seed * 40503u)) & mask;
}

static void
sb_reserve(strbuf_t *sb, size_t add)
{
    size_t need = sb->len + add + 1;
    if (need <= sb->cap) {
        return;
    }
    size_t next = sb->cap ? sb->cap : 4096;
    while (next < need) {
        next *= 2;
    }
    char *new_data = (char *)realloc(sb->data, next);
    if (!new_data) {
        fprintf(stderr, "YYJSON_COPPER_ERROR realloc json buffer\n");
        exit(1);
    }
    sb->data = new_data;
    sb->cap = next;
}

static void
sb_appendf(strbuf_t *sb, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    va_list ap2;
    va_copy(ap2, ap);
    int n = vsnprintf(NULL, 0, fmt, ap);
    va_end(ap);
    if (n < 0) {
        fprintf(stderr, "YYJSON_COPPER_ERROR vsnprintf length\n");
        exit(1);
    }
    sb_reserve(sb, (size_t)n);
    int n2 = vsnprintf(sb->data + sb->len, sb->cap - sb->len, fmt, ap2);
    va_end(ap2);
    if (n2 != n) {
        fprintf(stderr, "YYJSON_COPPER_ERROR vsnprintf emit\n");
        exit(1);
    }
    sb->len += (size_t)n;
}

static uint64_t
poison_word(uint32_t i, uint32_t seed, uint32_t salt, int poison)
{
    uint64_t x = mix64(((uint64_t)i << 32) ^ ((uint64_t)seed << 7) ^ salt);
    if (!poison) {
        return x & 0x7fffffffull;
    }
    return 0x00000000400000ull + ((x & 0x7ffffull) << 3);
}

static strbuf_t
make_json(uint32_t rows, uint32_t seed, int poison)
{
    uint32_t mask = rows - 1;
    strbuf_t sb = {0};
    sb_appendf(&sb, "{\"schema\":\"copper-yyjson\",\"seed\":%u,\"items\":[", seed);
    for (uint32_t i = 0; i < rows; ++i) {
        uint32_t id = permute_index(i, mask, seed);
        uint32_t next = permute_index(i + 1, mask, seed ^ 0x9e37u);
        uint64_t key = mix64((uint64_t)id + seed);
        uint64_t probe0 = poison_word(id, seed, 0x11u, poison);
        uint64_t probe1 = poison_word(id, seed, 0x29u, poison);
        uint32_t tag0 = (uint32_t)(key & 0xffffu);
        uint32_t tag1 = (uint32_t)((key >> 16) & 0xffffu);
        uint32_t tag2 = (uint32_t)((key >> 32) & 0xffffu);
        sb_appendf(
            &sb,
            "%s{\"id\":%u,\"key\":%llu,\"next\":%u,"
            "\"probe0\":%llu,\"probe1\":%llu,"
            "\"name\":\"node_%08x_%08x\",\"tags\":[%u,%u,%u]}",
            i ? "," : "",
            id,
            (unsigned long long)key,
            next,
            (unsigned long long)probe0,
            (unsigned long long)probe1,
            id,
            seed,
            tag0,
            tag1,
            tag2);
    }
    sb_appendf(&sb, "]}");
    return sb;
}

static yyjson_val *
obj_get_checked(yyjson_val *obj, const char *key)
{
    yyjson_val *val = yyjson_obj_get(obj, key);
    if (!val) {
        fprintf(stderr, "YYJSON_COPPER_ERROR missing key %s\n", key);
        exit(1);
    }
    return val;
}

static uint64_t
uint_field(yyjson_val *obj, const char *key)
{
    yyjson_val *val = obj_get_checked(obj, key);
    if (!yyjson_is_uint(val)) {
        fprintf(stderr, "YYJSON_COPPER_ERROR non-uint field %s\n", key);
        exit(1);
    }
    return yyjson_get_uint(val);
}

static void
fold_item(yyjson_val *item)
{
    uint64_t id = uint_field(item, "id");
    uint64_t key = uint_field(item, "key");
    uint64_t next = uint_field(item, "next");
    uint64_t probe0 = uint_field(item, "probe0");
    uint64_t probe1 = uint_field(item, "probe1");
    yyjson_val *name = obj_get_checked(item, "name");
    yyjson_val *tags = obj_get_checked(item, "tags");
    fold(id ^ key);
    fold((next << 1) ^ yyjson_get_len(name));
    fold(probe0 ^ (probe1 << 7));
    yyjson_arr_iter iter = yyjson_arr_iter_with(tags);
    yyjson_val *tag;
    while ((tag = yyjson_arr_iter_next(&iter))) {
        fold(yyjson_get_uint(tag));
    }
}

static void
run_doc(char *json, size_t json_len, uint32_t rows, uint32_t lookups,
        uint32_t traversals, uint32_t seed)
{
    yyjson_read_err err;
    yyjson_doc *doc = yyjson_read_opts(json, json_len, YYJSON_READ_NOFLAG, NULL, &err);
    if (!doc) {
        fprintf(stderr, "YYJSON_COPPER_ERROR read code=%u pos=%zu msg=%s\n",
                (unsigned)err.code, err.pos, err.msg ? err.msg : "");
        exit(1);
    }
    yyjson_val *root = yyjson_doc_get_root(doc);
    yyjson_val *items = yyjson_obj_get(root, "items");
    if (!items || !yyjson_is_arr(items) || yyjson_arr_size(items) != rows) {
        fprintf(stderr, "YYJSON_COPPER_ERROR malformed items array\n");
        exit(1);
    }

    yyjson_val **index = (yyjson_val **)calloc(rows, sizeof(*index));
    if (!index) {
        fprintf(stderr, "YYJSON_COPPER_ERROR calloc index\n");
        exit(1);
    }

    yyjson_arr_iter iter = yyjson_arr_iter_with(items);
    yyjson_val *item;
    while ((item = yyjson_arr_iter_next(&iter))) {
        uint32_t id = (uint32_t)uint_field(item, "id");
        if (id >= rows || index[id]) {
            fprintf(stderr, "YYJSON_COPPER_ERROR duplicate or out-of-range id\n");
            exit(1);
        }
        index[id] = item;
        fold_item(item);
    }

    uint32_t mask = rows - 1;
    for (uint32_t i = 0; i < lookups; ++i) {
        uint32_t id = permute_index(i + seed, mask, seed ^ 0x517cc1b7u);
        yyjson_val *cur = index[id];
        if (!cur) {
            fprintf(stderr, "YYJSON_COPPER_ERROR missing lookup id\n");
            exit(1);
        }
        fold_item(cur);
        uint32_t next = (uint32_t)uint_field(cur, "next") & mask;
        yyjson_val *nxt = index[next];
        if (nxt) {
            fold(uint_field(nxt, "key") ^ ((uint64_t)next << 32));
        }
    }

    yyjson_val *cur = index[seed & mask];
    for (uint32_t i = 0; i < traversals; ++i) {
        uint32_t next = (uint32_t)uint_field(cur, "next") & mask;
        cur = index[next] ? index[next] : index[(next + 1) & mask];
        fold_item(cur);
    }

    free(index);
    yyjson_doc_free(doc);
}

int
main(int argc, char **argv)
{
    uint32_t rows = 1024;
    uint32_t lookups = 3000;
    uint32_t traversals = 3000;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--rows") && i + 1 < argc) {
            rows = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--lookups") && i + 1 < argc) {
            lookups = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--traversals") && i + 1 < argc) {
            traversals = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--rounds") && i + 1 < argc) {
            rounds = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--no-poison")) {
            poison = 0;
        } else {
            fprintf(stderr, "usage: %s [--rows pow2] [--lookups n] [--traversals n] [--rounds n] [--seed n] [--no-poison]\n", argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(rows) || rows < 256 || rows > (1u << 20) || rounds == 0) {
        fprintf(stderr, "YYJSON_COPPER_ERROR invalid rows or rounds\n");
        return 2;
    }

    strbuf_t json = make_json(rows, seed, poison);
    for (uint32_t r = 0; r < rounds; ++r) {
        fold(r);
        run_doc(json.data, json.len, rows, lookups, traversals, seed + r);
    }

    printf("YYJSON_COPPER_RESULT rows=%u lookups=%u traversals=%u rounds=%u seed=%u poison=%d bytes=%llu version=%u checksum=0x%016llx\n",
           rows, lookups, traversals, rounds, seed, poison,
           (unsigned long long)json.len,
           (unsigned)yyjson_version(),
           (unsigned long long)checksum_acc);
    free(json.data);
    return 0;
}
