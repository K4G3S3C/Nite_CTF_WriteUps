# Stronk Rabin / \ Cryptography

- CTF: NiteCTF 2025
- Category: Cryptography
- Author: K4G3SEC
- Solver: W4ST3D
- Flag: `nite{rabin_stronk?_no_r4bin_brok3n}`

---

## Challenge
> "Break a Rabin Cryptosystem variant using a decryption Oracle."

We are given a cryptography service where $C = m^2 \pmod n$. To get the flag, we must recover the plaintext of a given ciphertext. The service provides a Decryption Oracle `DEC(c)` that returns one of the 4 square roots of `c`.

---

## Overview
- **System**: Rabin Cryptosystem ($n = p \cdot q \cdots$).
- **Oracle**: We can send any `c` to get $\sqrt{c} \pmod n$.
- **Factoring**: The Rabin decryption function is equivalent to factoring. If we ask for the root of $x^2 \pmod n$ and get back $y \neq \pm x$, then $\gcd(x-y, n)$ reveals a factor of $n$.

---

## Root Cause
The presence of a `DEC` oracle for Rabin encryption breaks the security of the key. By sending chosen values, we can split the modulus `n` into its prime factors. Once `n` is factored, we can compute square roots ourselves using the Chinese Remainder Theorem (CRT).

---

## Exploitation Steps
1. **Recover Modulus**: Use the encryption oracle `ENC(m)` to find `n` via GCD of $m^2 - c$.
2. **Factor n**:
   - Pick random $r$.
   - Compute $c = r^2 \pmod n$.
   - Ask `DEC(c)` to get root $x$.
   - Compute $\gcd(r - x, n)$. If $x \neq \pm r$, we find a factor.
   - Repeat until `n` is fully factored into primes.
3. **Decrypt Target**:
   - Compute the 4 (or 16) square roots of the challenge ciphertext `C` using the prime factors.
   - Search the roots for the `nite{` pattern.

---
