from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from web3 import Web3
from .. import models
from ..blockchain.web3_client import client
from ..blockchain import landchain_service
from .property_service import record_tx

def tokenize(db: Session, property_id: int, data):
    p = db.scalar(select(models.Property).where(models.Property.property_id == property_id))
    if not p: raise HTTPException(404, "Property does not exist")
    if not p.blockchain_registered: raise HTTPException(409, "Property is not registered on the current blockchain")
    if not p.blockchain_verified: raise HTTPException(409, "Property has not been verified")
    if p.tokenized: raise HTTPException(409, "Property has already been tokenized")
    try:
        chain_property = landchain_service.read_property(property_id)
        if not chain_property: raise HTTPException(409, "Property is not registered on the current blockchain")
        if not chain_property["verified"]: raise HTTPException(409, "Property has not been verified on the blockchain")
        artifact = client.artifact("PropertyToken"); signer = client.signer()
        factory = client.w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
        tx = factory.constructor(data.token_name, data.symbol, data.total_supply).build_transaction({"from":signer.address,"nonce":client.w3.eth.get_transaction_count(signer.address),"chainId":client.w3.eth.chain_id,"gas":2_000_000,"gasPrice":client.w3.eth.gas_price})
        signed = signer.sign_transaction(tx); tx_hash = client.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = client.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status != 1 or not receipt.contractAddress: raise RuntimeError("Token deployment failed")
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400, "Token deployment failed. Check compiled artifacts, signer, and local node.") from None
    address = Web3.to_checksum_address(receipt.contractAddress)
    row = models.PropertyToken(property_id=property_id,token_name=data.token_name,symbol=data.symbol,total_supply=data.total_supply,price_per_token=data.price_per_token,contract_address=address,deployment_transaction_hash=Web3.to_hex(receipt.transactionHash))
    p.tokenized = True; p.token_contract_address = address
    db.add(row); record_tx(db, property_id, "token_deployed", receipt)
    db.commit()
    return {"property_id":property_id,"token_name":row.token_name,"symbol":row.symbol,"total_supply":data.total_supply,"contract_address":address,"transaction_hash":row.deployment_transaction_hash,"status":"confirmed"}

def balance(db: Session, property_id: int, wallet: str):
    row = db.scalar(select(models.PropertyToken).where(models.PropertyToken.property_id == property_id))
    if not row: raise HTTPException(404, "Property has not been tokenized")
    if not Web3.is_address(wallet): raise HTTPException(422, "Invalid wallet address")
    try: amount = client.token(row.contract_address).functions.balanceOf(Web3.to_checksum_address(wallet)).call()
    except Exception: raise HTTPException(503, "Unable to read token balance from blockchain") from None
    return {"property_id":property_id,"contract_address":row.contract_address,"symbol":row.symbol,"wallet":Web3.to_checksum_address(wallet),"balance":amount}

def transfer(db: Session, property_id: int, data):
    row = db.scalar(select(models.PropertyToken).where(models.PropertyToken.property_id == property_id))
    if not row: raise HTTPException(404, "Property has not been tokenized")
    if not Web3.is_address(data.sender) or not Web3.is_address(data.recipient): raise HTTPException(422, "Invalid wallet address")
    sender=Web3.to_checksum_address(data.sender); recipient=Web3.to_checksum_address(data.recipient); signer=client.signer()
    if signer.address.lower() != sender.lower(): raise HTTPException(403, "Backend signer does not match sender wallet")
    token=client.token(row.contract_address)
    old_sender=token.functions.balanceOf(sender).call(); old_recipient=token.functions.balanceOf(recipient).call()
    if data.amount <= 0: raise HTTPException(422, "Amount must be positive")
    if old_sender < data.amount: raise HTTPException(400, "Insufficient token balance")
    try: receipt=client.send(token.functions.transfer(recipient,data.amount))
    except Exception: raise HTTPException(400, "Token transfer failed on blockchain") from None
    tx_hash=record_tx(db,property_id,"tokens_transferred",receipt); db.commit()
    return {"transaction_hash":tx_hash,"previous_balance":old_sender,"new_balance":old_sender-data.amount,"recipient_previous_balance":old_recipient,"recipient_new_balance":old_recipient+data.amount,"status":"confirmed"}
