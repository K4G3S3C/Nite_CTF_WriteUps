# Antakshari / \ AI

- CTF: NiteCTF 2025
- Category: AI
- Author: K4G3SEC
- Solver: W4ST3D
- Flag: `nite{Diehard_1891771341083729}`

---

## Challenge
> "Identify the hidden movie based on connections between cast members in a latent space."

We are given a `latent_vectors.npy` file representing movies/actors in a high-dimensional space and a partial graph structure. The goal is to find the "6th member" of a specific cluster connected to Node 3.

---

## Overview
- **Data**: `latent_vectors.npy` (201 vectors, 64 dimensions).
- **Structure**: Nodes represents entities (movies/actors).
- **Task**: A cluster of nodes `[134, 189, 108, 37, 177]` is given. We must find a node that is strongly connected (high cosine similarity) to this cluster and also connected to Node 3.
- **Metric**: Cosine Similarity serves as the edge weight/connection strength.

---

## Solution Approach
1. **Load Vectors**: Read the raw binary vectors from the provided numpy file.
2. **Cluster Analysis**: Calculate the centroid or average direction of the given cluster `[134, 189, 108, 37, 177]`.
3. **Similarity Search**:
   - Iterate through all 201 vectors.
   - Calculate Cosine Similarity between each vector and the cluster members.
   - Identify candidates with high similarity (> 0.4).
4. **Graph Intersection**: Filter candidates that also have a strong connection to **Node 3**.
5. **Flag**: The node satisfying these conditions corresponds to the hidden movie/actor, revealing the flag.

---
