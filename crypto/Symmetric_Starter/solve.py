from z3 import *
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Cipher import AES

def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

# Read output
with open("out.txt", "r") as f:
    ciphertext_hex = f.readline().strip()
    shifts_hex = f.readline().strip()

ciphertext = bytes.fromhex(ciphertext_hex)
shifts_int = int(shifts_hex, 16)
# shifts_int effectively contains all s_i bits.
# It was constructed by shifts += bit.
# s_0 is the first char added.
# So shifts string is "s_0 s_1 ... s_127".
# int(shifts, 2) interprets this as binary number.
# So s_0 is the MSB of shifts_int?
# shifts = "10..." -> int("10...", 2). Yes.
# The length of shifts string is 128 (since 128 blocks).
# Let's verify length.
# ciphertext length 4128 hex chars -> 2064 bytes? 
# Wait. MESSAGE length is 2048 bytes (0x800).
# encrypt() returns joined XORs.
# ciphertext hex length should be 2048 * 2 = 4096.
# Let's check line 1 of out_txt length.
# 4129 bytes in file.
# 4096 chars + 1 newline + 32 chars (shifts) = 4129?
# 4096 + 1 = 4097. 
# 32 hex chars for shifts = 16 bytes = 128 bits.
# 4097 + 32 = 4129. Correct.

SHIFTS_LEN = 128
shifts_bits = f"{shifts_int:0{SHIFTS_LEN}b}"
# shifts_bits[0] corresponds to s_0 (first bit added to string)
# because shifts += bit. int(shifts, 2) makes the first char the MSB.

# Z3 Solver
solver = Solver()
nonce_0 = BitVec('nonce_0', 128)

current_nonce = nonce_0
MOD_MASK = (1 << 128) - 1

current_shifts_str = ""

# Simulate the process symbolically
# Use logic equivalent to the chal.py
# N = 3
# MOD = 1 << 0x80

for i in range(SHIFTS_LEN):
    s_i_observed = int(shifts_bits[i])
    
    # Constraint: MSB of current nonce matches observed bit
    # current_nonce >> 127 == s_i_observed
    solver.add(Extract(127, 127, current_nonce) == s_i_observed)
    
    # Update state for next step
    # shifts += bit
    # The value added to nonce is int(shifts, 2).
    # We know the full sequence of s_i, so we can precalculate the added value
    # int(shifts_so_far, 2)
    # shifts_so_far is shifts_bits[:i+1]
    
    S_i = int(shifts_bits[:i+1], 2)
    
    # nonce = (nonce + S_i) & (MOD-1)
    # in Z3: current_nonce + S_i (BitVec handles overflow automatically mod 2^128)
    nonce_prime = current_nonce + S_i
    
    # nonce = rol(nonce, N)
    # rol 3
    # ((x << 3) | (x >> 125)) 
    # In Z3: RotateLeft(nonce_prime, 3)
    current_nonce = RotateLeft(nonce_prime, 3)

print("Solving for key...")
if solver.check() == sat:
    model = solver.model()
    recovered_key_int = model[nonce_0].as_long()
    recovered_key = long_to_bytes(recovered_key_int, 16)
    print(f"Recovered Key: {recovered_key.hex()}")
    
    # Decrypt
    CIPHER = AES.new(key=recovered_key, mode=AES.MODE_ECB)
    
    # Re-instantiate generator logic to decrypt
    def rol(x, n): return ((x << n) | (x >> (0x80 - n))) & ((1<<128)-1)
    
    def keystream_gen(key):
        nonce = bytes_to_long(key)
        shifts = ""
        while True:
            shifts += f"{nonce >> 127:b}"
            nonce = (nonce + int(shifts, 2)) & ((1<<128)-1)
            yield CIPHER.encrypt(nonce.to_bytes(16, 'big'))
            nonce = rol(nonce, 3)

    ks = keystream_gen(recovered_key)
    decrypted = b""
    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i+16]
        k_block = next(ks)
        decrypted += xor(block, k_block)
        
    print(f"Decrypted: {decrypted}")
    
    # Search for flag
    import re
    flag_match = re.search(rb'nite\{.*?\}', decrypted)
    if flag_match:
        print(f"Flag found: {flag_match.group().decode()}")
    else:
        print("Flag not found in decrypted text.")
        
else:
    print("Unsatisfiable")
