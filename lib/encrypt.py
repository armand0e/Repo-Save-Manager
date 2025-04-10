from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad
from Crypto.Hash import HMAC, SHA1
# import gzip # Keep commented unless gzip is needed
import os

def encrypt_es3(data, password):
    """Encrypt data using AES-128-CBC with PBKDF2 key derivation, returning raw bytes (IV + ciphertext)"""
    
    # Optional Gzip (match reference, default off)
    # if should_gzip:
    #     data = gzip.compress(data)

    # Generate random IV (salt)
    iv = os.urandom(16)

    # Derive key using PBKDF2 with password and IV as salt
    key = PBKDF2(password, iv, dkLen=16, count=100, prf=lambda p, s: HMAC.new(p, s, SHA1).digest())
    # print(f"[DEBUG encrypt] Derived key: {key.hex()}") # Optional debug

    # Create cipher
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # Encrypt data
    padded_data = pad(data, AES.block_size) 
    encrypted_data = cipher.encrypt(padded_data)
    
    # Combine IV and encrypted data
    combined_data = iv + encrypted_data
    
    # Return raw bytes
    return combined_data