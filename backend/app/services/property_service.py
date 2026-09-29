from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from web3 import Web3
from .. import models
from ..blockchain import landchain_service
from ..blockchain.web3_client import client

def record_tx(db: Session, prop_id: int | None, kind: str, receipt):
    tx_hash = Web3.to_hex(receipt.transactionHash)
    db.add(models.BlockchainTransaction(property_id=prop_id, transaction_type=kind, transaction_hash=tx_hash, status="confirmed"))
    return tx_hash

def register(db: Session, payload):
    user = db.get(models.User, payload.owner_user_id)
    if not user: raise HTTPException(404, "Owner user was not found")
    try:
        if client.signer().address.lower() != user.wallet_address.lower(): raise HTTPException(403, "Backend signer must match the selected property owner for initial on-chain registration")
    except RuntimeError: raise HTTPException(503, "Blockchain signer is not configured") from None
    if db.scalar(select(models.Property).where(models.Property.property_id == payload.property_id)): raise HTTPException(409, "Property already exists in the database")
    try: receipt = landchain_service.register(payload.property_id, payload.land_reference_code, payload.document_hash)
    except Exception as exc: raise HTTPException(400, friendly(exc)) from None
    # Persist the registered state only after a successful receipt.
    prop = models.Property(**payload.model_dump(), blockchain_registered=True, blockchain_verified=False)
    db.add(prop)
    tx_hash = record_tx(db, payload.property_id, "property_registered", receipt)
    try: db.commit()
    except Exception as exc: db.rollback(); raise HTTPException(500, f"Blockchain registration confirmed, but database synchronization failed: {exc.__class__.__name__}") from None
    db.refresh(prop)
    return {"property": property_out(prop), "transaction_hash": tx_hash, "status": "confirmed"}

def property_out(p):
    return {"id":p.id,"property_id":int(p.property_id),"owner_user_id":p.owner_user_id,"title":p.title,"location_address":p.location_address,"area_sq_ft":p.area_sq_ft,"property_value":float(p.property_value),"land_reference_code":p.land_reference_code,"document_hash":p.document_hash,"blockchain_registered":p.blockchain_registered,"blockchain_verified":p.blockchain_verified,"tokenized":p.tokenized,"token_contract_address":p.token_contract_address,"created_at":p.created_at.isoformat()}

def friendly(exc):
    text = str(exc).lower()
    if "already exists" in text: return "Property already exists on the blockchain."
    if "already verified" in text: return "Property has already been verified."
    if "does not exist" in text: return "Property does not exist on the blockchain."
    if "only owner" in text: return "Only the current on-chain owner can transfer this property. Configure the backend signer for that owner's wallet."
    if "invalid new owner" in text: return "Invalid new owner address."
    if "not verified" in text: return "Property has not been verified."
    return "Blockchain operation failed. Check the local node, signer, contract deployment, and transaction logs."

def inspect(db: Session, property_id: int):
    p = db.scalar(select(models.Property).where(models.Property.property_id == property_id))
    if not p: raise HTTPException(404, "Property does not exist in the database")
    try: chain = landchain_service.read_property(property_id)
    except Exception as exc: raise HTTPException(503, "Unable to inspect current blockchain deployment") from None
    database = property_out(p)
    if chain is None:
        return {"database": database, "blockchain": None, "message": "Property exists in database but is not registered on the current LandChain deployment.", "consistency": {"exists_in_database": True, "exists_on_chain": False, "owner_matches": False, "verification_matches": False, "document_hash_matches": False, "synchronized": False, "mismatches": ["exists_on_chain"]}}
    owner = db.get(models.User, p.owner_user_id)
    checks = {"exists_in_database": True, "exists_on_chain": chain["exists"], "registration_flag_matches": p.blockchain_registered == chain["exists"], "owner_matches": bool(owner and owner.wallet_address.lower() == chain["owner"].lower()), "verification_matches": p.blockchain_verified == chain["verified"], "document_hash_matches": p.document_hash == chain["document_hash"]}
    checks["synchronized"] = all(checks.values())
    checks["mismatches"] = [k for k,v in checks.items() if k != "synchronized" and not v]
    return {"database": database, "blockchain": chain, "consistency": checks}

def verify(db: Session, property_id: int):
    p = db.scalar(select(models.Property).where(models.Property.property_id == property_id))
    if not p: raise HTTPException(404, "Property does not exist")
    try:
        chain = landchain_service.read_property(property_id)
        if not chain: raise HTTPException(409, "Property does not exist on the current blockchain")
        receipt = landchain_service.verify(property_id)
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400, friendly(exc)) from None
    p.blockchain_verified = True
    db.add(models.PropertyVerification(property_id=property_id, verifier_address=client.signer().address, transaction_hash=Web3.to_hex(receipt.transactionHash)))
    tx_hash = record_tx(db, property_id, "property_verified", receipt)
    db.commit()
    return {"property_id":property_id,"transaction_hash":tx_hash,"status":"confirmed"}

def transfer_owner(db: Session, property_id: int, new_owner: str):
    p = db.scalar(select(models.Property).where(models.Property.property_id == property_id))
    if not p: raise HTTPException(404, "Property does not exist")
    if not Web3.is_address(new_owner) or Web3.to_checksum_address(new_owner) == "0x0000000000000000000000000000000000000000": raise HTTPException(422, "Invalid new owner address")
    new_owner = Web3.to_checksum_address(new_owner)
    user = db.scalar(select(models.User).where(models.User.wallet_address.ilike(new_owner)))
    if not user: raise HTTPException(422, "New owner must be a registered user so database ownership can stay synchronized")
    try:
        chain = landchain_service.read_property(property_id)
        if not chain: raise HTTPException(409, "Property does not exist on the blockchain")
        previous = chain["owner"]
        if client.signer().address.lower() != previous.lower(): raise HTTPException(403, "Only the current on-chain owner can transfer; backend signer does not match")
        receipt = landchain_service.transfer(property_id, new_owner)
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400, friendly(exc)) from None
    p.owner_user_id = user.id
    tx_hash = record_tx(db, property_id, "ownership_transferred", receipt)
    db.commit()
    return {"previous_owner":previous,"new_owner":new_owner,"transaction_hash":tx_hash,"status":"confirmed"}
