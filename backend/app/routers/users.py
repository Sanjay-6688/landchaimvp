from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router=APIRouter()
@router.post("/users", response_model=schemas.UserOut, status_code=201)
def create_user(data: schemas.UserCreate, db: Session=Depends(get_db)):
    user=models.User(**data.model_dump()); db.add(user)
    try: db.commit(); db.refresh(user)
    except IntegrityError: db.rollback(); raise HTTPException(409,"Email or wallet address is already registered") from None
    return user
@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session=Depends(get_db)): return db.scalars(select(models.User).order_by(models.User.id)).all()
