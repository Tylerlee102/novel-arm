// Deterministic AArch64 Expat XML parser workload for COPPER full-system runs.
//
// This calls the public libexpat parser ABI through the Ubuntu ARM64 guest
// library stack. The XML contains address-shaped attribute values loaded as
// ordinary data, plus nested records to exercise parser-owned pointer-rich
// structures without adding any proprietary benchmark dependency.

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>

#include <gem5/m5ops.h>

typedef char XML_Char;
typedef char XML_LChar;
typedef struct XML_ParserStruct *XML_Parser;

enum XML_Status {
    XML_STATUS_ERROR = 0,
    XML_STATUS_OK = 1,
    XML_STATUS_SUSPENDED = 2
};

typedef void (*XML_StartElementHandler)(
    void *userData,
    const XML_Char *name,
    const XML_Char **atts
);
typedef void (*XML_EndElementHandler)(void *userData, const XML_Char *name);
typedef void (*XML_CharacterDataHandler)(void *userData, const XML_Char *s, int len);

extern XML_Parser XML_ParserCreate(const XML_Char *encoding);
extern void XML_ParserFree(XML_Parser parser);
extern void XML_SetUserData(XML_Parser parser, void *userData);
extern void XML_SetElementHandler(
    XML_Parser parser,
    XML_StartElementHandler start,
    XML_EndElementHandler end
);
extern void XML_SetCharacterDataHandler(XML_Parser parser, XML_CharacterDataHandler handler);
extern enum XML_Status XML_Parse(XML_Parser parser, const char *s, int len, int isFinal);
extern int XML_GetErrorCode(XML_Parser parser);
extern const XML_LChar *XML_ErrorString(int code);
extern unsigned long XML_GetCurrentLineNumber(XML_Parser parser);

typedef struct {
    uint64_t checksum;
    uint64_t elements;
    uint64_t attrs;
    uint64_t text_bytes;
    uint64_t pointer_like_attrs;
    uint64_t max_depth;
    uint64_t depth;
} ParseState;

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

static uint64_t cksum_bytes(uint64_t seed, const char *s, int len) {
    uint64_t h = seed ^ 0x9e3779b97f4a7c15ULL;
    for (int i = 0; i < len; i++) {
        h ^= (uint64_t)(unsigned char)s[i] + 0x100000001b3ULL;
        h = rotl64(h, 7) * 0x100000001b3ULL;
    }
    return h;
}

static int starts_with_hex_pointer(const char *s) {
    return s && s[0] == '0' && (s[1] == 'x' || s[1] == 'X') && strlen(s) >= 10;
}

static void on_start(void *userData, const XML_Char *name, const XML_Char **atts) {
    ParseState *st = (ParseState *)userData;
    st->elements++;
    st->depth++;
    if (st->depth > st->max_depth) {
        st->max_depth = st->depth;
    }
    st->checksum ^= cksum_bytes(st->checksum + st->elements, name, (int)strlen(name));
    for (const XML_Char **p = atts; p && p[0] && p[1]; p += 2) {
        st->attrs++;
        st->checksum ^= cksum_bytes(st->checksum ^ st->attrs, p[0], (int)strlen(p[0]));
        st->checksum ^= cksum_bytes(st->checksum + 0x55aa55aaULL, p[1], (int)strlen(p[1]));
        if (starts_with_hex_pointer(p[1])) {
            st->pointer_like_attrs++;
        }
    }
}

static void on_end(void *userData, const XML_Char *name) {
    ParseState *st = (ParseState *)userData;
    st->checksum ^= cksum_bytes(st->checksum ^ 0xa5a5a5a5ULL, name, (int)strlen(name));
    if (st->depth) {
        st->depth--;
    }
}

static void on_text(void *userData, const XML_Char *s, int len) {
    ParseState *st = (ParseState *)userData;
    st->text_bytes += (uint64_t)len;
    st->checksum ^= cksum_bytes(st->checksum ^ 0x1234fedcULL, s, len);
}

static uint64_t parse_u64_arg(const char *s, uint64_t fallback) {
    if (!s || !*s) {
        return fallback;
    }
    char *end = 0;
    uint64_t v = strtoull(s, &end, 0);
    return end && *end == 0 ? v : fallback;
}

static void append_or_die(char **cursor, size_t *remaining, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(*cursor, *remaining, fmt, ap);
    va_end(ap);
    if (n < 0 || (size_t)n >= *remaining) {
        fprintf(stderr, "XML buffer overflow while generating workload\n");
        exit(2);
    }
    *cursor += n;
    *remaining -= (size_t)n;
}

static char *build_xml(
    uint64_t records,
    uint64_t attrs,
    uint64_t rounds,
    uint64_t seed,
    size_t *out_len
) {
    size_t estimate = (size_t)(256 + records * (240 + attrs * 80) + rounds * 64);
    char *buf = (char *)malloc(estimate);
    if (!buf) {
        fprintf(stderr, "malloc failed\n");
        exit(2);
    }
    char *cur = buf;
    size_t rem = estimate;
    append_or_die(&cur, &rem, "<dataset seed=\"%llu\" rounds=\"%llu\">\n",
        (unsigned long long)seed, (unsigned long long)rounds);
    uint64_t x = mix64(seed ^ 0x5eed12345678ULL);
    for (uint64_t i = 0; i < records; i++) {
        x = mix64(x + i * 0x9e3779b97f4a7c15ULL);
        uint64_t addr = 0x400000ULL + ((x >> 4) & 0x0000fffffffffff8ULL);
        append_or_die(
            &cur,
            &rem,
            "  <record id=\"%llu\" addr=\"0x%016llx\" tag=\"r%llu\" ",
            (unsigned long long)i,
            (unsigned long long)addr,
            (unsigned long long)(x & 0xffffULL)
        );
        for (uint64_t a = 0; a < attrs; a++) {
            uint64_t val = mix64(x ^ (a * 0x100000001b3ULL));
            if ((a & 1ULL) == 0) {
                uint64_t fake = 0x400000ULL + ((val >> 5) & 0x0000fffffffffff8ULL);
                append_or_die(
                    &cur,
                    &rem,
                    "p%llu=\"0x%016llx\" ",
                    (unsigned long long)a,
                    (unsigned long long)fake
                );
            } else {
                append_or_die(
                    &cur,
                    &rem,
                    "k%llu=\"%llu\" ",
                    (unsigned long long)a,
                    (unsigned long long)(val & 0xffffffULL)
                );
            }
        }
        append_or_die(&cur, &rem, ">\n");
        append_or_die(
            &cur,
            &rem,
            "    <payload>node-%llu text-%016llx</payload>\n",
            (unsigned long long)i,
            (unsigned long long)mix64(x ^ 0xa11ceULL)
        );
        append_or_die(
            &cur,
            &rem,
            "    <edge dst=\"%llu\" weight=\"%llu\" />\n",
            (unsigned long long)((i * 131ULL + 17ULL) % (records ? records : 1)),
            (unsigned long long)(mix64(x ^ 0xb0bULL) & 0xffffULL)
        );
        append_or_die(&cur, &rem, "  </record>\n");
    }
    append_or_die(&cur, &rem, "</dataset>\n");
    *out_len = (size_t)(cur - buf);
    return buf;
}

int main(int argc, char **argv) {
    uint64_t records = 512;
    uint64_t attrs = 6;
    uint64_t rounds = 1;
    uint64_t seed = 0;
    uint64_t chunk = 4096;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--records") && i + 1 < argc) {
            records = parse_u64_arg(argv[++i], records);
        } else if (!strcmp(argv[i], "--attrs") && i + 1 < argc) {
            attrs = parse_u64_arg(argv[++i], attrs);
        } else if (!strcmp(argv[i], "--rounds") && i + 1 < argc) {
            rounds = parse_u64_arg(argv[++i], rounds);
        } else if (!strcmp(argv[i], "--seed") && i + 1 < argc) {
            seed = parse_u64_arg(argv[++i], seed);
        } else if (!strcmp(argv[i], "--chunk") && i + 1 < argc) {
            chunk = parse_u64_arg(argv[++i], chunk);
        }
    }
    if (records == 0 || attrs == 0 || rounds == 0 || chunk == 0 || chunk > (1ULL << 20)) {
        fprintf(stderr, "invalid workload parameters\n");
        return 2;
    }

    size_t xml_len = 0;
    char *xml = build_xml(records, attrs, rounds, seed, &xml_len);
    ParseState total = {0};
    total.checksum = mix64(seed ^ records ^ (attrs << 8) ^ (rounds << 16));

    for (uint64_t r = 0; r < rounds; r++) {
        XML_Parser parser = XML_ParserCreate(0);
        if (!parser) {
            fprintf(stderr, "XML_ParserCreate failed\n");
            free(xml);
            return 3;
        }
        ParseState st = {0};
        st.checksum = mix64(total.checksum ^ r);
        XML_SetUserData(parser, &st);
        XML_SetElementHandler(parser, on_start, on_end);
        XML_SetCharacterDataHandler(parser, on_text);

        if (r == 0) {
            m5_work_begin(0, 0);
            m5_reset_stats(0, 0);
        }
        size_t off = 0;
        while (off < xml_len) {
            size_t n = xml_len - off;
            if (n > (size_t)chunk) {
                n = (size_t)chunk;
            }
            int final = (off + n == xml_len);
            if (XML_Parse(parser, xml + off, (int)n, final) != XML_STATUS_OK) {
                int code = XML_GetErrorCode(parser);
                fprintf(
                    stderr,
                    "expat parse error line=%lu code=%d %s\n",
                    XML_GetCurrentLineNumber(parser),
                    code,
                    XML_ErrorString(code)
                );
                XML_ParserFree(parser);
                free(xml);
                return 4;
            }
            off += n;
        }

        total.checksum ^= mix64(st.checksum + r);
        total.elements += st.elements;
        total.attrs += st.attrs;
        total.text_bytes += st.text_bytes;
        total.pointer_like_attrs += st.pointer_like_attrs;
        if (st.max_depth > total.max_depth) {
            total.max_depth = st.max_depth;
        }
        XML_ParserFree(parser);
    }

    m5_dump_stats(0, 0);
    m5_work_end(0, 0);
    printf(
        "EXPAT_COPPER_RESULT records=%llu attrs=%llu rounds=%llu seed=%llu chunk=%llu xml_bytes=%llu elements=%llu attr_count=%llu text_bytes=%llu pointer_like_attrs=%llu max_depth=%llu checksum=0x%016llx\n",
        (unsigned long long)records,
        (unsigned long long)attrs,
        (unsigned long long)rounds,
        (unsigned long long)seed,
        (unsigned long long)chunk,
        (unsigned long long)xml_len,
        (unsigned long long)total.elements,
        (unsigned long long)total.attrs,
        (unsigned long long)total.text_bytes,
        (unsigned long long)total.pointer_like_attrs,
        (unsigned long long)total.max_depth,
        (unsigned long long)total.checksum
    );
    free(xml);
    return 0;
}
