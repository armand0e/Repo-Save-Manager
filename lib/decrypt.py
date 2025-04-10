from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad
from Crypto.Hash import HMAC, SHA1
# import gzip # Keep commented unless gzip is needed

def decrypt_es3(data, password):
    """Decrypt raw bytes using AES-128-CBC with PBKDF2 key derivation"""
    
    # Extract the IV (salt) from the first 16 bytes
    iv = data[:16]
    encrypted_data_only = data[16:] # Ciphertext only
    print(f"[DEBUG decrypt] Extracted IV (Salt): {iv.hex()}") # DEBUG
    
    # Derive the key using PBKDF2 with password and IV as salt
    key = PBKDF2(password, iv, dkLen=16, count=100, prf=lambda p, s: HMAC.new(p, s, SHA1).digest())
    print(f"[DEBUG decrypt] Derived key: {key.hex()}") # DEBUG

    # Create cipher
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # Decrypt data
    try:
        print(f"[DEBUG decrypt] Attempting cipher.decrypt on {len(encrypted_data_only)} bytes...") # DEBUG
        decrypted_padded_data = cipher.decrypt(encrypted_data_only)
        print("[DEBUG decrypt] Decryption successful (before unpad)") # DEBUG
        
        # Check for optional Gzip compression (match reference)
        # if decrypted_padded_data[:2] == b'\x1f\x8b': # GZip magic number
        #    print("[DEBUG decrypt] Gzip detected, decompressing...") # DEBUG
        #    decrypted_padded_data = gzip.decompress(decrypted_padded_data)
        
        print("[DEBUG decrypt] Attempting unpad...") # DEBUG
        unpadded_data = unpad(decrypted_padded_data, AES.block_size) 
        print("[DEBUG decrypt] Unpadding successful") # DEBUG
        return unpadded_data.decode('utf-8')
    except ValueError as pad_error:
        print(f"[DEBUG decrypt] ValueError during unpad: {pad_error}") # DEBUG
        raise ValueError(f"Padding is incorrect. Key derived from password might be wrong, or file is corrupt. Details: {pad_error}") # Re-raise with more context