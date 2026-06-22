#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct entry_t entry_t;

struct entry_t {
    uint64_t key;
    uint64_t value;
    volatile uint64_t poison0;
    volatile uint64_t poison1;
    uint32_t hits;
    uint32_t tag;
    entry_t *hash_next;
    entry_t *hash_prev;
    entry_t *lru_next;
    entry_t *lru_prev;
};

typedef struct {
    entry_t **buckets;
    entry_t *entries;
    entry_t *lru_head;
    entry_t *lru_tail;
    uint32_t items;
    uint32_t bucket_mask;
} cache_t;

static uint64_t checksum_acc = 0x243f6a8885a308d3ull;

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
    checksum_acc = (checksum_acc << 21) | (checksum_acc >> 43);
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

static uint64_t
make_key(uint32_t i, uint32_t seed)
{
    return (mix64(((uint64_t)i << 17) ^ ((uint64_t)seed << 1)) & 0x7fffffffffffull) | 1ull;
}

static uint64_t
poison_word(uint32_t i, uint32_t seed, uint32_t salt, int poison)
{
    uint64_t x = mix64(((uint64_t)i << 32) ^ ((uint64_t)seed << 11) ^ salt);
    if (!poison) {
        return x & 0x3ffff8ull;
    }
    return 0x00000000400000ull + ((x & 0x7ffffull) << 3);
}

static void
lru_remove(cache_t *cache, entry_t *e)
{
    if (e->lru_prev) {
        e->lru_prev->lru_next = e->lru_next;
    } else {
        cache->lru_head = e->lru_next;
    }
    if (e->lru_next) {
        e->lru_next->lru_prev = e->lru_prev;
    } else {
        cache->lru_tail = e->lru_prev;
    }
    e->lru_next = NULL;
    e->lru_prev = NULL;
}

static void
lru_push_front(cache_t *cache, entry_t *e)
{
    e->lru_prev = NULL;
    e->lru_next = cache->lru_head;
    if (cache->lru_head) {
        cache->lru_head->lru_prev = e;
    } else {
        cache->lru_tail = e;
    }
    cache->lru_head = e;
}

static void
lru_touch(cache_t *cache, entry_t *e)
{
    if (cache->lru_head == e) {
        return;
    }
    lru_remove(cache, e);
    lru_push_front(cache, e);
}

static uint32_t
bucket_index(cache_t *cache, uint64_t key)
{
    return (uint32_t)mix64(key) & cache->bucket_mask;
}

static void
hash_remove(cache_t *cache, entry_t *e)
{
    uint32_t idx = bucket_index(cache, e->key);
    if (e->hash_prev) {
        e->hash_prev->hash_next = e->hash_next;
    } else {
        cache->buckets[idx] = e->hash_next;
    }
    if (e->hash_next) {
        e->hash_next->hash_prev = e->hash_prev;
    }
    e->hash_next = NULL;
    e->hash_prev = NULL;
}

static void
hash_insert(cache_t *cache, entry_t *e)
{
    uint32_t idx = bucket_index(cache, e->key);
    e->hash_prev = NULL;
    e->hash_next = cache->buckets[idx];
    if (cache->buckets[idx]) {
        cache->buckets[idx]->hash_prev = e;
    }
    cache->buckets[idx] = e;
}

static entry_t *
cache_find(cache_t *cache, uint64_t key)
{
    entry_t *cur = cache->buckets[bucket_index(cache, key)];
    while (cur) {
        fold(cur->key ^ cur->value);
        if (cur->key == key) {
            return cur;
        }
        cur = cur->hash_next;
    }
    return NULL;
}

static void
entry_set(entry_t *e, uint64_t key, uint64_t value, uint32_t slot, uint32_t seed,
          int poison)
{
    e->key = key;
    e->value = value;
    e->poison0 = poison_word(slot, seed, 0x51u, poison);
    e->poison1 = poison_word(slot, seed, 0xa7u, poison);
    e->hits = 0;
    e->tag = (uint32_t)(mix64(key ^ value) & 0xffffffffu);
}

static void
cache_init(cache_t *cache, uint32_t items, uint32_t seed, int poison)
{
    uint32_t buckets = items * 2u;
    memset(cache, 0, sizeof(*cache));
    cache->items = items;
    cache->bucket_mask = buckets - 1u;
    cache->entries = (entry_t *)calloc(items, sizeof(entry_t));
    cache->buckets = (entry_t **)calloc(buckets, sizeof(entry_t *));
    if (!cache->entries || !cache->buckets) {
        fprintf(stderr, "CACHESVC_COPPER_ERROR allocation failed\n");
        exit(1);
    }
    for (uint32_t i = 0; i < items; ++i) {
        uint32_t slot = permute_index(i, items - 1u, seed);
        entry_t *e = &cache->entries[slot];
        uint64_t key = make_key(i, seed);
        uint64_t value = mix64(key ^ 0xfeedfacecafebeefull);
        entry_set(e, key, value, slot, seed, poison);
        hash_insert(cache, e);
        lru_push_front(cache, e);
    }
}

static void
cache_destroy(cache_t *cache)
{
    free(cache->buckets);
    free(cache->entries);
}

static void
scan_lru(cache_t *cache, uint32_t depth, uint32_t salt)
{
    entry_t *cur = cache->lru_head;
    for (uint32_t i = 0; i < depth && cur; ++i) {
        uint64_t p0 = cur->poison0;
        uint64_t p1 = cur->poison1;
        fold(cur->key ^ (cur->value << 1));
        fold(p0 ^ (p1 << 7) ^ salt);
        cur = cur->lru_next;
    }
}

static void
cache_request(cache_t *cache, uint32_t op, uint32_t seed, uint32_t scan_depth,
              int poison)
{
    uint32_t item_mask = cache->items - 1u;
    uint64_t r = mix64(((uint64_t)op << 32) ^ seed);
    uint32_t hit_slot = permute_index((uint32_t)r, item_mask, seed ^ 0x9e37u);
    uint64_t key = make_key(hit_slot, seed);
    if ((r & 31u) == 0) {
        key = make_key((uint32_t)(r >> 17) ^ op ^ 0x00c0ffeeu, seed ^ 0x45u);
    }

    entry_t *e = cache_find(cache, key);
    if (e) {
        uint64_t p0 = e->poison0;
        uint64_t p1 = e->poison1;
        e->hits++;
        e->value = mix64(e->value + op + e->hits);
        e->tag ^= (uint32_t)(e->value >> 13);
        fold(e->key ^ e->value ^ p0 ^ (p1 << 3));
        lru_touch(cache, e);
    } else {
        entry_t *victim = cache->lru_tail;
        if (!victim) {
            fprintf(stderr, "CACHESVC_COPPER_ERROR empty LRU\n");
            exit(1);
        }
        lru_remove(cache, victim);
        hash_remove(cache, victim);
        entry_set(victim, key, mix64(r ^ 0x123456789abcdef0ull), op, seed, poison);
        hash_insert(cache, victim);
        lru_push_front(cache, victim);
        fold(victim->key ^ victim->value ^ 0x5555aaaau);
    }

    if ((op & 15u) == 0) {
        scan_lru(cache, scan_depth, op ^ seed);
    }
}

static void
validate_cache(cache_t *cache)
{
    uint32_t lru_count = 0;
    entry_t *prev = NULL;
    for (entry_t *cur = cache->lru_head; cur; cur = cur->lru_next) {
        if (cur->lru_prev != prev) {
            fprintf(stderr, "CACHESVC_COPPER_ERROR broken lru prev\n");
            exit(1);
        }
        fold(cur->key ^ cur->tag);
        prev = cur;
        lru_count++;
        if (lru_count > cache->items) {
            fprintf(stderr, "CACHESVC_COPPER_ERROR lru cycle\n");
            exit(1);
        }
    }
    if (prev != cache->lru_tail || lru_count != cache->items) {
        fprintf(stderr, "CACHESVC_COPPER_ERROR lru count=%u items=%u\n",
                lru_count, cache->items);
        exit(1);
    }

    uint32_t hash_count = 0;
    for (uint32_t b = 0; b <= cache->bucket_mask; ++b) {
        entry_t *prev_hash = NULL;
        for (entry_t *cur = cache->buckets[b]; cur; cur = cur->hash_next) {
            if (cur->hash_prev != prev_hash) {
                fprintf(stderr, "CACHESVC_COPPER_ERROR broken hash prev\n");
                exit(1);
            }
            fold(cur->key ^ ((uint64_t)b << 32));
            prev_hash = cur;
            hash_count++;
            if (hash_count > cache->items) {
                fprintf(stderr, "CACHESVC_COPPER_ERROR hash cycle\n");
                exit(1);
            }
        }
    }
    if (hash_count != cache->items) {
        fprintf(stderr, "CACHESVC_COPPER_ERROR hash count=%u items=%u\n",
                hash_count, cache->items);
        exit(1);
    }
}

int
main(int argc, char **argv)
{
    uint32_t items = 2048;
    uint32_t requests = 12000;
    uint32_t scan_depth = 96;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--items") && i + 1 < argc) {
            items = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--requests") && i + 1 < argc) {
            requests = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--scan-depth") && i + 1 < argc) {
            scan_depth = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--rounds") && i + 1 < argc) {
            rounds = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--no-poison")) {
            poison = 0;
        } else {
            fprintf(stderr,
                    "usage: %s [--items pow2] [--requests n] [--scan-depth n] [--rounds n] [--seed n] [--no-poison]\n",
                    argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(items) || items < 256 || items > (1u << 20)) {
        fprintf(stderr, "CACHESVC_COPPER_ERROR items must be a power of two in [256,1048576]\n");
        return 2;
    }
    if (scan_depth == 0 || scan_depth > items) {
        fprintf(stderr, "CACHESVC_COPPER_ERROR scan-depth must be in [1,items]\n");
        return 2;
    }
    if (requests < 128 || rounds == 0 || rounds > 64) {
        fprintf(stderr, "CACHESVC_COPPER_ERROR invalid requests or rounds\n");
        return 2;
    }

    cache_t cache;
    cache_init(&cache, items, seed, poison);
    for (uint32_t r = 0; r < rounds; ++r) {
        for (uint32_t op = 0; op < requests; ++op) {
            cache_request(&cache, op + r * requests, seed + r * 17u, scan_depth,
                          poison);
        }
    }
    validate_cache(&cache);

    printf("CACHESVC_COPPER_RESULT items=%u requests=%u scan_depth=%u rounds=%u seed=%u poison=%u checksum=0x%016llx\n",
           items, requests, scan_depth, rounds, seed, poison,
           (unsigned long long)checksum_acc);

    cache_destroy(&cache);
    return 0;
}
