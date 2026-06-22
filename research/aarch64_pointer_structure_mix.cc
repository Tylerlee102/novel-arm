#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include <gem5/m5ops.h>


struct alignas(64) Node {
    Node *left;
    Node *right;
    Node *next;
    uint64_t payload[5];
};


static uint64_t rng_state = 0x517cc1b727220a95ULL;


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


int main(int argc, char **argv)
{
    const size_t nodes_count = read_size_arg(argc, argv, "--nodes", 32768);
    const size_t passes = read_size_arg(argc, argv, "--passes", 12);
    const size_t buckets_count = read_size_arg(argc, argv, "--buckets", 2048);
    const size_t fake_passes = read_size_arg(argc, argv, "--fake-passes", 3);
    const uint64_t seed = read_size_arg(
        argc, argv, "--seed", 0x517cc1b727220a95ULL);
    rng_state = seed;

    std::vector<Node> nodes(nodes_count);
    std::vector<Node *> order(nodes_count);
    std::vector<Node *> buckets(buckets_count, nullptr);
    std::vector<uintptr_t> fake(nodes_count);

    for (size_t i = 0; i < nodes_count; ++i) {
        order[i] = &nodes[i];
        nodes[i].left = nullptr;
        nodes[i].right = nullptr;
        nodes[i].next = nullptr;
        for (size_t j = 0; j < 5; ++j) {
            nodes[i].payload[j] =
                (i + 3) * 0x9e3779b185ebca87ULL ^
                (j + 1) * 0xc2b2ae3d27d4eb4fULL;
        }
    }

    for (size_t i = nodes_count - 1; i > 0; --i) {
        const size_t j = static_cast<size_t>(next_rand() % (i + 1));
        Node *tmp = order[i];
        order[i] = order[j];
        order[j] = tmp;
    }

    for (size_t i = 0; i < nodes_count; ++i) {
        const size_t left = 2 * i + 1;
        const size_t right = 2 * i + 2;
        order[i]->left = left < nodes_count ? order[left] : nullptr;
        order[i]->right = right < nodes_count ? order[right] : nullptr;
    }

    for (size_t i = 0; i < nodes_count; ++i) {
        const size_t bucket = (next_rand() ^ (i * 0x45d9f3bULL)) % buckets_count;
        order[i]->next = buckets[bucket];
        buckets[bucket] = order[i];
        fake[i] = reinterpret_cast<uintptr_t>(
            order[(i * 11400714819323198485ULL) % nodes_count]);
    }

    volatile uint64_t sink = 0;

    std::printf("STRUCT_MIX_ROI_RESET\n");
    m5_reset_stats(0, 0);

    for (size_t pass = 0; pass < passes; ++pass) {
        Node *cursor = order[(pass * 1315423911ULL) % nodes_count];
        for (size_t step = 0; step < nodes_count; ++step) {
            const uint64_t bits = cursor->payload[(step + pass) % 5] ^ step;
            Node *next = (bits & 1) ? cursor->left : cursor->right;
            if (next == nullptr) {
                next = order[(bits + pass * 97) % nodes_count];
            }
            sink ^= next->payload[(bits >> 3) % 5] +
                    reinterpret_cast<uintptr_t>(next);
            cursor = next;
        }
    }

    for (size_t pass = 0; pass < passes; ++pass) {
        const size_t start = (pass * 257) % buckets_count;
        for (size_t b = 0; b < buckets_count; ++b) {
            Node *cursor = buckets[(start + b) % buckets_count];
            size_t depth = 0;
            while (cursor != nullptr && depth < 64) {
                sink += cursor->payload[(depth + pass) % 5] ^
                        reinterpret_cast<uintptr_t>(cursor->next);
                cursor = cursor->next;
                ++depth;
            }
        }
    }

    uint64_t fake_mix = 0;
    for (size_t pass = 0; pass < fake_passes; ++pass) {
        for (size_t i = 0; i < fake.size(); ++i) {
            const uintptr_t raw = fake[(i * 19 + pass * 43) % fake.size()];
            fake_mix ^= (raw >> 5) ^ (raw << 11) ^ i ^ pass;
        }
    }

    for (size_t i = 0; i < nodes_count / 32; ++i) {
        order[i]->left = order[(i * 193 + 17) % nodes_count];
        sink ^= reinterpret_cast<uintptr_t>(order[i]->left);
    }

    std::printf("STRUCT_MIX_ROI_DUMP\n");
    m5_dump_stats(0, 0);

    const uint64_t checksum = sink ^ fake_mix;
    std::printf(
        "STRUCT_MIX nodes=%zu passes=%zu buckets=%zu fake_passes=%zu "
        "seed=0x%016" PRIx64 " checksum=0x%016" PRIx64 "\n",
        nodes_count,
        passes,
        buckets_count,
        fake_passes,
        seed,
        checksum);
    return checksum == 0 ? 2 : 0;
}
