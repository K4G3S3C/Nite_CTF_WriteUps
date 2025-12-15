#!/usr/bin/env python3
import json
import math
import random
import socket
import ssl
import sys
from typing import List, Tuple


HOST = "stronk.chals.nitectf25.live"
PORT = 1337


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x1, y1 = egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def inv_mod(a: int, m: int) -> int:
    a %= m
    g, x, _ = egcd(a, m)
    if g != 1:
        raise ValueError("inverse does not exist")
    return x % m


def crt_pair(a1: int, m1: int, a2: int, m2: int) -> Tuple[int, int]:
    # assumes gcd(m1,m2)=1
    t = ((a2 - a1) % m2) * inv_mod(m1 % m2, m2) % m2
    x = a1 + m1 * t
    return x % (m1 * m2), m1 * m2


def crt_many(residues: List[int], moduli: List[int]) -> int:
    x, m = residues[0] % moduli[0], moduli[0]
    for a, n in zip(residues[1:], moduli[1:]):
        x, m = crt_pair(x, m, a, n)
    return x


def i2b(x: int) -> bytes:
    if x == 0:
        return b"\x00"
    length = (x.bit_length() + 7) // 8
    return x.to_bytes(length, "big")


def is_probable_prime(n: int, rounds: int = 16) -> bool:
    if n < 2:
        return False
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    # write n-1 = d*2^s
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    def check(a: int) -> bool:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            return True
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                return True
        return False

    # deterministic-ish base set for ~1024-bit is fine probabilistically
    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        if not check(a):
            return False
    return True


class LineClient:
    def __init__(self, host: str, port: int):
        raw = socket.create_connection((host, port), timeout=60)
        ctx = ssl.create_default_context()
        self.sock = ctx.wrap_socket(raw, server_hostname=host)
        self.sock.settimeout(300)
        self.f = self.sock.makefile("rwb", buffering=0)

    def recv_line(self) -> str:
        while True:
            try:
                line = self.f.readline()
            except TimeoutError:
                continue
            if not line:
                raise EOFError("connection closed")
            return line.decode(errors="replace").strip()

    def send_obj(self, obj: dict) -> dict:
        msg = (json.dumps(obj) + "\n").encode()
        self.f.write(msg)
        line = self.recv_line()
        return json.loads(line)

    def call(self, func: str, *args):
        resp = self.send_obj({"func": func, "args": list(args)})
        retn = resp.get("retn")
        if isinstance(retn, str):
            raise RuntimeError(retn)
        return int(retn)


def recover_n(client: LineClient) -> int:
    g = 0
    for _ in range(10):
        m = random.getrandbits(700) | 1
        c = client.call("ENC", m)
        d = m * m - c
        g = math.gcd(g, d)
        if g != 0 and g.bit_length() >= 900:
            break

    # refine to remove accidental common factors
    for _ in range(12):
        m = random.getrandbits(700) | 1
        c = client.call("ENC", m)
        d = m * m - c
        g2 = math.gcd(g, d)
        if g2 != 0:
            g = g2

    if g == 0:
        raise RuntimeError("failed to recover modulus")

    # sanity check: ENC(m) == m^2 mod g
    for _ in range(3):
        m = random.getrandbits(512) | 1
        c = client.call("ENC", m)
        if c != (m * m) % g:
            raise RuntimeError("gcd result does not behave like modulus")

    return g


CAND_T = list(range(-8, 9, 2))


def split_with_dec1(client: LineClient, n: int, target: int) -> List[int]:
    # Recursively split target using gcd(DEC(1)-t, target) where t in {-8,-6,...,8}
    factors: List[int] = []
    stack = [target]
    while stack:
        x = stack.pop()
        if x == 1:
            continue
        if is_probable_prime(x):
            factors.append(x)
            continue

        found = False
        for _ in range(40):
            dec = client.call("DEC", 1)
            for t in CAND_T:
                g = math.gcd((dec - t) % n, x)
                if 1 < g < x:
                    stack.append(g)
                    stack.append(x // g)
                    found = True
                    break
            if found:
                break
        if not found:
            raise RuntimeError("failed to split composite factor using DEC(1)")

    return factors


def recover_primes(client: LineClient, n: int) -> List[int]:
    primes = split_with_dec1(client, n, n)
    primes.sort()
    if len(primes) != 4:
        raise RuntimeError(f"expected 4 primes, got {len(primes)}")
    if math.prod(primes) != n:
        raise RuntimeError("factorization does not multiply back to n")
    return primes


def all_roots_of_C(C: int, primes: List[int]) -> List[int]:
    roots_per_prime = []
    for p in primes:
        r = pow(C, (p + 1) // 4, p)
        roots_per_prime.append((r, (-r) % p))

    roots = []
    for mask in range(16):
        residues = []
        for j in range(4):
            bit = (mask >> j) & 1
            residues.append(roots_per_prime[j][bit])
        roots.append(crt_many(residues, primes))
    # unique
    roots = list(dict.fromkeys([x % math.prod(primes) for x in roots]))
    return roots


def pick_flag_candidate(roots: List[int], n: int) -> int:
    k = (n.bit_length() + 7) // 8
    candidates: List[Tuple[int, int]] = []
    for r in roots:
        if not (n // 2 < r < n):
            continue
        b = (r % n).to_bytes(k, "big")
        pos = b.find(b"nite{")
        if pos != -1:
            candidates.append((pos, r))

    if candidates:
        # prefer earliest occurrence of marker
        candidates.sort(key=lambda t: t[0])
        return candidates[0][1]

    # fallback: just enforce the challenge constraints
    for r in roots:
        if n // 2 < r < n:
            return r
    raise RuntimeError("no plausible root found")


def main() -> None:
    host = HOST
    port = PORT
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])

    client = LineClient(host, port)

    # banner line(s)
    first = client.recv_line()
    if first.startswith("Generating parameters"):
        # server may print a status line then C
        first = client.recv_line()

    obj = json.loads(first)
    C = int(obj["C"])
    print(f"[+] got C ({C.bit_length()} bits)")

    n = recover_n(client)
    print(f"[+] recovered n ({n.bit_length()} bits)")

    primes = recover_primes(client, n)
    print("[+] factored n")

    roots = all_roots_of_C(C, primes)
    print(f"[+] computed {len(roots)} roots")

    flag_int = pick_flag_candidate(roots, n)
    k = (n.bit_length() + 7) // 8
    flag_bytes = (flag_int % n).to_bytes(k, "big")
    start = flag_bytes.find(b"nite{")
    if start != -1:
        end = flag_bytes.find(b"}", start)
        if end != -1:
            print(flag_bytes[start : end + 1].decode("ascii", errors="replace"))
            return
    # last resort: printable view
    print(flag_bytes.decode("utf-8", errors="backslashreplace"))


if __name__ == "__main__":
    main()
