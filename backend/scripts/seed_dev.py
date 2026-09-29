"""Development-only seed: creates users and performs real local-chain operations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from web3 import Web3
from app.database import Base, SessionLocal, engine
from app import models
from app.blockchain.web3_client import client
from app.services import property_service, token_service
from app.schemas import PropertyCreate, TokenizeRequest

def main():
    if not client.connected(): raise SystemExit("Hardhat node is not reachable. Start it before seeding.")
    if not client.contract or not client.account: raise SystemExit("Set LANDCHAIN_CONTRACT_ADDRESS and BLOCKCHAIN_PRIVATE_KEY first.")
    Base.metadata.create_all(engine)
    accounts=client.w3.eth.accounts
    if len(accounts)<3: raise SystemExit("Need at least three unlocked Hardhat development accounts.")
    with SessionLocal() as db:
        seeded=[]
        for i, address in enumerate(accounts[:3]):
            email=f"demo{i+1}@landchain.local"
            user=db.scalar(select(models.User).where(models.User.email==email))
            if not user:
                user=models.User(full_name=["Avery Owner","Jordan Investor","Morgan Administrator"][i],email=email,wallet_address=Web3.to_checksum_address(address),role=["Owner","Investor","Administrator"][i]); db.add(user); db.commit(); db.refresh(user)
            seeded.append(user)
        owner=seeded[0]
        for pid,title,ref,hash_ in [(1002,"Riverside Apartments","DEMO-1002","sha256:landchain-demo-1002"),(1003,"Central Market Lot","DEMO-1003","sha256:landchain-demo-1003")]:
            existing=db.scalar(select(models.Property).where(models.Property.property_id==pid))
            if not existing:
                payload=PropertyCreate(property_id=pid,owner_user_id=owner.id,title=title,location_address=f"{pid} Demo Avenue, Local City",area_sq_ft=4200+pid%100,property_value=850000+pid,land_reference_code=ref,document_hash=hash_)
                property_service.register(db,payload)
                existing=db.scalar(select(models.Property).where(models.Property.property_id==pid))
            if not existing.blockchain_verified:
                property_service.verify(db,pid)
        p=db.scalar(select(models.Property).where(models.Property.property_id==1002))
        if not p.tokenized:
            token_service.tokenize(db,1002,TokenizeRequest(token_name="Riverside Property Shares",symbol="RIV",total_supply=10000,price_per_token=85))
            token=db.scalar(select(models.PropertyToken).where(models.PropertyToken.property_id==1002))
            receipt=client.send(client.token(token.contract_address).functions.transfer(seeded[1].wallet_address,100))
            property_service.record_tx(db,1002,"demo_tokens_distributed",receipt); db.commit()
        print("Development seed complete: 3 users, properties #1002 and #1003 registered and verified on-chain, and property #1002 tokenized.")

if __name__=="__main__": main()
