typedef unsigned int u32;
typedef unsigned long u64;
typedef unsigned long uptr;

#ifndef NODES
#define NODES 1024u
#endif
#ifndef DEGREE
#define DEGREE 8u
#endif
#ifndef EDGES
#define EDGES (NODES * DEGREE)
#endif
#ifndef PASSES
#define PASSES 3u
#endif
#ifndef FAKE_COUNT
#define FAKE_COUNT 2048u
#endif
#ifndef GAP_OPS
#define GAP_OPS 18u
#endif

struct Vertex {
    u32 first;
    u32 degree;
    u32 id;
    u32 rank;
    u32 next_rank;
    u32 dist;
    u32 comp;
    u32 frontier;
    u32 next_frontier;
    u32 value;
    u32 pad[6];
};

static struct Vertex vertices[NODES];
static u32 out_edge_ptrs[EDGES];
static u32 in_edge_ptrs[EDGES];
static u32 fake_ptrs[FAKE_COUNT];
static u32 bfs_queue[NODES];
static volatile u32 sink32;

static long sys_write(int fd, const void *buf, u64 len)
{
    register u64 x0 __asm__("x0") = (u64)fd;
    register const void *x1 __asm__("x1") = buf;
    register u64 x2 __asm__("x2") = len;
    register u64 x8 __asm__("x8") = 64;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x8) : "memory");
    return (long)x0;
}

static void sys_exit(int code)
{
    register u64 x0 __asm__("x0") = (u64)code;
    register u64 x8 __asm__("x8") = 93;
    __asm__ volatile("svc #0" : : "r"(x0), "r"(x8) : "memory");
    __builtin_unreachable();
}

static u32 addr32(const void *ptr)
{
    return (u32)(uptr)ptr;
}

static u32 rng_step(u32 *state)
{
    *state = (*state * 1664525u) + 1013904223u;
    return *state;
}

static u32 compute_gap(u32 acc, u32 raw)
{
    for (u32 k = 0; k < GAP_OPS; ++k)
        acc = (acc << 5) ^ (acc >> 3) ^ raw ^ (k * 0x9e37u);
    return acc;
}

static void init_graph(void)
{
    u32 s = 0x31415927u;
    for (u32 i = 0; i < NODES; ++i) {
        vertices[i].first = i * DEGREE;
        vertices[i].degree = DEGREE;
        vertices[i].id = i;
        vertices[i].rank = (i * 17u + 1u) & 0xffffu;
        vertices[i].next_rank = 0u;
        vertices[i].dist = 0x3fffffffu;
        vertices[i].comp = i;
        vertices[i].frontier = 0u;
        vertices[i].next_frontier = 0u;
        vertices[i].value = (i * 2654435761u) ^ 0xa5a5a5a5u;
    }

    for (u32 e = 0; e < EDGES; ++e) {
        u32 src = e / DEGREE;
        u32 r = rng_step(&s);
        u32 target = (src * 37u + (r >> 16) + e * 13u) & (NODES - 1u);
        out_edge_ptrs[e] = addr32(&vertices[target]);
    }

    for (u32 e = 0; e < EDGES; ++e) {
        u32 r = rng_step(&s);
        u32 target = ((e * 1103515245u) ^ (r >> 7)) & (NODES - 1u);
        in_edge_ptrs[e] = addr32(&vertices[target]);
    }

    for (u32 i = 0; i < FAKE_COUNT; ++i) {
        u32 target = (i * 193u + 31u) & (NODES - 1u);
        fake_ptrs[i] = addr32(&vertices[target]);
    }
}

static u32 bfs_kernel(void)
{
    u32 acc = 0u;
    for (u32 i = 0; i < NODES; ++i) {
        vertices[i].frontier = 0u;
        vertices[i].next_frontier = 0u;
        vertices[i].dist = 0x3fffffffu;
    }

    u32 head = 0u;
    u32 tail = 0u;
    vertices[0].frontier = 1u;
    vertices[0].dist = 0u;
    bfs_queue[tail++] = addr32(&vertices[0]);

    while (head != tail) {
        u32 raw_v = ((volatile u32 *)bfs_queue)[head++ & (NODES - 1u)];
        volatile struct Vertex *v = (volatile struct Vertex *)(uptr)raw_v;
        u32 base = v->first;
        u32 nd = v->dist + 1u;
        for (u32 k = 0; k < DEGREE; ++k) {
            u32 raw = ((volatile u32 *)out_edge_ptrs)[base + k];
            acc = compute_gap(acc, raw);
            volatile struct Vertex *t = (volatile struct Vertex *)(uptr)raw;
            if (t->dist == 0x3fffffffu) {
                ((struct Vertex *)(uptr)raw)->dist = nd;
                ((struct Vertex *)(uptr)raw)->frontier = 1u;
                bfs_queue[tail++ & (NODES - 1u)] = raw;
            }
            acc ^= t->value;
        }
        if (head > (NODES * 2u))
            break;
    }
    return acc ^ head ^ tail;
}

static u32 sssp_relax_kernel(void)
{
    u32 acc = 0u;
    for (u32 i = 0; i < NODES; ++i)
        vertices[i].dist = (i == 0u) ? 0u : 0x3fffffffu;

    for (u32 pass = 0; pass < PASSES; ++pass) {
        for (u32 i = 0; i < NODES; ++i) {
            volatile struct Vertex *v = (volatile struct Vertex *)&vertices[i];
            u32 base = v->first;
            u32 src_dist = v->dist;
            for (u32 k = 0; k < DEGREE; ++k) {
                u32 raw = ((volatile u32 *)out_edge_ptrs)[base + k];
                acc = compute_gap(acc, raw);
                volatile struct Vertex *t = (volatile struct Vertex *)(uptr)raw;
                u32 cand = src_dist + ((k + i + pass) & 15u) + 1u;
                if (cand < t->dist)
                    ((struct Vertex *)(uptr)raw)->dist = cand;
                acc ^= t->dist ^ t->value;
            }
        }
    }
    return acc;
}

static u32 pagerank_gather_kernel(void)
{
    u32 acc = 0u;
    for (u32 pass = 0; pass < PASSES; ++pass) {
        for (u32 i = 0; i < NODES; ++i)
            vertices[i].next_rank = 1u;
        for (u32 e = 0; e < EDGES; ++e) {
            u32 raw = ((volatile u32 *)in_edge_ptrs)[e];
            acc = compute_gap(acc, raw);
            volatile struct Vertex *src = (volatile struct Vertex *)(uptr)raw;
            u32 dst = (e * 17u + pass) & (NODES - 1u);
            vertices[dst].next_rank += (src->rank >> 3) + (src->value & 7u);
            acc ^= src->rank ^ vertices[dst].next_rank;
        }
        for (u32 i = 0; i < NODES; ++i)
            vertices[i].rank = vertices[i].next_rank;
    }
    return acc;
}

static u32 connected_components_kernel(void)
{
    u32 acc = 0u;
    for (u32 i = 0; i < NODES; ++i)
        vertices[i].comp = i;

    for (u32 pass = 0; pass < PASSES; ++pass) {
        for (u32 i = 0; i < NODES; ++i) {
            u32 base = vertices[i].first;
            u32 best = vertices[i].comp;
            for (u32 k = 0; k < DEGREE; ++k) {
                u32 raw = ((volatile u32 *)out_edge_ptrs)[base + k];
                acc = compute_gap(acc, raw);
                volatile struct Vertex *t = (volatile struct Vertex *)(uptr)raw;
                if (t->comp < best)
                    best = t->comp;
                acc ^= t->comp ^ t->value;
            }
            vertices[i].comp = best;
        }
    }
    return acc;
}

static u32 fake_pointer_scan(void)
{
    u32 acc = 0u;
    for (u32 i = 0; i < FAKE_COUNT; ++i) {
        u32 raw = ((volatile u32 *)fake_ptrs)[i];
        acc ^= raw + (i * 33u);
    }
    return acc;
}

static char hex_digit(u32 v)
{
    v &= 15u;
    return (char)(v < 10u ? ('0' + v) : ('a' + (v - 10u)));
}

static void emit_hex32(u32 value)
{
    char msg[80];
    static const char prefix[] = "AARCH64_GAPBS_MINI_DONE checksum=0x";
    u32 pos = 0u;
    for (u32 i = 0; i < sizeof(prefix) - 1u; ++i)
        msg[pos++] = prefix[i];
    for (int shift = 28; shift >= 0; shift -= 4)
        msg[pos++] = hex_digit(value >> (u32)shift);
    msg[pos++] = '\n';
    sys_write(1, msg, pos);
}

void _start(void)
{
    init_graph();
    u32 acc = bfs_kernel();
    acc ^= sssp_relax_kernel();
    acc ^= pagerank_gather_kernel();
    acc ^= connected_components_kernel();
    acc ^= fake_pointer_scan();
    sink32 = acc;
    emit_hex32(acc);
    sys_exit(0);
}
