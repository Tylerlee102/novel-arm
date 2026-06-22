#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include <gem5/m5ops.h>


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
        if (std::strncmp(argv[i], name, name_len) == 0 &&
            argv[i][name_len] == '=') {
            return static_cast<size_t>(
                std::strtoull(argv[i] + name_len + 1, nullptr, 0));
        }
    }
    return def;
}


static bool read_bool_arg(int argc, char **argv, const char *name, bool def)
{
    return read_size_arg(argc, argv, name, def ? 1 : 0) != 0;
}


int main(int argc, char **argv)
{
    const size_t nodes_count = read_size_arg(argc, argv, "--nodes", 65536);
    const size_t passes = read_size_arg(argc, argv, "--passes", 16);
    const size_t fake_count = read_size_arg(argc, argv, "--fake", 65536);
    const size_t fake_passes = read_size_arg(argc, argv, "--fake-passes", 4);
    const size_t rewrite_count =
        read_size_arg(argc, argv, "--rewrite", nodes_count / 16);
    const uint64_t seed = read_size_arg(
        argc, argv, "--seed", 0x9e3779b97f4a7c15ULL);
    const bool use_m5 = read_bool_arg(argc, argv, "--m5", true);
    rng_state = seed;

    std::vector<Node> nodes(nodes_count);
    std::vector<Node *> order(nodes_count);
    std::vector<uintptr_t> fake(fake_count);

    for (size_t i = 0; i < nodes_count; ++i) {
        order[i] = &nodes[i];
        nodes[i].next = nullptr;
        for (size_t j = 0; j < 7; ++j) {
            nodes[i].payload[j] =
                (i + 1) * 0x100000001b3ULL ^
                (j * 0x517cc1b727220a95ULL);
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
        fake[i] = reinterpret_cast<uintptr_t>(
            order[(i * 1315423911ULL) % nodes_count]);
    }

    volatile uint64_t sink = 0;
    Node *cursor = order[0];

    if (use_m5) {
        std::printf("HEAP_ROI_RESET\n");
        m5_reset_stats(0, 0);
    }

    for (size_t pass = 0; pass < passes; ++pass) {
        for (size_t i = 0; i < nodes_count; ++i) {
            Node *next = cursor->next;
            sink ^= next->payload[(i + pass) % 7] +
                    reinterpret_cast<uintptr_t>(next);
            cursor = next;
        }
    }

    uint64_t fake_mix = 0;
    for (size_t pass = 0; pass < fake_passes; ++pass) {
        for (size_t i = 0; i < fake_count; ++i) {
            const uintptr_t raw = fake[(i * 17 + pass * 31) % fake_count];
            fake_mix ^= (raw >> 4) ^ (raw << 13) ^
                        (i * 0x45d9f3bULL) ^ pass;
        }
    }

    const size_t bounded_rewrite =
        rewrite_count < nodes_count ? rewrite_count : nodes_count;
    for (size_t i = 0; i < bounded_rewrite; ++i) {
        nodes[i].next = order[(i * 97 + 13) % nodes_count];
    }
    for (size_t i = 0; i < bounded_rewrite; ++i) {
        Node *next = nodes[i].next;
        sink += next->payload[i % 7] ^ reinterpret_cast<uintptr_t>(next);
    }

    if (use_m5) {
        std::printf("HEAP_ROI_DUMP\n");
        m5_dump_stats(0, 0);
    }

    const uint64_t checksum =
        sink ^ fake_mix ^ reinterpret_cast<uintptr_t>(cursor);
    std::printf(
        "HEAP_ROI_STRESS nodes=%zu passes=%zu fake=%zu fake_passes=%zu "
        "rewrite=%zu seed=0x%016" PRIx64 " checksum=0x%016" PRIx64 "\n",
        nodes_count,
        passes,
        fake_count,
        fake_passes,
        bounded_rewrite,
        seed,
        checksum);
    return checksum == 0 ? 2 : 0;
}
