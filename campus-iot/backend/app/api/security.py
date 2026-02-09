"""
Security API - Blockchain & HMAC endpoints
Provides endpoints for viewing blockchain, security alerts, and testing signatures
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import hashlib
import json

from db.database import get_db
from models.blockchain import Block, SecurityAlert
from services.security_service import (
    hmac_verifier, 
    SimpleBlockchain, 
    verify_sensor_data,
    sign_data,
    HMAC_SECRET_KEY
)

router = APIRouter(prefix="/security", tags=["security"])


# =============================================================================
# BLOCKCHAIN ENDPOINTS
# =============================================================================

@router.get("/blockchain")
async def get_blockchain(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get the blockchain with pagination
    """
    total = db.query(Block).count()
    blocks = db.query(Block)\
        .order_by(desc(Block.index))\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return {
        "total": total,
        "blocks": [b.to_dict() for b in blocks],
        "chain_length": total
    }


@router.get("/blockchain/verify")
async def verify_blockchain(db: Session = Depends(get_db)):
    """
    Verify the integrity of the entire blockchain
    """
    blocks = db.query(Block).order_by(Block.index).all()
    
    if not blocks:
        return {
            "valid": True,
            "message": "Blockchain is empty",
            "blocks_verified": 0
        }
    
    chain = [b.to_dict() for b in blocks]
    blockchain = SimpleBlockchain(db)
    is_valid, message = blockchain.verify_chain(chain)
    
    return {
        "valid": is_valid,
        "message": message,
        "blocks_verified": len(chain),
        "last_block_index": chain[-1]["index"] if chain else None
    }


@router.get("/blockchain/block/{index}")
async def get_block(index: int, db: Session = Depends(get_db)):
    """
    Get a specific block by index
    """
    block = db.query(Block).filter(Block.index == index).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    return block.to_dict()


@router.post("/blockchain/add")
async def add_block(
    sensor_type: str,
    sensor_value: str,
    db: Session = Depends(get_db)
):
    """
    Manually add a block to the blockchain (for testing)
    """
    # Get last block
    last_block = db.query(Block).order_by(desc(Block.index)).first()
    
    if last_block:
        previous_hash = last_block.hash
        new_index = last_block.index + 1
    else:
        # Create genesis block first
        genesis = _create_genesis_block(db)
        previous_hash = genesis.hash
        new_index = 1
    
    # Mine new block
    blockchain = SimpleBlockchain(db)
    data = {"type": sensor_type, "value": sensor_value}
    block_data = blockchain.mine_block(data, previous_hash, new_index)
    
    # Save to database
    new_block = Block(
        index=block_data["index"],
        timestamp=datetime.fromisoformat(block_data["timestamp"]),
        sensor_type=block_data["sensor_type"],
        sensor_value=block_data["sensor_value"],
        data_hash=block_data["data_hash"],
        previous_hash=block_data["previous_hash"],
        hash=block_data["hash"],
        nonce=block_data["nonce"],
        signature_valid=True
    )
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    
    return {
        "message": "Block added successfully",
        "block": new_block.to_dict()
    }


def _create_genesis_block(db: Session) -> Block:
    """Create genesis block if not exists"""
    genesis = db.query(Block).filter(Block.index == 0).first()
    if genesis:
        return genesis
    
    blockchain = SimpleBlockchain(db)
    genesis_data = blockchain.create_genesis_block()
    
    genesis = Block(
        index=0,
        timestamp=datetime.fromisoformat(genesis_data["timestamp"]),
        sensor_type="genesis",
        sensor_value="0",
        data_hash=genesis_data["data_hash"],
        previous_hash=genesis_data["previous_hash"],
        hash=genesis_data["hash"],
        nonce=0,
        signature_valid=True
    )
    db.add(genesis)
    db.commit()
    db.refresh(genesis)
    return genesis


# =============================================================================
# HMAC VERIFICATION ENDPOINTS
# =============================================================================

@router.post("/verify")
async def verify_data(raw_data: str, db: Session = Depends(get_db)):
    """
    Verify HMAC signature on sensor data
    """
    parsed, is_valid, message = verify_sensor_data(raw_data)
    
    # Log security alert if invalid
    if not is_valid and message != "unsigned":
        alert = SecurityAlert(
            alert_type="invalid_signature",
            severity="warning",
            description=message,
            raw_data=raw_data[:500]
        )
        db.add(alert)
        db.commit()
    
    return {
        "valid": is_valid,
        "message": message,
        "parsed_data": parsed
    }


@router.post("/sign")
async def sign_message(message: str):
    """
    Sign a message with HMAC (for testing/demo)
    """
    signature = sign_data(message)
    return {
        "message": message,
        "signature": signature,
        "signed_format": f"{message}|sig:{signature}"
    }


@router.get("/test-signature")
async def test_signature():
    """
    Generate a test signed message for demo purposes
    """
    import time
    
    test_data = {
        "type": "temperature",
        "value": 23.5,
        "timestamp": int(time.time() * 1000)
    }
    
    message = f"temperature:{test_data['value']}|ts:{test_data['timestamp']}"
    signature = sign_data(message)
    
    return {
        "test_data": test_data,
        "message_to_sign": message,
        "signature": signature,
        "full_payload": f"{message}|sig:{signature}",
        "secret_key_hint": HMAC_SECRET_KEY[:10] + "..."
    }


# =============================================================================
# SECURITY ALERTS ENDPOINTS
# =============================================================================

@router.get("/alerts")
async def get_security_alerts(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    unresolved_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get security alerts
    """
    query = db.query(SecurityAlert)
    
    if severity:
        query = query.filter(SecurityAlert.severity == severity)
    
    if unresolved_only:
        query = query.filter(SecurityAlert.resolved == False)
    
    total = query.count()
    alerts = query.order_by(desc(SecurityAlert.timestamp)).limit(limit).all()
    
    return {
        "total": total,
        "alerts": [a.to_dict() for a in alerts]
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    resolved_by: str = "admin",
    db: Session = Depends(get_db)
):
    """
    Mark a security alert as resolved
    """
    alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = resolved_by
    db.commit()
    
    return {"message": "Alert resolved", "alert": alert.to_dict()}


# =============================================================================
# STATS ENDPOINTS
# =============================================================================

@router.get("/stats")
async def get_security_stats(db: Session = Depends(get_db)):
    """
    Get security statistics
    """
    total_blocks = db.query(Block).count()
    valid_signatures = db.query(Block).filter(Block.signature_valid == True).count()
    invalid_signatures = db.query(Block).filter(Block.signature_valid == False).count()
    
    total_alerts = db.query(SecurityAlert).count()
    unresolved_alerts = db.query(SecurityAlert).filter(SecurityAlert.resolved == False).count()
    critical_alerts = db.query(SecurityAlert).filter(SecurityAlert.severity == "critical").count()
    
    # Verify chain integrity
    blocks = db.query(Block).order_by(Block.index).all()
    chain = [b.to_dict() for b in blocks]
    blockchain = SimpleBlockchain(db)
    chain_valid, _ = blockchain.verify_chain(chain)
    
    return {
        "blockchain": {
            "total_blocks": total_blocks,
            "chain_valid": chain_valid,
            "valid_signatures": valid_signatures,
            "invalid_signatures": invalid_signatures
        },
        "alerts": {
            "total": total_alerts,
            "unresolved": unresolved_alerts,
            "critical": critical_alerts
        },
        "security_score": _calculate_security_score(
            total_blocks, valid_signatures, unresolved_alerts, chain_valid
        )
    }


def _calculate_security_score(total_blocks: int, valid_sigs: int, unresolved: int, chain_valid: bool) -> int:
    """
    Calculate a security score from 0-100
    """
    if total_blocks == 0:
        return 100
    
    score = 100
    
    # Deduct for invalid signatures
    if total_blocks > 0:
        invalid_ratio = (total_blocks - valid_sigs) / total_blocks
        score -= int(invalid_ratio * 40)
    
    # Deduct for unresolved alerts
    score -= min(unresolved * 5, 30)
    
    # Deduct for broken chain
    if not chain_valid:
        score -= 30
    
    return max(0, score)
