#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sqlite3.h"
#include "yyjson.h"

typedef struct {
    char *data;
    size_t len;
    size_t cap;
} strbuf_t;

static uint64_t checksum_acc = 0xbb67ae8584caa73bull;

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
    checksum_acc = (checksum_acc << 19) | (checksum_acc >> 45);
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
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR realloc json buffer\n");
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
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR vsnprintf length\n");
        exit(1);
    }
    sb_reserve(sb, (size_t)n);
    int n2 = vsnprintf(sb->data + sb->len, sb->cap - sb->len, fmt, ap2);
    va_end(ap2);
    if (n2 != n) {
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR vsnprintf emit\n");
        exit(1);
    }
    sb->len += (size_t)n;
}

static uint64_t
poison_word(uint32_t i, uint32_t seed, uint32_t salt, int poison)
{
    uint64_t x = mix64(((uint64_t)i << 32) ^ ((uint64_t)seed << 9) ^ salt);
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
    sb_appendf(&sb, "{\"schema\":\"copper-json-sqlite\",\"seed\":%u,\"records\":[", seed);
    for (uint32_t i = 0; i < rows; ++i) {
        uint32_t id = permute_index(i, mask, seed);
        uint64_t key = mix64((uint64_t)id + ((uint64_t)seed << 16)) & 0x7fffffffULL;
        uint32_t group = (uint32_t)((key ^ (key >> 7)) & 63u);
        uint64_t probe0 = poison_word(id, seed, 0x41u, poison);
        uint64_t probe1 = poison_word(id, seed, 0x9du, poison);
        sb_appendf(
            &sb,
            "%s{\"id\":%u,\"key\":%llu,\"group\":%u,"
            "\"probe0\":%llu,\"probe1\":%llu,"
            "\"name\":\"req_%08x_%08x\"}",
            i ? "," : "",
            id,
            (unsigned long long)key,
            group,
            (unsigned long long)probe0,
            (unsigned long long)probe1,
            id,
            seed);
    }
    sb_appendf(&sb, "]}");
    return sb;
}

static void
die_sql(sqlite3 *db, const char *where, int rc)
{
    fprintf(stderr, "JSONSQLITE_COPPER_ERROR %s rc=%d msg=%s\n",
            where, rc, sqlite3_errmsg(db));
    exit(1);
}

static void
exec_sql(sqlite3 *db, const char *sql)
{
    char *err = NULL;
    int rc = sqlite3_exec(db, sql, NULL, NULL, &err);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR exec rc=%d msg=%s sql=%s\n",
                rc, err ? err : "", sql);
        sqlite3_free(err);
        exit(1);
    }
}

static void
prepare(sqlite3 *db, sqlite3_stmt **stmt, const char *sql)
{
    int rc = sqlite3_prepare_v2(db, sql, -1, stmt, NULL);
    if (rc != SQLITE_OK) {
        die_sql(db, sql, rc);
    }
}

static yyjson_val *
obj_get_checked(yyjson_val *obj, const char *key)
{
    yyjson_val *val = yyjson_obj_get(obj, key);
    if (!val) {
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR missing key %s\n", key);
        exit(1);
    }
    return val;
}

static uint64_t
uint_field(yyjson_val *obj, const char *key)
{
    yyjson_val *val = obj_get_checked(obj, key);
    if (!yyjson_is_uint(val)) {
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR non-uint field %s\n", key);
        exit(1);
    }
    return yyjson_get_uint(val);
}

static void
ingest_json(sqlite3 *db, char *json, size_t json_len, uint32_t rows)
{
    yyjson_read_err err;
    yyjson_doc *doc = yyjson_read_opts(json, json_len, YYJSON_READ_NOFLAG, NULL, &err);
    if (!doc) {
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR read code=%u pos=%zu msg=%s\n",
                (unsigned)err.code, err.pos, err.msg ? err.msg : "");
        exit(1);
    }
    yyjson_val *root = yyjson_doc_get_root(doc);
    yyjson_val *records = yyjson_obj_get(root, "records");
    if (!records || !yyjson_is_arr(records) || yyjson_arr_size(records) != rows) {
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR malformed records array\n");
        exit(1);
    }

    sqlite3_stmt *ins = NULL;
    prepare(db, &ins, "INSERT INTO records(id,k,g,probe0,probe1,name) VALUES(?,?,?,?,?,?);");
    exec_sql(db, "BEGIN IMMEDIATE;");
    yyjson_arr_iter iter = yyjson_arr_iter_with(records);
    yyjson_val *item;
    while ((item = yyjson_arr_iter_next(&iter))) {
        uint64_t id = uint_field(item, "id");
        uint64_t key = uint_field(item, "key");
        uint64_t group = uint_field(item, "group");
        uint64_t probe0 = uint_field(item, "probe0");
        uint64_t probe1 = uint_field(item, "probe1");
        yyjson_val *name_val = obj_get_checked(item, "name");
        const char *name = yyjson_get_str(name_val);
        size_t name_len = yyjson_get_len(name_val);

        sqlite3_bind_int64(ins, 1, (sqlite3_int64)id);
        sqlite3_bind_int64(ins, 2, (sqlite3_int64)key);
        sqlite3_bind_int64(ins, 3, (sqlite3_int64)group);
        sqlite3_bind_int64(ins, 4, (sqlite3_int64)probe0);
        sqlite3_bind_int64(ins, 5, (sqlite3_int64)probe1);
        sqlite3_bind_text(ins, 6, name, (int)name_len, SQLITE_TRANSIENT);
        int rc = sqlite3_step(ins);
        if (rc != SQLITE_DONE) {
            die_sql(db, "insert", rc);
        }
        sqlite3_reset(ins);
        sqlite3_clear_bindings(ins);
        fold(id ^ key ^ (probe0 << 1) ^ (probe1 << 3) ^ name_len);
    }
    exec_sql(db, "COMMIT;");
    sqlite3_finalize(ins);
    yyjson_doc_free(doc);
}

static void
query_database(sqlite3 *db, uint32_t rows, uint32_t queries, uint32_t updates,
               uint32_t seed)
{
    sqlite3_stmt *point = NULL;
    sqlite3_stmt *range = NULL;
    sqlite3_stmt *groupq = NULL;
    sqlite3_stmt *upd = NULL;
    prepare(db, &point, "SELECT k, probe0, probe1, length(name) FROM records WHERE id=?;");
    prepare(db, &range, "SELECT coalesce(sum(probe0),0), count(*) FROM records WHERE k BETWEEN ? AND ?;");
    prepare(db, &groupq, "SELECT coalesce(sum(k),0), coalesce(sum(probe1),0), count(*) FROM records WHERE g=?;");
    prepare(db, &upd, "UPDATE records SET probe1=? WHERE id=?;");

    uint32_t mask = rows - 1;
    for (uint32_t i = 0; i < queries; ++i) {
        uint32_t id = permute_index(i + seed, mask, seed ^ 0x517cc1b7u);
        sqlite3_bind_int64(point, 1, (sqlite3_int64)id);
        int rc = sqlite3_step(point);
        if (rc != SQLITE_ROW) {
            die_sql(db, "point query", rc);
        }
        fold((uint64_t)sqlite3_column_int64(point, 0));
        fold((uint64_t)sqlite3_column_int64(point, 1));
        fold((uint64_t)sqlite3_column_int64(point, 2));
        fold((uint64_t)sqlite3_column_int(point, 3));
        sqlite3_reset(point);
        sqlite3_clear_bindings(point);

        uint64_t a = mix64((uint64_t)i + seed) & 0x7fffffffULL;
        uint64_t b = a + 4096u;
        sqlite3_bind_int64(range, 1, (sqlite3_int64)a);
        sqlite3_bind_int64(range, 2, (sqlite3_int64)b);
        rc = sqlite3_step(range);
        if (rc != SQLITE_ROW) {
            die_sql(db, "range query", rc);
        }
        fold((uint64_t)sqlite3_column_int64(range, 0));
        fold((uint64_t)sqlite3_column_int64(range, 1));
        sqlite3_reset(range);
        sqlite3_clear_bindings(range);

        uint32_t group = (uint32_t)((i + seed) & 63u);
        sqlite3_bind_int64(groupq, 1, (sqlite3_int64)group);
        rc = sqlite3_step(groupq);
        if (rc != SQLITE_ROW) {
            die_sql(db, "group query", rc);
        }
        fold((uint64_t)sqlite3_column_int64(groupq, 0));
        fold((uint64_t)sqlite3_column_int64(groupq, 1));
        fold((uint64_t)sqlite3_column_int64(groupq, 2));
        sqlite3_reset(groupq);
        sqlite3_clear_bindings(groupq);
    }

    exec_sql(db, "BEGIN IMMEDIATE;");
    for (uint32_t i = 0; i < updates; ++i) {
        uint32_t id = permute_index(i + seed * 3u, mask, seed ^ 0x9e37u);
        uint64_t value = 0x00000000400000ull + ((mix64(id ^ seed) & 0x7ffffull) << 3);
        sqlite3_bind_int64(upd, 1, (sqlite3_int64)value);
        sqlite3_bind_int64(upd, 2, (sqlite3_int64)id);
        int rc = sqlite3_step(upd);
        if (rc != SQLITE_DONE) {
            die_sql(db, "update", rc);
        }
        fold(value ^ id);
        sqlite3_reset(upd);
        sqlite3_clear_bindings(upd);
    }
    exec_sql(db, "COMMIT;");

    sqlite3_finalize(upd);
    sqlite3_finalize(groupq);
    sqlite3_finalize(range);
    sqlite3_finalize(point);
}

static void
run_round(char *json, size_t json_len, uint32_t rows, uint32_t queries,
          uint32_t updates, uint32_t seed)
{
    sqlite3 *db = NULL;
    int rc = sqlite3_open_v2(
        "file:jsonsvc?mode=memory&cache=private",
        &db,
        SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_URI,
        NULL);
    if (rc != SQLITE_OK) {
        die_sql(db, "open", rc);
    }
    exec_sql(db, "PRAGMA journal_mode=OFF;");
    exec_sql(db, "PRAGMA synchronous=OFF;");
    exec_sql(db, "PRAGMA temp_store=MEMORY;");
    exec_sql(db, "PRAGMA cache_size=-8192;");
    exec_sql(db, "CREATE TABLE records(id INTEGER PRIMARY KEY, k INTEGER NOT NULL, g INTEGER NOT NULL, probe0 INTEGER NOT NULL, probe1 INTEGER NOT NULL, name TEXT NOT NULL);");
    exec_sql(db, "CREATE INDEX records_k_idx ON records(k);");
    exec_sql(db, "CREATE INDEX records_g_idx ON records(g);");

    ingest_json(db, json, json_len, rows);
    query_database(db, rows, queries, updates, seed);
    sqlite3_close(db);
}

int
main(int argc, char **argv)
{
    uint32_t rows = 512;
    uint32_t queries = 1200;
    uint32_t updates = 512;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--rows") && i + 1 < argc) {
            rows = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--queries") && i + 1 < argc) {
            queries = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--updates") && i + 1 < argc) {
            updates = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--rounds") && i + 1 < argc) {
            rounds = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--no-poison")) {
            poison = 0;
        } else {
            fprintf(stderr, "usage: %s [--rows pow2] [--queries n] [--updates n] [--rounds n] [--seed n] [--no-poison]\n", argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(rows) || rows < 256 || rows > (1u << 20) || rounds == 0) {
        fprintf(stderr, "JSONSQLITE_COPPER_ERROR invalid rows or rounds\n");
        return 2;
    }

    strbuf_t json = make_json(rows, seed, poison);
    for (uint32_t r = 0; r < rounds; ++r) {
        fold(r);
        run_round(json.data, json.len, rows, queries, updates, seed + r);
    }

    printf("JSONSQLITE_COPPER_RESULT rows=%u queries=%u updates=%u rounds=%u seed=%u poison=%d bytes=%llu yyjson_version=%u sqlite_version=%s checksum=0x%016llx\n",
           rows, queries, updates, rounds, seed, poison,
           (unsigned long long)json.len,
           (unsigned)yyjson_version(),
           sqlite3_libversion(),
           (unsigned long long)checksum_acc);
    free(json.data);
    return 0;
}
