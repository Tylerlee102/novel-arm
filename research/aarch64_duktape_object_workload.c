#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "duktape.h"

static const char *js_workload =
"var rows = ROWS;\n"
"var lookups = LOOKUPS;\n"
"var updates = UPDATES;\n"
"var traversals = TRAVERSALS;\n"
"var seed = SEED;\n"
"var poison = POISON;\n"
"var mask = rows - 1;\n"
"var checksum = 0x2468ace;\n"
"function mix(x) {\n"
"  x = (x ^ (x >>> 16)) >>> 0;\n"
"  x = Math.imul(x, 1103515245) + 12345;\n"
"  x = (x ^ (x >>> 13)) >>> 0;\n"
"  return x & 0x7fffffff;\n"
"}\n"
"function fold(x) {\n"
"  checksum = (Math.imul((checksum ^ x) >>> 0, 1664525) + 1013904223) & 0x7fffffff;\n"
"}\n"
"var nodes = new Array(rows);\n"
"var map = Object.create(null);\n"
"var head = null;\n"
"for (var i = 0; i < rows; i++) {\n"
"  var slot = (Math.imul(i, 2654435761) + Math.imul(seed, 40503)) & mask;\n"
"  var k = slot * 8 + 3;\n"
"  var v = mix(k + i + seed);\n"
"  var p0 = poison ? (0x400000 + ((mix(k + seed) & 0x3ffff) << 3)) : mix(v + 17 + seed);\n"
"  var p1 = poison ? (0x500000 + ((mix(k + 1 + seed) & 0x3ffff) << 3)) : mix(v + 31 + seed);\n"
"  var payload = String.fromCharCode(p0 & 255, (p0 >>> 8) & 255, (p0 >>> 16) & 255, (p0 >>> 24) & 255,\n"
"                                    p1 & 255, (p1 >>> 8) & 255, (p1 >>> 16) & 255, (p1 >>> 24) & 255);\n"
"  var node = { k: k, v: v, payload: payload, next: head };\n"
"  nodes[i] = node;\n"
"  map['k' + k] = node;\n"
"  head = node;\n"
"  fold((k ^ v) & 0x7fffffff);\n"
"}\n"
"for (var j = 0; j < lookups; j++) {\n"
"  var idx = (Math.imul(j, 1103515245) + 12345 + Math.imul(seed, 97)) & mask;\n"
"  var n = map['k' + nodes[idx].k];\n"
"  fold(n.v);\n"
"  fold((n.payload.charCodeAt(0) ^ n.payload.charCodeAt(4)) & 0x7fffffff);\n"
"  if (n.next) fold(n.next.k);\n"
"}\n"
"for (var u = 0; u < updates; u++) {\n"
"  var uidx = (Math.imul(u, 69069) + 7 + Math.imul(seed, 53)) & mask;\n"
"  var un = nodes[uidx];\n"
"  un.v = mix(un.v ^ u ^ seed);\n"
"  map['k' + un.k] = un;\n"
"  fold(un.v);\n"
"}\n"
"var cursor = head;\n"
"for (var t = 0; t < traversals; t++) {\n"
"  cursor = cursor && cursor.next ? cursor.next : head;\n"
"  fold((cursor.k ^ cursor.v) & 0x7fffffff);\n"
"}\n"
"if (typeof Duktape !== 'undefined' && Duktape.gc) {\n"
"  for (var g = 0; g < 8; g++) Duktape.gc();\n"
"}\n"
"checksum;\n";

static int
is_power_of_two(uint32_t x)
{
    return x && ((x & (x - 1)) == 0);
}

static void
set_int(duk_context *ctx, const char *name, duk_int_t value)
{
    duk_push_int(ctx, value);
    duk_put_global_string(ctx, name);
}

int
main(int argc, char **argv)
{
    uint32_t rows = 1024;
    uint32_t lookups = 3000;
    uint32_t updates = 1024;
    uint32_t traversals = 3000;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--rows") && i + 1 < argc) {
            rows = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--lookups") && i + 1 < argc) {
            lookups = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--updates") && i + 1 < argc) {
            updates = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--traversals") && i + 1 < argc) {
            traversals = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--no-poison")) {
            poison = 0;
        } else {
            fprintf(stderr, "usage: %s [--rows pow2] [--lookups n] [--updates n] [--traversals n] [--seed n] [--no-poison]\n", argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(rows) || rows < 256 || rows > (1u << 20)) {
        fprintf(stderr, "DUKTAPE_COPPER_ERROR rows must be a power of two in [256,1048576]\n");
        return 2;
    }

    duk_context *ctx = duk_create_heap_default();
    if (!ctx) {
        fprintf(stderr, "DUKTAPE_COPPER_ERROR heap create failed\n");
        return 1;
    }
    set_int(ctx, "ROWS", (duk_int_t)rows);
    set_int(ctx, "LOOKUPS", (duk_int_t)lookups);
    set_int(ctx, "UPDATES", (duk_int_t)updates);
    set_int(ctx, "TRAVERSALS", (duk_int_t)traversals);
    set_int(ctx, "SEED", (duk_int_t)seed);
    set_int(ctx, "POISON", (duk_int_t)poison);

    int rc = duk_peval_string(ctx, js_workload);
    if (rc != 0) {
        fprintf(stderr, "DUKTAPE_COPPER_ERROR rc=%d msg=%s\n",
                rc, duk_safe_to_string(ctx, -1));
        duk_destroy_heap(ctx);
        return 1;
    }
    duk_int_t checksum = duk_to_int(ctx, -1);
    duk_pop(ctx);
    duk_destroy_heap(ctx);

    printf("DUKTAPE_COPPER_RESULT rows=%u lookups=%u updates=%u traversals=%u seed=%u poison=%d checksum=0x%llx\n",
           rows, lookups, updates, traversals, seed, poison,
           (unsigned long long)(uint32_t)checksum);
    return 0;
}
