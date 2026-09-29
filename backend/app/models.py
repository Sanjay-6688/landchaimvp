from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    wallet_address: Mapped[str] = mapped_column(String(42), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(24), default="Investor")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    properties: Mapped[list["Property"]] = relationship(back_populates="owner")

class Property(Base):
    __tablename__ = "properties"
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    location_address: Mapped[str] = mapped_column(Text)
    area_sq_ft: Mapped[float] = mapped_column(Float)
    property_value: Mapped[float] = mapped_column(Numeric(18, 2))
    land_reference_code: Mapped[str] = mapped_column(String(120))
    document_hash: Mapped[str] = mapped_column(Text)
    blockchain_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    blockchain_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    tokenized: Mapped[bool] = mapped_column(Boolean, default=False)
    token_contract_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    owner: Mapped[User] = relationship(back_populates="properties")
    verification: Mapped["PropertyVerification | None"] = relationship(back_populates="property", uselist=False, cascade="all, delete-orphan")
    token: Mapped["PropertyToken | None"] = relationship(back_populates="property", uselist=False, cascade="all, delete-orphan")
    transactions: Mapped[list["BlockchainTransaction"]] = relationship(back_populates="property", cascade="all, delete-orphan")

class PropertyVerification(Base):
    __tablename__ = "property_verifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("properties.property_id", ondelete="CASCADE"), unique=True)
    verifier_address: Mapped[str] = mapped_column(String(42))
    transaction_hash: Mapped[str] = mapped_column(String(66))
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    property: Mapped[Property] = relationship(back_populates="verification")

class PropertyToken(Base):
    __tablename__ = "property_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("properties.property_id", ondelete="CASCADE"), unique=True)
    token_name: Mapped[str] = mapped_column(String(120))
    symbol: Mapped[str] = mapped_column(String(16))
    total_supply: Mapped[int] = mapped_column(Numeric(78, 0))
    price_per_token: Mapped[float] = mapped_column(Numeric(18, 2))
    contract_address: Mapped[str] = mapped_column(String(42), unique=True)
    deployment_transaction_hash: Mapped[str] = mapped_column(String(66))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    property: Mapped[Property] = relationship(back_populates="token")

class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("properties.property_id", ondelete="SET NULL"), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(48))
    transaction_hash: Mapped[str] = mapped_column(String(66), unique=True)
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    property: Mapped[Property | None] = relationship(back_populates="transactions")
