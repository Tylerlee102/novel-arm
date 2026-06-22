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

typedef struct bench_node_t bench_node_t;

struct bench_node_t {
    uint64_t sid;
    uint64_t seq;
    volatile uint64_t ticket0;
    volatile uint64_t ticket1;
    uint8_t key[32];
    uint8_t iv[16];
    bench_node_t *next;
    bench_node_t *prev;
};

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
    checksum_acc = (checksum_acc << 19) | (checksum_acc >> 45);
}

static int
is_power_of_two(uint32_t x)
{
    return x && ((x & (x - 1)) == 0);
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
init_nodes(bench_node_t *nodes, uint32_t records, uint32_t seed, int poison)
{
    for (uint32_t i = 0; i < records; ++i) {
        bench_node_t *n = &nodes[i];
        n->sid = mix64(((uint64_t)i << 17) ^ seed ^ 0x53504545444c494bull);
        n->seq = mix64(n->sid ^ 0x455650484d414353ull);
        n->ticket0 = poison_word(i, seed, 0x51u, poison);
        n->ticket1 = poison_word(i, seed, 0x73u, poison);
        for (uint32_t j = 0; j < sizeof(n->key); ++j) {
            n->key[j] = (uint8_t)(mix64(n->sid ^ ((uint64_t)j << 3) ^ seed) >> 24);
        }
        for (uint32_t j = 0; j < sizeof(n->iv); ++j) {
            n->iv[j] = (uint8_t)(mix64(n->seq ^ ((uint64_t)j << 7) ^ seed) >> 32);
        }
        n->next = &nodes[(i + 1u) & (records - 1u)];
        n->prev = &nodes[(i + records - 1u) & (records - 1u)];
    }
}

static bench_node_t *
walk_nodes(bench_node_t *start, uint32_t depth)
{
    bench_node_t *cur = start;
    for (uint32_t i = 0; i < depth; ++i) {
        uint64_t t0 = cur->ticket0;
        uint64_t t1 = cur->ticket1;
        fold(cur->sid ^ cur->seq ^ t0 ^ (t1 << 1));
        cur = ((t0 ^ t1 ^ i) & 1u) ? cur->next : cur->prev;
    }
    return cur;
}

static void
fill_buffer(uint8_t *buf, size_t len, uint32_t seed, uint32_t size_idx)
{
    uint64_t state = mix64(seed ^ ((uint64_t)size_idx << 32) ^ 0x627566666572ull);
    for (size_t i = 0; i < len; ++i) {
        if ((i & 7u) == 0) {
            state = mix64(state + i + len);
        }
        buf[i] = (uint8_t)(state >> ((i & 7u) * 8u));
    }
}

static int
aes_ctr_once(bench_node_t *node, const uint8_t *in, uint8_t *out, size_t len)
{
    int out_len = 0;
    int final_len = 0;
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        return 0;
    }
    if (!EVP_EncryptInit_ex(ctx, EVP_aes_128_ctr(), NULL, node->key, node->iv)) {
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }
    if (!EVP_EncryptUpdate(ctx, out, &out_len, in, (int)len)) {
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }
    if (!EVP_EncryptFinal_ex(ctx, out + out_len, &final_len)) {
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }
    EVP_CIPHER_CTX_free(ctx);
    fold(((uint64_t)out[0] << 40) ^ ((uint64_t)out_len << 8) ^ final_len);
    return 1;
}

static int
sha_hmac_once(bench_node_t *node, const uint8_t *buf, size_t len)
{
    uint8_t digest[32];
    uint8_t mac[32];
    unsigned int mac_len = 0;
    if (!SHA256(buf, len, digest)) {
        return 0;
    }
    if (!HMAC(EVP_sha256(), node->key, 32, buf, len, mac, &mac_len)) {
        return 0;
    }
    (void)CRYPTO_memcmp(digest, mac, mac_len < 32 ? mac_len : 32);
    node->seq = mix64(node->seq ^ digest[3] ^ ((uint64_t)mac[11] << 8));
    fold(((uint64_t)digest[0] << 56) ^ ((uint64_t)mac[0] << 48) ^ mac_len);
    return 1;
}

int
main(int argc, char **argv)
{
    uint32_t records = 128;
    uint32_t iterations = 16;
    uint32_t scan_depth = 8;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;
    const size_t sizes[] = {64u, 256u, 1024u, 4096u};
    const uint32_t size_count = (uint32_t)(sizeof(sizes) / sizeof(sizes[0]));
    uint64_t total_bytes = 0;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--records") && i + 1 < argc) {
            records = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--iterations") && i + 1 < argc) {
            iterations = (uint32_t)strtoul(argv[++i], NULL, 0);
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
                    "usage: %s [--records pow2] [--iterations n] [--scan-depth n] [--rounds n] [--seed n] [--no-poison]\n",
                    argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(records) || records < 64 || records > (1u << 20)) {
        fprintf(stderr, "OPENSSL_SPEEDLIKE_COPPER_ERROR records must be a power of two in [64,1048576]\n");
        return 2;
    }
    if (iterations == 0 || iterations > 4096 || scan_depth == 0 ||
        scan_depth > records || rounds == 0 || rounds > 128) {
        fprintf(stderr, "OPENSSL_SPEEDLIKE_COPPER_ERROR invalid iteration, scan-depth, or rounds\n");
        return 2;
    }

    bench_node_t *nodes = (bench_node_t *)calloc(records, sizeof(bench_node_t));
    uint8_t *in = (uint8_t *)malloc(4096u);
    uint8_t *out = (uint8_t *)malloc(4096u + 32u);
    if (!nodes || !in || !out) {
        fprintf(stderr, "OPENSSL_SPEEDLIKE_COPPER_ERROR allocation failed\n");
        return 1;
    }

    init_nodes(nodes, records, seed, poison);
    bench_node_t *cursor = &nodes[seed & (records - 1u)];

    for (uint32_t r = 0; r < rounds; ++r) {
        for (uint32_t s = 0; s < size_count; ++s) {
            fill_buffer(in, sizes[s], seed + r * 17u, s);
            for (uint32_t i = 0; i < iterations; ++i) {
                cursor = walk_nodes(cursor, scan_depth);
                if (!aes_ctr_once(cursor, in, out, sizes[s])) {
                    fprintf(stderr, "OPENSSL_SPEEDLIKE_COPPER_ERROR aes failed\n");
                    return 1;
                }
                cursor = walk_nodes(cursor, scan_depth);
                if (!sha_hmac_once(cursor, out, sizes[s])) {
                    fprintf(stderr, "OPENSSL_SPEEDLIKE_COPPER_ERROR sha/hmac failed\n");
                    return 1;
                }
                total_bytes += sizes[s] * 3u;
            }
        }
    }

    for (uint32_t i = 0; i < records; i += records / 16u) {
        fold(nodes[i].sid ^ nodes[i].seq ^ nodes[i].ticket0 ^ nodes[i].ticket1);
    }

    printf("OPENSSL_SPEEDLIKE_COPPER_RESULT records=%u iterations=%u scan_depth=%u rounds=%u seed=%u poison=%u buffers=%u total_bytes=%llu checksum=0x%016llx\n",
           records, iterations, scan_depth, rounds, seed, poison, size_count,
           (unsigned long long)total_bytes, (unsigned long long)checksum_acc);

    free(out);
    free(in);
    free(nodes);
    return 0;
}
