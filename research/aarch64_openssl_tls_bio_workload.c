#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gem5/m5ops.h>

typedef struct bio_st BIO;
typedef struct ssl_ctx_st SSL_CTX;
typedef struct ssl_method_st SSL_METHOD;
typedef struct ssl_st SSL;
typedef struct rand_meth_st RAND_METHOD;

const SSL_METHOD *TLS_method(void);
int OPENSSL_init_ssl(uint64_t opts, const void *settings);
SSL_CTX *SSL_CTX_new(const SSL_METHOD *meth);
void SSL_CTX_free(SSL_CTX *ctx);
long SSL_CTX_ctrl(SSL_CTX *ctx, int cmd, long larg, void *parg);
int SSL_CTX_set_cipher_list(SSL_CTX *ctx, const char *str);
int SSL_CTX_use_psk_identity_hint(SSL_CTX *ctx, const char *identity_hint);
void SSL_CTX_set_psk_client_callback(
    SSL_CTX *ctx,
    unsigned int (*cb)(SSL *ssl, const char *hint, char *identity,
                       unsigned int max_identity_len, unsigned char *psk,
                       unsigned int max_psk_len));
void SSL_CTX_set_psk_server_callback(
    SSL_CTX *ctx,
    unsigned int (*cb)(SSL *ssl, const char *identity, unsigned char *psk,
                       unsigned int max_psk_len));
SSL *SSL_new(SSL_CTX *ctx);
void SSL_free(SSL *ssl);
void SSL_set_bio(SSL *ssl, BIO *rbio, BIO *wbio);
void SSL_set_connect_state(SSL *ssl);
void SSL_set_accept_state(SSL *ssl);
int SSL_do_handshake(SSL *ssl);
int SSL_get_error(const SSL *ssl, int ret);
int SSL_read(SSL *ssl, void *buf, int num);
int SSL_write(SSL *ssl, const void *buf, int num);
int BIO_new_bio_pair(BIO **bio1, size_t writebuf1, BIO **bio2,
                     size_t writebuf2);
void BIO_free_all(BIO *bio);
unsigned long ERR_get_error(void);
void ERR_error_string_n(unsigned long e, char *buf, size_t len);
void RAND_seed(const void *buf, int num);
int RAND_status(void);
int RAND_set_rand_method(const RAND_METHOD *meth);

struct rand_meth_st {
    int (*seed)(const void *buf, int num);
    int (*bytes)(unsigned char *buf, int num);
    void (*cleanup)(void);
    int (*add)(const void *buf, int num, double randomness);
    int (*pseudorand)(unsigned char *buf, int num);
    int (*status)(void);
};

#define SSL_ERROR_WANT_READ 2
#define SSL_ERROR_WANT_WRITE 3
#define SSL_CTRL_SET_MIN_PROTO_VERSION 123
#define SSL_CTRL_SET_MAX_PROTO_VERSION 124
#define TLS1_2_VERSION 0x0303
#define OPENSSL_INIT_NO_LOAD_CONFIG 0x00000080L

typedef struct session_t session_t;

struct session_t {
    uint64_t sid;
    uint64_t seq;
    volatile uint64_t ticket0;
    volatile uint64_t ticket1;
    uint8_t payload[160];
    uint8_t transcript[64];
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

typedef struct {
    SSL_CTX *client_ctx;
    SSL_CTX *server_ctx;
} tls_engine_t;

static uint64_t checksum_acc = 0xa54ff53a5f1d36f1ull;
static unsigned char g_psk[32];
static uint64_t rand_state = 0x6a09e667f3bcc909ull;

static void
stage(const char *name)
{
    fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_STAGE %s\n", name);
    fflush(stderr);
}

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
    return (uint32_t)(((uint64_t)i * 2654435761u) +
                      ((uint64_t)seed * 2246822519u)) &
           mask;
}

static uint64_t
make_sid(uint32_t i, uint32_t seed)
{
    return (mix64(((uint64_t)i << 21) ^ ((uint64_t)seed << 9) ^
                  0x544c535f42494f50ull) &
            0x0000fffffffffff8ull) |
           8ull;
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

static void
print_ssl_errors(const char *label)
{
    unsigned long err = 0;
    int saw = 0;
    while ((err = ERR_get_error()) != 0) {
        char buf[160];
        ERR_error_string_n(err, buf, sizeof(buf));
        fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR %s: %s\n", label, buf);
        saw = 1;
    }
    if (!saw) {
        fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR %s\n", label);
    }
}

static int
det_rand_seed(const void *buf, int num)
{
    const unsigned char *p = (const unsigned char *)buf;
    for (int i = 0; i < num; ++i) {
        rand_state = mix64(rand_state ^ ((uint64_t)p[i] << ((i & 7) * 8)) ^
                           (uint64_t)i);
    }
    return 1;
}

static int
det_rand_bytes(unsigned char *buf, int num)
{
    for (int i = 0; i < num; ++i) {
        if ((i & 7) == 0) {
            rand_state = mix64(rand_state + 0x9e3779b97f4a7c15ull);
        }
        buf[i] = (unsigned char)(rand_state >> ((i & 7) * 8));
    }
    return 1;
}

static void
det_rand_cleanup(void)
{
}

static int
det_rand_add(const void *buf, int num, double randomness)
{
    (void)randomness;
    return det_rand_seed(buf, num);
}

static int
det_rand_status(void)
{
    return 1;
}

static RAND_METHOD det_rand_method = {
    det_rand_seed,
    det_rand_bytes,
    det_rand_cleanup,
    det_rand_add,
    det_rand_bytes,
    det_rand_status,
};

static unsigned int
client_psk_cb(SSL *ssl, const char *hint, char *identity,
              unsigned int max_identity_len, unsigned char *psk,
              unsigned int max_psk_len)
{
    (void)ssl;
    (void)hint;
    const char id[] = "copper-psk";
    if (max_identity_len < sizeof(id) || max_psk_len < sizeof(g_psk)) {
        return 0;
    }
    memcpy(identity, id, sizeof(id));
    memcpy(psk, g_psk, sizeof(g_psk));
    return (unsigned int)sizeof(g_psk);
}

static unsigned int
server_psk_cb(SSL *ssl, const char *identity, unsigned char *psk,
              unsigned int max_psk_len)
{
    (void)ssl;
    if (!identity || strcmp(identity, "copper-psk") != 0 ||
        max_psk_len < sizeof(g_psk)) {
        return 0;
    }
    memcpy(psk, g_psk, sizeof(g_psk));
    return (unsigned int)sizeof(g_psk);
}

static int
tls_engine_init(tls_engine_t *engine, uint32_t seed)
{
    memset(engine, 0, sizeof(*engine));
    stage("seed_psk");
    for (uint32_t i = 0; i < sizeof(g_psk); ++i) {
        g_psk[i] = (uint8_t)(mix64(seed ^ ((uint64_t)i << 13) ^
                                   0x50534b544c533132ull) >>
                             24);
    }
    rand_state = mix64(rand_state ^ seed ^ 0x544c535f52414e44ull);
    if (!RAND_set_rand_method(&det_rand_method)) {
        print_ssl_errors("RAND_set_rand_method failed");
        return 0;
    }
    stage("openssl_init");
    if (!OPENSSL_init_ssl(OPENSSL_INIT_NO_LOAD_CONFIG, NULL)) {
        print_ssl_errors("OPENSSL_init_ssl failed");
        return 0;
    }
    RAND_seed(g_psk, (int)sizeof(g_psk));
    fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_STAGE rand_status=%d\n",
            RAND_status());
    fflush(stderr);
    stage("ctx_new");
    engine->client_ctx = SSL_CTX_new(TLS_method());
    engine->server_ctx = SSL_CTX_new(TLS_method());
    if (!engine->client_ctx || !engine->server_ctx) {
        print_ssl_errors("SSL_CTX_new failed");
        return 0;
    }
    SSL_CTX_ctrl(engine->client_ctx, SSL_CTRL_SET_MIN_PROTO_VERSION,
                 TLS1_2_VERSION, NULL);
    SSL_CTX_ctrl(engine->client_ctx, SSL_CTRL_SET_MAX_PROTO_VERSION,
                 TLS1_2_VERSION, NULL);
    SSL_CTX_ctrl(engine->server_ctx, SSL_CTRL_SET_MIN_PROTO_VERSION,
                 TLS1_2_VERSION, NULL);
    SSL_CTX_ctrl(engine->server_ctx, SSL_CTRL_SET_MAX_PROTO_VERSION,
                 TLS1_2_VERSION, NULL);
    stage("cipher_list");
    if (!SSL_CTX_set_cipher_list(engine->client_ctx, "PSK-AES128-CBC-SHA256") ||
        !SSL_CTX_set_cipher_list(engine->server_ctx, "PSK-AES128-CBC-SHA256")) {
        print_ssl_errors("SSL_CTX_set_cipher_list failed");
        return 0;
    }
    SSL_CTX_set_psk_client_callback(engine->client_ctx, client_psk_cb);
    SSL_CTX_set_psk_server_callback(engine->server_ctx, server_psk_cb);
    stage("psk_callbacks");
    if (!SSL_CTX_use_psk_identity_hint(engine->server_ctx, "copper-psk")) {
        print_ssl_errors("SSL_CTX_use_psk_identity_hint failed");
        return 0;
    }
    return 1;
}

static void
tls_engine_destroy(tls_engine_t *engine)
{
    SSL_CTX_free(engine->client_ctx);
    SSL_CTX_free(engine->server_ctx);
}

static int
tls_handshake_pair(SSL *client, SSL *server)
{
    int client_done = 0;
    int server_done = 0;
    for (uint32_t step = 0; step < 10000 && (!client_done || !server_done);
         ++step) {
        if (!client_done) {
            int ret = SSL_do_handshake(client);
            if (ret == 1) {
                client_done = 1;
            } else {
                int err = SSL_get_error(client, ret);
                if (err != SSL_ERROR_WANT_READ && err != SSL_ERROR_WANT_WRITE) {
                    print_ssl_errors("client handshake failed");
                    return 0;
                }
            }
        }
        if (!server_done) {
            int ret = SSL_do_handshake(server);
            if (ret == 1) {
                server_done = 1;
            } else {
                int err = SSL_get_error(server, ret);
                if (err != SSL_ERROR_WANT_READ && err != SSL_ERROR_WANT_WRITE) {
                    print_ssl_errors("server handshake failed");
                    return 0;
                }
            }
        }
    }
    if (!client_done || !server_done) {
        fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR handshake timeout\n");
        return 0;
    }
    return 1;
}

static int
ssl_read_retry(SSL *ssl, unsigned char *buf, int len)
{
    for (uint32_t step = 0; step < 1000; ++step) {
        int ret = SSL_read(ssl, buf, len);
        if (ret > 0) {
            return ret;
        }
        int err = SSL_get_error(ssl, ret);
        if (err != SSL_ERROR_WANT_READ && err != SSL_ERROR_WANT_WRITE) {
            print_ssl_errors("SSL_read failed");
            return -1;
        }
    }
    fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR SSL_read timeout\n");
    return -1;
}

static int
ssl_write_retry(SSL *ssl, const unsigned char *buf, int len)
{
    int off = 0;
    for (uint32_t step = 0; step < 1000 && off < len; ++step) {
        int ret = SSL_write(ssl, buf + off, len - off);
        if (ret > 0) {
            off += ret;
            continue;
        }
        int err = SSL_get_error(ssl, ret);
        if (err != SSL_ERROR_WANT_READ && err != SSL_ERROR_WANT_WRITE) {
            print_ssl_errors("SSL_write failed");
            return 0;
        }
    }
    return off == len;
}

static int
tls_exchange(tls_engine_t *engine, session_t *s, uint32_t records)
{
    SSL *client = SSL_new(engine->client_ctx);
    SSL *server = SSL_new(engine->server_ctx);
    BIO *client_bio = NULL;
    BIO *server_bio = NULL;
    unsigned char msg[192];
    unsigned char rx[256];
    unsigned char echo[256];
    if (!client || !server) {
        print_ssl_errors("SSL_new failed");
        SSL_free(client);
        SSL_free(server);
        return 0;
    }
    if (!BIO_new_bio_pair(&client_bio, 0, &server_bio, 0)) {
        print_ssl_errors("BIO_new_bio_pair failed");
        SSL_free(client);
        SSL_free(server);
        BIO_free_all(client_bio);
        BIO_free_all(server_bio);
        return 0;
    }
    SSL_set_bio(client, client_bio, client_bio);
    SSL_set_bio(server, server_bio, server_bio);
    SSL_set_connect_state(client);
    SSL_set_accept_state(server);
    if (!tls_handshake_pair(client, server)) {
        SSL_free(client);
        SSL_free(server);
        return 0;
    }

    for (uint32_t r = 0; r < records; ++r) {
        uint64_t t0 = s->ticket0;
        uint64_t t1 = s->ticket1;
        memcpy(msg, s->payload, sizeof(s->payload));
        memcpy(msg + 160, &s->sid, sizeof(s->sid));
        memcpy(msg + 168, &s->seq, sizeof(s->seq));
        memcpy(msg + 176, &t0, sizeof(t0));
        memcpy(msg + 184, &t1, sizeof(t1));
        if (!ssl_write_retry(client, msg, (int)sizeof(msg))) {
            SSL_free(client);
            SSL_free(server);
            return 0;
        }
        int got = ssl_read_retry(server, rx, (int)sizeof(rx));
        if (got != (int)sizeof(msg)) {
            fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR server read got=%d\n",
                    got);
            SSL_free(client);
            SSL_free(server);
            return 0;
        }
        for (int i = 0; i < got; ++i) {
            echo[i] = (unsigned char)(rx[i] ^ (unsigned char)(r + i));
        }
        if (!ssl_write_retry(server, echo, got)) {
            SSL_free(client);
            SSL_free(server);
            return 0;
        }
        int back = ssl_read_retry(client, rx, (int)sizeof(rx));
        if (back != got) {
            fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR client read got=%d\n",
                    back);
            SSL_free(client);
            SSL_free(server);
            return 0;
        }
        memcpy(s->transcript, rx, sizeof(s->transcript));
        s->seq = mix64(s->seq ^ t0 ^ (t1 << 1) ^ rx[3] ^ ((uint64_t)rx[17] << 8));
        fold(s->seq ^ ((uint64_t)rx[5] << 40) ^ t0 ^ r);
    }
    SSL_free(client);
    SSL_free(server);
    return 1;
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
    s->seq = mix64(sid ^ seed ^ 0x746c735f62696f31ull);
    s->ticket0 = poison_word(slot, seed, 0x71u, poison);
    s->ticket1 = poison_word(slot, seed, 0xb5u, poison);
    for (uint32_t i = 0; i < sizeof(s->payload); ++i) {
        s->payload[i] = (uint8_t)(mix64(sid ^ seed ^ ((uint64_t)i << 8)) >> 16);
    }
    memset(s->transcript, 0, sizeof(s->transcript));
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
        fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR allocation failed\n");
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
scan_lru(service_t *svc, uint32_t depth)
{
    session_t *cur = svc->lru_head;
    for (uint32_t i = 0; i < depth && cur; ++i) {
        uint64_t t0 = cur->ticket0;
        uint64_t t1 = cur->ticket1;
        fold(cur->sid ^ cur->seq ^ t0 ^ (t1 << 1));
        cur = cur->lru_next;
    }
}

static void
service_request(service_t *svc, tls_engine_t *engine, uint32_t op,
                uint32_t seed, uint32_t scan_depth, uint32_t records,
                int poison)
{
    uint32_t mask = svc->sessions_count - 1u;
    uint64_t r = mix64(((uint64_t)op << 32) ^ seed ^ 0x746c735f72657131ull);
    uint32_t hit_id = permute_index((uint32_t)r, mask, seed ^ 0x55u);
    uint64_t sid = make_sid(hit_id, seed);
    if ((r & 63u) == 0) {
        sid = make_sid((uint32_t)(r >> 17) ^ op ^ 0x544c5301u, seed ^ 0x13u);
    }

    session_t *s = service_find(svc, sid);
    if (s) {
        if (!tls_exchange(engine, s, records)) {
            fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR tls exchange failed\n");
            exit(1);
        }
        lru_touch(svc, s);
    } else {
        session_t *victim = svc->lru_tail;
        if (!victim) {
            fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR empty LRU\n");
            exit(1);
        }
        lru_remove(svc, victim);
        hash_remove(svc, victim);
        session_set(victim, sid, (uint32_t)(victim - svc->sessions), seed + op,
                    poison);
        hash_insert(svc, victim);
        lru_push_front(svc, victim);
        if (!tls_exchange(engine, victim, records)) {
            fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR tls exchange failed\n");
            exit(1);
        }
    }
    scan_lru(svc, scan_depth);
}

static void
validate_service(service_t *svc)
{
    uint32_t lru_count = 0;
    session_t *prev = NULL;
    for (session_t *cur = svc->lru_head; cur; cur = cur->lru_next) {
        if (cur->lru_prev != prev) {
            fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR broken lru prev\n");
            exit(1);
        }
        fold(cur->sid ^ cur->seq);
        prev = cur;
        lru_count++;
        if (lru_count > svc->sessions_count) {
            fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR lru cycle\n");
            exit(1);
        }
    }
    if (prev != svc->lru_tail || lru_count != svc->sessions_count) {
        fprintf(stderr,
                "OPENSSL_TLS_BIO_COPPER_ERROR lru count=%u sessions=%u\n",
                lru_count, svc->sessions_count);
        exit(1);
    }
}

int
main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    uint32_t sessions = 16;
    uint32_t handshakes = 16;
    uint32_t records = 1;
    uint32_t scan_depth = 4;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--sessions") && i + 1 < argc) {
            sessions = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--handshakes") && i + 1 < argc) {
            handshakes = (uint32_t)strtoul(argv[++i], NULL, 0);
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
                    "usage: %s [--sessions pow2] [--handshakes n] [--records n] [--scan-depth n] [--rounds n] [--seed n] [--no-poison]\n",
                    argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(sessions) || sessions < 16 || sessions > (1u << 16)) {
        fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR sessions must be a power of two in [16,65536]\n");
        return 2;
    }
    if (handshakes == 0 || handshakes > (1u << 20) || records == 0 ||
        records > 8 || rounds == 0 || rounds > 64) {
        fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR invalid handshakes, records, or rounds\n");
        return 2;
    }
    if (scan_depth == 0 || scan_depth > sessions) {
        fprintf(stderr, "OPENSSL_TLS_BIO_COPPER_ERROR scan-depth must be in [1,sessions]\n");
        return 2;
    }

    tls_engine_t engine;
    if (!tls_engine_init(&engine, seed)) {
        return 1;
    }

    service_t svc;
    service_init(&svc, sessions, seed, poison);
    stage("roi_begin");
    m5_work_begin(0, 0);
    m5_reset_stats(0, 0);
    stage("roi_active");
    for (uint32_t r = 0; r < rounds; ++r) {
        for (uint32_t op = 0; op < handshakes; ++op) {
            service_request(&svc, &engine, op + r * handshakes, seed + r * 31u,
                            scan_depth, records, poison);
        }
    }
    validate_service(&svc);

    printf("OPENSSL_TLS_BIO_COPPER_RESULT sessions=%u handshakes=%u records=%u scan_depth=%u rounds=%u seed=%u poison=%u checksum=0x%016llx\n",
           sessions, handshakes, records, scan_depth, rounds, seed, poison,
           (unsigned long long)checksum_acc);

    m5_dump_stats(0, 0);
    m5_work_end(0, 0);
    service_destroy(&svc);
    tls_engine_destroy(&engine);
    return 0;
}
