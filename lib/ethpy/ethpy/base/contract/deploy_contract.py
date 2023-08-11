"""Helper function for deploying contracts using web3."""

from __future__ import annotations

from typing import Any

from eth_typing import Address
from web3 import Web3
from web3.contract.contract import Contract


def deploy_contract_and_return(
    web3: Web3, abi: list[Any], bytecode: str, deploy_addr: str, args: list | None = None
) -> tuple[Address, Contract]:
    """Deploys a contract given the abi and the bytecode, and returns the web3 contract object along with the address.

    Note this function is blocking until the tx receipt returns, indicating a successful deployment

    Arguments
    ---------
    web3: Web3
        web3 provider object
    abi: list[Any]
        The contract abi
    bytecode: str
        The contract bytecode
    deploy_addr:
        The address of the account that's deploying the contract
    args: list[Any] | None:
        List of arguments to pass to the contract constructor
        No arguments if None

    Returns
    -------
    str
        The deployed contract address

    """
    contract_addr: Address = deploy_contract(web3, abi, bytecode, deploy_addr, args)  # type: ignore
    contract = web3.eth.contract(address=contract_addr, abi=abi)
    return contract_addr, contract


def deploy_contract(web3: Web3, abi: list[Any], bytecode: str, deploy_addr: str, args: list[Any] | None = None) -> str:
    """Deploys a contract given the abi and the bytecode.

    Note this function is blocking until the tx receipt returns, indicating a successful deployment

    Arguments
    ---------
    web3: Web3
        web3 provider object
    abi: list[Any]
        The contract abi
    bytecode: str
        The contract bytecode
    deploy_addr:
        The address of the account that's deploying the contract
    args: list[Any] | None:
        List of arguments to pass to the contract constructor
        No arguments if None

    Returns
    -------
    str
        The deployed contract address

    """
    if args is None:
        args = []
    contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract.constructor(*args).transact({"from": deploy_addr})
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt["contractAddress"] is not None:
        contract_addr = tx_receipt["contractAddress"]
        return contract_addr
    raise AssertionError("Deploying contract didn't return contract address")
