#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char PCRE2_UCHAR;
typedef const unsigned char *PCRE2_SPTR;
typedef size_t PCRE2_SIZE;
typedef struct pcre2_real_code_8 pcre2_code_8;
typedef struct pcre2_real_match_data_8 pcre2_match_data_8;

#define PCRE2_ZERO_TERMINATED (~(PCRE2_SIZE)0)

pcre2_code_8 *pcre2_compile_8(PCRE2_SPTR, PCRE2_SIZE, uint32_t, int *, PCRE2_SIZE *, void *);
void pcre2_code_free_8(pcre2_code_8 *);
pcre2_match_data_8 *pcre2_match_data_create_from_pattern_8(const pcre2_code_8 *, void *);
void pcre2_match_data_free_8(pcre2_match_data_8 *);
int pcre2_match_8(const pcre2_code_8 *, PCRE2_SPTR, PCRE2_SIZE, PCRE2_SIZE, uint32_t, pcre2_match_data_8 *, void *);
PCRE2_SIZE *pcre2_get_ovector_pointer_8(pcre2_match_data_8 *);
int pcre2_get_error_message_8(int, PCRE2_UCHAR *, PCRE2_SIZE);

typedef struct record_t record_t;

struct record_t {
    char *text;
    size_t len;
    uint64_t sid;
    volatile uint64_t ticket0;
    volatile uint64_t ticket1;
    record_t *next;
    record_t *prev;
};

typedef struct {
    const char *expr;
    uint64_t salt;
    pcre2_code_8 *code;
    pcre2_match_data_8 *match_data;
} regex_t;

static uint64_t checksum_acc = 0x510e527fade682d1ull;

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
    return (uint32_t)(((uint64_t)i * 2654435761u) + ((uint64_t)seed * 40503u)) & mask;
}

static uint64_t
poison_word(uint32_t i, uint32_t seed, uint32_t salt, int poison)
{
    uint64_t x = mix64(((uint64_t)i << 32) ^ ((uint64_t)seed << 7) ^ salt);
    if (!poison) {
        return x & 0x7fffffffull;
    }
    return 0x00000000400000ull + ((x & 0x7ffffull) << 3);
}

static char *
make_record_text(uint32_t i, uint32_t seed, int poison, uint64_t *ticket0, uint64_t *ticket1)
{
    uint64_t x = mix64(((uint64_t)i << 24) ^ seed ^ 0x50435245325f5245ull);
    uint32_t user = (uint32_t)(x & 0xffffu);
    uint32_t item = (uint32_t)((x >> 16) & 0xffffu);
    uint32_t ip0 = 10u + (uint32_t)((x >> 8) & 7u);
    uint32_t ip1 = (uint32_t)((x >> 20) & 255u);
    uint32_t ip2 = (uint32_t)((x >> 32) & 255u);
    uint32_t ip3 = 1u + (uint32_t)((x >> 44) & 127u);
    uint32_t status = (uint32_t[]){200u, 302u, 404u, 500u}[(x >> 56) & 3u];
    uint64_t token = mix64(x ^ 0x746f6b656e5f3132ull);
    *ticket0 = poison_word(i, seed, 0x91u, poison);
    *ticket1 = poison_word(i, seed, 0xb7u, poison);

    const char *verb = ((x >> 4) & 1u) ? "POST" : "GET";
    const char *kind = (const char *[]){"item", "cart", "checkout", "profile"}[(x >> 5) & 3u];
    int n = snprintf(
        NULL,
        0,
        "ts=%08x method=%s user=u%04x path=/api/v%u/%s/%u ip=%u.%u.%u.%u "
        "token=%016llx ptr=%016llx aux=%016llx status=%u msg=\"node_%04x_%04x\"",
        i + seed,
        verb,
        user,
        (uint32_t)(1u + ((x >> 11) & 3u)),
        kind,
        item,
        ip0,
        ip1,
        ip2,
        ip3,
        (unsigned long long)token,
        (unsigned long long)*ticket0,
        (unsigned long long)*ticket1,
        status,
        user,
        item);
    if (n < 0) {
        return NULL;
    }
    char *buf = (char *)malloc((size_t)n + 1u);
    if (!buf) {
        return NULL;
    }
    snprintf(
        buf,
        (size_t)n + 1u,
        "ts=%08x method=%s user=u%04x path=/api/v%u/%s/%u ip=%u.%u.%u.%u "
        "token=%016llx ptr=%016llx aux=%016llx status=%u msg=\"node_%04x_%04x\"",
        i + seed,
        verb,
        user,
        (uint32_t)(1u + ((x >> 11) & 3u)),
        kind,
        item,
        ip0,
        ip1,
        ip2,
        ip3,
        (unsigned long long)token,
        (unsigned long long)*ticket0,
        (unsigned long long)*ticket1,
        status,
        user,
        item);
    return buf;
}

static record_t *
build_records(uint32_t records, uint32_t seed, int poison)
{
    record_t *items = (record_t *)calloc(records, sizeof(record_t));
    if (!items) {
        return NULL;
    }
    for (uint32_t i = 0; i < records; ++i) {
        items[i].sid = mix64(((uint64_t)i << 13) ^ seed);
        uint64_t ticket0 = 0;
        uint64_t ticket1 = 0;
        items[i].text = make_record_text(i, seed, poison, &ticket0, &ticket1);
        items[i].ticket0 = ticket0;
        items[i].ticket1 = ticket1;
        if (!items[i].text) {
            return NULL;
        }
        items[i].len = strlen(items[i].text);
        items[i].next = &items[(i + 1u) & (records - 1u)];
        items[i].prev = &items[(i + records - 1u) & (records - 1u)];
    }
    return items;
}

static int
compile_regexes(regex_t *regexes, uint32_t count)
{
    for (uint32_t i = 0; i < count; ++i) {
        int error_code = 0;
        PCRE2_SIZE error_offset = 0;
        regexes[i].code = pcre2_compile_8(
            (PCRE2_SPTR)regexes[i].expr,
            PCRE2_ZERO_TERMINATED,
            0,
            &error_code,
            &error_offset,
            NULL);
        if (!regexes[i].code) {
            PCRE2_UCHAR msg[128];
            pcre2_get_error_message_8(error_code, msg, sizeof(msg));
            fprintf(stderr, "PCRE2_COPPER_ERROR compile pattern=%u offset=%zu msg=%s\n",
                    i, (size_t)error_offset, (char *)msg);
            return 0;
        }
        regexes[i].match_data = pcre2_match_data_create_from_pattern_8(regexes[i].code, NULL);
        if (!regexes[i].match_data) {
            fprintf(stderr, "PCRE2_COPPER_ERROR match_data pattern=%u\n", i);
            return 0;
        }
    }
    return 1;
}

static void
free_regexes(regex_t *regexes, uint32_t count)
{
    for (uint32_t i = 0; i < count; ++i) {
        if (regexes[i].match_data) {
            pcre2_match_data_free_8(regexes[i].match_data);
        }
        if (regexes[i].code) {
            pcre2_code_free_8(regexes[i].code);
        }
    }
}

static uint64_t
run_matches(record_t *records, uint32_t record_count, regex_t *regexes, uint32_t regex_count,
            uint32_t lookups, uint32_t scan_depth, uint32_t rounds, uint32_t seed)
{
    uint32_t mask = record_count - 1u;
    uint64_t matches = 0;
    for (uint32_t round = 0; round < rounds; ++round) {
        for (uint32_t i = 0; i < lookups; ++i) {
            uint32_t idx = permute_index(i + round * 131u, mask, seed ^ (round * 17u));
            record_t *rec = &records[idx];
            for (uint32_t step = 0; step < scan_depth; ++step) {
                regex_t *rx = &regexes[(idx + step + round) % regex_count];
                int rc = pcre2_match_8(
                    rx->code,
                    (PCRE2_SPTR)rec->text,
                    rec->len,
                    0,
                    0,
                    rx->match_data,
                    NULL);
                fold((uint64_t)(rc + 33) ^ rx->salt ^ rec->sid);
                fold(rec->ticket0 ^ (rec->ticket1 << 1));
                if (rc > 0) {
                    PCRE2_SIZE *ov = pcre2_get_ovector_pointer_8(rx->match_data);
                    for (int j = 0; j < rc && j < 4; ++j) {
                        fold((uint64_t)ov[2 * j] ^ ((uint64_t)ov[2 * j + 1] << 32));
                    }
                    matches += (uint64_t)rc;
                }
                rec = rec->next;
            }
        }
    }
    return matches;
}

static uint32_t
parse_u32(const char *s, uint32_t fallback)
{
    char *end = NULL;
    unsigned long value = strtoul(s, &end, 0);
    return (end && *end == '\0') ? (uint32_t)value : fallback;
}

int
main(int argc, char **argv)
{
    uint32_t records_count = 512;
    uint32_t lookups = 1500;
    uint32_t scan_depth = 4;
    uint32_t rounds = 1;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--records") == 0 && i + 1 < argc) {
            records_count = parse_u32(argv[++i], records_count);
        } else if (strcmp(argv[i], "--lookups") == 0 && i + 1 < argc) {
            lookups = parse_u32(argv[++i], lookups);
        } else if (strcmp(argv[i], "--scan-depth") == 0 && i + 1 < argc) {
            scan_depth = parse_u32(argv[++i], scan_depth);
        } else if (strcmp(argv[i], "--rounds") == 0 && i + 1 < argc) {
            rounds = parse_u32(argv[++i], rounds);
        } else if (strcmp(argv[i], "--seed") == 0 && i + 1 < argc) {
            seed = parse_u32(argv[++i], seed);
        } else if (strcmp(argv[i], "--no-poison") == 0) {
            poison = 0;
        } else {
            fprintf(stderr, "usage: %s [--records N] [--lookups N] [--scan-depth N] [--rounds N] [--seed N] [--no-poison]\n", argv[0]);
            return 2;
        }
    }
    if (!is_power_of_two(records_count) || records_count < 16 || scan_depth == 0) {
        fprintf(stderr, "PCRE2_COPPER_ERROR invalid input records=%u scan_depth=%u\n",
                records_count, scan_depth);
        return 2;
    }

    regex_t regexes[] = {
        {"user=(u[0-9a-f]{4})", 0x1111u, NULL, NULL},
        {"path=/api/v[0-9]+/(item|cart|checkout|profile)/([0-9]+)", 0x2222u, NULL, NULL},
        {"ip=([0-9]{1,3}\\.){3}[0-9]{1,3}", 0x3333u, NULL, NULL},
        {"token=([0-9a-f]{16})", 0x4444u, NULL, NULL},
        {"ptr=([0-9a-f]{16})", 0x5555u, NULL, NULL},
        {"status=(200|302|404|500)", 0x6666u, NULL, NULL},
        {"method=(GET|POST).*msg=\"node_([0-9a-f]{4})_([0-9a-f]{4})\"", 0x7777u, NULL, NULL},
    };
    uint32_t regex_count = (uint32_t)(sizeof(regexes) / sizeof(regexes[0]));

    if (!compile_regexes(regexes, regex_count)) {
        free_regexes(regexes, regex_count);
        return 1;
    }
    record_t *records = build_records(records_count, seed, poison);
    if (!records) {
        fprintf(stderr, "PCRE2_COPPER_ERROR build records\n");
        free_regexes(regexes, regex_count);
        return 1;
    }

    uint64_t matches = run_matches(records, records_count, regexes, regex_count,
                                   lookups, scan_depth, rounds, seed);
    for (uint32_t i = 0; i < records_count; ++i) {
        free(records[i].text);
    }
    free(records);
    free_regexes(regexes, regex_count);

    printf("PCRE2_COPPER_RESULT records=%u lookups=%u scan_depth=%u rounds=%u seed=%u poison=%u matches=%llu checksum=0x%016llx\n",
           records_count,
           lookups,
           scan_depth,
           rounds,
           seed,
           poison ? 1u : 0u,
           (unsigned long long)matches,
           (unsigned long long)checksum_acc);
    return 0;
}
