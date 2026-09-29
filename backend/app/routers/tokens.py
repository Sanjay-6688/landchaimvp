from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas
from ..database import get_db
from ..services import token_service

router=APIRouter()
@router.get("/tokens/{property_id}/balance")
def balance(property_id: int, wallet: str, db: Session=Depends(get_db)): return token_service.balance(db,property_id,wallet)
@router.post("/tokens/{property_id}/transfer")
def transfer(property_id: int, data: schemas.TokenTransferRequest, db: Session=Depends(get_db)): return token_service.transfer(db,property_id,data)
