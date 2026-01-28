"""
Security Service - HMAC Verification & Blockchain
Provides data integrity and authenticity verification for IoT sensor data
"""

import hmac
import hashlib
import time
import json
import logging
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Shared secret key (in production, use environment variable)
HMAC_SECRET_KEY = "campus-orion-iot-secret-2024"

# Tolerance for timestamp validation (seconds)
TIMESTAMP_TOLERANCE = 300  # 5 minutes


class HMACVerifier:
    """
    Verifies HMAC-SHA256 signatures on sensor data
    """
    
    def __init__(self, secret_key: str = HMAC_SECRET_KEY):
        self.secret_key = secret_key.encode('utf-8')
    
    def compute_signature(self, message: str) -> str:
        """Compute HMAC-SHA256 signature for a message"""
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, message: str, signature: str) -> bool:
        """Verify if the signature matches the message"""
        expected = self.compute_signature(message)
        return hmac.compare_digest(expected.lower(), signature.lower())
    
    def parse_signed_data(self, raw_data: str) -> Tuple[Optional[Dict], bool, str]:
        """
        Parse and verify signed sensor data
        Format: TYPE:VALUE|ts:TIMESTAMP|sig:SIGNATURE
        
        Returns: (parsed_data, is_valid, error_message)
        """
        try:
            # Split signature from data
            if "|sig:" not in raw_data:
                # No signature - data is unsigned (legacy format)
                return self._parse_unsigned(raw_data), True, "unsigned"
            
            parts = raw_data.rsplit("|sig:", 1)
            if len(parts) != 2:
                return None, False, "Invalid format: missing signature"
            
            data_part, signature = parts
            
            # Verify signature
            if not self.verify_signature(data_part, signature):
                logger.warning(f"[SECURITY] Invalid signature for: {data_part[:50]}...")
                return None, False, "Invalid signature - data may be tampered"
            
            # Parse data
            parsed = self._parse_data(data_part)
            if not parsed:
                return None, False, "Failed to parse data"
            
            # Verify timestamp (prevent replay attacks)
            if "timestamp" in parsed:
                ts = parsed["timestamp"]
                now = int(time.time() * 1000)  # milliseconds
                if abs(now - ts) > TIMESTAMP_TOLERANCE * 1000:
                    logger.warning(f"[SECURITY] Timestamp too old: {ts}")
                    return parsed, False, "Timestamp expired - possible replay attack"
            
            logger.info(f"[SECURITY] Valid signature for {parsed.get('type', 'unknown')}")
            return parsed, True, "valid"
            
        except Exception as e:
            logger.error(f"[SECURITY] Parse error: {e}")
            return None, False, str(e)
    
    def _parse_data(self, data: str) -> Optional[Dict]:
        """Parse TYPE:VALUE|ts:TIMESTAMP format"""
        result = {}
        parts = data.split("|")
        
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                if key == "ts":
                    result["timestamp"] = int(value)
                elif key in ["temperature", "humidity", "presence", "light", "co2"]:
                    result["type"] = key
                    try:
                        result["value"] = float(value)
                    except:
                        result["value"] = value
                else:
                    result[key] = value
        
        return result if result else None
    
    def _parse_unsigned(self, data: str) -> Optional[Dict]:
        """Parse unsigned data (legacy format)"""
        try:
            # Try JSON first
            return json.loads(data)
        except:
            # Try simple format
            return self._parse_data(data)


class SimpleBlockchain:
    """
    Simplified blockchain for storing sensor data integrity proofs
    Each block contains: index, timestamp, data_hash, previous_hash, nonce
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.difficulty = 2  # Number of leading zeros required
    
    def compute_hash(self, block_data: Dict) -> str:
        """Compute SHA256 hash of block data"""
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def create_genesis_block(self) -> Dict:
        """Create the first block in the chain"""
        return {
            "index": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "data_hash": "0" * 64,
            "sensor_type": "genesis",
            "sensor_value": "0",
            "previous_hash": "0" * 64,
            "nonce": 0,
            "hash": self.compute_hash({
                "index": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "data_hash": "0" * 64,
                "previous_hash": "0" * 64,
                "nonce": 0
            })
        }
    
    def mine_block(self, data: Dict, previous_hash: str, index: int) -> Dict:
        """
        Mine a new block with proof of work
        """
        # Hash the sensor data
        data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        
        nonce = 0
        timestamp = datetime.utcnow().isoformat()
        
        while True:
            block_data = {
                "index": index,
                "timestamp": timestamp,
                "data_hash": data_hash,
                "previous_hash": previous_hash,
                "nonce": nonce
            }
            
            block_hash = self.compute_hash(block_data)
            
            # Check if hash meets difficulty requirement
            if block_hash[:self.difficulty] == "0" * self.difficulty:
                return {
                    **block_data,
                    "sensor_type": data.get("type", "unknown"),
                    "sensor_value": str(data.get("value", "")),
                    "hash": block_hash
                }
            
            nonce += 1
            
            # Safety limit
            if nonce > 100000:
                # Accept without full PoW for IoT efficiency
                return {
                    **block_data,
                    "sensor_type": data.get("type", "unknown"),
                    "sensor_value": str(data.get("value", "")),
                    "hash": block_hash
                }
    
    def verify_chain(self, chain: List[Dict]) -> Tuple[bool, str]:
        """
        Verify the integrity of the entire blockchain
        Returns: (is_valid, error_message)
        """
        if not chain:
            return True, "Empty chain"
        
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            
            # Verify previous hash link
            if current["previous_hash"] != previous["hash"]:
                return False, f"Chain broken at block {i}: previous_hash mismatch"
            
            # Verify block hash
            block_data = {
                "index": current["index"],
                "timestamp": current["timestamp"],
                "data_hash": current["data_hash"],
                "previous_hash": current["previous_hash"],
                "nonce": current["nonce"]
            }
            
            computed_hash = self.compute_hash(block_data)
            if computed_hash != current["hash"]:
                return False, f"Chain corrupted at block {i}: hash mismatch"
        
        return True, "Chain valid"
    
    def detect_tampering(self, chain: List[Dict], block_index: int, original_data: Dict) -> bool:
        """
        Check if a specific block's data has been tampered with
        """
        if block_index >= len(chain):
            return False
        
        block = chain[block_index]
        expected_hash = hashlib.sha256(
            json.dumps(original_data, sort_keys=True).encode()
        ).hexdigest()
        
        return block["data_hash"] != expected_hash


# Global instances
hmac_verifier = HMACVerifier()


def verify_sensor_data(raw_data: str) -> Tuple[Optional[Dict], bool, str]:
    """
    Convenience function to verify sensor data
    """
    return hmac_verifier.parse_signed_data(raw_data)


def sign_data(data: str) -> str:
    """
    Sign data with HMAC (for testing)
    """
    return hmac_verifier.compute_signature(data)
