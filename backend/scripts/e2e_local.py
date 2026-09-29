"""Run a real API-to-PostgreSQL-to-Hardhat development flow for property #1001.

Run only against the disposable development database and local Hardhat chain.
It expects a clean property ID 1001 and can reuse the demo users from seed_dev.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from web3 import Web3
from app.config import settings

API = "http://127.0.0.1:8000/api"

def require(condition, message):
    if not condition: raise RuntimeError(message)

def main():
    w3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url))
    require(w3.is_connected(), "Local Hardhat node is not connected")
    accounts = w3.eth.accounts
    require(len(accounts) >= 3, "Need three local Hardhat accounts")
    with httpx.Client(timeout=150) as client:
        health = client.get(f"{API}/health").raise_for_status().json()
        require(health["blockchain"] == "connected", "API cannot reach the local chain")
        require(health["postgresql"] == "connected", "E2E requires PostgreSQL; SQLite is not accepted for this run")

        listed = client.get(f"{API}/users").raise_for_status().json()
        users = []
        for index, wallet in enumerate(accounts[:3]):
            user = next((u for u in listed if u["wallet_address"].lower() == wallet.lower()), None)
            if user is None:
                response = client.post(f"{API}/users", json={"full_name": ["E2E Owner", "E2E Investor", "E2E Administrator"][index], "email": f"e2e-{index+1}@landchain.local", "wallet_address": wallet, "role": ["Owner", "Investor", "Administrator"][index]})
                response.raise_for_status(); user = response.json()
            users.append(user)

        registered = client.post(f"{API}/properties/register", json={"property_id":1001,"owner_user_id":users[0]["id"],"title":"E2E Local Property","location_address":"100 End-to-End Drive","area_sq_ft":4000,"property_value":950000,"land_reference_code":"E2E-1001","document_hash":"sha256:landchain-e2e-1001"})
        registered.raise_for_status(); registration = registered.json()
        inspection = client.get(f"{API}/properties/1001/inspect").raise_for_status().json()
        require(inspection["consistency"]["synchronized"], "Registration was not synchronized")
        verification = client.post(f"{API}/properties/1001/verify", json={}).raise_for_status().json()
        ownership = client.post(f"{API}/properties/1001/transfer", json={"new_owner":accounts[1]}).raise_for_status().json()
        token = client.post(f"{API}/properties/1001/tokenize", json={"token_name":"E2E Property Shares","symbol":"E2E","total_supply":1000,"price_per_token":100}).raise_for_status().json()
        initial = client.get(f"{API}/tokens/1001/balance", params={"wallet":accounts[0]}).raise_for_status().json()
        transfer = client.post(f"{API}/tokens/1001/transfer", json={"sender":accounts[0],"recipient":accounts[2],"amount":100}).raise_for_status().json()
        sender = client.get(f"{API}/tokens/1001/balance", params={"wallet":accounts[0]}).raise_for_status().json()
        recipient = client.get(f"{API}/tokens/1001/balance", params={"wallet":accounts[2]}).raise_for_status().json()
        inspection = client.get(f"{API}/properties/1001/inspect").raise_for_status().json()
        require(initial["balance"] == 1000, "Unexpected initial token balance")
        require(sender["balance"] == 900 and recipient["balance"] == 100, "Token balances did not update")
        require(inspection["consistency"]["synchronized"], "Final property state is not synchronized")
        print({"property_id":1001,"registration_tx":registration["transaction_hash"],"verification_tx":verification["transaction_hash"],"ownership_tx":ownership["transaction_hash"],"token_contract":token["contract_address"],"token_transfer_tx":transfer["transaction_hash"],"balances":{"sender":sender["balance"],"recipient":recipient["balance"]},"synchronized":inspection["consistency"]["synchronized"]})

if __name__ == "__main__": main()
