#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <vector>


struct alignas(64) Node {
    Node *next;
    uint64_t payload[7];
};


static uint64_t rng_state = 0x9e3779b97f4a7c15ULL;


static uint64_t next_rand()
{
    uint64_t x = rng_state;
    x ^= x << 7;
    x ^= x >> 9;
    x ^= x << 8;
    rng_state = x;
    return x;
}


static size_t read_size_arg(int argc, char **argv, const char *name, size_t def)
{
    const size_t name_len = std::strlen(name);
    for (int i = 1; i < argc; ++i) {
        if (std::strncmp(argv[i], name, name_len) == 0 && argv[i][name_len] == '=') {
            return static_cast<size_t>(std::strtoull(argv[i] + name_len + 1, nullptr, 0));
        }
    }
    return def;
}


int main(int argc, char **argv)
{
    const size_t nodes_count = read_size_arg(argc, argv, "--nodes", 65536);
    const size_t passes = read_size_arg(argc, argv, "--passes", 8);
    const size_t fake_count = read_size_arg(argc, argv, "--fake", 65536);

    std::vector<Node> nodes(nodes_count);
    std::vector<Node *> order(nodes_count);
    std::vector<uintptr_t> fake(fake_count);

    for (size_t i = 0; i < nodes_count; ++i) {
        order[i] = &nodes[i];
        nodes[i].next = nullptr;
        for (size_t j = 0; j < 7; ++j) {
            nodes[i].payload[j] = (i + 1) * 0x100000001b3ULL ^ (j * 0x517cc1b727220a95ULL);
        }
    }

    for (size_t i = nodes_count - 1; i > 0; --i) {
        const size_t j = static_cast<size_t>(next_rand() % (i + 1));
        Node *tmp = order[i];
        order[i] = order[j];
        order[j] = tmp;
    }

    for (size_t i = 0; i < nodes_count; ++i) {
        order[i]->next = order[(i + 1) % nodes_count];
    }

    for (size_t i = 0; i < fake_count; ++i) {
        fake[i] = reinterpret_cast<uintptr_t>(order[(i * 1315423911ULL) % nodes_count]);
    }

    volatile uint64_t sink = 0;
    Node *cursor = order[0];

    for (size_t pass = 0; pass < passes; ++pass) {
        for (size_t i = 0; i < nodes_count; ++i) {
            Node *next = cursor->next;
            sink ^= next->payload[(i + pass) % 7] + reinterpret_cast<uintptr_t>(next);
            cursor = next;
        }
    }

    uint64_t fake_mix = 0;
    for (size_t pass = 0; pass < 2; ++pass) {
        for (size_t i = 0; i < fake_count; ++i) {
            const uintptr_t raw = fake[(i * 17 + pass * 31) % fake_count];
            fake_mix ^= (raw >> 4) ^ (raw << 13) ^ (i * 0x45d9f3bULL);
        }
    }

    const size_t rewrite_count = nodes_count / 16;
    for (size_t i = 0; i < rewrite_count; ++i) {
        nodes[i].next = order[(i * 97 + 13) % nodes_count];
    }
    for (size_t i = 0; i < rewrite_count; ++i) {
        Node *next = nodes[i].next;
        sink += next->payload[i % 7] ^ reinterpret_cast<uintptr_t>(next);
    }

    const uint64_t checksum = sink ^ fake_mix ^ reinterpret_cast<uintptr_t>(cursor);
    std::printf(
        "HEAP_STRESS nodes=%zu passes=%zu fake=%zu rewrite=%zu checksum=0x%016" PRIx64 "\n",
        nodes_count,
        passes,
        fake_count,
        rewrite_count,
        checksum
    );
    return checksum == 0 ? 2 : 0;
}
