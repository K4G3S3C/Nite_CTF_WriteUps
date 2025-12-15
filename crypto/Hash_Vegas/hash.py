#!/usr/bin/env python3
"""
Hash Vegas CTF Exploit using Hash Length Extension Attack

Vulnerability:
1. Lottery vouchers are created with hash(secret + "username|amount")
2. When buying, one of sha256/sha3_224/sha1 is randomly chosen
3. When redeeming, it tries all three hash functions
4. The amount is parsed by taking the rightmost integer after splitting by '|'

Attack:
1. Buy lottery tickets until we get one (60% chance each time)
2. Use hash length extension on the voucher to append "|1000000000"
3. The hash will still be valid (for sha256 or sha1)
4. The parser will extract 1000000000 as the amount
"""

import socket
import ssl
import re
import hashpumpy
import sys
from sha1_extend import sha1_extend

# Configuration
HOST = 'vegas.chals.nitectf25.live'
PORT = 1337
USERNAME = "A"  # Short username
TARGET_AMOUNT = 1000000000
SECRET_LENGTH = 32  # os.urandom(16).hex() = 32 characters

def recv_until(sock, pattern, timeout=10):
    """Receive data until pattern is found"""
    data = b''
    sock.settimeout(timeout)
    try:
        while pattern not in data:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            # Debug: show what we received
            # print(f"[DEBUG] Received: {chunk[:100]}")
    except socket.timeout:
        print(f"[!] Timeout waiting for pattern: {pattern[:50]}")
        print(f"[!] Received so far: {data[:200]}")
    return data

def send_line(sock, line):
    """Send a line of data"""
    if isinstance(line, str):
        line = line.encode()
    sock.sendall(line + b'\n')

def try_hash_extension(original_data_hex, original_hash_hex, append_data):
    """
    Try hash length extension for both SHA256 and SHA1
    Returns list of (new_data_hex, new_hash_hex, algorithm_name) tuples
    """
    original_data = bytes.fromhex(original_data_hex)
    results = []
    
    # Try SHA256
    try:
        new_hash_sha256, new_data_sha256 = hashpumpy.hashpump(
            original_hash_hex, original_data, append_data, SECRET_LENGTH
        )
        
        if isinstance(new_hash_sha256, bytes):
            new_hash_sha256 = new_hash_sha256.decode()
        
        # Truncate to 20 bytes (40 hex chars) like the server does
        new_hash_sha256_truncated = new_hash_sha256[:40]
        
        results.append((new_data_sha256.hex(), new_hash_sha256_truncated, "SHA256"))
    except Exception as e:
        print(f"[!] SHA256 extension failed: {e}")
    
    # Try SHA1
    try:
        new_hash_sha1, new_data_sha1 = sha1_extend(
            original_hash_hex, original_data, append_data, SECRET_LENGTH
        )
        
        # SHA-1 is already 20 bytes
        results.append((new_data_sha1.hex(), new_hash_sha1, "SHA1"))
    except Exception as e:
        print(f"[!] SHA1 extension failed: {e}")
    
    return results

def main():
    # Create SSL connection
    print("[*] Connecting to server...")
    context = ssl.create_default_context()
    with socket.create_connection((HOST, PORT)) as sock:
        with context.wrap_socket(sock, server_hostname=HOST) as ssock:
            print("[+] Connected!")
            
            # Receive banner and username prompt
            data = recv_until(ssock, b'Enter your username: ')
            # print(data.decode())
            
            # Send username
            print(f"[*] Entering username: {USERNAME}")
            send_line(ssock, USERNAME)
            
            # Wait for menu
            data = recv_until(ssock, b'Enter your choice: ')
            # print(data.decode())
            
            # Buy lottery tickets until we win
            voucher_data = None
            voucher_code = None
            
            for attempt in range(50):
                print(f"[*] Attempt {attempt + 1}: Buying lottery ticket...")
                
                # Choose lottery (option 3)
                send_line(ssock, '3')
                
                # Wait for payment prompt and read it
                data = recv_until(ssock, b'): ')
                
                # Pay $1
                send_line(ssock, '1')
                
                # Read response - wait for the menu again
                response = recv_until(ssock, b'choice: ', timeout=5)
                response_str = response.decode()
                
                # Debug: print the response
                if attempt < 3:  # Only show first few attempts
                    print(f"Response: {response_str[:300]}")
                
                # Check if we won
                if 'You won!' in response_str:
                    print("[+] Won a lottery ticket!")
                    
                    # Extract voucher data and code using regex
                    data_match = re.search(r'Voucher data:\s+([0-9a-f]+)', response_str)
                    code_match = re.search(r'Voucher code:\s+([0-9a-f]+)', response_str)
                    
                    if data_match and code_match:
                        voucher_data = data_match.group(1)
                        voucher_code = code_match.group(1)
                        print(f"[+] Voucher data: {voucher_data}")
                        print(f"[+] Voucher code: {voucher_code}")
                        print(f"[+] Original data: {bytes.fromhex(voucher_data)}")
                        break
                else:
                    print("[-] Lost this round...")
            
            if not voucher_data or not voucher_code:
                print("[-] Failed to get a winning ticket!")
                return
            
            # Perform hash length extension
            print("\n[*] Performing hash length extension attack...")
            append_data = b'|' + str(TARGET_AMOUNT).encode()
            
            extended_vouchers = try_hash_extension(
                voucher_data, voucher_code, append_data
            )
            
            if not extended_vouchers:
                print("[!] Failed to create extended vouchers")
                return
            
            # Try each extended voucher
            for new_data_hex, new_hash, algorithm in extended_vouchers:
                print(f"\n[*] Trying {algorithm} extended voucher...")
                print(f"[*] Extended data: {bytes.fromhex(new_data_hex)[:50]}...")
                print(f"[*] Extended hash: {new_hash}")
                
                # Redeem the voucher with the EXTENDED hash
                send_line(ssock, '4')
                recv_until(ssock, b'code(hex): ')
                send_line(ssock, new_hash)  # Use extended hash, not original!
                recv_until(ssock, b'data(hex): ')
                send_line(ssock, new_data_hex)
                
                response = recv_until(ssock, b'choice: ')
                
                if b'Invalid voucher' not in response:
                    # Success!
                    print(f"\n[+] SUCCESS! {algorithm} voucher was accepted!")
                    print(response.decode())
                    break
                else:
                    print(f"[-] {algorithm} voucher was rejected")
            
            if b'Invalid voucher' in response:
                print("\n[!] All vouchers were rejected - must be SHA3-224")
                print("[!] Exiting - retry with a new connection")
                sys.exit(1)
            
            # Check balance
            print("\n[*] Checking balance...")
            send_line(ssock, '5')
            response = recv_until(ssock, b'choice: ')
            print(response.decode())
            
            # Get flag
            print("\n[*] Getting flag...")
            send_line(ssock, '6')
            response = recv_until(ssock, b'\n')
            print(f"\n{'='*60}")
            print(response.decode())
            
            # Get more output
            try:
                response = recv_until(ssock, b'\n', timeout=2)
                print(response.decode())
                print('='*60)
            except:
                pass
            
            # Exit with success code
            sys.exit(0)

if __name__ == '__main__':
    main()
