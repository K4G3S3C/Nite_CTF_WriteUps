
import struct
import math

def read_vectors(filename, n_vectors, dim):
    with open(filename, 'rb') as f:
        f.read(10)
        f.seek(8)
        header_len = struct.unpack('<H', f.read(2))[0]
        f.read(header_len)
        data_bytes = f.read()
        fmt = '<' + 'd' * (n_vectors * dim)
        values = struct.unpack(fmt, data_bytes)
    vectors = []
    for i in range(n_vectors):
        vec = values[i*dim : (i+1)*dim]
        vectors.append(vec)
    return vectors

def cosine_similarity(v1, v2):
    dot = sum(a*b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a*a for a in v1))
    norm2 = math.sqrt(sum(a*a for a in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

vectors = read_vectors('/Users/ref/Desktop/CTF/ai/antakshari/handout/latent_vectors.npy', 201, 64)

cluster = [134, 189, 108, 37, 177] # Neighbors of 3
# Also include 3? If 3 is movie, we look for actors.
# Actors should be connected to 3.
# But maybe one actor is not directly connected to 3 but connected to other actors? (Unlikely for "movie cast" unless latent space is weird).
# But let's check neighbors of the cluster members.

print(f"Expanding cluster: {cluster}")
candidates = {}
for member in cluster:
    for i, v in enumerate(vectors):
        if i in cluster or i == 3: continue
        s = cosine_similarity(vectors[member], v)
        if s > 0.4: # Check clear connections
            if i not in candidates: candidates[i] = []
            candidates[i].append((member, s))

print("\nPotential 6th members (connected to cluster members):")
for cand, connections in candidates.items():
    print(f"Node {cand}:")
    for mem, s in connections:
        print(f"  - via {mem}: {s:.4f}")
    # Check connect to 3
    s3 = cosine_similarity(vectors[3], vectors[cand])
    print(f"  - via 3: {s3:.4f}")

