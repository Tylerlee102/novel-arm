typedef unsigned int u32;
typedef unsigned long u64;
typedef unsigned long uptr;

#ifndef NODES
#define NODES 4096u
#endif
#ifndef EDGES
#define EDGES 16384u
#endif
#ifndef PASSES
#define PASSES 4u
#endif
#ifndef HASH_BUCKETS
#define HASH_BUCKETS 2048u
#endif
#ifndef HASH_ITEMS
#define HASH_ITEMS 8192u
#endif
#ifndef QUERIES
#define QUERIES 32768u
#endif
#ifndef TREE_NODES
#define TREE_NODES 4095u
#endif
#ifndef FAKE_COUNT
#define FAKE_COUNT 8192u
#endif

struct Node {
    u32 next;
    u32 value;
    u32 pad[14];
};

struct HItem {
    u32 next;
    u32 key;
    u32 value;
    u32 pad[13];
};

struct TNode {
    u32 left;
    u32 right;
    u32 key;
    u32 value;
    u32 pad[12];
};

static struct Node nodes[NODES];
static u32 edge_ptrs[EDGES];
static u32 fake_ptrs[FAKE_COUNT];
static struct HItem hitems[HASH_ITEMS];
static u32 buckets[HASH_BUCKETS];
static u32 queries[QUERIES];
static struct TNode tree[TREE_NODES];
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

static u32 rng_step(u32 *state)
{
    *state = (*state * 1664525u) + 1013904223u;
    return *state;
}

static u32 addr32(const void *ptr)
{
    return (u32)(uptr)ptr;
}

static void init_nodes(void)
{
    u32 s = 0x12345678u;
    for (u32 i = 0; i < NODES; ++i) {
        u32 j = (i * 1109u + 97u) & (NODES - 1u);
        nodes[i].next = addr32(&nodes[j]);
        nodes[i].value = i ^ 0x9e3779b9u;
    }
    for (u32 i = 0; i < EDGES; ++i) {
        u32 target = rng_step(&s) & (NODES - 1u);
        edge_ptrs[i] = addr32(&nodes[target]);
    }
    for (u32 i = 0; i < FAKE_COUNT; ++i) {
        u32 target = (i * 193u + 31u) & (NODES - 1u);
        fake_ptrs[i] = addr32(&nodes[target]);
    }
}

static void init_hash(void)
{
    for (u32 i = 0; i < HASH_BUCKETS; ++i)
        buckets[i] = 0u;
    for (u32 i = 0; i < HASH_ITEMS; ++i) {
        u32 key = (i * 2654435761u) ^ 0xa5a5a5a5u;
        u32 b = key & (HASH_BUCKETS - 1u);
        hitems[i].key = key;
        hitems[i].value = key ^ (i * 17u);
        hitems[i].next = buckets[b];
        buckets[b] = addr32(&hitems[i]);
    }
    for (u32 i = 0; i < QUERIES; ++i) {
        u32 item = (i * 73u + 19u) & (HASH_ITEMS - 1u);
        queries[i] = hitems[item].key;
    }
}

static void init_tree(void)
{
    for (u32 i = 0; i < TREE_NODES; ++i) {
        u32 left = 2u * i + 1u;
        u32 right = 2u * i + 2u;
        tree[i].left = left < TREE_NODES ? addr32(&tree[left]) : 0u;
        tree[i].right = right < TREE_NODES ? addr32(&tree[right]) : 0u;
        tree[i].key = i * 3u + 1u;
        tree[i].value = i ^ 0x13579bdfu;
    }
}

static u32 graph_gather_kernel(void)
{
    u32 acc = 0u;
    for (u32 p = 0; p < PASSES; ++p) {
        for (u32 i = 0; i < EDGES; ++i) {
            u32 raw = ((volatile u32 *)edge_ptrs)[i];
            for (u32 k = 0; k < 10u; ++k)
                acc = (acc << 3) ^ (acc >> 2) ^ raw ^ k;
            volatile struct Node *n = (volatile struct Node *)(uptr)raw;
            acc ^= n->value;
            acc ^= ((volatile struct Node *)(uptr)n->next)->value;
        }
    }
    return acc;
}

static u32 hash_probe_kernel(void)
{
    u32 acc = 0u;
    for (u32 i = 0; i < QUERIES; ++i) {
        u32 key = ((volatile u32 *)queries)[i];
        u32 cur = ((volatile u32 *)buckets)[key & (HASH_BUCKETS - 1u)];
        u32 depth = 0u;
        while (cur != 0u && depth < 8u) {
            volatile struct HItem *it = (volatile struct HItem *)(uptr)cur;
            if (it->key == key) {
                acc ^= it->value;
                break;
            }
            cur = it->next;
            ++depth;
        }
    }
    return acc;
}

static u32 tree_lookup_kernel(void)
{
    u32 acc = 0u;
    for (u32 q = 0; q < QUERIES; ++q) {
        u32 key = (q * 17u + 5u) % (TREE_NODES * 3u);
        u32 cur = addr32(&tree[0]);
        for (u32 depth = 0; depth < 12u && cur != 0u; ++depth) {
            volatile struct TNode *n = (volatile struct TNode *)(uptr)cur;
            acc ^= n->value;
            cur = key < n->key ? n->left : n->right;
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
    char msg[64];
    static const char prefix[] = "AARCH64_C_KERNEL_SUITE_DONE checksum=0x";
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
    init_nodes();
    init_hash();
    init_tree();
    u32 acc = graph_gather_kernel();
    acc ^= hash_probe_kernel();
    acc ^= tree_lookup_kernel();
    acc ^= fake_pointer_scan();
    sink32 = acc;
    emit_hex32(acc);
    sys_exit(0);
}
