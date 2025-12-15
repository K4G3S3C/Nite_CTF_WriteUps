import socket
import ssl
import hashlib
import time
import re
from sage.all import *

# Constants
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
K = GF(p)
a = K(0)
b = K(7)
E = EllipticCurve(K, [a, b])
G = E.point((0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
             0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8))
n = E.order()
# n is roughly 2^256
# Nonce k is 200 bits
NONCE_BITS = 200
BOUND = 2**NONCE_BITS

HOST = "smol.chalz.nitectf25.live"
PORT = 1337

class Remote:
    def __init__(self, host, port):
        sock = socket.create_connection((host, int(port)))
        context = ssl.create_default_context()
        # Disable certificate verification if needed for CTF (sometimes self-signed)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.conn = context.wrap_socket(sock, server_hostname=host)
        self.buf = b""
        
    def recv_until(self, delim):
        while delim not in self.buf:
            try:
                chunk = self.conn.recv(4096)
                if not chunk:
                    print("DEBUG: Connection closed")
                    break
                self.buf += chunk
                print(f"DEBUG RECV: {chunk}")
            except socket.timeout:
                print("DEBUG: Timeout")
                break
        
        idx = self.buf.find(delim)
        if idx == -1:
            # Return whatever we have if delim never found (or empty)
            ret = self.buf
            self.buf = b""
            return ret
        
        ret = self.buf[:idx+len(delim)]
        self.buf = self.buf[idx+len(delim):]
        return ret

    def sendline(self, data):
        self.conn.sendall(data + b"\n")
        
    def close(self):
        self.conn.close()

def get_signature(rem):
    # Select 2) Sign a message
    rem.recv_until(b"> ")
    rem.sendline(b"2")
    
    # Send message hex
    msg = b"test_msg" 
    msg_hex = msg.hex().encode()
    rem.recv_until(b"Enter message as hex: ")
    rem.sendline(msg_hex)
    
    # Parse m, a, b
    # Read until double newline or enough content
    # Note: server prints m = ..., a = ..., b = ...
    resp = rem.recv_until(b"b =") 
    resp += rem.recv_until(b"\n\n") 
    
    text = resp.decode()
    
    # Extract m, a, b
    m_match = re.search(r"m = (\d+)", text)
    a_match = re.search(r"a = (\d+)", text)
    b_match = re.search(r"b = (\d+)", text)
    
    if not (m_match and a_match and b_match):
        print("Failed to parse m, a, b")
        return None
        
    m_val = int(m_match.group(1))
    a_val = int(a_match.group(1))
    b_val = int(b_match.group(1))
    
    # Recover r
    r = gcd(a_val - pow(10, 11), m_val)
    if r == 1 or r == m_val:
        # If gcd fails to split properly
        pass
        
    s = m_val // r
    
    # Calculate z
    z = int(hashlib.sha256(msg).hexdigest(), 16)
    
    return (int(r), int(s), int(z))

def solve():
    rem = Remote(HOST, PORT)
    print(f"Connected to {HOST}:{PORT}")
    
    signatures = []
    NUM_SIGS = 10 
    
    print("Collecting signatures...")
    for i in range(NUM_SIGS):
        print(f"Collecting {i+1}/{NUM_SIGS}...")
        sig = get_signature(rem)
        if sig:
            signatures.append(sig)
        else:
            print("Failed to get signature")
            
    # HNP Lattice Attack
    print("Building lattice...")
    
    ts = []
    us = []
    for r, s, z in signatures:
        s_inv = inverse_mod(s, n)
        ts.append((s_inv * z) % n)
        us.append((s_inv * r) % n)
        
    m = len(signatures)
    
    B_upper = 2**NONCE_BITS
    
    mat = Matrix(ZZ, m + 2, m + 1)
    
    scale = n
    weight_d = B_upper
    
    for i in range(m):
        mat[i, i] = n * scale
        
    for i in range(m):
        mat[m, i] = us[i] * scale
        mat[m+1, i] = ts[i] * scale
        
    mat[m, m] = weight_d
    mat[m+1, m] = 0
    
    print("Running LLL...")
    L = mat.LLL()
    
    priv_key_d = None
    
    for row in L:
        last_val = row[m]
        if last_val % weight_d == 0:
            potential_d = abs(last_val // weight_d)
            if potential_d == 0: continue
            
            r0, s0, z0 = signatures[0]
            candidates = [potential_d, n - potential_d] # Just in case
            for cand in candidates:
                try:
                    k_check = (inverse_mod(s0, n) * (z0 + r0 * cand)) % n
                    if k_check < 2**(NONCE_BITS+10): 
                        print(f"Found d: {cand}")
                        priv_key_d = cand
                        break
                except:
                    continue
        if priv_key_d: break
        
    if not priv_key_d:
        print("Failed to find d with lattice reduction.")
        rem.close()
        return

    # Forge Signature
    print("Forging signature for 'gimme_flag'...")
    target_msg = b"gimme_flag"
    z_target = int(hashlib.sha256(target_msg).hexdigest(), 16)
    
    # Standard ECDSA sign
    k_forge = 123456789 
    R_forge = k_forge * G
    r_forge = int(R_forge.x()) % n
    k_inv_forge = inverse_mod(k_forge, n)
    s_forge = (k_inv_forge * (z_target + r_forge * priv_key_d)) % n
    
    print(f"Forged: r={r_forge}, s={s_forge}")
    
    # Submit
    rem.recv_until(b"> ")
    rem.sendline(b"3")
    
    rem.recv_until(b"Enter r: ")
    rem.sendline(str(r_forge).encode())
    rem.recv_until(b"Enter s: ")
    rem.sendline(str(s_forge).encode())
    
    # Read until flag closure
    # Might need to read more lines
    response = rem.recv_until(b"}") 
    print("Response from server:")
    print(response.decode())
    
    rem.close()

if __name__ == "__main__":
    solve()
