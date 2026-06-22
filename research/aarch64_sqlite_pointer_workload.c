#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sqlite3.h"

static uint64_t checksum_acc = 0x9e3779b97f4a7c15ull;

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
    checksum_acc = (checksum_acc << 17) | (checksum_acc >> 47);
}

static void
die_sql(sqlite3 *db, const char *where, int rc)
{
    fprintf(stderr, "SQLITE_COPPER_ERROR %s rc=%d msg=%s\n",
            where, rc, sqlite3_errmsg(db));
    exit(1);
}

static void
exec_sql(sqlite3 *db, const char *sql)
{
    char *err = NULL;
    int rc = sqlite3_exec(db, sql, NULL, NULL, &err);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQLITE_COPPER_ERROR exec rc=%d msg=%s sql=%s\n",
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

static void
step_done(sqlite3 *db, sqlite3_stmt *stmt, const char *where)
{
    int rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        die_sql(db, where, rc);
    }
    sqlite3_reset(stmt);
    sqlite3_clear_bindings(stmt);
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
fill_blob(uint8_t *buf, int len, uint64_t seed, int poison)
{
    for (int off = 0; off < len; off += 8) {
        uint64_t word = mix64(seed + (uint64_t)off);
        if (poison && ((off & 15) == 0)) {
            word = 0x00000000400000ull + ((word & 0x3ffffull) << 3);
        }
        int copy = (len - off) < 8 ? (len - off) : 8;
        memcpy(buf + off, &word, (size_t)copy);
    }
}

int
main(int argc, char **argv)
{
    uint32_t rows = 4096;
    uint32_t lookups = 12000;
    uint32_t ranges = 512;
    uint32_t updates = 2048;
    uint32_t payload_rows = 4096;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--rows") && i + 1 < argc) {
            rows = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--lookups") && i + 1 < argc) {
            lookups = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--ranges") && i + 1 < argc) {
            ranges = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--updates") && i + 1 < argc) {
            updates = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--payload-rows") && i + 1 < argc) {
            payload_rows = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--no-poison")) {
            poison = 0;
        } else {
            fprintf(stderr, "usage: %s [--rows pow2] [--lookups n] [--ranges n] [--updates n] [--payload-rows n] [--seed n] [--no-poison]\n", argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(rows) || rows < 256 || rows > (1u << 20)) {
        fprintf(stderr, "SQLITE_COPPER_ERROR rows must be a power of two in [256,1048576]\n");
        return 2;
    }
    if (!is_power_of_two(payload_rows) || payload_rows < 256) {
        fprintf(stderr, "SQLITE_COPPER_ERROR payload_rows must be a power of two and >=256\n");
        return 2;
    }

    uint32_t *keys = (uint32_t *)malloc((size_t)rows * sizeof(uint32_t));
    uint8_t blob[96];
    if (!keys) {
        fprintf(stderr, "SQLITE_COPPER_ERROR malloc keys\n");
        return 1;
    }
    const uint32_t key_mask = rows - 1;
    for (uint32_t i = 0; i < rows; ++i) {
        keys[i] = permute_index(i, key_mask, seed) * 8u + 3u;
    }

    sqlite3 *db = NULL;
    int rc = sqlite3_open_v2(
        "file:coppertop?mode=memory&cache=private",
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
    exec_sql(db, "PRAGMA page_size=4096;");
    exec_sql(db, "CREATE TABLE kv(k INTEGER PRIMARY KEY, v INTEGER NOT NULL, pad BLOB NOT NULL);");
    exec_sql(db, "CREATE INDEX kv_v_idx ON kv(v);");
    exec_sql(db, "CREATE TABLE payload(id INTEGER PRIMARY KEY, word INTEGER NOT NULL, pad BLOB NOT NULL);");

    sqlite3_stmt *ins = NULL;
    sqlite3_stmt *pins = NULL;
    sqlite3_stmt *point = NULL;
    sqlite3_stmt *range = NULL;
    sqlite3_stmt *vscan = NULL;
    sqlite3_stmt *upd = NULL;
    sqlite3_stmt *payload = NULL;

    prepare(db, &ins, "INSERT INTO kv(k,v,pad) VALUES(?,?,?);");
    prepare(db, &pins, "INSERT INTO payload(id,word,pad) VALUES(?,?,?);");
    prepare(db, &point, "SELECT v, length(pad) FROM kv WHERE k=?;");
    prepare(db, &range, "SELECT coalesce(sum(v),0), count(*) FROM kv WHERE k BETWEEN ? AND ?;");
    prepare(db, &vscan, "SELECT coalesce(sum(k),0), count(*) FROM kv WHERE v BETWEEN ? AND ?;");
    prepare(db, &upd, "UPDATE kv SET v=? WHERE k=?;");
    prepare(db, &payload, "SELECT word, length(pad) FROM payload WHERE id=?;");

    exec_sql(db, "BEGIN IMMEDIATE;");
    for (uint32_t i = 0; i < rows; ++i) {
        uint32_t k = keys[i];
        int64_t v = (int64_t)(mix64((uint64_t)k + ((uint64_t)seed << 32)) & 0x7fffffff);
        fill_blob(blob, (int)sizeof(blob), (uint64_t)k, 0);
        sqlite3_bind_int64(ins, 1, (sqlite3_int64)k);
        sqlite3_bind_int64(ins, 2, (sqlite3_int64)v);
        sqlite3_bind_blob(ins, 3, blob, (int)sizeof(blob), SQLITE_TRANSIENT);
        step_done(db, ins, "insert kv");
        fold((uint64_t)k ^ (uint64_t)v);
    }
    for (uint32_t i = 0; i < payload_rows; ++i) {
        uint32_t id = permute_index(i, payload_rows - 1, seed) + 1u;
        uint64_t word = 0x00000000400000ull + ((mix64((uint64_t)id + ((uint64_t)seed << 24)) & 0x7ffffull) << 3);
        fill_blob(blob, (int)sizeof(blob), word, poison);
        sqlite3_bind_int64(pins, 1, (sqlite3_int64)id);
        sqlite3_bind_int64(pins, 2, (sqlite3_int64)word);
        sqlite3_bind_blob(pins, 3, blob, (int)sizeof(blob), SQLITE_TRANSIENT);
        step_done(db, pins, "insert payload");
        fold(word ^ id);
    }
    exec_sql(db, "COMMIT;");

    for (uint32_t i = 0; i < lookups; ++i) {
        uint32_t idx = permute_index(i, key_mask, seed);
        sqlite3_bind_int64(point, 1, (sqlite3_int64)keys[idx]);
        rc = sqlite3_step(point);
        if (rc != SQLITE_ROW) {
            die_sql(db, "point", rc);
        }
        fold((uint64_t)sqlite3_column_int64(point, 0));
        fold((uint64_t)sqlite3_column_int(point, 1));
        sqlite3_reset(point);
        sqlite3_clear_bindings(point);
    }

    for (uint32_t i = 0; i < ranges; ++i) {
        uint32_t a = (uint32_t)(mix64((uint64_t)i * 17u + seed) & key_mask) * 8u + 3u;
        uint32_t width = 8u * (1u + (uint32_t)(mix64((uint64_t)i + 99u + seed) & 31u));
        uint32_t b = a + width;
        sqlite3_bind_int64(range, 1, (sqlite3_int64)a);
        sqlite3_bind_int64(range, 2, (sqlite3_int64)b);
        rc = sqlite3_step(range);
        if (rc != SQLITE_ROW) {
            die_sql(db, "range", rc);
        }
        fold((uint64_t)sqlite3_column_int64(range, 0));
        fold((uint64_t)sqlite3_column_int64(range, 1));
        sqlite3_reset(range);
        sqlite3_clear_bindings(range);

        int64_t va = (int64_t)(mix64((uint64_t)i * 31u + seed) & 0x3fffffff);
        int64_t vb = va + (int64_t)(mix64((uint64_t)i + 7u + seed) & 0xfffff);
        sqlite3_bind_int64(vscan, 1, (sqlite3_int64)va);
        sqlite3_bind_int64(vscan, 2, (sqlite3_int64)vb);
        rc = sqlite3_step(vscan);
        if (rc != SQLITE_ROW) {
            die_sql(db, "vscan", rc);
        }
        fold((uint64_t)sqlite3_column_int64(vscan, 0));
        fold((uint64_t)sqlite3_column_int64(vscan, 1));
        sqlite3_reset(vscan);
        sqlite3_clear_bindings(vscan);
    }

    exec_sql(db, "BEGIN IMMEDIATE;");
    for (uint32_t i = 0; i < updates; ++i) {
        uint32_t idx = permute_index(i * 13u + 5u, key_mask, seed);
        uint32_t k = keys[idx];
        int64_t v = (int64_t)(mix64((uint64_t)k ^ 0xa5a5a5a5u ^ i ^ ((uint64_t)seed << 32)) & 0x7fffffff);
        sqlite3_bind_int64(upd, 1, (sqlite3_int64)v);
        sqlite3_bind_int64(upd, 2, (sqlite3_int64)k);
        step_done(db, upd, "update");
        fold((uint64_t)k ^ (uint64_t)v);
    }
    exec_sql(db, "COMMIT;");

    for (uint32_t i = 0; i < payload_rows; ++i) {
        uint32_t id = permute_index(i * 9u + 11u, payload_rows - 1, seed) + 1u;
        sqlite3_bind_int64(payload, 1, (sqlite3_int64)id);
        rc = sqlite3_step(payload);
        if (rc != SQLITE_ROW) {
            die_sql(db, "payload", rc);
        }
        fold((uint64_t)sqlite3_column_int64(payload, 0));
        fold((uint64_t)sqlite3_column_int(payload, 1));
        sqlite3_reset(payload);
        sqlite3_clear_bindings(payload);
    }

    sqlite3_finalize(payload);
    sqlite3_finalize(upd);
    sqlite3_finalize(vscan);
    sqlite3_finalize(range);
    sqlite3_finalize(point);
    sqlite3_finalize(pins);
    sqlite3_finalize(ins);
    sqlite3_close(db);
    free(keys);

    printf("SQLITE_COPPER_RESULT rows=%u lookups=%u ranges=%u updates=%u payload_rows=%u seed=%u poison=%d checksum=0x%016llx\n",
           rows, lookups, ranges, updates, payload_rows, seed, poison,
           (unsigned long long)checksum_acc);
    return 0;
}
