"""Test the ability of bots to hit a target rate."""
from __future__ import annotations

import asyncio
import logging

import pytest
from ethpy import EthConfig
from ethpy.base import wait_for_transaction_receipt
from ethpy.hyperdrive import HyperdriveAddresses
from ethpy.hyperdrive.interface import HyperdriveReadWriteInterface
from fixedpointmath import FixedPoint
from hypertypes import IERC4626HyperdriveContract
from hypertypes.types import ERC20MintableContract
from web3 import Web3
from web3.types import RPCEndpoint

from agent0.hyperdrive.exec import async_execute_agent_trades
from agent0.hyperdrive.interactive import LocalChain, InteractiveHyperdrive
from agent0.hyperdrive.policies.zoo import Zoo
from agent0.hyperdrive.interactive.event_types import CloseLong, CloseShort
from agent0.hyperdrive.interactive.interactive_hyperdrive_agent import InteractiveHyperdriveAgent

# avoid unnecessary warning from using fixtures defined in outer scope
# pylint: disable=redefined-outer-name
# allow accessing _web3 member of chain
# pylint: disable=protected-member

TRADE_AMOUNTS = [0.003, 1e4, 1e5]  # 0.003 is three times the minimum transaction amount of local test deploy
# We hit the target rate to the 5th decimal of precision.
# That means 0.050001324091154488 is close enough to a target rate of 0.05.
PRECISION = FixedPoint(1e-5)
YEAR_IN_SECONDS = 31_536_000


@pytest.fixture(scope="function")
def interactive_hyperdrive(chain: LocalChain) -> InteractiveHyperdrive:
    """Create interactive hyperdrive.

    Arguments
    ---------
    chain: LocalChain
        Local chain.

    Returns
    -------
    InteractiveHyperdrive
        Interactive hyperdrive."""
    interactive_config = InteractiveHyperdrive.Config(
        position_duration=YEAR_IN_SECONDS,  # 1 year term
    )
    return InteractiveHyperdrive(chain, interactive_config)


@pytest.fixture(scope="function")
def arbitrage_andy(interactive_hyperdrive) -> InteractiveHyperdriveAgent:
    """Create Arbitrage Andy interactive hyperdrive agent used to arbitrage the fixed rate to the variable rate.

    Arguments
    ---------
    interactive_hyperdrive: InteractiveHyperdrive
        Interactive hyperdrive.

    Returns
    -------
    InteractiveHyperdriveAgent
        Arbitrage Andy interactive hyperdrive agent."""
    # create arbitrage andy
    andy_base = FixedPoint(1e9)
    andy_config = Zoo.lp_and_arb.Config(
        lp_portion=FixedPoint(0),
        minimum_trade_amount=interactive_hyperdrive.hyperdrive_interface.pool_config.minimum_transaction_amount,
    )
    return interactive_hyperdrive.init_agent(
        base=andy_base, name="andy", policy=Zoo.lp_and_arb, policy_config=andy_config
    )


@pytest.fixture(scope="function")
def manual_agent(interactive_hyperdrive) -> InteractiveHyperdriveAgent:
    """Create manual interactive hyperdrive agent used to manually move markets.

    Arguments
    ---------
    interactive_hyperdrive: InteractiveHyperdrive
        Interactive hyperdrive.

    Returns
    -------
    InteractiveHyperdriveAgent
        Manual interactive hyperdrive agent."""
    return interactive_hyperdrive.init_agent(base=FixedPoint(1e9))


@pytest.mark.anvil
@pytest.mark.parametrize("trade_amount", TRADE_AMOUNTS)
def test_open_long(
    interactive_hyperdrive: InteractiveHyperdrive,
    trade_amount: float,
    arbitrage_andy: InteractiveHyperdriveAgent,
    manual_agent: InteractiveHyperdriveAgent,
):
    """Open a long to hit the target rate."""
    # change the fixed rate
    manual_agent.open_short(bonds=FixedPoint(trade_amount))

    # report starting fixed rate
    logging.info("starting fixed rate is %s", interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate())

    # arbitrage it back (the only trade capable of this is a long)
    arbitrage_andy.execute_policy_action()

    # report results
    fixed_rate = interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate()
    variable_rate = interactive_hyperdrive.hyperdrive_interface.current_pool_state.variable_rate
    logging.info("ending fixed rate is %s", fixed_rate)
    logging.info("variable rate is %s", variable_rate)
    abs_diff = abs(fixed_rate - variable_rate)
    logging.info("difference is %s", abs_diff)
    assert abs_diff < PRECISION


@pytest.mark.anvil
@pytest.mark.parametrize("trade_amount", TRADE_AMOUNTS)
def test_open_short(
    interactive_hyperdrive: InteractiveHyperdrive,
    trade_amount: float,
    arbitrage_andy: InteractiveHyperdriveAgent,
    manual_agent: InteractiveHyperdriveAgent,
):
    """Open a short to hit the target rate."""
    # change the fixed rate
    manual_agent.open_long(base=FixedPoint(trade_amount))

    # report starting fixed rate
    logging.info("starting fixed rate is %s", interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate())

    # arbitrage it back (the only trade capable of this is a short)
    arbitrage_andy.execute_policy_action()

    # report results
    fixed_rate = interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate()
    variable_rate = interactive_hyperdrive.hyperdrive_interface.current_pool_state.variable_rate
    logging.info("ending fixed rate is %s", fixed_rate)
    logging.info("variable rate is %s", variable_rate)
    abs_diff = abs(fixed_rate - variable_rate)
    logging.info("difference is %s", abs_diff)
    assert abs_diff < PRECISION


# pylint: disable=too-many-locals
@pytest.mark.anvil
@pytest.mark.parametrize("trade_amount", [0.003, 10])
def test_close_long(
    interactive_hyperdrive: InteractiveHyperdrive,
    trade_amount: float,
    arbitrage_andy: InteractiveHyperdriveAgent,
    manual_agent: InteractiveHyperdriveAgent,
):
    """Close a long to hit the target rate."""
    # report starting fixed rate
    logging.info("starting fixed rate is %s", interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate())

    # give andy a long position twice the trade amount, to be sufficiently large when closing
    pool_bonds_before = interactive_hyperdrive.hyperdrive_interface.current_pool_state.pool_info.bond_reserves
    pool_shares_before = interactive_hyperdrive.hyperdrive_interface.current_pool_state.pool_info.share_reserves
    block_time_before = interactive_hyperdrive.hyperdrive_interface.current_pool_state.block_time
    event = arbitrage_andy.open_long(base=FixedPoint(3 * trade_amount))
    pool_bonds_after = interactive_hyperdrive.hyperdrive_interface.current_pool_state.pool_info.bond_reserves
    pool_shares_after = interactive_hyperdrive.hyperdrive_interface.current_pool_state.pool_info.share_reserves
    block_time_after = interactive_hyperdrive.hyperdrive_interface.current_pool_state.block_time
    d_bonds = pool_bonds_after - pool_bonds_before  # instead of event.bond_amount
    d_shares = pool_shares_after - pool_shares_before  # instead of event.base_amount
    d_time = block_time_after - block_time_before
    logging.info("Andy opened long %s base.", 3 * trade_amount)
    logging.info("Δtime=%s", d_time)
    logging.info(
        " pool  Δbonds= %s%s, Δbase= %s%s", "+" if d_bonds > 0 else "", d_bonds, "+" if d_shares > 0 else "", d_shares
    )
    logging.info(
        " event Δbonds= %s%s, Δbase= %s%s",
        "+" if event.bond_amount > 0 else "",
        event.bond_amount,
        "+" if event.base_amount > 0 else "",
        event.base_amount,
    )
    # undo this trade manually
    manual_agent.open_short(bonds=FixedPoint(event.bond_amount * FixedPoint(1.006075)))
    logging.info(
        "manually opened short. event Δbonds= %s%s, Δbase= %s%s",
        "+" if event.bond_amount > 0 else "",
        event.bond_amount,
        "+" if event.base_amount > 0 else "",
        event.base_amount,
    )

    # report fixed rate
    logging.info("fixed rate is %s", interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate())

    # change the fixed rate
    event = manual_agent.open_long(base=FixedPoint(trade_amount))
    logging.info(
        "manually opened short. event Δbonds= %s%s, Δbase= %s%s",
        "+" if event.bond_amount > 0 else "",
        event.bond_amount,
        "+" if event.base_amount > 0 else "",
        event.base_amount,
    )
    # report fixed rate
    logging.info("fixed rate is %s", interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate())

    # arbitrage it all back in one trade
    pool_bonds_before = interactive_hyperdrive.hyperdrive_interface.current_pool_state.pool_info.bond_reserves
    pool_shares_before = interactive_hyperdrive.hyperdrive_interface.current_pool_state.pool_info.share_reserves
    block_time_before = interactive_hyperdrive.hyperdrive_interface.current_pool_state.block_time
    event_list = arbitrage_andy.execute_policy_action()
    logging.info("Andy executed %s", event_list)
    event = event_list[0] if isinstance(event_list, list) else event_list
    assert isinstance(event, CloseLong)
    pool_bonds_after = interactive_hyperdrive.hyperdrive_interface.current_pool_state.pool_info.bond_reserves
    pool_shares_after = interactive_hyperdrive.hyperdrive_interface.current_pool_state.pool_info.share_reserves
    block_time_after = interactive_hyperdrive.hyperdrive_interface.current_pool_state.block_time
    d_bonds = pool_bonds_after - pool_bonds_before  # instead of event.bond_amount
    d_shares = pool_shares_after - pool_shares_before  # instead of event.base_amount
    d_time = block_time_after - block_time_before
    logging.info("Andy closed long. amount determined by policy.")
    logging.info("Δtime=%s", d_time)
    logging.info(
        " pool  Δbonds= %s%s, Δbase= %s%s", "+" if d_bonds > 0 else "", d_bonds, "+" if d_shares > 0 else "", d_shares
    )
    logging.info(
        " event Δbonds= %s%s, Δbase= %s%s",
        "+" if event.bond_amount > 0 else "",
        event.bond_amount,
        "+" if event.base_amount > 0 else "",
        event.base_amount,
    )

    # report results
    fixed_rate = interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate()
    variable_rate = interactive_hyperdrive.hyperdrive_interface.current_pool_state.variable_rate
    logging.info("ending fixed rate is %s", fixed_rate)
    logging.info("variable rate is %s", variable_rate)
    abs_diff = abs(fixed_rate - variable_rate)
    logging.info("difference is %s", abs_diff)
    assert abs_diff < PRECISION


@pytest.mark.anvil
def test_already_at_target(interactive_hyperdrive: InteractiveHyperdrive, arbitrage_andy: InteractiveHyperdriveAgent):
    """Already at target, do nothing."""
    # report starting fixed rate
    logging.info("starting fixed rate is %s", interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate())

    # modify Andy to be done_on_empty
    andy_interactive_policy = arbitrage_andy.agent.policy
    assert hasattr(andy_interactive_policy, "sub_policy") and isinstance(
        getattr(andy_interactive_policy, "sub_policy"), Zoo.lp_and_arb
    )
    andy_policy = getattr(andy_interactive_policy, "sub_policy")
    assert hasattr(andy_policy, "policy_config") and isinstance(
        getattr(andy_policy, "policy_config"), Zoo.lp_and_arb.Config
    )
    andy_policy.policy_config.done_on_empty = True

    # arbitrage it back
    arbitrage_andy.execute_policy_action()

    # report results
    fixed_rate = interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate()
    variable_rate = interactive_hyperdrive.hyperdrive_interface.current_pool_state.variable_rate
    logging.info("ending fixed rate is %s", fixed_rate)
    logging.info("variable rate is %s", variable_rate)
    abs_diff = abs(fixed_rate - variable_rate)
    logging.info("difference is %s", abs_diff)
    assert abs_diff < PRECISION


@pytest.mark.anvil
def test_reduce_long(interactive_hyperdrive: InteractiveHyperdrive, arbitrage_andy: InteractiveHyperdriveAgent):
    """Reduce a long position."""

    # give Andy a long
    event = arbitrage_andy.open_long(base=FixedPoint(10))

    # advance time to maturity
    interactive_hyperdrive.chain.advance_time(int(YEAR_IN_SECONDS / 2), create_checkpoints=False)

    # see if he reduces the long
    event = arbitrage_andy.execute_policy_action()
    event = event[0] if isinstance(event, list) else event
    logging.info("event is %s", event)
    assert isinstance(event, CloseLong)


@pytest.mark.anvil
def test_reduce_short(interactive_hyperdrive: InteractiveHyperdrive, arbitrage_andy: InteractiveHyperdriveAgent):
    """Reduce a short position."""

    logging.info("starting fixed rate is %s", interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate())

    # give Andy a short
    event = arbitrage_andy.open_short(bonds=FixedPoint(10))

    logging.info("fixed rate after open short is %s", interactive_hyperdrive.hyperdrive_interface.calc_fixed_rate())

    # advance time to maturity
    interactive_hyperdrive.chain.advance_time(int(YEAR_IN_SECONDS / 2), create_checkpoints=False)

    # see if he reduces the short
    event = arbitrage_andy.execute_policy_action()
    event = event[0] if isinstance(event, list) else event
    logging.info("event is %s", event)
    assert isinstance(event, CloseShort)


@pytest.mark.anvil
def test_max_open_long(chain: LocalChain):
    """Open a max long."""
    web3 = chain._web3

    # connect to external anvil
    web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:9999"))

    # Load anvil state with already deployed hyperdrive
    with open("bytecode.hex", "r", encoding="utf-8") as file:
        hex_data = file.read()
    response = web3.provider.make_request(method=RPCEndpoint("anvil_loadState"), params=[hex_data])
    logging.info("anvil_loadState response is %s", response)

    # rawdog trade with the pool
    amount_of_base_to_mint = int(1_000_000 * 10**18)
    base_token_contract_address = "0xa82fF9aFd8f496c3d6ac40E2a0F282E47488CFc9"
    hyperdrive_contract_addsress = "0x55652FF92Dc17a21AD6810Cce2F4703fa2339CAE"
    base_token_contract: ERC20MintableContract = ERC20MintableContract.factory(w3=web3)(
        web3.to_checksum_address(base_token_contract_address)
    )
    signer_checksum_address = web3.eth.accounts[0]
    signer_private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

    # mint
    unsent_mint_tx = base_token_contract.functions.mint(amount_of_base_to_mint)
    built_tx = unsent_mint_tx.build_transaction(
        {"from": web3.eth.accounts[0], "gas": 1000000, "nonce": web3.eth.get_transaction_count(signer_checksum_address)}
    )
    signed_txn = web3.eth.account.sign_transaction(built_tx, signer_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    logging.info("mint txn is %s", tx_receipt)
    assert tx_receipt["status"] == 1

    # approve
    unsent_approve_tx = base_token_contract.functions.approve(
        web3.to_checksum_address(hyperdrive_contract_addsress),
        amount_of_base_to_mint,
    )
    built_tx = unsent_approve_tx.build_transaction(
        {"from": web3.eth.accounts[0], "gas": 1000000, "nonce": web3.eth.get_transaction_count(signer_checksum_address)}
    )
    signed_txn = web3.eth.account.sign_transaction(built_tx, signer_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    logging.info("approve txn is %s", tx_receipt)
    assert tx_receipt["status"] == 1

    hyperdrive_contract: IERC4626HyperdriveContract = IERC4626HyperdriveContract.factory(w3=web3)(
        web3.to_checksum_address(hyperdrive_contract_addsress)
    )
    # inspect pool
    pool_info = hyperdrive_contract.functions.getPoolInfo().call()
    logging.info("pool info is %s", pool_info)

    # open long
    fn_args = (
        int(20),
        1,  # min_output
        1,  # min_share_price
        (  # IHyperdrive.Options
            signer_checksum_address,  # destination
            True,  # asBase
            bytes(0),  # extraData
        ),
    )
    func_handle = hyperdrive_contract.get_function_by_name("openLong")(*fn_args)
    unsent_txn = func_handle.build_transaction(
        {
            "from": signer_checksum_address,
            "nonce": web3.eth.get_transaction_count(signer_checksum_address),
            "gas": 10000000,
        }
    )
    signed_txn = web3.eth.account.sign_transaction(unsent_txn, signer_private_key)
    logging.info("signed_txn is %s", signed_txn)

    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    logging.info("tx_receipt is %s", tx_receipt)

    # check if the trade was successful
    assert tx_receipt["status"] == 1
