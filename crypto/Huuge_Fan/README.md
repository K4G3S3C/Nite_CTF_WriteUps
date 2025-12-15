# Huuge Fan / \ Cryptography

- CTF: NiteCTF 2025
- Category: Cryptography
- Author: K4G3SEC
- Solver: W4ST3D
- Flag: `nite{1m_^_#ug3_f4n_of_8KZ!!_afa5d267f6ae51da6ab8019d1e}`

---

## Challenge
> "Recover the hidden flag using a customized Digital Signature scheme vulnerable to lattice attacks."

We encounter a signing oracle that uses an ECDSA-like scheme over a finite field. The challenge leaks multiple signatures `(r, s)` and the nonce generation involves a shared prefix.

---

## Overview
- **Scheme**: Signatures are generated as $s = k^{-1}(z + r \cdot d) \pmod n$.
- **Vulnerability**: The nonces $k$ are constructed as `Prefix + Error`, where `Prefix` is constant or shared across a batch, and `Error` is small.
- **Problem Type**: **Hidden Number Problem (HNP)**. Identifying the "hidden" small error term allows recovering the private key `d`.

---

## Root Cause
The nonces `k` are not uniformly random. They share a significant number of Most Significant Bits (MSBs) derived from base conversions. This partial nonce exposure allows modelling the system as a lattice problem (CVP/SVP).

---

## Exploitation Steps
1. **Data Collection**: Gather `(r, s, z)` tuples from the `out.txt`.
2. **Lattice Construction**:
   - Formulate the HNP inequalities: $\alpha \cdot t - u - k \approx 0 \pmod n$.
   - Construct a matrix with basis vectors corresponding to the modular equations and the bounds on the error term.
3. **Reduction**: Use **BKZ** (Block Korkin-Zolotarev) or **LLL** lattice reduction to find the Shortest Vector.
4. **Key Recovery**: The coefficients of the shortest vector reveal the error terms, which in turn solve for the private key `d`.
5. **Decryption**: Use `d` to decrypt the flag.

---
