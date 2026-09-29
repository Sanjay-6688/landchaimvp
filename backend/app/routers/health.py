from fastapi import APIRouter
from sqlalchemy import text
from ..database import SessionLocal, engine
from ..blockchain.web3_client import client
from ..config import settings

router = APIRouter()
@router.get("/health")
def health():
    database_status="unavailable"
    try:
        with SessionLocal() as db: db.execute(text("SELECT 1"))
        database_status="connected" if engine.dialect.name == "postgresql" else "not_postgresql"
    except Exception: pass
    blockchain_status="connected" if client.connected() else "unavailable"
    chain_id=current_block=None
    if blockchain_status == "connected":
        try: chain_id=client.w3.eth.chain_id; current_block=client.w3.eth.block_number
        except Exception: blockchain_status="unavailable"
    return {"backend":"ok","postgresql":database_status,"blockchain":blockchain_status,"chain_id":chain_id,"current_block":current_block,"landchain_contract_address":settings.landchain_contract_address or None}
