"""
Blockchain Model - Stores integrity proofs for sensor data
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from db.database import Base


class Block(Base):
    """
    Blockchain block for data integrity
    Each block contains a hash of sensor data and links to previous block
    """
    __tablename__ = "blockchain"
    
    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, nullable=False, unique=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Sensor data info
    sensor_type = Column(String(50))
    sensor_value = Column(String(100))
    data_hash = Column(String(64), nullable=False)  # SHA256 hash of original data
    
    # Blockchain links
    previous_hash = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False, unique=True)
    nonce = Column(Integer, default=0)
    
    # Security metadata
    signature_valid = Column(Boolean, default=True)
    source_ip = Column(String(45))  # IPv4 or IPv6
    
    def to_dict(self):
        return {
            "id": self.id,
            "index": self.index,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sensor_type": self.sensor_type,
            "sensor_value": self.sensor_value,
            "data_hash": self.data_hash,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "nonce": self.nonce,
            "signature_valid": self.signature_valid
        }


class SecurityAlert(Base):
    """
    Security alerts for tampering attempts or invalid signatures
    """
    __tablename__ = "security_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    alert_type = Column(String(50), nullable=False)  # invalid_signature, replay_attack, chain_broken
    severity = Column(String(20), default="warning")  # info, warning, critical
    
    description = Column(Text)
    raw_data = Column(Text)  # Original data that triggered alert
    source_ip = Column(String(45))
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "description": self.description,
            "raw_data": self.raw_data[:100] if self.raw_data else None,  # Truncate for display
            "source_ip": self.source_ip,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }
