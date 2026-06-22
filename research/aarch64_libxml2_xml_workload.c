#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <libxml/parser.h>
#include <libxml/tree.h>

typedef struct node_t node_t;

struct node_t {
    uint32_t id;
    uint32_t user;
    uint32_t kind;
    volatile uint64_t ticket0;
    volatile uint64_t ticket1;
    node_t *next;
    node_t *prev;
};

typedef struct {
    char *data;
    size_t len;
    size_t cap;
} sbuf_t;

static uint64_t checksum_acc = 0x6c6962786d6c3251ull;

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

static uint64_t
poison_word(uint32_t i, uint32_t seed, uint32_t salt, int poison)
{
    uint64_t x = mix64(((uint64_t)i << 32) ^ ((uint64_t)seed << 9) ^ salt);
    if (!poison) {
        return x & 0x7fffffffull;
    }
    return 0x00000000400000ull + ((x & 0xfffffull) << 3);
}

static int
is_power_of_two(uint32_t x)
{
    return x && ((x & (x - 1u)) == 0u);
}

static uint32_t
permute_index(uint32_t i, uint32_t mask, uint32_t seed)
{
    return (uint32_t)(((uint64_t)i * 2654435761u) + ((uint64_t)seed * 747796405u)) & mask;
}

static int
sbuf_reserve(sbuf_t *buf, size_t extra)
{
    if (buf->len + extra + 1u <= buf->cap) {
        return 1;
    }
    size_t new_cap = buf->cap ? buf->cap : 4096u;
    while (new_cap < buf->len + extra + 1u) {
        new_cap *= 2u;
    }
    char *new_data = (char *)realloc(buf->data, new_cap);
    if (!new_data) {
        return 0;
    }
    buf->data = new_data;
    buf->cap = new_cap;
    return 1;
}

static int
sbuf_appendf(sbuf_t *buf, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    va_list ap_copy;
    va_copy(ap_copy, ap);
    int need = vsnprintf(NULL, 0, fmt, ap);
    va_end(ap);
    if (need < 0) {
        va_end(ap_copy);
        return 0;
    }
    if (!sbuf_reserve(buf, (size_t)need)) {
        va_end(ap_copy);
        return 0;
    }
    vsnprintf(buf->data + buf->len, buf->cap - buf->len, fmt, ap_copy);
    va_end(ap_copy);
    buf->len += (size_t)need;
    return 1;
}

static node_t *
build_nodes(uint32_t records, uint32_t seed, int poison)
{
    node_t *nodes = (node_t *)calloc(records, sizeof(node_t));
    if (!nodes) {
        return NULL;
    }
    for (uint32_t i = 0; i < records; ++i) {
        uint64_t x = mix64(((uint64_t)i << 21) ^ seed ^ 0x786d6c726563ull);
        nodes[i].id = i;
        nodes[i].user = (uint32_t)(x & 0xffffu);
        nodes[i].kind = (uint32_t)((x >> 17) & 7u);
        nodes[i].ticket0 = poison_word(i, seed, 0x51u, poison);
        nodes[i].ticket1 = poison_word(i, seed, 0xa9u, poison);
        nodes[i].next = &nodes[(i + 1u) & (records - 1u)];
        nodes[i].prev = &nodes[(i + records - 1u) & (records - 1u)];
    }
    return nodes;
}

static char *
make_xml_doc(node_t *nodes, uint32_t records, uint32_t seed, uint32_t round, size_t *out_len)
{
    static const char *kinds[] = {
        "item", "cart", "profile", "checkout", "search", "media", "auth", "cache"};
    sbuf_t buf = {0};
    if (!sbuf_appendf(&buf, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")) {
        return NULL;
    }
    if (!sbuf_appendf(&buf, "<trace seed=\"%u\" round=\"%u\">\n", seed, round)) {
        free(buf.data);
        return NULL;
    }
    for (uint32_t i = 0; i < records; ++i) {
        node_t *n = &nodes[permute_index(i, records - 1u, seed + round)];
        uint64_t token = mix64(((uint64_t)n->user << 32) ^ n->ticket0 ^ round);
        if (!sbuf_appendf(
                &buf,
                "  <record id=\"%u\" user=\"u%04x\" kind=\"%s\" ptr=\"0x%016llx\" aux=\"0x%016llx\">\n",
                n->id,
                n->user,
                kinds[n->kind & 7u],
                (unsigned long long)n->ticket0,
                (unsigned long long)n->ticket1)) {
            free(buf.data);
            return NULL;
        }
        if (!sbuf_appendf(
                &buf,
                "    <path>/api/v%u/%s/%u</path><token>%016llx</token><edge next=\"%u\" prev=\"%u\" />\n",
                1u + ((n->id + seed) & 3u),
                kinds[n->kind & 7u],
                (uint32_t)(token & 0xffffu),
                (unsigned long long)token,
                n->next->id,
                n->prev->id)) {
            free(buf.data);
            return NULL;
        }
        if (!sbuf_appendf(&buf, "  </record>\n")) {
            free(buf.data);
            return NULL;
        }
    }
    if (!sbuf_appendf(&buf, "</trace>\n")) {
        free(buf.data);
        return NULL;
    }
    *out_len = buf.len;
    return buf.data;
}

static uint64_t
parse_and_dump(char *xml, size_t len, uint32_t scan_depth)
{
    uint64_t dumped_total = 0;
    for (uint32_t scan = 0; scan < scan_depth; ++scan) {
        xmlDocPtr doc = xmlReadMemory(xml, (int)len, "copper.xml", "UTF-8", 0);
        if (!doc) {
            fprintf(stderr, "LIBXML2_COPPER_ERROR parse scan=%u\n", scan);
            return 0;
        }
        xmlChar *dump = NULL;
        int dump_size = 0;
        xmlDocDumpMemory(doc, &dump, &dump_size);
        if (!dump || dump_size <= 0) {
            fprintf(stderr, "LIBXML2_COPPER_ERROR dump scan=%u\n", scan);
            xmlFreeDoc(doc);
            return 0;
        }
        for (int i = 0; i < dump_size; i += 17) {
            fold((uint64_t)dump[i] ^ ((uint64_t)i << 8) ^ (uint64_t)dump_size);
        }
        dumped_total += (uint64_t)dump_size;
        xmlFree(dump);
        xmlFreeDoc(doc);
    }
    return dumped_total;
}

int
main(int argc, char **argv)
{
    uint32_t records = 64;
    uint32_t rounds = 2;
    uint32_t scan_depth = 2;
    uint32_t seed = 0;
    int poison = 1;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--records") && i + 1 < argc) {
            records = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--rounds") && i + 1 < argc) {
            rounds = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--scan-depth") && i + 1 < argc) {
            scan_depth = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = (uint32_t)strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--no-poison")) {
            poison = 0;
        } else {
            fprintf(stderr,
                    "usage: %s [--records N] [--rounds N] [--scan-depth N] [--seed N] [--no-poison]\n",
                    argv[0]);
            return 2;
        }
    }

    if (!is_power_of_two(records) || records < 2u) {
        fprintf(stderr, "LIBXML2_COPPER_ERROR records must be a power of two >= 2\n");
        return 2;
    }

    xmlInitParser();
    node_t *nodes = build_nodes(records, seed, poison);
    if (!nodes) {
        fprintf(stderr, "LIBXML2_COPPER_ERROR alloc nodes\n");
        return 1;
    }

    uint64_t dumped_total = 0;
    uint64_t xml_total = 0;
    for (uint32_t round = 0; round < rounds; ++round) {
        size_t xml_len = 0;
        char *xml = make_xml_doc(nodes, records, seed, round, &xml_len);
        if (!xml) {
            free(nodes);
            xmlCleanupParser();
            return 1;
        }
        xml_total += (uint64_t)xml_len;
        fold(xml_len);
        uint64_t dumped = parse_and_dump(xml, xml_len, scan_depth);
        free(xml);
        if (!dumped) {
            free(nodes);
            xmlCleanupParser();
            return 1;
        }
        dumped_total += dumped;
        fold(dumped);
    }

    uint64_t pointer_like_words = (uint64_t)records * 2u;
    for (uint32_t i = 0; i < records; i += (records / 8u ? records / 8u : 1u)) {
        fold(nodes[i].ticket0);
        fold(nodes[i].ticket1);
        fold((uintptr_t)nodes[i].next ^ (uintptr_t)nodes[i].prev);
    }

    printf("LIBXML2_COPPER_RESULT records=%u rounds=%u scan_depth=%u seed=%u poison=%d "
           "xml_bytes=%llu dumped_bytes=%llu pointer_like_words=%llu checksum=0x%016llx\n",
           records,
           rounds,
           scan_depth,
           seed,
           poison,
           (unsigned long long)xml_total,
           (unsigned long long)dumped_total,
           (unsigned long long)pointer_like_words,
           (unsigned long long)checksum_acc);

    free(nodes);
    xmlCleanupParser();
    return 0;
}
