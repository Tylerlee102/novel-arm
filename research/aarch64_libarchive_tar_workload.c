#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef COPPER_USE_PUBLIC_LIBARCHIVE_HEADERS
#include <archive.h>
#include <archive_entry.h>
#else
struct archive;
struct archive_entry;
typedef long la_ssize_t;
#define ARCHIVE_OK 0
struct archive *archive_read_new(void);
int archive_read_support_filter_none(struct archive *);
int archive_read_support_format_tar(struct archive *);
int archive_read_open_memory(struct archive *, const void *, size_t);
int archive_read_next_header(struct archive *, struct archive_entry **);
la_ssize_t archive_read_data(struct archive *, void *, size_t);
int archive_read_free(struct archive *);
const char *archive_entry_pathname(struct archive_entry *);
int64_t archive_entry_size(struct archive_entry *);
#endif

typedef struct entry_meta_t entry_meta_t;

struct entry_meta_t {
    uint32_t id;
    uint32_t user;
    uint32_t len;
    volatile uint64_t ticket0;
    volatile uint64_t ticket1;
    entry_meta_t *next;
    entry_meta_t *prev;
};

typedef struct {
    unsigned char *data;
    size_t len;
    size_t cap;
} mbuf_t;

static uint64_t checksum_acc = 0x6c69626172636851ull;

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
    return x && ((x & (x - 1u)) == 0u);
}

static uint32_t
permute_index(uint32_t i, uint32_t mask, uint32_t seed)
{
    return (uint32_t)(((uint64_t)i * 1103515245u) + ((uint64_t)seed * 12345u)) & mask;
}

static uint64_t
poison_word(uint32_t i, uint32_t seed, uint32_t salt, int poison)
{
    uint64_t x = mix64(((uint64_t)i << 32) ^ ((uint64_t)seed << 11) ^ salt);
    if (!poison) {
        return x & 0x7fffffffull;
    }
    return 0x00000000400000ull + ((x & 0xfffffull) << 3);
}

static int
mbuf_reserve(mbuf_t *buf, size_t extra)
{
    if (buf->len + extra <= buf->cap) {
        return 1;
    }
    size_t new_cap = buf->cap ? buf->cap : 8192u;
    while (new_cap < buf->len + extra) {
        new_cap *= 2u;
    }
    unsigned char *new_data = (unsigned char *)realloc(buf->data, new_cap);
    if (!new_data) {
        return 0;
    }
    buf->data = new_data;
    buf->cap = new_cap;
    return 1;
}

static int
mbuf_append(mbuf_t *buf, const void *data, size_t len)
{
    if (!mbuf_reserve(buf, len)) {
        return 0;
    }
    memcpy(buf->data + buf->len, data, len);
    buf->len += len;
    return 1;
}

static void
put_octal(char *dst, size_t width, uint64_t value)
{
    memset(dst, 0, width);
    if (width > 1u) {
        snprintf(dst, width, "%0*llo", (int)width - 1, (unsigned long long)value);
    }
}

static int
append_tar_entry(mbuf_t *tar, const char *name, const unsigned char *payload, size_t payload_len)
{
    unsigned char hdr[512];
    memset(hdr, 0, sizeof(hdr));
    snprintf((char *)hdr, 100, "%s", name);
    put_octal((char *)hdr + 100, 8, 0644);
    put_octal((char *)hdr + 108, 8, 0);
    put_octal((char *)hdr + 116, 8, 0);
    put_octal((char *)hdr + 124, 12, payload_len);
    put_octal((char *)hdr + 136, 12, 1700000000u);
    memset(hdr + 148, ' ', 8);
    hdr[156] = '0';
    memcpy(hdr + 257, "ustar", 5);
    memcpy(hdr + 263, "00", 2);
    unsigned int sum = 0;
    for (size_t i = 0; i < sizeof(hdr); ++i) {
        sum += hdr[i];
    }
    snprintf((char *)hdr + 148, 8, "%06o", sum);
    hdr[154] = '\0';
    hdr[155] = ' ';

    if (!mbuf_append(tar, hdr, sizeof(hdr))) {
        return 0;
    }
    if (!mbuf_append(tar, payload, payload_len)) {
        return 0;
    }
    size_t pad = (512u - (payload_len & 511u)) & 511u;
    if (pad) {
        unsigned char zeros[512] = {0};
        if (!mbuf_append(tar, zeros, pad)) {
            return 0;
        }
    }
    return 1;
}

static entry_meta_t *
build_entries(uint32_t entries, uint32_t seed, int poison)
{
    entry_meta_t *meta = (entry_meta_t *)calloc(entries, sizeof(entry_meta_t));
    if (!meta) {
        return NULL;
    }
    for (uint32_t i = 0; i < entries; ++i) {
        uint64_t x = mix64(((uint64_t)i << 23) ^ seed ^ 0x7461725f6d657461ull);
        meta[i].id = i;
        meta[i].user = (uint32_t)(x & 0xffffu);
        meta[i].len = 128u + (uint32_t)(x & 127u);
        meta[i].ticket0 = poison_word(i, seed, 0x33u, poison);
        meta[i].ticket1 = poison_word(i, seed, 0x77u, poison);
        meta[i].next = &meta[(i + 1u) & (entries - 1u)];
        meta[i].prev = &meta[(i + entries - 1u) & (entries - 1u)];
    }
    return meta;
}

static unsigned char *
make_payload(const entry_meta_t *entry, uint32_t round, size_t *out_len)
{
    size_t len = entry->len;
    unsigned char *payload = (unsigned char *)malloc(len);
    if (!payload) {
        return NULL;
    }
    int n = snprintf(
        (char *)payload,
        len,
        "id=%u user=u%04x round=%u ptr=0x%016llx aux=0x%016llx next=%u prev=%u\n",
        entry->id,
        entry->user,
        round,
        (unsigned long long)entry->ticket0,
        (unsigned long long)entry->ticket1,
        entry->next->id,
        entry->prev->id);
    if (n < 0) {
        free(payload);
        return NULL;
    }
    uint64_t x = mix64(((uint64_t)entry->id << 32) ^ round ^ entry->ticket0);
    for (size_t i = (size_t)n; i < len; ++i) {
        x = mix64(x + i);
        payload[i] = (unsigned char)('a' + (x % 26u));
    }
    *out_len = len;
    return payload;
}

static unsigned char *
build_tar(entry_meta_t *entries, uint32_t count, uint32_t round, uint32_t seed, size_t *out_len)
{
    mbuf_t tar = {0};
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t idx = permute_index(i, count - 1u, seed + round);
        entry_meta_t *entry = &entries[idx];
        char name[96];
        snprintf(name, sizeof(name), "records/u%04x/item_%04u_%02u.txt", entry->user, entry->id, round);
        size_t payload_len = 0;
        unsigned char *payload = make_payload(entry, round, &payload_len);
        if (!payload) {
            free(tar.data);
            return NULL;
        }
        int ok = append_tar_entry(&tar, name, payload, payload_len);
        free(payload);
        if (!ok) {
            free(tar.data);
            return NULL;
        }
    }
    unsigned char zeros[1024] = {0};
    if (!mbuf_append(&tar, zeros, sizeof(zeros))) {
        free(tar.data);
        return NULL;
    }
    *out_len = tar.len;
    return tar.data;
}

static uint64_t
read_archive(const unsigned char *tar, size_t tar_len, uint32_t scans)
{
    uint64_t bytes_read = 0;
    unsigned char buffer[257];
    for (uint32_t scan = 0; scan < scans; ++scan) {
        struct archive *archive = archive_read_new();
        if (!archive) {
            fprintf(stderr, "LIBARCHIVE_COPPER_ERROR read_new scan=%u\n", scan);
            return 0;
        }
        archive_read_support_filter_none(archive);
        archive_read_support_format_tar(archive);
        if (archive_read_open_memory(archive, tar, tar_len) != ARCHIVE_OK) {
            fprintf(stderr, "LIBARCHIVE_COPPER_ERROR open scan=%u\n", scan);
            archive_read_free(archive);
            return 0;
        }
        struct archive_entry *entry = NULL;
        while (archive_read_next_header(archive, &entry) == ARCHIVE_OK) {
            const char *name = archive_entry_pathname(entry);
            int64_t size = archive_entry_size(entry);
            fold((uint64_t)size ^ (uint64_t)scan);
            if (name) {
                for (const unsigned char *p = (const unsigned char *)name; *p; ++p) {
                    fold(*p);
                }
            }
            for (;;) {
                la_ssize_t got = archive_read_data(archive, buffer, sizeof(buffer));
                if (got == 0) {
                    break;
                }
                if (got < 0) {
                    fprintf(stderr, "LIBARCHIVE_COPPER_ERROR data scan=%u\n", scan);
                    archive_read_free(archive);
                    return 0;
                }
                bytes_read += (uint64_t)got;
                for (la_ssize_t i = 0; i < got; i += 29) {
                    fold(buffer[i] ^ ((uint64_t)i << 16));
                }
            }
        }
        archive_read_free(archive);
    }
    return bytes_read;
}

int
main(int argc, char **argv)
{
    uint32_t entries = 16;
    uint32_t rounds = 1;
    uint32_t scans = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--entries") && i + 1 < argc) {
            entries = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--rounds") && i + 1 < argc) {
            rounds = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--scans") && i + 1 < argc) {
            scans = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--no-poison")) {
            poison = 0;
        } else {
            fprintf(stderr,
                    "usage: %s [--entries N] [--rounds N] [--scans N] [--seed N] [--no-poison]\n",
                    argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(entries) || entries < 2u) {
        fprintf(stderr, "LIBARCHIVE_COPPER_ERROR entries must be a power of two >= 2\n");
        return 2;
    }

    entry_meta_t *meta = build_entries(entries, seed, poison);
    if (!meta) {
        fprintf(stderr, "LIBARCHIVE_COPPER_ERROR alloc meta\n");
        return 1;
    }

    uint64_t archive_bytes = 0;
    uint64_t payload_bytes = 0;
    for (uint32_t round = 0; round < rounds; ++round) {
        size_t tar_len = 0;
        unsigned char *tar = build_tar(meta, entries, round, seed, &tar_len);
        if (!tar) {
            free(meta);
            return 1;
        }
        archive_bytes += (uint64_t)tar_len;
        fold(tar_len);
        uint64_t read_bytes = read_archive(tar, tar_len, scans);
        free(tar);
        if (!read_bytes) {
            free(meta);
            return 1;
        }
        payload_bytes += read_bytes;
        fold(read_bytes);
    }

    uint64_t pointer_like_words = (uint64_t)entries * 2u;
    for (uint32_t i = 0; i < entries; i += (entries / 8u ? entries / 8u : 1u)) {
        fold(meta[i].ticket0);
        fold(meta[i].ticket1);
        fold((uintptr_t)meta[i].next ^ (uintptr_t)meta[i].prev);
    }

    printf("LIBARCHIVE_COPPER_RESULT entries=%u rounds=%u scans=%u seed=%u poison=%d "
           "archive_bytes=%llu payload_bytes=%llu pointer_like_words=%llu checksum=0x%016llx\n",
           entries,
           rounds,
           scans,
           seed,
           poison,
           (unsigned long long)archive_bytes,
           (unsigned long long)payload_bytes,
           (unsigned long long)pointer_like_words,
           (unsigned long long)checksum_acc);

    free(meta);
    return 0;
}
