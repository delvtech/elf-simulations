"""Implements abstract classes that control user behavior"""
from __future__ import annotations  # types will be strings by default in 3.11

from typing import TYPE_CHECKING
from dataclasses import dataclass, field

import elfpy.types as types

if TYPE_CHECKING:
    from elfpy.markets.hyperdrive import Market
    from typing import Any


@dataclass
class Long:
    r"""An open long position.

    Parameters
    ----------
    balance : float
        The amount of bonds that the position is long.
    """

    balance: float


@dataclass
class Short:
    r"""An open short position.

    Parameters
    ----------
    balance : float
        The amount of bonds that the position is short.
    open_share_price: float
        The share price at the time the short was opened.
    """

    balance: float
    open_share_price: float


@dataclass
class Borrow:
    r"""An open borrow position

    Parameters
    ----------
    borrow_token : TokenType
    .. todo: add explanation
    borrow_amount : float
    .. todo: add explanation
    collateral_token : TokenType
    .. todo: add explanation
    collateral_amount: float
    .. todo: add explanation
    start_time : float
    .. todo: add explanation
    """
    borrow_token: types.TokenType
    borrow_amount: float
    borrow_shares: float
    collateral_token: types.TokenType
    collateral_amount: float
    start_time: float


@dataclass()
class Wallet:
    r"""Stores what is in the agent's wallet

    Parameters
    ----------
    address : int
        The trader's address.
    balance : Quantity
        The base assets that held by the trader.
    lp_tokens : float
        The LP tokens held by the trader.
    longs : Dict[float, Long]
        The long positions held by the trader.
    shorts : Dict[float, Short]
        The short positions held by the trader.
    fees_paid : float
        The fees paid by the wallet.
    """

    # pylint: disable=too-many-instance-attributes
    # dataclasses can have many attributes

    # agent identifier
    address: int

    # fungible
    balance: types.Quantity = field(default_factory=lambda: types.Quantity(amount=0, unit=types.TokenType.BASE))
    # TODO: Support multiple typed balances:
    #     balance: Dict[types.TokenType, types.Quantity] = field(default_factory=dict)
    lp_tokens: float = 0

    # non-fungible (identified by key=mint_time, stored as dict)
    longs: dict[float, Long] = field(default_factory=dict)
    shorts: dict[float, Short] = field(default_factory=dict)
    # borrow and  collateral have token type, which is not represented here
    # this therefore assumes that only one token type can be used at any given mint time
    borrows: dict[float, Borrow] = field(default_factory=dict)
    fees_paid: float = 0

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def get_state(self, market: Market) -> dict[str, float]:
        r"""The wallet's current state of public variables

        .. todo:: This will go away once we finish refactoring the state
        """
        lp_token_value = 0
        # proceed further only if the agent has LP tokens and avoid divide by zero
        if self.lp_tokens > 0 and market.market_state.lp_total_supply > 0:
            share_of_pool = self.lp_tokens / market.market_state.lp_total_supply
            pool_value = (
                market.market_state.bond_reserves * market.spot_price  # in base
                + market.market_state.share_reserves * market.market_state.share_price  # in base
            )
            lp_token_value = pool_value * share_of_pool  # in base
        share_reserves = market.market_state.share_reserves
        # compute long values in units of base
        longs_value = 0
        longs_value_no_mock = 0
        for mint_time, long in self.longs.items():
            if long.balance > 0 and share_reserves:
                balance = market.close_long(self.address, long.balance, mint_time)[1].balance.amount
            else:
                balance = 0.0
            longs_value += balance
            longs_value_no_mock += long.balance * market.spot_price
        # compute short values in units of base
        shorts_value = 0
        shorts_value_no_mock = 0
        for mint_time, short in self.shorts.items():
            balance = 0.0
            if (
                short.balance > 0
                and share_reserves > 0
                and market.market_state.bond_reserves - market.market_state.bond_buffer > short.balance
            ):
                balance = market.close_short(self.address, short.open_share_price, short.balance, mint_time)[
                    1
                ].balance.amount
            shorts_value += balance
            base_no_mock = short.balance * (1 - market.spot_price)
            shorts_value_no_mock += base_no_mock
        return {
            f"agent_{self.address}_base": self.balance.amount,
            f"agent_{self.address}_lp_tokens": lp_token_value,
            f"agent_{self.address}_num_longs": len(self.longs),
            f"agent_{self.address}_num_shorts": len(self.shorts),
            f"agent_{self.address}_total_longs": longs_value,
            f"agent_{self.address}_total_shorts": shorts_value,
            f"agent_{self.address}_total_longs_no_mock": longs_value_no_mock,
            f"agent_{self.address}_total_shorts_no_mock": shorts_value_no_mock,
        }

    def get_state_keys(self) -> list:
        """Get state keys for a wallet."""
        return [
            f"agent_{self.address}_base",
            f"agent_{self.address}_lp_tokens",
            f"agent_{self.address}_num_longs",
            f"agent_{self.address}_num_shorts",
            f"agent_{self.address}_total_longs",
            f"agent_{self.address}_total_shorts",
            f"agent_{self.address}_total_longs_no_mock",
            f"agent_{self.address}_total_shorts_no_mock",
        ]
