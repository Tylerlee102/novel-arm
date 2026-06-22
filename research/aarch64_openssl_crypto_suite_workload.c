#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct evp_cipher_st EVP_CIPHER;
typedef struct evp_cipher_ctx_st EVP_CIPHER_CTX;
typedef struct evp_md_st EVP_MD;

const EVP_CIPHER *EVP_aes_128_ctr(void);
const EVP_MD *EVP_sha256(void);
EVP_CIPHER_CTX *EVP_CIPHER_CTX_new(void);
void EVP_CIPHER_CTX_free(EVP_CIPHER_CTX *c);
int EVP_EncryptInit_ex(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *cipher, void *impl,
                       const unsigned char *key, const unsigned char *iv);
int EVP_EncryptUpdate(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl,
                      const unsigned char *in, int inl);
int EVP_EncryptFinal_ex(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl);
unsigned char *HMAC(const EVP_MD *evp_md, const void *key, int key_len,
                    const unsigned char *d, size_t n, unsigned char *md,
                    unsigned int *md_len);
unsigned char *SHA256(const unsigned char *d, size_t n, unsigned char *md);
int CRYPTO_memcmp(const void *in_a, const void *in_b, size_t len);

typedef struct session_t session_t;

struct session_t {
    uint64_t sid;
    uint64_t seq;
    volatile uint64_t ticket0;
    volatile uint64_t ticket1;
    uint8_t key[32];
    uint8_t iv[16];
    uint8_t payload[256];
    uint8_t ciphertext[288];
    uint8_t digest[32];
    uint8_t mac[32];
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

static uint64_t checksum_acc = 0x3c6ef372fe94f82bull;

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
    return (uint32_t)(((uint64_t)i * 2654435761u) + ((uint64_t)seed * 1103515245u)) & mask;
}

static uint64_t
make_sid(uint32_t i, uint32_t seed)
{
    return (mix64(((uint64_t)i << 23) ^ ((uint64_t)seed << 7) ^ 0x43525950544f5353ull) & 0x0000fffffffffff8ull) | 8ull;
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
    s->seq = mix64(sid ^ seed ^ 0x657670686d616331ull);
    s->ticket0 = poison_word(slot, seed, 0x9du, poison);
    s->ticket1 = poison_word(slot, seed, 0xd7u, poison);
    for (uint32_t i = 0; i < sizeof(s->key); ++i) {
        s->key[i] = (uint8_t)(mix64(sid ^ seed ^ i) >> 24);
    }
    for (uint32_t i = 0; i < sizeof(s->iv); ++i) {
        s->iv[i] = (uint8_t)(mix64(sid ^ (i << 4) ^ 0x1234u) >> 32);
    }
    for (uint32_t i = 0; i < sizeof(s->payload); ++i) {
        s->payload[i] = (uint8_t)(mix64(sid ^ ((uint64_t)i << 8) ^ seed) >> 16);
    }
    memset(s->ciphertext, 0, sizeof(s->ciphertext));
    memset(s->digest, 0, sizeof(s->digest));
    memset(s->mac, 0, sizeof(s->mac));
}

static int
openssl_crypto_round(session_t *s, uint32_t rounds)
{
    uint8_t buf[288];
    uint8_t digest[32];
    uint8_t mac[32];
    unsigned int mac_len = 0;
    int out_len = 0;
    int final_len = 0;

    for (uint32_t r = 0; r < rounds; ++r) {
        uint64_t t0 = s->ticket0;
        uint64_t t1 = s->ticket1;
        memcpy(buf, s->payload, sizeof(s->payload));
        memcpy(buf + 256, &s->sid, sizeof(s->sid));
        memcpy(buf + 264, &s->seq, sizeof(s->seq));
        memcpy(buf + 272, &t0, sizeof(t0));
        memcpy(buf + 280, &t1, sizeof(t1));

        EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
        if (!ctx) {
            return 0;
        }
        if (!EVP_EncryptInit_ex(ctx, EVP_aes_128_ctr(), NULL, s->key, s->iv)) {
            EVP_CIPHER_CTX_free(ctx);
            return 0;
        }
        if (!EVP_EncryptUpdate(ctx, s->ciphertext, &out_len, buf, (int)sizeof(buf))) {
            EVP_CIPHER_CTX_free(ctx);
            return 0;
        }
        if (!EVP_EncryptFinal_ex(ctx, s->ciphertext + out_len, &final_len)) {
            EVP_CIPHER_CTX_free(ctx);
            return 0;
        }
        EVP_CIPHER_CTX_free(ctx);

        SHA256(s->ciphertext, (size_t)(out_len + final_len), digest);
        if (!HMAC(EVP_sha256(), s->key, 32, s->ciphertext,
                  (size_t)(out_len + final_len), mac, &mac_len)) {
            return 0;
        }
        (void)CRYPTO_memcmp(digest, mac, mac_len < 32 ? mac_len : 32);
        memcpy(s->digest, digest, sizeof(s->digest));
        memcpy(s->mac, mac, sizeof(s->mac));
        s->seq = mix64(s->seq ^ digest[0] ^ ((uint64_t)mac[7] << 8) ^ t0 ^ r);
        fold(((uint64_t)digest[3] << 40) ^ ((uint64_t)mac[11] << 8) ^ t1);
    }
    return 1;
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
        fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR allocation failed\n");
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
scan_lru(service_t *svc, uint32_t depth, uint32_t crypto_rounds)
{
    session_t *cur = svc->lru_head;
    for (uint32_t i = 0; i < depth && cur; ++i) {
        if (!openssl_crypto_round(cur, crypto_rounds)) {
            fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR crypto round failed\n");
            exit(1);
        }
        cur = cur->lru_next;
    }
}

static void
service_request(service_t *svc, uint32_t op, uint32_t seed, uint32_t scan_depth,
                uint32_t crypto_rounds, int poison)
{
    uint32_t mask = svc->sessions_count - 1u;
    uint64_t r = mix64(((uint64_t)op << 32) ^ seed ^ 0x63727970746f7375ull);
    uint32_t hit_slot = permute_index((uint32_t)r, mask, seed ^ 0xa1u);
    uint64_t sid = make_sid(hit_slot, seed);
    if ((r & 127u) == 0) {
        sid = make_sid((uint32_t)(r >> 21) ^ op ^ 0x00455650u, seed ^ 0x47u);
    }

    session_t *s = service_find(svc, sid);
    if (s) {
        if (!openssl_crypto_round(s, crypto_rounds)) {
            fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR crypto round failed\n");
            exit(1);
        }
        lru_touch(svc, s);
    } else {
        session_t *victim = svc->lru_tail;
        if (!victim) {
            fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR empty LRU\n");
            exit(1);
        }
        lru_remove(svc, victim);
        hash_remove(svc, victim);
        session_set(victim, sid, (uint32_t)(victim - svc->sessions), seed + op,
                    poison);
        hash_insert(svc, victim);
        lru_push_front(svc, victim);
        fold(victim->sid ^ victim->seq ^ 0x455650u);
    }

    if ((op & 63u) == 0) {
        scan_lru(svc, scan_depth, crypto_rounds);
    }
}

static void
validate_service(service_t *svc)
{
    uint32_t lru_count = 0;
    session_t *prev = NULL;
    for (session_t *cur = svc->lru_head; cur; cur = cur->lru_next) {
        if (cur->lru_prev != prev) {
            fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR broken lru prev\n");
            exit(1);
        }
        fold(cur->sid ^ cur->seq);
        prev = cur;
        lru_count++;
        if (lru_count > svc->sessions_count) {
            fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR lru cycle\n");
            exit(1);
        }
    }
    if (prev != svc->lru_tail || lru_count != svc->sessions_count) {
        fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR lru count=%u sessions=%u\n",
                lru_count, svc->sessions_count);
        exit(1);
    }
}

int
main(int argc, char **argv)
{
    uint32_t sessions = 64;
    uint32_t requests = 64;
    uint32_t crypto_rounds = 1;
    uint32_t scan_depth = 4;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--sessions") && i + 1 < argc) {
            sessions = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--requests") && i + 1 < argc) {
            requests = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--crypto-rounds") && i + 1 < argc) {
            crypto_rounds = (uint32_t)strtoul(argv[++i], NULL, 0);
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
                    "usage: %s [--sessions pow2] [--requests n] [--crypto-rounds n] [--scan-depth n] [--rounds n] [--seed n] [--no-poison]\n",
                    argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(sessions) || sessions < 64 || sessions > (1u << 20)) {
        fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR sessions must be a power of two in [64,1048576]\n");
        return 2;
    }
    if (requests < 64 || crypto_rounds == 0 || crypto_rounds > 32 || rounds == 0 || rounds > 64) {
        fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR invalid requests, crypto-rounds, or rounds\n");
        return 2;
    }
    if (scan_depth == 0 || scan_depth > sessions) {
        fprintf(stderr, "OPENSSL_CRYPTO_COPPER_ERROR scan-depth must be in [1,sessions]\n");
        return 2;
    }

    service_t svc;
    service_init(&svc, sessions, seed, poison);
    for (uint32_t r = 0; r < rounds; ++r) {
        for (uint32_t op = 0; op < requests; ++op) {
            service_request(&svc, op + r * requests, seed + r * 29u, scan_depth,
                            crypto_rounds, poison);
        }
    }
    validate_service(&svc);

    printf("OPENSSL_CRYPTO_COPPER_RESULT sessions=%u requests=%u crypto_rounds=%u scan_depth=%u rounds=%u seed=%u poison=%u checksum=0x%016llx\n",
           sessions, requests, crypto_rounds, scan_depth, rounds, seed, poison,
           (unsigned long long)checksum_acc);

    service_destroy(&svc);
    return 0;
}
