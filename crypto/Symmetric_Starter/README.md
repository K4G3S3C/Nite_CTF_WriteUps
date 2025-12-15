# Symmetric Starter / \ Cryptography

- CTF: NiteCTF 2025
- Category: Cryptography
- Author: K4G3SEC
- Solver: W4ST3D
- Flag: `nite{wh00ps_l34k3d_2_mUch}`

---

## Challenge
> "Decrypt the flag encrypted with a custom stream cipher using a side-channel leak."

We are given an encryption script `chal.py` that uses a 128-bit rotating nonce to generate a keystream. The output file `out.txt` provides the ciphertext and a "shifts" string that leaks internal state bits.

---

## Overview
- **Cipher**: Custom stream cipher. State updates via `nonce = (nonce + shifts) & mask` and `rol(nonce, 3)`.
- **Leak**: The `shifts` value is a concatenation of the MSB of the nonce at each step.
- **Goal**: Recover the initial nonce (Key) to decrypt the ciphertext.

---

## Exploitation Steps
1. **Model the State**: The state transition is linear/bitwise. We can use a bit-vector solver.
2. **Z3 Solver**:
   - Declare a 128-bit BitVec `nonce_0`.
   - Simulate the 128 steps of the cipher symbolically.
   - **Constraint**: At step `i`, `nonce` MSB must equal the `i-th` bit of the leaked `shifts`.
3. **Solve**: Z3 satisfies the constraints to find the one unique `nonce_0` that matches the leak.
4. **Decrypt**: Re-run the generator with the recovered key to XOR out the flag.

---
