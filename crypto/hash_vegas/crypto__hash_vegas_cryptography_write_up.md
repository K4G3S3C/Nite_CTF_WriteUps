# Hash Vegas / \ Cryptography

- CTF: NiteCTF 2025
- Category: Cryptography
- Author: K4G3SEC
- Solver: W4ST3D
- Flag: `nite{9ty%_0f_g4mbler5_qu17_b3f0re_th3y_mak3_1t_big}`

---

## Challenge
> “I think the casino is broken. I bought a ticket, the system said I won, and then my bank account instantly hit zero.”

The service exposes a casino over TLS with multiple games; the exploit targets the Lottery voucher system.

---

## Overview
The Lottery generates vouchers on wins:
- `voucher_data`: hex of `"username|amount"`
- `voucher_code`: first 20 bytes of `hash(secret || voucher_data)`
- Validation tries multiple hashes: SHA‑256 (truncated), SHA3‑224 (truncated), and SHA‑1 (native 20 bytes).
- The amount is parsed from the rightmost `|`‑separated integer.

---

## Root Cause
- Vouchers use raw hash MACs: `hash(secret || data)`.
- Server randomly picks a hash per voucher and truncates non‑SHA‑1 outputs to 20 bytes.
- **SHA‑1** (Merkle–Damgård) is vulnerable to **length extension**, enabling:
  ```
  SHA1(secret || m) → SHA1(secret || m || padding || suffix)
  ```
- The parser trusts the final token as the amount; appending `|1000000000` overrides the original amount.

Result: You can extend a valid SHA‑1 voucher to claim a huge amount while preserving hash validity.

---

## Exploitation Steps
1. Connect and buy lottery tickets until “You won!” appears.
2. Extract `voucher_data` and `voucher_code`.
3. Attempt **SHA‑1 length extension** by appending `|1000000000`:
   - Compute `extended_hash`, `extended_data` using the original `voucher_code` as the starting state.
4. Redeem with the extended pair.
5. If accepted, request the flag.

Note: Only SHA‑1 vouchers are exploitable; given the challenge’s distribution, success is probabilistic.

---

## Exploit Implementation
Recommended script: `fast_exploit.py`
- Automates ticket purchases.
- Performs SHA‑1 length extension with `sha1_extend.py`.
- Redeems and retrieves the flag on success.

Usage:
```bash
python3 fast_exploit.py
```

Dependencies:
- Python 3.11+
- `sha1_extend.py` bundled; optional local testing with `pip install hashpumpy`

---
