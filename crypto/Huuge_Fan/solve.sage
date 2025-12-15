import hashlib
import pathlib
from sage.all import *

# Constants from chall.py
m = 2**446 - 0x8335DC163BB124B65129C96FDE933D8D723A70AADC873D6D54A7BB0D
m_len = len(str(m))
BASE = int(str(m)[:4])
# print(f"Base: {BASE}")

def flip(ele):
    V = ele.parent()
    ele = list(ele)[::-1]
    return V(ele)

def to_integer(vec, be: bool=True):
    # This recreates the logic from chall.py
    if len(vec) == 0:
        return Integer(0)
    # The original uses vec[::-1] if be else vec.
    # But vec is a vector from V, so slicing returns a list usually, but code says "vec.apply_map".
    # vec in chall is a vector in FreeModule. Slicing a vector in sage returns a vector or list?
    # chall.py: `vec = vec[::-1]`.
    
    # We implement integer conversion based on digits in BASE
    # We recover digits directly from n.
    pass

def solve():
    # Read output
    with open("out.txt", "r") as f:
        data_str = f.read()
    
    # Eval with sage context is tricky if string contains sage types?
    # out.txt is pformat output. Integers are python/sage integers. hexadecimal strings.
    # We can probably eval it safely.
    # The structure: list of tuples (n, list of (msg_hex, r, s))
    try:
        data = eval(data_str.replace("Integer", "")) # remove Wrapper if any, but it's plain text numbers
    except:
        # If the file contains raw numbers, eval works.
        # Check if chall.py's pprint/pformat produces `Integer(123)` or just `123`.
        # Usually pprint of sage integers is just numbers.
        data = eval(data_str)

    # Prepare data for HNP
    # We gather (t, u) pairs
    # t = r s^-1 mod m
    # u = z s^-1 - a 10^131 mod m
    
    samples = []
    
    def get_digits(num):
         dd = []
         curr = num
         for _ in range(5):
             dd.append(curr % BASE)
             curr //= BASE
         return dd[::-1]

    for (n_val, signs) in data:
        # Recover prefixes from n_val
        # n = P * Q
        # P = d4 + d3 B + ...
        # Q = d0 + d1 B + ... (or vice versa)
        # B = 1817
        
        # Iterate divisors of n_val
        divs = divisors(Integer(n_val))
        
        found_pair = False
        digits_p = []
        
        for d in divs:
            d_val = Integer(d)
            q_val = Integer(n_val) // d_val
            
            # Optimization: check if d_val is roughly sqrt(n_val)?
            # d_val should have 5 digits in BASE roughly
            # BASE^4 <= d_val < BASE^5.
            # n_val approx BASE^10.
            # So d_val approx BASE^5.
            # Just relying on get_digits logic is safer.
            
            dg_p = get_digits(d_val)
            dg_q = get_digits(q_val)
            
            if dg_p == dg_q[::-1]:
                 digits_p = dg_p
                 found_pair = True
                 break
                 
        if not found_pair:
             # Skip this recording if we can't recover
             continue
            
        # The prefixes are the digits.
        # But which one is v0? From the formula above, v0 is the most significant digit in base expansion.
        # Code: `secret_identity` elements make up parts.
        # `t = V(parts)`. `parts = [d0, d1, d2, d3, d4]`.
        # `to_integer(t)` logic:
        # `vec` reversed -> `[d4, d3, d2, d1, d0]`.
        # `d4 * base^0 + d3 * base^1 + ... + d0 * base^4`.
        # So yes, d0 is MSB as calculated by get_digits.
        
        # Also need to sort inputs?
        # `nonces` were sorted.
        # `secret_identity` came from sorted nonces.
        # So `parts` has sorted prefixes!
        # `d0 <= d1 <= d2 <= d3 <= d4`.
        
        # So we sort the recovered digits to verify matching.
        prefixes = sorted(digits_p)
        
        # Now we have 5 prefixes for the 5 signatures.
        # The signatures in `signs` loop over `nonces` which are sorted.
        # So signature i corresponds to prefix i.
        
        for i in range(5):
            msg_hex, r, s = signs[i]
            prefix = prefixes[i]
            
            # k = prefix * 10^131 + error
            # suffix_len = m_len - 4 = 135 - 4 = 131.
            
            a = prefix * (10**131)
            
            # Setup HNP:
            # k s = z + r d
            # (a + e) s = z + r d
            # e s - r d = z - s a
            # e - r s^-1 d = z s^-1 - a  (mod m)
            # e - t d = u
            
            z = int(hashlib.sha256(bytes.fromhex(msg_hex)).hexdigest(), 16)
            
            r_int = Integer(r)
            s_int = Integer(s)
            
            try:
                s_inv = inverse_mod(s_int, m)
            except:
                continue
                
            # Center the error
            # k = prefix * 10^131 + e
            # e in [0, 10^131)
            # e' = e - offset. offset = 10^131 // 2
            # k = prefix * 10^131 + offset + e'
            # known = prefix * 10^131 + offset
            
            offset = (10**131) // 2
            known = a + offset
            
            # e' - t d = u'
            # u' = z s^-1 - known  (mod m)
            
            t = (r_int * s_inv) % m
            u = (z * s_inv - known) % m
            
            samples.append((t, u))

    # Build Lattice
    # We use subset of samples
    N = 130 # Increase samples
    if len(samples) < N:
        N = len(samples)
        
    subset = samples[:N]
    print(f"Using {N} samples.")
    
    # Standard HNP CVP embedding
    # Matrix rows:
    # (m, 0, ..., 0)
    # ...
    # (0, ..., m, 0)
    # (t1, t2, ..., tN, 1/Scale?) -> 0 in embedding?
    # We use:
    # Basis B corresponding to { v | v = (e1..eN) }? 
    # Use the structure:
    # [ m  0  ... 0  0 ]
    # [ 0  m  ... 0  0 ]
    # ...
    # [ t1 t2 ... tN C ]
    # [ u1 u2 ... uN 0 ]  <-- Target vector to subtract
    
    # Actually, simpler is to put target in the lattice and look for short vector.
    # LLL basis:
    # [ m  0 ... 0  0 ]
    # [ ...          ]
    # [ t1 t2 ... tN 0 ]
    # [ u1 u2 ... uN K ]
    
    # Expected short vector:
    # -1 * row_u + d * row_t + ...
    # = (-u1 + d t1, ..., K) = (-e1, ..., -e2, -K)
    # We pick K approx 10^131.
    
    # K approx size of centered error
    K = (10**131) // 2
    
    dim = N + 2
    M = Matrix(ZZ, dim, dim)
    
    for i in range(N):
        M[i, i] = m
        
    for i in range(N):
        M[N, i] = subset[i][0] # t_i
        M[N+1, i] = subset[i][1] # u_i
        
    M[N+1, N+1] = K
    # M[N, N+1] is 0
    # M[N, N]... wait. 
    # We need to handle the d column scaling? No, we don't hold d in the vector.
    # The combination is `d * row_N - 1 * row_{N+1}`
    # last column: d * 0 - 1 * K = -K.
    # So we recover d implicitly.
    
    # Run BKZ
    print(f"Running BKZ with block size 30 on dim {dim}...")
    L = M.BKZ(block_size=30)
    
    # Check vectors
    found = False
    
    min_norm = Infinity
    
    for row in L:
        nrm = float(row.norm())
        if nrm < min_norm and nrm > 0:
            min_norm = nrm
            
        # Check possible e values
        # Last element should be +/- K
        last = abs(row[N+1])
        
        # print(f"Row norm: {nrm}, last: {last}, K: {K}")

        if last > 0 and last % K == 0:
            scale = row[N+1] // K
            print(f"Found vector with scale {scale}. Norm: {nrm}")
            
            # vec = scale * (e1, ..., K)  (approximately)
            # Actually vec = scale * Target + LatticeVectors.
            # But LatticeVectors have 0 at end.
            # So vec = scale * Target + vectors in (m...)(t...).
            # Modulo m, vec = scale * (e1, ..., eN, K)?
            # Yes, because lattice vectors are 0 mod m in the first N coords?
            # No. Lattice is:
            # (m, 0)
            # (t, u, 0) -> this row has t in first col.
            # Wait, diagonal matrix M has m in [i,i].
            # Target row has (t, u, K)?
            # No, my matrix was:
            # (m, 0.., 0)
            # ...
            # (t1, t2.., 0)
            # (u1, u2.., K)
            
            # So target row is R_{N+1} = (u, K).
            # Other rows R_N = (t, 0).
            # R_i = (m, 0).
            
            # v = c * R_{N+1} + d * R_N + ...
            # v = c * (u, K) + d * (t, 0) + ...
            # v = (c u + d t + k m, c K).
            # v_i = c u_i + d t_i + k m. (using scalar d for row N, but actually row N is vector t)
            # Wait, row N is (t1, t2, ..., tN, 0).
            # It's multiplied by scalar X.
            # v = c u + X t + k m.
            # v_i - c u_i = X t_i (mod m).
            # X = (v_i - c u_i) * t_i^-1.
            # X corresponds to 'd'.
            # So d = X.
            # We just need to recover X.
            
            # Pick i=0
            v0 = row[0]
            t0, u0 = subset[0]
            
            # X = (v0 - scale * u0) * t0^-1  (mod m)
            
            d_cand = ((v0 - scale * u0) * inverse_mod(t0, m)) % m
            
            try:
                num = int(d_cand)
                flag = num.to_bytes((num.bit_length() + 7) // 8, 'big')
                if b"nite" in flag:
                    print(f"Flag found: {flag}")
                    found = True
                    break
            except:
                pass
                
    if not found:
        print("Flag not found with current parameters.")
        print(f"Minimum norm found: {min_norm}")
        expected = sqrt(dim) * (m**(N/dim)) * (K**(1/dim))
        print(f"Expected Min Norm (Gaussian): {float(expected)}")

if __name__ == "__main__":
    solve()
