#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct session_t session_t;
typedef struct record_t record_t;

struct record_t {
    uint64_t seq;
    uint64_t len;
    volatile uint64_t ticket_word;
    volatile uint64_t mask_word;
    uint64_t auth0;
    uint64_t auth1;
    record_t *next;
};

struct session_t {
    uint64_t sid;
    uint64_t epoch;
    uint64_t key0;
    uint64_t key1;
    uint64_t aad;
    uint32_t hits;
    uint32_t bucket_tag;
    session_t *hash_next;
    session_t *hash_prev;
    session_t *lru_next;
    session_t *lru_prev;
    record_t *records;
    record_t *record_head;
};

typedef struct {
    session_t **buckets;
    session_t *sessions;
    record_t *records;
    session_t *lru_head;
    session_t *lru_tail;
    uint32_t sessions_count;
    uint32_t records_per_session;
    uint32_t bucket_mask;
} service_t;

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
    checksum_acc = (checksum_acc << 17) | (checksum_acc >> 47);
}

static int
is_power_of_two(uint32_t x)
{
    return x && ((x & (x - 1)) == 0);
}

static uint32_t
permute_index(uint32_t i, uint32_t mask, uint32_t seed)
{
    return (uint32_t)(((uint64_t)i * 2654435761u) + ((uint64_t)seed * 2246822519u)) & mask;
}

static uint64_t
make_sid(uint32_t i, uint32_t seed)
{
    return (mix64(((uint64_t)i << 21) ^ ((uint64_t)seed << 3) ^ 0x544c5353434f5050ull) & 0x0000fffffffffff8ull) | 8ull;
}

static uint64_t
poison_word(uint32_t i, uint32_t seed, uint32_t salt, int poison)
{
    uint64_t x = mix64(((uint64_t)i << 32) ^ ((uint64_t)seed << 9) ^ salt);
    if (!poison) {
        return x & 0x3ffff8ull;
    }
    return 0x00000000400000ull + ((x & 0x1fffffull) << 3);
}

static uint64_t
auth_round(uint64_t state, uint64_t word, uint64_t key)
{
    state += word ^ key;
    state ^= state >> 23;
    state *= 0x2127599bf4325c37ull;
    state ^= state >> 47;
    return state;
}

static uint64_t
constant_time_record_auth(session_t *s, record_t *r)
{
    uint64_t state = s->key0 ^ (s->key1 << 1) ^ s->aad ^ r->seq;
    uint64_t t0 = r->ticket_word;
    uint64_t t1 = r->mask_word;
    state = auth_round(state, r->len, s->key0);
    state = auth_round(state, t0, s->key1);
    state = auth_round(state, t1, s->key0 ^ s->epoch);
    state = auth_round(state, r->auth0, s->key1 ^ s->aad);
    state = auth_round(state, r->auth1, s->key0 + r->seq);
    return state;
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
        fold(cur->sid ^ cur->epoch ^ cur->aad);
        if (cur->sid == sid) {
            return cur;
        }
        cur = cur->hash_next;
    }
    return NULL;
}

static void
record_init(record_t *r, uint32_t global_slot, uint32_t seed, uint32_t ridx,
            int poison)
{
    r->seq = mix64(((uint64_t)global_slot << 8) ^ ridx ^ seed);
    r->len = 64u + ((global_slot + ridx) & 255u);
    r->ticket_word = poison_word(global_slot, seed, 0x71u + ridx, poison);
    r->mask_word = poison_word(global_slot, seed, 0xb5u + 3u * ridx, poison);
    r->auth0 = mix64(r->seq ^ 0x13579bdf2468ace0ull);
    r->auth1 = mix64(r->len ^ 0xfedcba9876543210ull);
    r->next = NULL;
}

static void
session_set(service_t *svc, session_t *s, uint64_t sid, uint32_t slot,
            uint32_t seed, int poison)
{
    uint32_t base = slot * svc->records_per_session;
    s->sid = sid;
    s->epoch = mix64(sid ^ seed ^ 0x45504f43484b4559ull);
    s->key0 = mix64(sid ^ 0x243f6a8885a308d3ull);
    s->key1 = mix64(sid ^ 0x13198a2e03707344ull);
    s->aad = mix64(sid ^ s->epoch);
    s->hits = 0;
    s->bucket_tag = (uint32_t)(mix64(sid ^ s->key0) & 0xffffffffu);
    s->records = &svc->records[base];
    s->record_head = &svc->records[base];
    for (uint32_t r = 0; r < svc->records_per_session; ++r) {
        record_init(&svc->records[base + r], base + r, seed, r, poison);
        if (r + 1u < svc->records_per_session) {
            svc->records[base + r].next = &svc->records[base + r + 1u];
        }
    }
}

static void
service_init(service_t *svc, uint32_t sessions, uint32_t records_per_session,
             uint32_t seed, int poison)
{
    uint32_t buckets = sessions * 2u;
    memset(svc, 0, sizeof(*svc));
    svc->sessions_count = sessions;
    svc->records_per_session = records_per_session;
    svc->bucket_mask = buckets - 1u;
    svc->sessions = (session_t *)calloc(sessions, sizeof(session_t));
    svc->records = (record_t *)calloc((uint64_t)sessions * records_per_session, sizeof(record_t));
    svc->buckets = (session_t **)calloc(buckets, sizeof(session_t *));
    if (!svc->sessions || !svc->records || !svc->buckets) {
        fprintf(stderr, "TLSSVC_COPPER_ERROR allocation failed\n");
        exit(1);
    }
    for (uint32_t i = 0; i < sessions; ++i) {
        uint32_t slot = permute_index(i, sessions - 1u, seed);
        session_t *s = &svc->sessions[slot];
        session_set(svc, s, make_sid(i, seed), slot, seed, poison);
        hash_insert(svc, s);
        lru_push_front(svc, s);
    }
}

static void
service_destroy(service_t *svc)
{
    free(svc->buckets);
    free(svc->records);
    free(svc->sessions);
}

static void
process_records(session_t *s, uint32_t limit)
{
    record_t *cur = s->record_head;
    uint32_t count = 0;
    while (cur && count < limit) {
        uint64_t auth = constant_time_record_auth(s, cur);
        cur->auth0 ^= mix64(auth + s->hits);
        cur->auth1 += auth ^ s->epoch;
        fold(auth ^ cur->seq ^ cur->ticket_word);
        cur = cur->next;
        count++;
    }
}

static void
scan_lru_sessions(service_t *svc, uint32_t depth, uint32_t record_limit,
                  uint32_t salt)
{
    session_t *cur = svc->lru_head;
    for (uint32_t i = 0; i < depth && cur; ++i) {
        fold(cur->sid ^ cur->epoch ^ salt);
        process_records(cur, record_limit);
        cur = cur->lru_next;
    }
}

static void
service_request(service_t *svc, uint32_t op, uint32_t seed, uint32_t scan_depth,
                uint32_t record_limit, int poison)
{
    uint32_t mask = svc->sessions_count - 1u;
    uint64_t r = mix64(((uint64_t)op << 32) ^ seed ^ 0xa5a5a5a55a5a5a5aull);
    uint32_t hit_slot = permute_index((uint32_t)r, mask, seed ^ 0x51u);
    uint64_t sid = make_sid(hit_slot, seed);
    if ((r & 63u) == 0) {
        sid = make_sid((uint32_t)(r >> 19) ^ op ^ 0x0000babeu, seed ^ 0x73u);
    }

    session_t *s = service_find(svc, sid);
    if (s) {
        s->hits++;
        s->epoch = mix64(s->epoch + op + s->hits);
        s->aad ^= mix64(s->sid ^ s->epoch);
        s->bucket_tag ^= (uint32_t)(s->aad >> 17);
        process_records(s, record_limit);
        lru_touch(svc, s);
    } else {
        session_t *victim = svc->lru_tail;
        if (!victim) {
            fprintf(stderr, "TLSSVC_COPPER_ERROR empty LRU\n");
            exit(1);
        }
        lru_remove(svc, victim);
        hash_remove(svc, victim);
        session_set(svc, victim, sid, (uint32_t)(victim - svc->sessions), seed + op,
                    poison);
        hash_insert(svc, victim);
        lru_push_front(svc, victim);
        fold(victim->sid ^ victim->epoch ^ 0xfeedfaceu);
    }

    if ((op & 31u) == 0) {
        scan_lru_sessions(svc, scan_depth, record_limit, op ^ seed);
    }
}

static void
validate_service(service_t *svc)
{
    uint32_t lru_count = 0;
    session_t *prev = NULL;
    for (session_t *cur = svc->lru_head; cur; cur = cur->lru_next) {
        if (cur->lru_prev != prev) {
            fprintf(stderr, "TLSSVC_COPPER_ERROR broken lru prev\n");
            exit(1);
        }
        fold(cur->sid ^ cur->bucket_tag);
        prev = cur;
        lru_count++;
        if (lru_count > svc->sessions_count) {
            fprintf(stderr, "TLSSVC_COPPER_ERROR lru cycle\n");
            exit(1);
        }
    }
    if (prev != svc->lru_tail || lru_count != svc->sessions_count) {
        fprintf(stderr, "TLSSVC_COPPER_ERROR lru count=%u sessions=%u\n",
                lru_count, svc->sessions_count);
        exit(1);
    }

    uint32_t hash_count = 0;
    for (uint32_t b = 0; b <= svc->bucket_mask; ++b) {
        session_t *prev_hash = NULL;
        for (session_t *cur = svc->buckets[b]; cur; cur = cur->hash_next) {
            if (cur->hash_prev != prev_hash) {
                fprintf(stderr, "TLSSVC_COPPER_ERROR broken hash prev\n");
                exit(1);
            }
            fold(cur->sid ^ ((uint64_t)b << 32));
            prev_hash = cur;
            hash_count++;
            if (hash_count > svc->sessions_count) {
                fprintf(stderr, "TLSSVC_COPPER_ERROR hash cycle\n");
                exit(1);
            }
        }
    }
    if (hash_count != svc->sessions_count) {
        fprintf(stderr, "TLSSVC_COPPER_ERROR hash count=%u sessions=%u\n",
                hash_count, svc->sessions_count);
        exit(1);
    }
}

int
main(int argc, char **argv)
{
    uint32_t sessions = 512;
    uint32_t requests = 4096;
    uint32_t records = 4;
    uint32_t scan_depth = 32;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--sessions") && i + 1 < argc) {
            sessions = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--requests") && i + 1 < argc) {
            requests = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--records") && i + 1 < argc) {
            records = (uint32_t)strtoul(argv[++i], NULL, 0);
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
                    "usage: %s [--sessions pow2] [--requests n] [--records n] [--scan-depth n] [--rounds n] [--seed n] [--no-poison]\n",
                    argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(sessions) || sessions < 128 || sessions > (1u << 20)) {
        fprintf(stderr, "TLSSVC_COPPER_ERROR sessions must be a power of two in [128,1048576]\n");
        return 2;
    }
    if (records == 0 || records > 16 || requests < 128 || rounds == 0 || rounds > 64) {
        fprintf(stderr, "TLSSVC_COPPER_ERROR invalid records, requests, or rounds\n");
        return 2;
    }
    if (scan_depth == 0 || scan_depth > sessions) {
        fprintf(stderr, "TLSSVC_COPPER_ERROR scan-depth must be in [1,sessions]\n");
        return 2;
    }

    service_t svc;
    service_init(&svc, sessions, records, seed, poison);
    for (uint32_t r = 0; r < rounds; ++r) {
        for (uint32_t op = 0; op < requests; ++op) {
            service_request(&svc, op + r * requests, seed + r * 19u, scan_depth,
                            records, poison);
        }
    }
    validate_service(&svc);

    printf("TLSSVC_COPPER_RESULT sessions=%u requests=%u records=%u scan_depth=%u rounds=%u seed=%u poison=%u checksum=0x%016llx\n",
           sessions, requests, records, scan_depth, rounds, seed, poison,
           (unsigned long long)checksum_acc);

    service_destroy(&svc);
    return 0;
}
