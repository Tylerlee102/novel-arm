#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include <gem5/m5ops.h>


struct alignas(64) TargetLine {
    uint64_t payload[8];
};


static uint64_t rng_state = 0x243f6a8885a308d3ULL;


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


static uint64_t read_u64_arg(int argc, char **argv, const char *name, uint64_t def)
{
    return static_cast<uint64_t>(read_size_arg(argc, argv, name, def));
}


static bool read_bool_arg(int argc, char **argv, const char *name, bool def)
{
    return read_size_arg(argc, argv, name, def ? 1 : 0) != 0;
}


static uint64_t mix_word(uint64_t acc, uint64_t raw, size_t i, size_t pass)
{
    uint64_t x = raw ^ (raw >> 23) ^ (raw << 17);
    x += (static_cast<uint64_t>(i) + 1) * 0x9e3779b185ebca87ULL;
    x ^= (static_cast<uint64_t>(pass) + 0x51ed2705ULL) * 0x94d049bb133111ebULL;
    acc ^= x + (acc << 6) + (acc >> 2);
    return acc;
}


int main(int argc, char **argv)
{
    const size_t items = read_size_arg(argc, argv, "--items", 8192);
    const size_t passes = read_size_arg(argc, argv, "--passes", 4);
    const bool secret = read_bool_arg(argc, argv, "--secret", false);
    const bool probe_targets = read_bool_arg(argc, argv, "--probe-targets", false);
    const size_t probe_passes = read_size_arg(argc, argv, "--probe-passes", 1);
    const size_t evict_kb = read_size_arg(argc, argv, "--evict-kb", 0);
    const bool reset_after_evict =
        read_bool_arg(argc, argv, "--reset-after-evict", true);
    const bool split_probe_stats =
        read_bool_arg(argc, argv, "--split-probe-stats", false);
    const bool use_m5 = read_bool_arg(argc, argv, "--m5", true);
    const uint64_t seed =
        read_u64_arg(argc, argv, "--seed", 0x243f6a8885a308d3ULL);
    rng_state = seed;

    std::vector<TargetLine> targets(items);
    std::vector<uintptr_t> words(items);
    std::vector<size_t> perm(items);
    std::vector<uint64_t> evict((evict_kb * 1024) / sizeof(uint64_t));

    for (size_t i = 0; i < items; ++i) {
        perm[i] = i;
        for (size_t j = 0; j < 8; ++j) {
            targets[i].payload[j] =
                (i + 1) * 0x100000001b3ULL ^
                (j + 0x9e37ULL) * 0x517cc1b727220a95ULL;
        }
    }

    for (size_t i = items - 1; i > 0; --i) {
        const size_t j = static_cast<size_t>(next_rand() % (i + 1));
        const size_t tmp = perm[i];
        perm[i] = perm[j];
        perm[j] = tmp;
    }

    for (size_t i = 0; i < items; ++i) {
        if (secret) {
            words[i] = reinterpret_cast<uintptr_t>(&targets[perm[i]]);
        } else {
            const uint64_t junk =
                0xffff000000000000ULL |
                ((static_cast<uint64_t>(i) * 0x45d9f3bULL) ^
                 next_rand() ^ (seed << 1));
            words[i] = static_cast<uintptr_t>(junk);
        }
    }

    for (size_t i = 0; i < evict.size(); ++i) {
        evict[i] = 0xffff000000000000ULL ^
                   (static_cast<uint64_t>(i) * 0xd6e8feb86659fd93ULL) ^
                   (seed >> ((i % 7) + 1));
    }

    volatile uint64_t checksum = 0x6a09e667f3bcc909ULL ^ seed;
    volatile uintptr_t *stream = words.data();
    volatile uint64_t *evict_stream = evict.data();

    if (use_m5) {
        std::printf("DMP_ORACLE_RESET\n");
        m5_reset_stats(0, 0);
    }

    for (size_t i = 0; i < evict.size(); ++i) {
        checksum = mix_word(checksum, evict_stream[i], i, 0xeeeeULL);
    }

    if (use_m5 && reset_after_evict && !evict.empty()) {
        std::printf("DMP_ORACLE_POST_EVICT_RESET\n");
        m5_reset_stats(0, 0);
    }

    for (size_t pass = 0; pass < passes; ++pass) {
        for (size_t i = 0; i < items; ++i) {
            const uintptr_t raw = stream[(i * 17 + pass * 31) % items];
            checksum = mix_word(checksum, static_cast<uint64_t>(raw), i, pass);
        }
    }

    if (use_m5 && probe_targets && split_probe_stats) {
        std::printf("DMP_ORACLE_SCAN_DUMP\n");
        m5_dump_stats(0, 0);
        std::printf("DMP_ORACLE_PROBE_RESET\n");
        m5_reset_stats(0, 0);
    }

    if (probe_targets) {
        for (size_t pass = 0; pass < probe_passes; ++pass) {
            for (size_t i = 0; i < items; ++i) {
                const size_t idx = perm[(i * 17 + pass * 31) % items];
                const TargetLine *line = &targets[idx];
                checksum = mix_word(
                    checksum,
                    line->payload[(i + pass) & 7] ^
                        reinterpret_cast<uintptr_t>(line),
                    i,
                    pass + 0x50524f4245ULL);
            }
        }
    }

    if (use_m5) {
        std::printf("DMP_ORACLE_DUMP\n");
        m5_dump_stats(0, 0);
    }

    const uintptr_t sample0 = items ? words[0] : 0;
    const uintptr_t sample1 = items > 1 ? words[1] : sample0;
    std::printf(
        "DMP_ORACLE_RESULT items=%zu passes=%zu secret=%u "
        "probe_targets=%u probe_passes=%zu evict_kb=%zu "
        "reset_after_evict=%u split_probe_stats=%u seed=0x%016" PRIx64
        " sample0=0x%016" PRIxPTR " sample1=0x%016" PRIxPTR
        " checksum=0x%016" PRIx64 "\n",
        items,
        passes,
        secret ? 1 : 0,
        probe_targets ? 1 : 0,
        probe_passes,
        evict_kb,
        reset_after_evict ? 1 : 0,
        split_probe_stats ? 1 : 0,
        seed,
        sample0,
        sample1,
        static_cast<uint64_t>(checksum));
    return checksum == 0 ? 2 : 0;
}
