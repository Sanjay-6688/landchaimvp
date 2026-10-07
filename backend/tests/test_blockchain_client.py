from types import SimpleNamespace
from unittest.mock import Mock

from app.blockchain.web3_client import client


def test_send_estimates_gas_with_safety_margin(monkeypatch):
    signer = Mock(address="0x0000000000000000000000000000000000000001")
    signer.sign_transaction.return_value = SimpleNamespace(raw_transaction=b"signed")
    receipt = SimpleNamespace(status=1)
    eth = SimpleNamespace(
        get_transaction_count=lambda _address: 7,
        chain_id=11155111,
        gas_price=10,
        get_block=lambda _tag: {"gasLimit": 30_000_000},
        send_raw_transaction=lambda _raw: b"tx-hash",
        wait_for_transaction_receipt=lambda _hash, timeout: receipt,
    )
    monkeypatch.setattr(client, "signer", lambda: signer)
    monkeypatch.setattr(client, "w3", SimpleNamespace(eth=eth))

    function = Mock()
    function.estimate_gas.return_value = 100_000
    function.build_transaction.return_value = {"to": "contract"}

    result = client.send(function)

    function.estimate_gas.assert_called_once_with({"from": signer.address})
    assert function.build_transaction.call_args.args[0]["gas"] == 125_000
    assert function.build_transaction.call_args.args[0]["nonce"] == 7
    assert result is receipt
