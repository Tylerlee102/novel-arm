#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"

static const char *lua_workload =
"local rows = ROWS\n"
"local lookups = LOOKUPS\n"
"local updates = UPDATES\n"
"local traversals = TRAVERSALS\n"
"local poison = POISON\n"
"local seed = SEED\n"
"local mask = rows - 1\n"
"local checksum = 0x1234567\n"
"local function mix(x)\n"
"  x = (x ~ (x >> 16)) & 0x7fffffff\n"
"  x = (x * 1103515245 + 12345) & 0x7fffffff\n"
"  x = (x ~ (x >> 13)) & 0x7fffffff\n"
"  return x\n"
"end\n"
"local function fold(x)\n"
"  checksum = ((checksum ~ x) * 1664525 + 1013904223) & 0x7fffffff\n"
"end\n"
"local nodes = {}\n"
"local map = {}\n"
"local head = nil\n"
"for i = 1, rows do\n"
"  local slot = (((i - 1) * 2654435761) + (seed * 40503)) & mask\n"
"  local k = slot * 8 + 3\n"
"  local v = mix(k + i + seed)\n"
"  local p0 = poison and (0x400000 + ((mix(k) & 0x3ffff) << 3)) or mix(v + 17)\n"
"  local p1 = poison and (0x500000 + ((mix(k + 1) & 0x3ffff) << 3)) or mix(v + 31)\n"
"  local payload = string.pack('<I8I8I8I8', p0, p1, mix(k + 2), mix(k + 3))\n"
"  local node = {k = k, v = v, payload = payload, next = head}\n"
"  nodes[i] = node\n"
"  map[k] = node\n"
"  head = node\n"
"  fold(k ~ v)\n"
"end\n"
"for i = 1, lookups do\n"
"  local idx = (((i * 1103515245) + 12345 + (seed * 97)) & mask) + 1\n"
"  local node = map[nodes[idx].k]\n"
"  fold(node.v)\n"
"  local a, b = string.unpack('<I8I8', node.payload)\n"
"  fold((a ~ b) & 0x7fffffff)\n"
"  if node.next then fold(node.next.k) end\n"
"end\n"
"for i = 1, updates do\n"
"  local idx = (((i * 69069) + 7 + (seed * 53)) & mask) + 1\n"
"  local node = nodes[idx]\n"
"  node.v = mix(node.v ~ i)\n"
"  map[node.k] = node\n"
"  fold(node.v)\n"
"end\n"
"local cursor = head\n"
"for i = 1, traversals do\n"
"  cursor = cursor and cursor.next or head\n"
"  fold(cursor.k ~ cursor.v)\n"
"end\n"
"for i = 1, 8 do collectgarbage('step', rows) end\n"
"return checksum\n";

static int
is_power_of_two(uint32_t x)
{
    return x && ((x & (x - 1)) == 0);
}

static void
set_int(lua_State *L, const char *name, lua_Integer value)
{
    lua_pushinteger(L, value);
    lua_setglobal(L, name);
}

int
main(int argc, char **argv)
{
    uint32_t rows = 4096;
    uint32_t lookups = 16000;
    uint32_t updates = 4096;
    uint32_t traversals = 16000;
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
        fprintf(stderr, "LUA_COPPER_ERROR rows must be a power of two in [256,1048576]\n");
        return 2;
    }

    lua_State *L = luaL_newstate();
    if (!L) {
        fprintf(stderr, "LUA_COPPER_ERROR luaL_newstate failed\n");
        return 1;
    }
    luaL_openlibs(L);
    set_int(L, "ROWS", (lua_Integer)rows);
    set_int(L, "LOOKUPS", (lua_Integer)lookups);
    set_int(L, "UPDATES", (lua_Integer)updates);
    set_int(L, "TRAVERSALS", (lua_Integer)traversals);
    set_int(L, "POISON", (lua_Integer)poison);
    set_int(L, "SEED", (lua_Integer)seed);

    int rc = luaL_dostring(L, lua_workload);
    if (rc != LUA_OK) {
        fprintf(stderr, "LUA_COPPER_ERROR rc=%d msg=%s\n",
                rc, lua_tostring(L, -1));
        lua_close(L);
        return 1;
    }
    lua_Integer checksum = lua_tointeger(L, -1);
    lua_pop(L, 1);
    lua_close(L);

    printf("LUA_COPPER_RESULT rows=%u lookups=%u updates=%u traversals=%u seed=%u poison=%d checksum=0x%llx\n",
           rows, lookups, updates, traversals, seed, poison,
           (unsigned long long)checksum);
    return 0;
}
