# Smol Fan / \ Cryptography

- CTF: NiteCTF 2025
- Category: Cryptography
- Author: K4G3SEC
- Solver: W4ST3D
- Flag: `nite{1'm_a_smol_f4n_of_LLL!}`

---

## Challenge
> "Recover the private key from a signing oracle with restricted nonce size."

The server allows signing arbitrary messages but uses a weak nonce generator. We must recover the private key and forge a signature for the restricted message `"gimme_flag"`.

---

## Overview
- **Curve**: P-256 (Secp256r1).
- **Vulnerability**: The nonce $k$ is explicitly capped at 200 bits ($k < 2^{200}$), while the order $n$ is $\approx 2^{256}$.
- **Impact**: The 56-bit bias in the nonce is sufficient for a Lattice Attack.

---

## Root Cause
ECDSA nonces must be uniformly random over $[1, n-1]$. Restricting $k$ to a smaller range leaks information about the private key with every signature. Given enough signatures (approx 10), we can recover the key.

---

## Exploitation Steps
1. **Harvest Signatures**: Collect ~10 signatures from the server.
2. **Lattice Setup**:
   - Construct a standard HNP lattice matrix.
   - Scale rows by $n$ and $2^{BITS}$ to balance the weights.
3. **LLL Reduction**: Run the LLL algorithm to find the vector corresponding to the private key `d`.
4. **Forgery**:
   - Compute `s` for `"gimme_flag"` using the recovered `d`.
   - Send the forged pair `(r, s)` to the server.
5. **Profit**: The server validates the forgery and returns the flag.

---
