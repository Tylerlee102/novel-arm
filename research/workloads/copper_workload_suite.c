#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Node {
    uint64_t value;
    struct Node *next;
    struct Node *left;
    struct Node *right;
} Node;

static uint64_t mix(uint64_t x) {
    x ^= x >> 33;
    x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33;
    x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return x;
}

static size_t input_n(const char *input) {
    if (strcmp(input, "small") == 0) return 256;
    if (strcmp(input, "large") == 0) return 4096;
    return 1024;
}

static Node *nodes_new(size_t n) {
    Node *nodes = (Node *)calloc(n, sizeof(Node));
    if (!nodes) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }
    for (size_t i = 0; i < n; i++) nodes[i].value = mix(i + 1);
    return nodes;
}

static uint64_t linked_list(size_t n) {
    Node *nodes = nodes_new(n);
    for (size_t i = 0; i + 1 < n; i++) nodes[i].next = &nodes[i + 1];
    uint64_t sum = 0;
    for (Node *p = &nodes[0]; p; p = p->next) sum ^= p->value;
    free(nodes);
    return sum;
}

static uint64_t tree_traversal_rec(Node *node) {
    if (!node) return 0;
    return node->value ^ tree_traversal_rec(node->left) ^ (tree_traversal_rec(node->right) << 1);
}

static uint64_t tree_traversal(size_t n) {
    Node *nodes = nodes_new(n);
    for (size_t i = 0; i < n; i++) {
        size_t left = 2 * i + 1;
        size_t right = 2 * i + 2;
        if (left < n) nodes[i].left = &nodes[left];
        if (right < n) nodes[i].right = &nodes[right];
    }
    uint64_t sum = tree_traversal_rec(&nodes[0]);
    free(nodes);
    return sum;
}

static uint64_t hash_table_chaining(size_t n) {
    size_t buckets = n / 8 + 1;
    Node *nodes = nodes_new(n);
    Node **table = (Node **)calloc(buckets, sizeof(Node *));
    if (!table) exit(2);
    for (size_t i = 0; i < n; i++) {
        size_t b = mix(i) % buckets;
        nodes[i].next = table[b];
        table[b] = &nodes[i];
    }
    uint64_t sum = 0;
    for (size_t b = 0; b < buckets; b++) {
        for (Node *p = table[b]; p; p = p->next) sum += p->value ^ b;
    }
    free(table);
    free(nodes);
    return sum;
}

static uint64_t graph_adjacency_walk(size_t n) {
    size_t edges = n * 3;
    size_t *adj = (size_t *)malloc(edges * sizeof(size_t));
    if (!adj) exit(2);
    for (size_t i = 0; i < edges; i++) adj[i] = mix(i) % n;
    uint64_t sum = 0;
    size_t v = 0;
    for (size_t step = 0; step < edges; step++) {
        v = adj[(v * 3 + step) % edges];
        sum ^= mix(v + step);
    }
    free(adj);
    return sum;
}

static uint64_t patricia(size_t n) {
    Node *nodes = nodes_new(n);
    for (size_t i = 1; i < n; i++) {
        Node *p = &nodes[0];
        uint64_t key = mix(i);
        for (int bit = 0; bit < 12; bit++) {
            if ((key >> bit) & 1ULL) {
                if (!p->right) p->right = &nodes[i];
                p = p->right;
            } else {
                if (!p->left) p->left = &nodes[i];
                p = p->left;
            }
        }
        p->value ^= key;
    }
    uint64_t sum = tree_traversal_rec(&nodes[0]);
    free(nodes);
    return sum;
}

static uint64_t array_scan(size_t n) {
    uint64_t *a = (uint64_t *)malloc(n * sizeof(uint64_t));
    if (!a) exit(2);
    for (size_t i = 0; i < n; i++) a[i] = mix(i);
    uint64_t sum = 0;
    for (size_t i = 0; i < n; i++) sum += a[i];
    free(a);
    return sum;
}

static uint64_t matrix_or_array_loop(size_t n) {
    size_t side = 1;
    while (side * side < n) side++;
    uint64_t *m = (uint64_t *)malloc(side * side * sizeof(uint64_t));
    if (!m) exit(2);
    for (size_t i = 0; i < side * side; i++) m[i] = i + 1;
    uint64_t sum = 0;
    for (size_t r = 0; r < side; r++) {
        for (size_t c = 0; c < side; c++) sum += m[r * side + c] * (c + 1);
    }
    free(m);
    return sum;
}

static uint64_t compute_heavy_low_memory(size_t n) {
    uint64_t x = 0x12345678abcdefULL;
    for (size_t i = 0; i < n * 100; i++) x = mix(x + i);
    return x;
}

static uint64_t random_non_pointer_access(size_t n) {
    uint64_t *a = (uint64_t *)malloc(n * sizeof(uint64_t));
    if (!a) exit(2);
    for (size_t i = 0; i < n; i++) a[i] = mix(i);
    uint64_t sum = 0;
    for (size_t i = 0; i < n; i++) sum ^= a[mix(i) % n];
    free(a);
    return sum;
}

static uint64_t pointer_chain_variant(size_t n, size_t stride, size_t passes) {
    Node *nodes = nodes_new(n);
    for (size_t i = 0; i < n; i++) nodes[i].next = &nodes[(i + stride) % n];
    uint64_t sum = 0;
    Node *p = &nodes[0];
    for (size_t i = 0; i < n * passes; i++) {
        sum ^= p->value;
        p = p->next;
    }
    free(nodes);
    return sum;
}

static uint64_t mixed_pointer_array(size_t n) {
    return pointer_chain_variant(n, 7, 2) ^ array_scan(n);
}

static uint64_t noisy_allocation_pattern(size_t n) {
    uint64_t sum = 0;
    for (size_t i = 0; i < n / 4 + 1; i++) {
        size_t count = 8 + (mix(i) % 32);
        Node *nodes = nodes_new(count);
        for (size_t j = 0; j < count; j++) sum ^= nodes[j].value;
        free(nodes);
    }
    return sum;
}

static uint64_t branchy_pointer_chains(size_t n) {
    Node *nodes = nodes_new(n);
    for (size_t i = 0; i < n; i++) {
        nodes[i].left = &nodes[(i * 3 + 1) % n];
        nodes[i].right = &nodes[(i * 7 + 5) % n];
    }
    uint64_t sum = 0;
    Node *p = &nodes[0];
    for (size_t i = 0; i < n * 2; i++) {
        sum ^= p->value;
        p = ((sum >> (i % 13)) & 1ULL) ? p->left : p->right;
    }
    free(nodes);
    return sum;
}

static uint64_t run_one(const char *name, size_t n) {
    if (strcmp(name, "linked_list") == 0) return linked_list(n);
    if (strcmp(name, "tree_traversal") == 0) return tree_traversal(n);
    if (strcmp(name, "hash_table_chaining") == 0) return hash_table_chaining(n);
    if (strcmp(name, "graph_adjacency_walk") == 0) return graph_adjacency_walk(n);
    if (strcmp(name, "patricia") == 0) return patricia(n);
    if (strcmp(name, "array_scan") == 0) return array_scan(n);
    if (strcmp(name, "matrix_or_array_loop") == 0) return matrix_or_array_loop(n);
    if (strcmp(name, "compute_heavy_low_memory") == 0) return compute_heavy_low_memory(n);
    if (strcmp(name, "random_non_pointer_access") == 0) return random_non_pointer_access(n);
    if (strcmp(name, "short_pointer_chains") == 0) return pointer_chain_variant(n, 3, 4);
    if (strcmp(name, "long_pointer_chains") == 0) return pointer_chain_variant(n, 17, 4);
    if (strcmp(name, "mixed_pointer_array") == 0) return mixed_pointer_array(n);
    if (strcmp(name, "noisy_allocation_pattern") == 0) return noisy_allocation_pattern(n);
    if (strcmp(name, "branchy_pointer_chains") == 0) return branchy_pointer_chains(n);
    fprintf(stderr, "unknown benchmark: %s\n", name);
    exit(1);
}

int main(int argc, char **argv) {
    const char *benchmark = argc > 1 ? argv[1] : "linked_list";
    const char *input = argc > 2 ? argv[2] : "small";
    size_t n = input_n(input);
    uint64_t checksum = run_one(benchmark, n);
    printf("%s,%s,%llu\n", benchmark, input, (unsigned long long)checksum);
    return 0;
}
