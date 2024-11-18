import os, re

PNG_HEADER = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52])
HEADER_LEN = 16
SIGNATURE = bytes.fromhex("5250474d56000000")
VERSION = bytes.fromhex("000301")
REMAIN = bytes.fromhex("0000000000")

class MVDecryptor:
    def __init__(self, encryption_key):
        if self.is_valid_encryption_key(encryption_key):
            self.encryption_key = encryption_key
            self.encryption_code = self.split_encryption_code()
            self.ignore_fake_header = False
        else:
            raise ValueError("Encryption key invalid")
    
    def is_valid_encryption_key(self, key_str):
        return bool(re.fullmatch(r'[a-fA-F0-9]{32}', key_str))

    def split_encryption_code(self):
        return [int(self.encryption_key[i:i+2], 16) for i in range(0, len(self.encryption_key), 2)]

    def build_fake_header(self):
        header_structure = SIGNATURE + VERSION + REMAIN
        return header_structure

    def verify_fake_header(self, file_header):
        fake_header = self.build_fake_header()
        return file_header[:HEADER_LEN] == fake_header

    def xor_bytes(self, data):
        xor_data = bytearray(data)
        for i in range(min(HEADER_LEN, len(xor_data))):
            xor_data[i] ^= self.encryption_code[i % len(self.encryption_code)]
        return xor_data

    def decrypt_file(self, file_path, delete_original=False):
        file_path = str(file_path)
        
        with open(file_path, 'rb') as f:
            data = f.read()

        if not self.ignore_fake_header and self.verify_fake_header(data[:HEADER_LEN]):
            data = data[HEADER_LEN:]
        
        decrypted_data = self.xor_bytes(data)
        _, ext = os.path.splitext(file_path)
        
        if ext == '.rpgmvp':
            output_ext = '.png'
            decrypted_data = PNG_HEADER + decrypted_data[HEADER_LEN:]
        elif ext == '.rpgmvm':
            output_ext = '.m4a'
        elif ext == '.rpgmvo':
            output_ext = '.ogg'
        else:
            raise ValueError("Unrecognized file to decrypt.")
        
        output_path = file_path.replace(ext, output_ext)
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        if delete_original:
            os.remove(file_path)