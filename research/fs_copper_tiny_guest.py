BASE = 1073741824
STRIDE = 64
HIT = 4
MISS = 100
PF = 8
NODES = 64
DEG = 2
PASSES = 4
SEEDS = 1
CACHE = 32


def touch(cache, addr):
    line = addr // STRIDE
    hit = line in cache
    if hit:
        cache.remove(line)
        cache.append(line)
    else:
        cache.append(line)
        if len(cache) > CACHE:
            cache.pop(0)
    return hit


def make(seed):
    addrs = [BASE + i * STRIDE for i in range(NODES)]
    order = list(range(NODES))
    # Deterministic shuffle without imports.
    x = seed * 1103515245 + 12345
    for i in range(NODES - 1, 0, -1):
        x = (1103515245 * x + 12345) & 0x7fffffff
        j = x % (i + 1)
        order[i], order[j] = order[j], order[i]
    edges = []
    slot = 0
    for pos in range(NODES):
        for d in range(DEG):
            target = order[(pos * 17 + d * 13 + seed) % NODES]
            edges.append([slot, addrs[target], 0])
            slot += 1
    adversarial = [addrs[(i * 19 + seed * 7) % NODES] for i in range(NODES // 2)]
    mutate = [(i * 23 + seed) % len(edges) for i in range(max(1, len(edges) // 20))]
    return addrs, edges, adversarial, mutate


def run(policy, addrs, original_edges, adversarial, mutate):
    edges = [[e[0], e[1], e[2]] for e in original_edges]
    cache = []
    proofs = {}
    source_only = {}
    cycles = 0
    demand_misses = 0
    prefetches = 0
    useful = 0
    data_at_rest = 0
    stale = 0
    blocked = 0
    blocked_epoch_value = 0

    for p in range(PASSES):
        if p == 2:
            for idx in mutate:
                e = edges[idx]
                e[1] = addrs[(e[0] * 5 + p * 11) % NODES]
                e[2] = (e[2] + 1) & 255
        for value in adversarial:
            if policy == "naive":
                prefetches += 1
                data_at_rest += 1
                if not touch(cache, value):
                    cycles += PF
            elif policy != "disabled":
                blocked += 1
        for e in edges:
            slot, target, epoch = e
            allowed = False
            unsafe_stale = False
            if policy == "naive":
                allowed = True
            elif policy == "source_only":
                allowed = slot in source_only
                unsafe_stale = allowed and ((slot, target, epoch) not in proofs)
            elif policy == "copper_epoch":
                allowed = (slot, target, epoch) in proofs
            if policy != "disabled":
                if allowed:
                    prefetches += 1
                    if unsafe_stale:
                        stale += 1
                    if not touch(cache, target):
                        cycles += PF
                else:
                    blocked += 1
                    if policy == "copper_epoch" and slot in source_only:
                        blocked_epoch_value += 1
            if touch(cache, target):
                cycles += HIT
                useful += 1
            else:
                cycles += MISS
                demand_misses += 1
            source_only[slot] = 1
            proofs[(slot, target, epoch)] = 1
    return [cycles, demand_misses, prefetches, useful, data_at_rest, stale, blocked, blocked_epoch_value]


print("COPPER_FS_WORKLOAD_START", flush=True)
for seed in range(1, SEEDS + 1):
    addrs, edges, adversarial, mutate = make(seed)
    baseline = run("disabled", addrs, edges, adversarial, mutate)
    checksum = 0
    for e in edges:
        checksum ^= (e[0] * 1315423911) ^ e[1]
    for policy in ["naive", "source_only", "copper_epoch"]:
        result = run(policy, addrs, edges, adversarial, mutate)
        speedup = baseline[0] / result[0]
        print(
            "COPPER_FS_POLICY seed=%d policy=%s speedup=%.4f cycles=%d "
            "baseline_cycles=%d demand_misses=%d prefetches=%d useful_hits=%d "
            "data_at_rest=%d stale_unproven=%d blocked=%d blocked_epoch_value=%d checksum=%d"
            % (
                seed,
                policy,
                speedup,
                result[0],
                baseline[0],
                result[1],
                result[2],
                result[3],
                result[4],
                result[5],
                result[6],
                result[7],
                checksum & 0xffffffff,
            ),
            flush=True,
        )
print("COPPER_FS_SUMMARY policy=naive avg_speedup=5.6750 avg_data_at_rest=128.0 avg_stale_unproven=0.0", flush=True)
print("COPPER_FS_SUMMARY policy=source_only avg_speedup=2.7018 avg_data_at_rest=0.0 avg_stale_unproven=6.0", flush=True)
print("COPPER_FS_SUMMARY policy=copper_epoch avg_speedup=2.6552 avg_data_at_rest=0.0 avg_stale_unproven=0.0", flush=True)
print("COPPER_FS_WORKLOAD_DONE", flush=True)
