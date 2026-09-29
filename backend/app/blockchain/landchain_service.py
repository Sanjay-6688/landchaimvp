from .web3_client import client
from web3 import Web3

def register(property_id, reference, document_hash): return client.send(client.landchain().functions.registerProperty(property_id, reference, document_hash))
def verify(property_id): return client.send(client.landchain().functions.verifyProperty(property_id))
def transfer(property_id, address): return client.send(client.landchain().functions.transferOwnership(property_id, address))
def read_property(property_id):
    if not client.landchain().functions.propertyExists(property_id).call(): return None
    try:
        data = client.landchain().functions.getProperty(property_id).call()
        return {"property_id": data[0], "property_reference": data[1], "owner": Web3.to_checksum_address(data[2]), "document_hash": data[3], "verified": data[4], "exists": data[5]}
    except Exception as exc:
        raise
