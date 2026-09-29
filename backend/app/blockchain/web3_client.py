import json
from pathlib import Path
from web3 import Web3
from web3.contract import Contract
from ..config import settings

LANDCHAIN_ABI = [
 {"type":"function","name":"registerProperty","stateMutability":"nonpayable","inputs":[{"name":"propertyId","type":"uint256"},{"name":"propertyReference","type":"string"},{"name":"documentHash","type":"string"}],"outputs":[]},
 {"type":"function","name":"verifyProperty","stateMutability":"nonpayable","inputs":[{"name":"propertyId","type":"uint256"}],"outputs":[]},
 {"type":"function","name":"transferOwnership","stateMutability":"nonpayable","inputs":[{"name":"propertyId","type":"uint256"},{"name":"newOwner","type":"address"}],"outputs":[]},
 {"type":"function","name":"getProperty","stateMutability":"view","inputs":[{"name":"propertyId","type":"uint256"}],"outputs":[{"name":"","type":"tuple","components":[{"name":"propertyId","type":"uint256"},{"name":"propertyReference","type":"string"},{"name":"owner","type":"address"},{"name":"documentHash","type":"string"},{"name":"verified","type":"bool"},{"name":"exists","type":"bool"}]}]},
 {"type":"function","name":"getOwner","stateMutability":"view","inputs":[{"name":"propertyId","type":"uint256"}],"outputs":[{"name":"","type":"address"}]},
 {"type":"function","name":"isVerified","stateMutability":"view","inputs":[{"name":"propertyId","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]}
 ,{"type":"function","name":"propertyExists","stateMutability":"view","inputs":[{"name":"propertyId","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]}
]
TOKEN_ABI = [
 {"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"account","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
 {"type":"function","name":"transfer","stateMutability":"nonpayable","inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]},
 {"type":"function","name":"symbol","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"string"}]},
 {"type":"function","name":"totalSupply","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint256"}]}
]

class BlockchainClient:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url, request_kwargs={"timeout": 10}))
        self.account = self.w3.eth.account.from_key(settings.blockchain_private_key) if settings.blockchain_private_key else None
        self.contract: Contract | None = self.w3.eth.contract(address=Web3.to_checksum_address(settings.landchain_contract_address), abi=LANDCHAIN_ABI) if settings.landchain_contract_address and Web3.is_address(settings.landchain_contract_address) else None

    def connected(self): return self.w3.is_connected()
    def signer(self):
        if not self.account: raise RuntimeError("Blockchain signer is not configured")
        return self.account
    def landchain(self):
        if not self.contract: raise RuntimeError("LandChain contract is not configured")
        return self.contract
    def token(self, address):
        if not Web3.is_address(address): raise RuntimeError("Invalid token contract address")
        return self.w3.eth.contract(address=Web3.to_checksum_address(address), abi=TOKEN_ABI)
    def send(self, function, *, gas=500000):
        signer = self.signer()
        tx = function.build_transaction({"from": signer.address, "nonce": self.w3.eth.get_transaction_count(signer.address), "chainId": self.w3.eth.chain_id, "gas": gas, "gasPrice": self.w3.eth.gas_price})
        signed = signer.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status != 1: raise RuntimeError("Blockchain transaction failed")
        return receipt
    def artifact(self, contract_name):
        # Hardhat emits compiler artifacts here; paths are resolved from this module.
        p = Path(__file__).resolve().parents[3] / "blockchain" / "artifacts" / "contracts" / f"{contract_name}.sol" / f"{contract_name}.json"
        if not p.exists(): raise RuntimeError(f"Missing compiled {contract_name} artifact; compile blockchain contracts first")
        return json.loads(p.read_text())

client = BlockchainClient()
