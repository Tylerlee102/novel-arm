// Deterministic AArch64 driver for the public MiBench Patricia trie kernel.
//
// This intentionally keeps the public MiBench patricia.c implementation as the
// trie engine and adds reviewer-friendly summary/checksum output for gem5
// full-system runs. It consumes the MiBench network/patricia small.udp fields
// supplied at runtime by the run script.

#include <arpa/inet.h>
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "patricia.h"

struct route_payload {
    uint32_t seq;
    uint32_t key;
    uint32_t src;
    uint32_t dst;
    uint32_t sport;
    uint32_t dport;
    uint64_t salt;
};

static uint64_t mix64(uint64_t x) {
    x ^= x >> 33;
    x *= UINT64_C(0xff51afd7ed558ccd);
    x ^= x >> 33;
    x *= UINT64_C(0xc4ceb9fe1a85ec53);
    x ^= x >> 33;
    return x;
}

static uint32_t make_key(
    uint32_t seq,
    uint32_t src,
    uint32_t dst,
    uint32_t sport,
    uint32_t dport,
    uint32_t seed
) {
    uint64_t x = ((uint64_t)src << 48)
        ^ ((uint64_t)dst << 32)
        ^ ((uint64_t)sport << 16)
        ^ (uint64_t)dport
        ^ ((uint64_t)seq * UINT64_C(0x9e3779b97f4a7c15))
        ^ seed;
    return (uint32_t)mix64(x);
}

static void *xcalloc(size_t n, size_t size, const char *label) {
    void *ptr = calloc(n, size);
    if (!ptr) {
        fprintf(stderr, "allocation failed for %s\n", label);
        exit(2);
    }
    return ptr;
}

static struct ptree *make_default_head(void) {
    struct ptree *head = (struct ptree *)xcalloc(1, sizeof(*head), "head");
    head->p_m = (struct ptree_mask *)xcalloc(1, sizeof(*head->p_m), "head mask");
    head->p_m->pm_mask = 0;
    head->p_m->pm_data = xcalloc(1, sizeof(struct route_payload), "default payload");
    head->p_mlen = 1;
    head->p_b = 0;
    head->p_left = head;
    head->p_right = head;
    return head;
}

static struct ptree *make_route_node(
    uint32_t seq,
    uint32_t key,
    uint32_t src,
    uint32_t dst,
    uint32_t sport,
    uint32_t dport
) {
    struct ptree *node = (struct ptree *)xcalloc(1, sizeof(*node), "route node");
    struct route_payload *payload =
        (struct route_payload *)xcalloc(1, sizeof(*payload), "route payload");

    node->p_m = (struct ptree_mask *)xcalloc(1, sizeof(*node->p_m), "route mask");
    node->p_key = htonl(key);
    node->p_m->pm_mask = htonl(UINT32_MAX);
    node->p_mlen = 1;

    payload->seq = seq;
    payload->key = key;
    payload->src = src;
    payload->dst = dst;
    payload->sport = sport;
    payload->dport = dport;
    payload->salt = mix64(((uint64_t)key << 32) ^ seq);
    node->p_m->pm_data = payload;
    return node;
}

static uint64_t payload_hash(const struct ptree *node) {
    if (!node || !node->p_m || !node->p_m->pm_data) {
        return UINT64_C(0x6eed0e9da4d94a4f);
    }
    const struct route_payload *p =
        (const struct route_payload *)node->p_m->pm_data;
    uint64_t h = UINT64_C(0xcbf29ce484222325);
    h ^= p->seq; h *= UINT64_C(0x100000001b3);
    h ^= p->key; h *= UINT64_C(0x100000001b3);
    h ^= p->src; h *= UINT64_C(0x100000001b3);
    h ^= p->dst; h *= UINT64_C(0x100000001b3);
    h ^= p->sport; h *= UINT64_C(0x100000001b3);
    h ^= p->dport; h *= UINT64_C(0x100000001b3);
    h ^= p->salt; h *= UINT64_C(0x100000001b3);
    return h;
}

static const char *arg_value(int argc, char **argv, const char *name, const char *fallback) {
    for (int i = 1; i + 1 < argc; i++) {
        if (strcmp(argv[i], name) == 0) {
            return argv[i + 1];
        }
    }
    return fallback;
}

int main(int argc, char **argv) {
    const char *input_path = arg_value(argc, argv, "--input", "");
    uint32_t limit = (uint32_t)strtoul(arg_value(argc, argv, "--limit", "2048"), 0, 0);
    uint32_t lookups = (uint32_t)strtoul(arg_value(argc, argv, "--lookups", "4096"), 0, 0);
    uint32_t rounds = (uint32_t)strtoul(arg_value(argc, argv, "--rounds", "1"), 0, 0);
    uint32_t seed = (uint32_t)strtoul(arg_value(argc, argv, "--seed", "0"), 0, 0);

    if (!input_path || input_path[0] == '\0') {
        fprintf(stderr, "missing --input path\n");
        return 2;
    }

    FILE *fp = fopen(input_path, "r");
    if (!fp) {
        fprintf(stderr, "failed to open %s: %s\n", input_path, strerror(errno));
        return 2;
    }

    uint32_t *keys = (uint32_t *)xcalloc(limit ? limit : 1, sizeof(uint32_t), "keys");
    struct ptree *head = make_default_head();
    char line[256];
    uint32_t parsed = 0;
    uint32_t inserted = 0;
    uint32_t duplicates = 0;
    uint64_t checksum = UINT64_C(0x84222325cbf29ce4) ^ seed;

    while (parsed < limit && fgets(line, sizeof(line), fp)) {
        double ts = 0.0;
        unsigned src = 0, dst = 0, sport = 0, dport = 0;
        int n = sscanf(line, "%lf %u %u %u %u", &ts, &src, &dst, &sport, &dport);
        if (n < 5) {
            continue;
        }
        uint32_t key = make_key(parsed, src, dst, sport, dport, seed);
        keys[parsed] = key;
        struct ptree *found = pat_search(htonl(key), head);
        if (found && found->p_key == htonl(key)) {
            duplicates++;
        } else {
            struct ptree *node = make_route_node(parsed, key, src, dst, sport, dport);
            if (!pat_insert(node, head)) {
                fprintf(stderr, "pat_insert failed at record %" PRIu32 "\n", parsed);
                return 3;
            }
            inserted++;
        }
        checksum ^= mix64(((uint64_t)key << 32) ^ (uint64_t)(uint32_t)(ts * 1000000.0));
        checksum = (checksum << 7) | (checksum >> 57);
        parsed++;
    }
    fclose(fp);

    uint64_t lookup_checksum = checksum ^ UINT64_C(0x517cc1b727220a95);
    uint32_t found_count = 0;
    uint32_t miss_count = 0;
    uint32_t total_lookups = 0;
    uint32_t key_count = parsed ? parsed : 1;

    for (uint32_t r = 0; r < rounds; r++) {
        for (uint32_t i = 0; i < lookups; i++) {
            uint32_t idx = (uint32_t)(mix64((uint64_t)i ^ ((uint64_t)r << 32) ^ seed) % key_count);
            uint32_t key = keys[idx];
            struct ptree *found = pat_search(htonl(key), head);
            if (found && found->p_key == htonl(key)) {
                found_count++;
                lookup_checksum ^= payload_hash(found) + i + ((uint64_t)r << 32);
            } else {
                miss_count++;
                lookup_checksum ^= mix64(key ^ UINT64_C(0x55aa55aa));
            }
            lookup_checksum = (lookup_checksum << 9) | (lookup_checksum >> 55);
            total_lookups++;
        }
    }

    printf(
        "MIBENCH_PATRICIA_COPPER_RESULT input_records=%" PRIu32
        " limit=%" PRIu32
        " inserted=%" PRIu32
        " duplicates=%" PRIu32
        " lookups=%" PRIu32
        " rounds=%" PRIu32
        " seed=%" PRIu32
        " found=%" PRIu32
        " misses=%" PRIu32
        " checksum=0x%016" PRIx64 "\n",
        parsed,
        limit,
        inserted,
        duplicates,
        total_lookups,
        rounds,
        seed,
        found_count,
        miss_count,
        lookup_checksum
    );

    return 0;
}
