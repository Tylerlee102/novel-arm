#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

unsigned char *SHA256(const unsigned char *d, size_t n, unsigned char *md);

typedef struct session_t session_t;

struct session_t {
    uint64_t sid;
    uint64_t seq;
    volatile uint64_t ticket0;
    volatile uint64_t ticket1;
    uint8_t payload[192];
    uint8_t digest[32];
    session_t *hash_next;
    session_t *hash_prev;
    session_t *lru_next;
    session_t *lru_prev;
};

typedef struct {
    session_t **buckets;
    session_t *sessions;
    session_t *lru_head;
    session_t *lru_tail;
    uint32_t sessions_count;
    uint32_t bucket_mask;
} service_t;

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
    return (uint32_t)(((uint64_t)i * 2654435761u) + ((uint64_t)seed * 747796405u)) & mask;
}

static uint64_t
make_sid(uint32_t i, uint32_t seed)
{
    return (mix64(((uint64_t)i << 19) ^ ((uint64_t)seed << 7) ^ 0x4f53534c53484132ull) & 0x0000fffffffffff8ull) | 8ull;
}

static uint64_t
poison_word(uint32_t i, uint32_t seed, uint32_t salt, int poison)
{
    uint64_t x = mix64(((uint64_t)i << 32) ^ ((uint64_t)seed << 5) ^ salt);
    if (!poison) {
        return x & 0x3ffff8ull;
    }
    return 0x00000000400000ull + ((x & 0x1fffffull) << 3);
}

static uint32_t
bucket_index(service_t *svc, uint64_t sid)
{
    return (uint32_t)mix64(sid) & svc->bucket_mask;
}

static void
lru_remove(service_t *svc, session_t *s)
{
    if (s->lru_prev) {
        s->lru_prev->lru_next = s->lru_next;
    } else {
        svc->lru_head = s->lru_next;
    }
    if (s->lru_next) {
        s->lru_next->lru_prev = s->lru_prev;
    } else {
        svc->lru_tail = s->lru_prev;
    }
    s->lru_next = NULL;
    s->lru_prev = NULL;
}

static void
lru_push_front(service_t *svc, session_t *s)
{
    s->lru_prev = NULL;
    s->lru_next = svc->lru_head;
    if (svc->lru_head) {
        svc->lru_head->lru_prev = s;
    } else {
        svc->lru_tail = s;
    }
    svc->lru_head = s;
}

static void
lru_touch(service_t *svc, session_t *s)
{
    if (svc->lru_head == s) {
        return;
    }
    lru_remove(svc, s);
    lru_push_front(svc, s);
}

static void
hash_remove(service_t *svc, session_t *s)
{
    uint32_t idx = bucket_index(svc, s->sid);
    if (s->hash_prev) {
        s->hash_prev->hash_next = s->hash_next;
    } else {
        svc->buckets[idx] = s->hash_next;
    }
    if (s->hash_next) {
        s->hash_next->hash_prev = s->hash_prev;
    }
    s->hash_next = NULL;
    s->hash_prev = NULL;
}

static void
hash_insert(service_t *svc, session_t *s)
{
    uint32_t idx = bucket_index(svc, s->sid);
    s->hash_prev = NULL;
    s->hash_next = svc->buckets[idx];
    if (svc->buckets[idx]) {
        svc->buckets[idx]->hash_prev = s;
    }
    svc->buckets[idx] = s;
}

static session_t *
service_find(service_t *svc, uint64_t sid)
{
    session_t *cur = svc->buckets[bucket_index(svc, sid)];
    while (cur) {
        fold(cur->sid ^ cur->seq);
        if (cur->sid == sid) {
            return cur;
        }
        cur = cur->hash_next;
    }
    return NULL;
}

static void
session_set(session_t *s, uint64_t sid, uint32_t slot, uint32_t seed, int poison)
{
    s->sid = sid;
    s->seq = mix64(sid ^ seed ^ 0x73657373696f6e31ull);
    s->ticket0 = poison_word(slot, seed, 0x81u, poison);
    s->ticket1 = poison_word(slot, seed, 0xc3u, poison);
    for (uint32_t i = 0; i < sizeof(s->payload); ++i) {
        s->payload[i] = (uint8_t)(mix64(sid ^ ((uint64_t)i << 8) ^ seed) >> 24);
    }
    memset(s->digest, 0, sizeof(s->digest));
}

static void
service_init(service_t *svc, uint32_t sessions, uint32_t seed, int poison)
{
    uint32_t buckets = sessions * 2u;
    memset(svc, 0, sizeof(*svc));
    svc->sessions_count = sessions;
    svc->bucket_mask = buckets - 1u;
    svc->sessions = (session_t *)calloc(sessions, sizeof(session_t));
    svc->buckets = (session_t **)calloc(buckets, sizeof(session_t *));
    if (!svc->sessions || !svc->buckets) {
        fprintf(stderr, "OPENSSL_SHA_COPPER_ERROR allocation failed\n");
        exit(1);
    }
    for (uint32_t i = 0; i < sessions; ++i) {
        uint32_t slot = permute_index(i, sessions - 1u, seed);
        session_t *s = &svc->sessions[slot];
        session_set(s, make_sid(i, seed), slot, seed, poison);
        hash_insert(svc, s);
        lru_push_front(svc, s);
    }
}

static void
service_destroy(service_t *svc)
{
    free(svc->buckets);
    free(svc->sessions);
}

static void
openssl_hash_session(session_t *s, uint32_t blocks)
{
    uint8_t buf[256];
    for (uint32_t b = 0; b < blocks; ++b) {
        uint64_t t0 = s->ticket0;
        uint64_t t1 = s->ticket1;
        memcpy(buf, s->payload, sizeof(s->payload));
        memcpy(buf + 192, &s->sid, sizeof(s->sid));
        memcpy(buf + 200, &s->seq, sizeof(s->seq));
        memcpy(buf + 208, &t0, sizeof(t0));
        memcpy(buf + 216, &t1, sizeof(t1));
        memset(buf + 224, (int)(b + s->seq), 32);
        SHA256(buf, sizeof(buf), s->digest);
        fold(((uint64_t)s->digest[0] << 56) ^ ((uint64_t)s->digest[7] << 8) ^ t0);
        s->seq = mix64(s->seq + s->digest[13] + b);
    }
}

static void
scan_lru(service_t *svc, uint32_t depth, uint32_t blocks)
{
    session_t *cur = svc->lru_head;
    for (uint32_t i = 0; i < depth && cur; ++i) {
        openssl_hash_session(cur, blocks);
        cur = cur->lru_next;
    }
}

static void
service_request(service_t *svc, uint32_t op, uint32_t seed, uint32_t scan_depth,
                uint32_t blocks, int poison)
{
    uint32_t mask = svc->sessions_count - 1u;
    uint64_t r = mix64(((uint64_t)op << 32) ^ seed ^ 0x0f1e2d3c4b5a6978ull);
    uint32_t hit_slot = permute_index((uint32_t)r, mask, seed ^ 0x91u);
    uint64_t sid = make_sid(hit_slot, seed);
    if ((r & 127u) == 0) {
        sid = make_sid((uint32_t)(r >> 21) ^ op ^ 0x00534148u, seed ^ 0x37u);
    }

    session_t *s = service_find(svc, sid);
    if (s) {
        openssl_hash_session(s, blocks);
        lru_touch(svc, s);
    } else {
        session_t *victim = svc->lru_tail;
        if (!victim) {
            fprintf(stderr, "OPENSSL_SHA_COPPER_ERROR empty LRU\n");
            exit(1);
        }
        lru_remove(svc, victim);
        hash_remove(svc, victim);
        session_set(victim, sid, (uint32_t)(victim - svc->sessions), seed + op,
                    poison);
        hash_insert(svc, victim);
        lru_push_front(svc, victim);
        fold(victim->sid ^ victim->seq ^ 0x53484132u);
    }

    if ((op & 63u) == 0) {
        scan_lru(svc, scan_depth, blocks);
    }
}

static void
validate_service(service_t *svc)
{
    uint32_t lru_count = 0;
    session_t *prev = NULL;
    for (session_t *cur = svc->lru_head; cur; cur = cur->lru_next) {
        if (cur->lru_prev != prev) {
            fprintf(stderr, "OPENSSL_SHA_COPPER_ERROR broken lru prev\n");
            exit(1);
        }
        fold(cur->sid ^ cur->seq);
        prev = cur;
        lru_count++;
        if (lru_count > svc->sessions_count) {
            fprintf(stderr, "OPENSSL_SHA_COPPER_ERROR lru cycle\n");
            exit(1);
        }
    }
    if (prev != svc->lru_tail || lru_count != svc->sessions_count) {
        fprintf(stderr, "OPENSSL_SHA_COPPER_ERROR lru count=%u sessions=%u\n",
                lru_count, svc->sessions_count);
        exit(1);
    }
}

int
main(int argc, char **argv)
{
    uint32_t sessions = 128;
    uint32_t requests = 256;
    uint32_t blocks = 1;
    uint32_t scan_depth = 8;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--sessions") && i + 1 < argc) {
            sessions = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--requests") && i + 1 < argc) {
            requests = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--blocks") && i + 1 < argc) {
            blocks = (uint32_t)strtoul(argv[++i], NULL, 0);
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
                    "usage: %s [--sessions pow2] [--requests n] [--blocks n] [--scan-depth n] [--rounds n] [--seed n] [--no-poison]\n",
                    argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(sessions) || sessions < 64 || sessions > (1u << 20)) {
        fprintf(stderr, "OPENSSL_SHA_COPPER_ERROR sessions must be a power of two in [64,1048576]\n");
        return 2;
    }
    if (requests < 64 || blocks == 0 || blocks > 32 || rounds == 0 || rounds > 64) {
        fprintf(stderr, "OPENSSL_SHA_COPPER_ERROR invalid requests, blocks, or rounds\n");
        return 2;
    }
    if (scan_depth == 0 || scan_depth > sessions) {
        fprintf(stderr, "OPENSSL_SHA_COPPER_ERROR scan-depth must be in [1,sessions]\n");
        return 2;
    }

    service_t svc;
    service_init(&svc, sessions, seed, poison);
    for (uint32_t r = 0; r < rounds; ++r) {
        for (uint32_t op = 0; op < requests; ++op) {
            service_request(&svc, op + r * requests, seed + r * 23u, scan_depth,
                            blocks, poison);
        }
    }
    validate_service(&svc);

    printf("OPENSSL_SHA_COPPER_RESULT sessions=%u requests=%u blocks=%u scan_depth=%u rounds=%u seed=%u poison=%u checksum=0x%016llx\n",
           sessions, requests, blocks, scan_depth, rounds, seed, poison,
           (unsigned long long)checksum_acc);

    service_destroy(&svc);
    return 0;
}
