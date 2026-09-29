from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from web3 import Web3

class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    email: str
    wallet_address: str
    role: str = "Investor"
    @field_validator("role")
    @classmethod
    def valid_role(cls, v):
        if v not in {"Investor", "Owner", "Administrator"}: raise ValueError("Role must be Investor, Owner, or Administrator")
        return v
    @field_validator("wallet_address")
    @classmethod
    def valid_wallet(cls, v):
        if not Web3.is_address(v): raise ValueError("Invalid wallet address")
        return Web3.to_checksum_address(v)

class UserOut(BaseModel):
    id: int; full_name: str; email: str; wallet_address: str; role: str; created_at: datetime
    model_config = ConfigDict(from_attributes=True)
class PropertyCreate(BaseModel):
    property_id: int = Field(gt=0); owner_user_id: int; title: str; location_address: str
    area_sq_ft: float = Field(gt=0); property_value: float = Field(gt=0); land_reference_code: str; document_hash: str
class TransferRequest(BaseModel): new_owner: str
class TokenizeRequest(BaseModel): token_name: str; symbol: str = Field(min_length=1, max_length=16); total_supply: int = Field(gt=0); price_per_token: float = Field(gt=0)
class TokenTransferRequest(BaseModel): sender: str; recipient: str; amount: int = Field(gt=0)
