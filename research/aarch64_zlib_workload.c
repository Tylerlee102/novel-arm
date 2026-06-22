// Deterministic AArch64 zlib compression/decompression workload for COPPER.
//
// This calls the public zlib ABI through the Ubuntu ARM64 guest library stack.
// The input buffer deliberately includes address-shaped words as data, then
// verifies round-trip decompression and prints a stable checksum.

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char Bytef;
typedef unsigned long uLong;
typedef unsigned long uLongf;

extern uLong compressBound(uLong sourceLen);
extern int compress2(
    Bytef *dest,
    uLongf *destLen,
    const Bytef *source,
    uLong sourceLen,
    int level
);
extern int uncompress(
    Bytef *dest,
    uLongf *destLen,
    const Bytef *source,
    uLong sourceLen
);
extern uLong crc32(uLong crc, const Bytef *buf, unsigned int len);

static uint64_t rotl64(uint64_t x, unsigned k) {
    return (x << k) | (x >> (64U - k));
}

static uint64_t mix64(uint64_t x) {
    x ^= x >> 33;
    x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33;
    x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return x;
}

static uint64_t checksum_bytes(const uint8_t *buf, size_t len, uint64_t seed) {
    uint64_t h = seed ^ 0xcbf29ce484222325ULL;
    for (size_t i = 0; i < len; i++) {
        h ^= (uint64_t)buf[i];
        h *= 0x100000001b3ULL;
        h = rotl64(h, 5);
    }
    return h;
}

static uint64_t parse_u64_arg(const char *s, uint64_t fallback) {
    if (!s || !*s) {
        return fallback;
    }
    char *end = 0;
    uint64_t v = strtoull(s, &end, 0);
    return end && *end == 0 ? v : fallback;
}

static void fill_input(uint8_t *buf, size_t bytes, uint64_t seed) {
    uint64_t x = mix64(seed ^ 0x316c69627aULL);
    for (size_t off = 0; off < bytes; off += 8) {
        x = mix64(x + off * 0x9e3779b97f4a7c15ULL);
        uint64_t word;
        if (((off / 8) & 3U) == 0) {
            word = 0x400000ULL + ((x >> 5) & 0x0000fffffffffff8ULL);
        } else if (((off / 8) & 3U) == 1) {
            word = 0x7a6c69622d303030ULL ^ x;
        } else {
            word = x;
        }
        size_t n = bytes - off;
        if (n > 8) {
            n = 8;
        }
        memcpy(buf + off, &word, n);
    }
}

int main(int argc, char **argv) {
    uint64_t bytes = 16384;
    uint64_t rounds = 4;
    uint64_t seed = 0;
    uint64_t level = 1;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--bytes") && i + 1 < argc) {
            bytes = parse_u64_arg(argv[++i], bytes);
        } else if (!strcmp(argv[i], "--rounds") && i + 1 < argc) {
            rounds = parse_u64_arg(argv[++i], rounds);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = parse_u64_arg(argv[++i], seed);
        } else if (!strcmp(argv[i], "--level") && i + 1 < argc) {
            level = parse_u64_arg(argv[++i], level);
        }
    }

    if (bytes < 256 || bytes > (1ULL << 22) || rounds == 0 || level > 9) {
        fprintf(stderr, "invalid zlib workload parameters\n");
        return 2;
    }

    uint8_t *src = (uint8_t *)malloc((size_t)bytes);
    uint8_t *dst = (uint8_t *)malloc((size_t)bytes);
    uLong bound = compressBound((uLong)bytes);
    uint8_t *cmp = (uint8_t *)malloc((size_t)bound);
    if (!src || !dst || !cmp) {
        fprintf(stderr, "malloc failed\n");
        free(src);
        free(dst);
        free(cmp);
        return 2;
    }

    fill_input(src, (size_t)bytes, seed);
    uint64_t checksum = checksum_bytes(src, (size_t)bytes, mix64(seed));
    uint64_t total_compressed = 0;
    uint64_t pointer_like_words = 0;
    uint64_t zcrc = 0;
    for (size_t off = 0; off + 8 <= (size_t)bytes; off += 8) {
        uint64_t word = 0;
        memcpy(&word, src + off, 8);
        if (word >= 0x400000ULL && word <= 0x0000ffffffffffffULL && (word & 7ULL) == 0) {
            pointer_like_words++;
        }
    }

    for (uint64_t r = 0; r < rounds; r++) {
        uLongf csz = (uLongf)bound;
        int rc = compress2(cmp, &csz, src, (uLong)bytes, (int)level);
        if (rc != 0) {
            fprintf(stderr, "compress2 failed: %d\n", rc);
            free(src);
            free(dst);
            free(cmp);
            return 3;
        }
        memset(dst, 0, (size_t)bytes);
        uLongf dsz = (uLongf)bytes;
        rc = uncompress(dst, &dsz, cmp, (uLong)csz);
        if (rc != 0 || dsz != (uLongf)bytes || memcmp(src, dst, (size_t)bytes)) {
            fprintf(stderr, "uncompress verification failed: rc=%d size=%lu\n", rc, dsz);
            free(src);
            free(dst);
            free(cmp);
            return 4;
        }
        total_compressed += (uint64_t)csz;
        zcrc ^= (uint64_t)crc32(0, cmp, (unsigned int)csz);
        checksum ^= checksum_bytes(cmp, (size_t)csz, mix64(checksum + r));
        checksum ^= checksum_bytes(dst, (size_t)bytes, mix64(checksum ^ 0x33ccULL));
        fill_input(src, (size_t)bytes, seed + r + 1);
    }

    printf(
        "ZLIB_COPPER_RESULT bytes=%llu rounds=%llu seed=%llu level=%llu pointer_like_words=%llu total_compressed=%llu zcrc=0x%08llx checksum=0x%016llx\n",
        (unsigned long long)bytes,
        (unsigned long long)rounds,
        (unsigned long long)seed,
        (unsigned long long)level,
        (unsigned long long)pointer_like_words,
        (unsigned long long)total_compressed,
        (unsigned long long)zcrc,
        (unsigned long long)checksum
    );

    free(src);
    free(dst);
    free(cmp);
    return 0;
}
