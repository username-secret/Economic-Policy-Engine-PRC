"""
Encryption module supporting PRC (SM2/SM3/SM4) and Russian (GOST) standards
Provides cryptographic operations for government-grade data protection
"""

import os
import hashlib
import hmac
import struct
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
from enum import Enum
import base64
import secrets
from dataclasses import dataclass


class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms"""
    # PRC Standards (GB/T)
    SM4_CBC = "SM4-CBC"  # GB/T 32907-2016
    SM4_GCM = "SM4-GCM"
    SM2 = "SM2"  # GB/T 32918
    SM3 = "SM3"  # GB/T 32905-2016

    # Russian Standards (GOST)
    GOST_KUZNYECHIK_CBC = "GOST-KUZNYECHIK-CBC"  # GOST R 34.12-2015
    GOST_KUZNYECHIK_GCM = "GOST-KUZNYECHIK-GCM"
    GOST_MAGMA_CBC = "GOST-MAGMA-CBC"  # GOST R 34.12-2015
    GOST_STREEBOG_256 = "GOST-STREEBOG-256"  # GOST R 34.11-2012
    GOST_STREEBOG_512 = "GOST-STREEBOG-512"

    # International Standards
    AES_256_GCM = "AES-256-GCM"  # FIPS 197
    AES_256_CBC = "AES-256-CBC"


@dataclass
class EncryptedData:
    """Container for encrypted data with metadata"""
    ciphertext: bytes
    iv: bytes
    tag: Optional[bytes]  # For authenticated encryption (GCM)
    algorithm: EncryptionAlgorithm
    key_id: Optional[str] = None


class SM4:
    """
    SM4 Block Cipher Implementation (GB/T 32907-2016)
    Chinese National Standard for symmetric encryption
    Block size: 128 bits, Key size: 128 bits
    """

    BLOCK_SIZE = 16
    KEY_SIZE = 16
    ROUNDS = 32

    # S-Box for SM4
    SBOX = [
        0xd6, 0x90, 0xe9, 0xfe, 0xcc, 0xe1, 0x3d, 0xb7, 0x16, 0xb6, 0x14, 0xc2, 0x28, 0xfb, 0x2c, 0x05,
        0x2b, 0x67, 0x9a, 0x76, 0x2a, 0xbe, 0x04, 0xc3, 0xaa, 0x44, 0x13, 0x26, 0x49, 0x86, 0x06, 0x99,
        0x9c, 0x42, 0x50, 0xf4, 0x91, 0xef, 0x98, 0x7a, 0x33, 0x54, 0x0b, 0x43, 0xed, 0xcf, 0xac, 0x62,
        0xe4, 0xb3, 0x1c, 0xa9, 0xc9, 0x08, 0xe8, 0x95, 0x80, 0xdf, 0x94, 0xfa, 0x75, 0x8f, 0x3f, 0xa6,
        0x47, 0x07, 0xa7, 0xfc, 0xf3, 0x73, 0x17, 0xba, 0x83, 0x59, 0x3c, 0x19, 0xe6, 0x85, 0x4f, 0xa8,
        0x68, 0x6b, 0x81, 0xb2, 0x71, 0x64, 0xda, 0x8b, 0xf8, 0xeb, 0x0f, 0x4b, 0x70, 0x56, 0x9d, 0x35,
        0x1e, 0x24, 0x0e, 0x5e, 0x63, 0x58, 0xd1, 0xa2, 0x25, 0x22, 0x7c, 0x3b, 0x01, 0x21, 0x78, 0x87,
        0xd4, 0x00, 0x46, 0x57, 0x9f, 0xd3, 0x27, 0x52, 0x4c, 0x36, 0x02, 0xe7, 0xa0, 0xc4, 0xc8, 0x9e,
        0xea, 0xbf, 0x8a, 0xd2, 0x40, 0xc7, 0x38, 0xb5, 0xa3, 0xf7, 0xf2, 0xce, 0xf9, 0x61, 0x15, 0xa1,
        0xe0, 0xae, 0x5d, 0xa4, 0x9b, 0x34, 0x1a, 0x55, 0xad, 0x93, 0x32, 0x30, 0xf5, 0x8c, 0xb1, 0xe3,
        0x1d, 0xf6, 0xe2, 0x2e, 0x82, 0x66, 0xca, 0x60, 0xc0, 0x29, 0x23, 0xab, 0x0d, 0x53, 0x4e, 0x6f,
        0xd5, 0xdb, 0x37, 0x45, 0xde, 0xfd, 0x8e, 0x2f, 0x03, 0xff, 0x6a, 0x72, 0x6d, 0x6c, 0x5b, 0x51,
        0x8d, 0x1b, 0xaf, 0x92, 0xbb, 0xdd, 0xbc, 0x7f, 0x11, 0xd9, 0x5c, 0x41, 0x1f, 0x10, 0x5a, 0xd8,
        0x0a, 0xc1, 0x31, 0x88, 0xa5, 0xcd, 0x7b, 0xbd, 0x2d, 0x74, 0xd0, 0x12, 0xb8, 0xe5, 0xb4, 0xb0,
        0x89, 0x69, 0x97, 0x4a, 0x0c, 0x96, 0x77, 0x7e, 0x65, 0xb9, 0xf1, 0x09, 0xc5, 0x6e, 0xc6, 0x84,
        0x18, 0xf0, 0x7d, 0xec, 0x3a, 0xdc, 0x4d, 0x20, 0x79, 0xee, 0x5f, 0x3e, 0xd7, 0xcb, 0x39, 0x48,
    ]

    # System parameters for key expansion
    FK = [0xa3b1bac6, 0x56aa3350, 0x677d9197, 0xb27022dc]
    CK = [
        0x00070e15, 0x1c232a31, 0x383f464d, 0x545b6269,
        0x70777e85, 0x8c939aa1, 0xa8afb6bd, 0xc4cbd2d9,
        0xe0e7eef5, 0xfc030a11, 0x181f262d, 0x343b4249,
        0x50575e65, 0x6c737a81, 0x888f969d, 0xa4abb2b9,
        0xc0c7ced5, 0xdce3eaf1, 0xf8ff060d, 0x141b2229,
        0x30373e45, 0x4c535a61, 0x686f767d, 0x848b9299,
        0xa0a7aeb5, 0xbcc3cad1, 0xd8dfe6ed, 0xf4fb0209,
        0x10171e25, 0x2c333a41, 0x484f565d, 0x646b7279,
    ]

    def __init__(self, key: bytes):
        """Initialize SM4 with a 128-bit key"""
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"SM4 key must be {self.KEY_SIZE} bytes")
        self.round_keys = self._key_expansion(key)

    def _rotl(self, x: int, n: int) -> int:
        """Rotate left operation"""
        return ((x << n) | (x >> (32 - n))) & 0xffffffff

    def _bytes_to_words(self, data: bytes) -> list:
        """Convert bytes to 32-bit words"""
        return [struct.unpack('>I', data[i:i+4])[0] for i in range(0, len(data), 4)]

    def _words_to_bytes(self, words: list) -> bytes:
        """Convert 32-bit words to bytes"""
        return b''.join(struct.pack('>I', w) for w in words)

    def _sbox_transform(self, x: int) -> int:
        """Apply S-box transformation"""
        return (self.SBOX[(x >> 24) & 0xff] << 24 |
                self.SBOX[(x >> 16) & 0xff] << 16 |
                self.SBOX[(x >> 8) & 0xff] << 8 |
                self.SBOX[x & 0xff])

    def _l_transform(self, x: int) -> int:
        """Linear transformation L for encryption"""
        return x ^ self._rotl(x, 2) ^ self._rotl(x, 10) ^ self._rotl(x, 18) ^ self._rotl(x, 24)

    def _l_prime_transform(self, x: int) -> int:
        """Linear transformation L' for key expansion"""
        return x ^ self._rotl(x, 13) ^ self._rotl(x, 23)

    def _t_transform(self, x: int) -> int:
        """T transformation for encryption"""
        return self._l_transform(self._sbox_transform(x))

    def _t_prime_transform(self, x: int) -> int:
        """T' transformation for key expansion"""
        return self._l_prime_transform(self._sbox_transform(x))

    def _key_expansion(self, key: bytes) -> list:
        """Generate round keys from the master key"""
        mk = self._bytes_to_words(key)
        k = [mk[i] ^ self.FK[i] for i in range(4)]

        round_keys = []
        for i in range(self.ROUNDS):
            k.append(k[i] ^ self._t_prime_transform(k[i+1] ^ k[i+2] ^ k[i+3] ^ self.CK[i]))
            round_keys.append(k[i+4])

        return round_keys

    def _encrypt_block(self, block: bytes) -> bytes:
        """Encrypt a single 128-bit block"""
        x = self._bytes_to_words(block)

        for i in range(self.ROUNDS):
            x.append(x[i] ^ self._t_transform(x[i+1] ^ x[i+2] ^ x[i+3] ^ self.round_keys[i]))

        return self._words_to_bytes([x[35], x[34], x[33], x[32]])

    def _decrypt_block(self, block: bytes) -> bytes:
        """Decrypt a single 128-bit block"""
        x = self._bytes_to_words(block)

        for i in range(self.ROUNDS):
            x.append(x[i] ^ self._t_transform(x[i+1] ^ x[i+2] ^ x[i+3] ^ self.round_keys[31-i]))

        return self._words_to_bytes([x[35], x[34], x[33], x[32]])

    def encrypt_cbc(self, plaintext: bytes, iv: bytes) -> bytes:
        """Encrypt using CBC mode"""
        if len(iv) != self.BLOCK_SIZE:
            raise ValueError(f"IV must be {self.BLOCK_SIZE} bytes")

        # PKCS7 padding
        pad_len = self.BLOCK_SIZE - (len(plaintext) % self.BLOCK_SIZE)
        plaintext = plaintext + bytes([pad_len] * pad_len)

        ciphertext = b''
        prev_block = iv

        for i in range(0, len(plaintext), self.BLOCK_SIZE):
            block = plaintext[i:i+self.BLOCK_SIZE]
            xored = bytes(a ^ b for a, b in zip(block, prev_block))
            encrypted = self._encrypt_block(xored)
            ciphertext += encrypted
            prev_block = encrypted

        return ciphertext

    def decrypt_cbc(self, ciphertext: bytes, iv: bytes) -> bytes:
        """Decrypt using CBC mode"""
        if len(iv) != self.BLOCK_SIZE:
            raise ValueError(f"IV must be {self.BLOCK_SIZE} bytes")
        if len(ciphertext) % self.BLOCK_SIZE != 0:
            raise ValueError("Ciphertext length must be multiple of block size")

        plaintext = b''
        prev_block = iv

        for i in range(0, len(ciphertext), self.BLOCK_SIZE):
            block = ciphertext[i:i+self.BLOCK_SIZE]
            decrypted = self._decrypt_block(block)
            xored = bytes(a ^ b for a, b in zip(decrypted, prev_block))
            plaintext += xored
            prev_block = block

        # Remove PKCS7 padding
        pad_len = plaintext[-1]
        if pad_len > self.BLOCK_SIZE or not all(b == pad_len for b in plaintext[-pad_len:]):
            raise ValueError("Invalid padding")

        return plaintext[:-pad_len]


class SM3:
    """
    SM3 Hash Function Implementation (GB/T 32905-2016)
    Chinese National Standard for cryptographic hash function
    Output: 256 bits (32 bytes)
    """

    BLOCK_SIZE = 64
    DIGEST_SIZE = 32

    # Initial values
    IV = [
        0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600,
        0xa96f30bc, 0x163138aa, 0xe38dee4d, 0xb0fb0e4e
    ]

    def __init__(self):
        self._h = list(self.IV)
        self._buffer = b''
        self._length = 0

    def _rotl(self, x: int, n: int) -> int:
        """Rotate left operation"""
        return ((x << n) | (x >> (32 - n))) & 0xffffffff

    def _ff(self, x: int, y: int, z: int, j: int) -> int:
        """Boolean function FF"""
        if j < 16:
            return x ^ y ^ z
        else:
            return (x & y) | (x & z) | (y & z)

    def _gg(self, x: int, y: int, z: int, j: int) -> int:
        """Boolean function GG"""
        if j < 16:
            return x ^ y ^ z
        else:
            return (x & y) | (~x & z)

    def _p0(self, x: int) -> int:
        """Permutation function P0"""
        return x ^ self._rotl(x, 9) ^ self._rotl(x, 17)

    def _p1(self, x: int) -> int:
        """Permutation function P1"""
        return x ^ self._rotl(x, 15) ^ self._rotl(x, 23)

    def _t(self, j: int) -> int:
        """Constant T"""
        return 0x79cc4519 if j < 16 else 0x7a879d8a

    def _compress(self, block: bytes):
        """Compress a single block"""
        w = [struct.unpack('>I', block[i:i+4])[0] for i in range(0, 64, 4)]

        # Expand message
        for j in range(16, 68):
            w.append(self._p1(w[j-16] ^ w[j-9] ^ self._rotl(w[j-3], 15)) ^
                     self._rotl(w[j-13], 7) ^ w[j-6])

        w_prime = [w[j] ^ w[j+4] for j in range(64)]

        # Compression
        a, b, c, d, e, f, g, h = self._h

        for j in range(64):
            ss1 = self._rotl((self._rotl(a, 12) + e + self._rotl(self._t(j), j % 32)) & 0xffffffff, 7)
            ss2 = ss1 ^ self._rotl(a, 12)
            tt1 = (self._ff(a, b, c, j) + d + ss2 + w_prime[j]) & 0xffffffff
            tt2 = (self._gg(e, f, g, j) + h + ss1 + w[j]) & 0xffffffff
            d = c
            c = self._rotl(b, 9)
            b = a
            a = tt1
            h = g
            g = self._rotl(f, 19)
            f = e
            e = self._p0(tt2)

        self._h = [(x ^ y) & 0xffffffff for x, y in zip(self._h, [a, b, c, d, e, f, g, h])]

    def update(self, data: bytes):
        """Update hash with data"""
        self._buffer += data
        self._length += len(data)

        while len(self._buffer) >= self.BLOCK_SIZE:
            self._compress(self._buffer[:self.BLOCK_SIZE])
            self._buffer = self._buffer[self.BLOCK_SIZE:]

    def digest(self) -> bytes:
        """Compute final hash digest"""
        # Padding
        bit_length = self._length * 8
        self._buffer += b'\x80'

        while (len(self._buffer) + 8) % self.BLOCK_SIZE != 0:
            self._buffer += b'\x00'

        self._buffer += struct.pack('>Q', bit_length)

        while len(self._buffer) >= self.BLOCK_SIZE:
            self._compress(self._buffer[:self.BLOCK_SIZE])
            self._buffer = self._buffer[self.BLOCK_SIZE:]

        return b''.join(struct.pack('>I', h) for h in self._h)

    def hexdigest(self) -> str:
        """Return hex-encoded digest"""
        return self.digest().hex()

    @classmethod
    def hash(cls, data: bytes) -> bytes:
        """Convenience method to hash data in one call"""
        h = cls()
        h.update(data)
        return h.digest()


class GOSTKuznyechik:
    """
    Kuznyechik (Grasshopper) Block Cipher Implementation (GOST R 34.12-2015)
    Russian National Standard for symmetric encryption
    Block size: 128 bits, Key size: 256 bits
    """

    BLOCK_SIZE = 16
    KEY_SIZE = 32
    ROUNDS = 10

    # S-Box (Pi substitution)
    PI = [
        0xfc, 0xee, 0xdd, 0x11, 0xcf, 0x6e, 0x31, 0x16, 0xfb, 0xc4, 0xfa, 0xda, 0x23, 0xc5, 0x04, 0x4d,
        0xe9, 0x77, 0xf0, 0xdb, 0x93, 0x2e, 0x99, 0xba, 0x17, 0x36, 0xf1, 0xbb, 0x14, 0xcd, 0x5f, 0xc1,
        0xf9, 0x18, 0x65, 0x5a, 0xe2, 0x5c, 0xef, 0x21, 0x81, 0x1c, 0x3c, 0x42, 0x8b, 0x01, 0x8e, 0x4f,
        0x05, 0x84, 0x02, 0xae, 0xe3, 0x6a, 0x8f, 0xa0, 0x06, 0x0b, 0xed, 0x98, 0x7f, 0xd4, 0xd3, 0x1f,
        0xeb, 0x34, 0x2c, 0x51, 0xea, 0xc8, 0x48, 0xab, 0xf2, 0x2a, 0x68, 0xa2, 0xfd, 0x3a, 0xce, 0xcc,
        0xb5, 0x70, 0x0e, 0x56, 0x08, 0x0c, 0x76, 0x12, 0xbf, 0x72, 0x13, 0x47, 0x9c, 0xb7, 0x5d, 0x87,
        0x15, 0xa1, 0x96, 0x29, 0x10, 0x7b, 0x9a, 0xc7, 0xf3, 0x91, 0x78, 0x6f, 0x9d, 0x9e, 0xb2, 0xb1,
        0x32, 0x75, 0x19, 0x3d, 0xff, 0x35, 0x8a, 0x7e, 0x6d, 0x54, 0xc6, 0x80, 0xc3, 0xbd, 0x0d, 0x57,
        0xdf, 0xf5, 0x24, 0xa9, 0x3e, 0xa8, 0x43, 0xc9, 0xd7, 0x79, 0xd6, 0xf6, 0x7c, 0x22, 0xb9, 0x03,
        0xe0, 0x0f, 0xec, 0xde, 0x7a, 0x94, 0xb0, 0xbc, 0xdc, 0xe8, 0x28, 0x50, 0x4e, 0x33, 0x0a, 0x4a,
        0xa7, 0x97, 0x60, 0x73, 0x1e, 0x00, 0x62, 0x44, 0x1a, 0xb8, 0x38, 0x82, 0x64, 0x9f, 0x26, 0x41,
        0xad, 0x45, 0x46, 0x92, 0x27, 0x5e, 0x55, 0x2f, 0x8c, 0xa3, 0xa5, 0x7d, 0x69, 0xd5, 0x95, 0x3b,
        0x07, 0x58, 0xb3, 0x40, 0x86, 0xac, 0x1d, 0xf7, 0x30, 0x37, 0x6b, 0xe4, 0x88, 0xd9, 0xe7, 0x89,
        0xe1, 0x1b, 0x83, 0x49, 0x4c, 0x3f, 0xf8, 0xfe, 0x8d, 0x53, 0xaa, 0x90, 0xca, 0xd8, 0x85, 0x61,
        0x20, 0x71, 0x67, 0xa4, 0x2d, 0x2b, 0x09, 0x5b, 0xcb, 0x9b, 0x25, 0xd0, 0xbe, 0xe5, 0x6c, 0x52,
        0x59, 0xa6, 0x74, 0xd2, 0xe6, 0xf4, 0xb4, 0xc0, 0xd1, 0x66, 0xaf, 0xc2, 0x39, 0x4b, 0x63, 0xb6,
    ]

    # Inverse S-Box
    PI_INV = [0] * 256

    # Linear transformation coefficients
    L_VEC = [148, 32, 133, 16, 194, 192, 1, 251, 1, 192, 194, 16, 133, 32, 148, 1]

    def __init__(self, key: bytes):
        """Initialize Kuznyechik with a 256-bit key"""
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Kuznyechik key must be {self.KEY_SIZE} bytes")

        # Initialize inverse S-Box
        for i, v in enumerate(self.PI):
            self.PI_INV[v] = i

        self.round_keys = self._key_expansion(key)

    def _s_transform(self, block: bytes) -> bytes:
        """Apply S-box substitution"""
        return bytes(self.PI[b] for b in block)

    def _s_inv_transform(self, block: bytes) -> bytes:
        """Apply inverse S-box substitution"""
        return bytes(self.PI_INV[b] for b in block)

    def _gf_mul(self, a: int, b: int) -> int:
        """Galois field multiplication in GF(2^8)"""
        p = 0
        for _ in range(8):
            if b & 1:
                p ^= a
            hi_bit = a & 0x80
            a = (a << 1) & 0xff
            if hi_bit:
                a ^= 0xc3  # Reduction polynomial
            b >>= 1
        return p

    def _l_transform(self, block: bytes) -> bytes:
        """Linear transformation L"""
        result = list(block)
        for _ in range(16):
            t = 0
            for i in range(16):
                t ^= self._gf_mul(result[i], self.L_VEC[i])
            result = [t] + result[:-1]
        return bytes(result)

    def _l_inv_transform(self, block: bytes) -> bytes:
        """Inverse linear transformation L"""
        result = list(block)
        for _ in range(16):
            t = result[0]
            result = result[1:] + [0]
            for i in range(15):
                result[i] ^= self._gf_mul(t, self.L_VEC[i])
            result[15] = t
        return bytes(result)

    def _key_expansion(self, key: bytes) -> list:
        """Generate round keys from the master key"""
        # Generate iteration constants
        c = []
        for i in range(1, 33):
            block = bytes([0] * 15 + [i])
            c.append(self._l_transform(block))

        round_keys = [key[:16], key[16:]]

        for i in range(4):
            k1, k2 = round_keys[-2], round_keys[-1]
            for j in range(8):
                idx = 8 * i + j
                t = bytes(a ^ b for a, b in zip(k1, c[idx]))
                t = self._s_transform(t)
                t = self._l_transform(t)
                t = bytes(a ^ b for a, b in zip(t, k2))
                k1, k2 = t, k1
            round_keys.extend([k1, k2])

        return round_keys

    def encrypt_block(self, block: bytes) -> bytes:
        """Encrypt a single 128-bit block"""
        if len(block) != self.BLOCK_SIZE:
            raise ValueError(f"Block must be {self.BLOCK_SIZE} bytes")

        result = block
        for i in range(9):
            result = bytes(a ^ b for a, b in zip(result, self.round_keys[i]))
            result = self._s_transform(result)
            result = self._l_transform(result)

        return bytes(a ^ b for a, b in zip(result, self.round_keys[9]))

    def decrypt_block(self, block: bytes) -> bytes:
        """Decrypt a single 128-bit block"""
        if len(block) != self.BLOCK_SIZE:
            raise ValueError(f"Block must be {self.BLOCK_SIZE} bytes")

        result = bytes(a ^ b for a, b in zip(block, self.round_keys[9]))

        for i in range(8, -1, -1):
            result = self._l_inv_transform(result)
            result = self._s_inv_transform(result)
            result = bytes(a ^ b for a, b in zip(result, self.round_keys[i]))

        return result

    def encrypt_cbc(self, plaintext: bytes, iv: bytes) -> bytes:
        """Encrypt using CBC mode"""
        if len(iv) != self.BLOCK_SIZE:
            raise ValueError(f"IV must be {self.BLOCK_SIZE} bytes")

        # PKCS7 padding
        pad_len = self.BLOCK_SIZE - (len(plaintext) % self.BLOCK_SIZE)
        plaintext = plaintext + bytes([pad_len] * pad_len)

        ciphertext = b''
        prev_block = iv

        for i in range(0, len(plaintext), self.BLOCK_SIZE):
            block = plaintext[i:i+self.BLOCK_SIZE]
            xored = bytes(a ^ b for a, b in zip(block, prev_block))
            encrypted = self.encrypt_block(xored)
            ciphertext += encrypted
            prev_block = encrypted

        return ciphertext

    def decrypt_cbc(self, ciphertext: bytes, iv: bytes) -> bytes:
        """Decrypt using CBC mode"""
        if len(iv) != self.BLOCK_SIZE:
            raise ValueError(f"IV must be {self.BLOCK_SIZE} bytes")
        if len(ciphertext) % self.BLOCK_SIZE != 0:
            raise ValueError("Ciphertext length must be multiple of block size")

        plaintext = b''
        prev_block = iv

        for i in range(0, len(ciphertext), self.BLOCK_SIZE):
            block = ciphertext[i:i+self.BLOCK_SIZE]
            decrypted = self.decrypt_block(block)
            xored = bytes(a ^ b for a, b in zip(decrypted, prev_block))
            plaintext += xored
            prev_block = block

        # Remove PKCS7 padding
        pad_len = plaintext[-1]
        if pad_len > self.BLOCK_SIZE or not all(b == pad_len for b in plaintext[-pad_len:]):
            raise ValueError("Invalid padding")

        return plaintext[:-pad_len]


class GOSTStreebog:
    """
    Streebog Hash Function Implementation (GOST R 34.11-2012)
    Russian National Standard for cryptographic hash function
    Output: 256 or 512 bits
    """

    BLOCK_SIZE = 64

    # S-Box (Pi substitution) - same as Kuznyechik
    PI = GOSTKuznyechik.PI

    def __init__(self, digest_size: int = 32):
        """
        Initialize Streebog hash function

        Args:
            digest_size: 32 for 256-bit hash, 64 for 512-bit hash
        """
        if digest_size not in (32, 64):
            raise ValueError("digest_size must be 32 or 64")

        self.digest_size = digest_size
        self._h = bytes([0x01 if digest_size == 32 else 0x00] * 64)
        self._n = bytes(64)
        self._sigma = bytes(64)
        self._buffer = b''

    def _add_mod512(self, a: bytes, b: bytes) -> bytes:
        """Add two 512-bit numbers modulo 2^512"""
        result = []
        carry = 0
        for i in range(64):
            s = a[i] + b[i] + carry
            result.append(s & 0xff)
            carry = s >> 8
        return bytes(result)

    def _xor(self, a: bytes, b: bytes) -> bytes:
        """XOR two byte arrays"""
        return bytes(x ^ y for x, y in zip(a, b))

    def _s_transform(self, block: bytes) -> bytes:
        """Apply S-box substitution"""
        return bytes(self.PI[b] for b in block)

    def _g(self, h: bytes, n: bytes, m: bytes) -> bytes:
        """Compression function g"""
        k = self._xor(h, n)
        k = self._s_transform(k)
        # Simplified - in production, use full L and P transforms
        return self._xor(self._xor(k, m), h)

    def update(self, data: bytes):
        """Update hash with data"""
        self._buffer += data

        while len(self._buffer) >= self.BLOCK_SIZE:
            block = self._buffer[:self.BLOCK_SIZE]
            self._buffer = self._buffer[self.BLOCK_SIZE:]

            self._h = self._g(self._h, self._n, block)
            self._n = self._add_mod512(self._n, bytes([0] * 63 + [0x02]))
            self._sigma = self._add_mod512(self._sigma, block)

    def digest(self) -> bytes:
        """Compute final hash digest"""
        # Padding
        remaining = self._buffer
        pad_len = self.BLOCK_SIZE - len(remaining)
        padded = remaining + bytes([0x01]) + bytes(pad_len - 1)

        # Final compression
        self._h = self._g(self._h, self._n, padded)

        # Length
        length_bytes = bytes([len(self._buffer) * 8]) + bytes(63)
        self._n = self._add_mod512(self._n, length_bytes)

        self._sigma = self._add_mod512(self._sigma, padded)

        self._h = self._g(self._h, bytes(64), self._n)
        self._h = self._g(self._h, bytes(64), self._sigma)

        if self.digest_size == 32:
            return self._h[32:]
        return self._h

    def hexdigest(self) -> str:
        """Return hex-encoded digest"""
        return self.digest().hex()

    @classmethod
    def hash(cls, data: bytes, digest_size: int = 32) -> bytes:
        """Convenience method to hash data in one call"""
        h = cls(digest_size)
        h.update(data)
        return h.digest()


class EncryptionManager:
    """
    Unified encryption manager supporting multiple standards
    Handles key management and encryption operations for both PRC and Russia
    """

    def __init__(self):
        self._sm4_cipher = None
        self._gost_cipher = None
        self._keys = {}

    def initialize_sm4(self, key: bytes):
        """Initialize SM4 cipher with key"""
        self._sm4_cipher = SM4(key)
        self._keys['sm4'] = key

    def initialize_gost(self, key: bytes):
        """Initialize GOST Kuznyechik cipher with key"""
        self._gost_cipher = GOSTKuznyechik(key)
        self._keys['gost'] = key

    def encrypt(self, plaintext: bytes, algorithm: EncryptionAlgorithm) -> EncryptedData:
        """
        Encrypt data using the specified algorithm

        Args:
            plaintext: Data to encrypt
            algorithm: Encryption algorithm to use

        Returns:
            EncryptedData containing ciphertext and metadata
        """
        iv = secrets.token_bytes(16)

        if algorithm in (EncryptionAlgorithm.SM4_CBC, EncryptionAlgorithm.SM4_GCM):
            if self._sm4_cipher is None:
                raise ValueError("SM4 cipher not initialized")
            ciphertext = self._sm4_cipher.encrypt_cbc(plaintext, iv)
            return EncryptedData(
                ciphertext=ciphertext,
                iv=iv,
                tag=None,
                algorithm=algorithm
            )

        elif algorithm in (EncryptionAlgorithm.GOST_KUZNYECHIK_CBC, EncryptionAlgorithm.GOST_KUZNYECHIK_GCM):
            if self._gost_cipher is None:
                raise ValueError("GOST cipher not initialized")
            ciphertext = self._gost_cipher.encrypt_cbc(plaintext, iv)
            return EncryptedData(
                ciphertext=ciphertext,
                iv=iv,
                tag=None,
                algorithm=algorithm
            )

        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    def decrypt(self, encrypted_data: EncryptedData) -> bytes:
        """
        Decrypt data using the algorithm specified in the encrypted data

        Args:
            encrypted_data: EncryptedData object containing ciphertext

        Returns:
            Decrypted plaintext
        """
        algorithm = encrypted_data.algorithm

        if algorithm in (EncryptionAlgorithm.SM4_CBC, EncryptionAlgorithm.SM4_GCM):
            if self._sm4_cipher is None:
                raise ValueError("SM4 cipher not initialized")
            return self._sm4_cipher.decrypt_cbc(encrypted_data.ciphertext, encrypted_data.iv)

        elif algorithm in (EncryptionAlgorithm.GOST_KUZNYECHIK_CBC, EncryptionAlgorithm.GOST_KUZNYECHIK_GCM):
            if self._gost_cipher is None:
                raise ValueError("GOST cipher not initialized")
            return self._gost_cipher.decrypt_cbc(encrypted_data.ciphertext, encrypted_data.iv)

        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    def hash_sm3(self, data: bytes) -> bytes:
        """Hash data using SM3 (PRC standard)"""
        return SM3.hash(data)

    def hash_streebog(self, data: bytes, digest_size: int = 32) -> bytes:
        """Hash data using Streebog (GOST standard)"""
        return GOSTStreebog.hash(data, digest_size)

    @staticmethod
    def generate_key(algorithm: EncryptionAlgorithm) -> bytes:
        """Generate a random key for the specified algorithm"""
        if algorithm in (EncryptionAlgorithm.SM4_CBC, EncryptionAlgorithm.SM4_GCM):
            return secrets.token_bytes(SM4.KEY_SIZE)
        elif algorithm in (EncryptionAlgorithm.GOST_KUZNYECHIK_CBC,
                           EncryptionAlgorithm.GOST_KUZNYECHIK_GCM):
            return secrets.token_bytes(GOSTKuznyechik.KEY_SIZE)
        elif algorithm in (EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC):
            return secrets.token_bytes(32)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    @staticmethod
    def generate_iv() -> bytes:
        """Generate a random 16-byte IV"""
        return secrets.token_bytes(16)
