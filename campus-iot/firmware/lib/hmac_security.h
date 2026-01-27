/**
 * HMAC-SHA256 Security Library for IoT
 * 
 * Provides message authentication for sensor data
 * Uses software implementation compatible with Arduino UNO R4 WiFi
 * 
 * Usage:
 *   HMACSecurity hmac("your-secret-key");
 *   String signature = hmac.sign("temperature:23.5");
 *   // Send: "temperature:23.5|sig:ABC123..."
 */

#ifndef HMAC_SECURITY_H
#define HMAC_SECURITY_H

#include <Arduino.h>

// SHA256 constants
#define SHA256_BLOCK_SIZE 64
#define SHA256_HASH_SIZE 32

class SHA256 {
private:
    uint32_t state[8];
    uint8_t buffer[SHA256_BLOCK_SIZE];
    uint32_t bitCount[2];
    
    static const uint32_t K[64];
    
    void transform(const uint8_t* data);
    
    inline uint32_t rotr(uint32_t x, uint32_t n) {
        return (x >> n) | (x << (32 - n));
    }
    
    inline uint32_t ch(uint32_t x, uint32_t y, uint32_t z) {
        return (x & y) ^ (~x & z);
    }
    
    inline uint32_t maj(uint32_t x, uint32_t y, uint32_t z) {
        return (x & y) ^ (x & z) ^ (y & z);
    }
    
    inline uint32_t sigma0(uint32_t x) {
        return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
    }
    
    inline uint32_t sigma1(uint32_t x) {
        return rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25);
    }
    
    inline uint32_t gamma0(uint32_t x) {
        return rotr(x, 7) ^ rotr(x, 18) ^ (x >> 3);
    }
    
    inline uint32_t gamma1(uint32_t x) {
        return rotr(x, 17) ^ rotr(x, 19) ^ (x >> 10);
    }

public:
    void init();
    void update(const uint8_t* data, size_t len);
    void final(uint8_t* hash);
    
    // Convenience method
    void hash(const uint8_t* data, size_t len, uint8_t* output);
};

// SHA256 round constants
const uint32_t SHA256::K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

void SHA256::init() {
    state[0] = 0x6a09e667;
    state[1] = 0xbb67ae85;
    state[2] = 0x3c6ef372;
    state[3] = 0xa54ff53a;
    state[4] = 0x510e527f;
    state[5] = 0x9b05688c;
    state[6] = 0x1f83d9ab;
    state[7] = 0x5be0cd19;
    bitCount[0] = 0;
    bitCount[1] = 0;
}

void SHA256::transform(const uint8_t* data) {
    uint32_t W[64];
    uint32_t a, b, c, d, e, f, g, h;
    uint32_t t1, t2;
    
    // Prepare message schedule
    for (int i = 0; i < 16; i++) {
        W[i] = ((uint32_t)data[i * 4] << 24) |
               ((uint32_t)data[i * 4 + 1] << 16) |
               ((uint32_t)data[i * 4 + 2] << 8) |
               ((uint32_t)data[i * 4 + 3]);
    }
    
    for (int i = 16; i < 64; i++) {
        W[i] = gamma1(W[i - 2]) + W[i - 7] + gamma0(W[i - 15]) + W[i - 16];
    }
    
    // Initialize working variables
    a = state[0]; b = state[1]; c = state[2]; d = state[3];
    e = state[4]; f = state[5]; g = state[6]; h = state[7];
    
    // Main loop
    for (int i = 0; i < 64; i++) {
        t1 = h + sigma1(e) + ch(e, f, g) + K[i] + W[i];
        t2 = sigma0(a) + maj(a, b, c);
        h = g; g = f; f = e; e = d + t1;
        d = c; c = b; b = a; a = t1 + t2;
    }
    
    // Update state
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

void SHA256::update(const uint8_t* data, size_t len) {
    size_t i = 0;
    size_t index = (bitCount[0] >> 3) & 0x3F;
    
    bitCount[0] += len << 3;
    if (bitCount[0] < (len << 3)) bitCount[1]++;
    bitCount[1] += len >> 29;
    
    size_t partLen = SHA256_BLOCK_SIZE - index;
    
    if (len >= partLen) {
        memcpy(&buffer[index], data, partLen);
        transform(buffer);
        
        for (i = partLen; i + SHA256_BLOCK_SIZE - 1 < len; i += SHA256_BLOCK_SIZE) {
            transform(&data[i]);
        }
        index = 0;
    }
    
    memcpy(&buffer[index], &data[i], len - i);
}

void SHA256::final(uint8_t* hash) {
    uint8_t padding[SHA256_BLOCK_SIZE];
    uint8_t bits[8];
    size_t index = (bitCount[0] >> 3) & 0x3F;
    size_t padLen = (index < 56) ? (56 - index) : (120 - index);
    
    // Store bit count (big-endian)
    for (int i = 0; i < 4; i++) {
        bits[i] = (bitCount[1] >> (24 - i * 8)) & 0xFF;
        bits[i + 4] = (bitCount[0] >> (24 - i * 8)) & 0xFF;
    }
    
    // Pad message
    memset(padding, 0, sizeof(padding));
    padding[0] = 0x80;
    update(padding, padLen);
    update(bits, 8);
    
    // Output hash (big-endian)
    for (int i = 0; i < 8; i++) {
        hash[i * 4] = (state[i] >> 24) & 0xFF;
        hash[i * 4 + 1] = (state[i] >> 16) & 0xFF;
        hash[i * 4 + 2] = (state[i] >> 8) & 0xFF;
        hash[i * 4 + 3] = state[i] & 0xFF;
    }
}

void SHA256::hash(const uint8_t* data, size_t len, uint8_t* output) {
    init();
    update(data, len);
    final(output);
}


/**
 * HMAC-SHA256 Implementation
 */
class HMACSecurity {
private:
    uint8_t key[SHA256_BLOCK_SIZE];
    SHA256 sha256;
    
    void prepareKey(const char* secretKey) {
        size_t keyLen = strlen(secretKey);
        memset(key, 0, SHA256_BLOCK_SIZE);
        
        if (keyLen > SHA256_BLOCK_SIZE) {
            // Hash the key if too long
            sha256.hash((const uint8_t*)secretKey, keyLen, key);
        } else {
            memcpy(key, secretKey, keyLen);
        }
    }
    
public:
    HMACSecurity(const char* secretKey) {
        prepareKey(secretKey);
    }
    
    /**
     * Compute HMAC-SHA256 signature
     * Returns hex string of signature
     */
    String sign(const String& message) {
        uint8_t ipad[SHA256_BLOCK_SIZE];
        uint8_t opad[SHA256_BLOCK_SIZE];
        uint8_t innerHash[SHA256_HASH_SIZE];
        uint8_t finalHash[SHA256_HASH_SIZE];
        
        // Prepare pads
        for (int i = 0; i < SHA256_BLOCK_SIZE; i++) {
            ipad[i] = key[i] ^ 0x36;
            opad[i] = key[i] ^ 0x5c;
        }
        
        // Inner hash: H(ipad || message)
        sha256.init();
        sha256.update(ipad, SHA256_BLOCK_SIZE);
        sha256.update((const uint8_t*)message.c_str(), message.length());
        sha256.final(innerHash);
        
        // Outer hash: H(opad || inner_hash)
        sha256.init();
        sha256.update(opad, SHA256_BLOCK_SIZE);
        sha256.update(innerHash, SHA256_HASH_SIZE);
        sha256.final(finalHash);
        
        // Convert to hex string
        String hex = "";
        for (int i = 0; i < SHA256_HASH_SIZE; i++) {
            if (finalHash[i] < 16) hex += "0";
            hex += String(finalHash[i], HEX);
        }
        return hex;
    }
    
    /**
     * Sign a sensor reading and format for transmission
     * Format: TYPE:VALUE|ts:TIMESTAMP|sig:SIGNATURE
     */
    String signSensorData(const String& sensorType, float value, unsigned long timestamp) {
        // Create message to sign
        String data = sensorType + ":" + String(value, 2) + "|ts:" + String(timestamp);
        String signature = sign(data);
        
        // Return formatted message
        return data + "|sig:" + signature;
    }
    
    /**
     * Sign a sensor reading (int version)
     */
    String signSensorData(const String& sensorType, int value, unsigned long timestamp) {
        String data = sensorType + ":" + String(value) + "|ts:" + String(timestamp);
        String signature = sign(data);
        return data + "|sig:" + signature;
    }
    
    /**
     * Verify a signed message
     * Returns true if signature is valid
     */
    bool verify(const String& message, const String& signature) {
        String computed = sign(message);
        return computed.equalsIgnoreCase(signature);
    }
};

#endif // HMAC_SECURITY_H
