from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..services import property_service

router=APIRouter()
@router.post("/properties/register", status_code=201)
def register(data: schemas.PropertyCreate, db: Session=Depends(get_db)): return property_service.register(db,data)
@router.get("/properties")
def list_properties(db: Session=Depends(get_db)):
    rows=db.scalars(select(models.Property).order_by(models.Property.property_id)).all()
    return [property_service.property_out(p) for p in rows]
@router.get("/properties/{property_id}")
def get_property(property_id: int, db: Session=Depends(get_db)):
    p=db.scalar(select(models.Property).where(models.Property.property_id==property_id))
    if not p: raise HTTPException(404,"Property does not exist")
    return property_service.property_out(p)
@router.get("/properties/{property_id}/inspect")
def inspect(property_id: int, db: Session=Depends(get_db)): return property_service.inspect(db,property_id)
@router.post("/properties/{property_id}/verify")
def verify(property_id: int, db: Session=Depends(get_db)): return property_service.verify(db,property_id)
@router.post("/properties/{property_id}/transfer")
def transfer(property_id: int, data: schemas.TransferRequest, db: Session=Depends(get_db)): return property_service.transfer_owner(db,property_id,data.new_owner)
@router.post("/properties/{property_id}/tokenize")
def tokenize(property_id: int, data: schemas.TokenizeRequest, db: Session=Depends(get_db)):
    from ..services.token_service import tokenize as do_tokenize
    return do_tokenize(db,property_id,data)
