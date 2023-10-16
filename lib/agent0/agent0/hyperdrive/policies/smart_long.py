"""Agent policy for leveraged long positions"""
from __future__ import annotations

from typing import TYPE_CHECKING

from agent0.hyperdrive.state import (HyperdriveActionType,
                                     HyperdriveMarketAction)
from elfpy import WEI
from elfpy.types import MarketType, Trade
from fixedpointmath import FixedPoint, FixedPointMath

from .hyperdrive_policy import HyperdrivePolicy

if TYPE_CHECKING:
    from agent0.hyperdrive.state import HyperdriveWallet
    from ethpy.hyperdrive import HyperdriveInterface
    from numpy.random._generator import Generator as NumpyGenerator
# pylint: disable=too-few-public-methods


class SmartLong(HyperdrivePolicy):
    """Agent that opens longs to push the fixed-rate towards the variable-rate."""

    @classmethod
    def description(cls) -> str:
        """Describe the policy in a user friendly manner that allows newcomers to decide whether to use it.

        Returns
        -------
        str
            A description of the policy.
        """

        raw_description = """
        My strategy:
            - I'm not willing to open a long if it will cause the fixed-rate apr to go below the variable rate
                - I simulate the outcome of my trade, and only execute on this condition
            - I only close if the position has matured
            - I only open one long at a time
        """
        return super().describe(raw_description)

    # pylint: disable=too-many-arguments

    def __init__(
        self,
        budget: FixedPoint,
        rng: NumpyGenerator,
        trade_chance: FixedPoint,
        risk_threshold: FixedPoint,
        slippage_tolerance: FixedPoint | None = None,
    ) -> None:
        """Add custom stuff then call basic policy init"""
        if not isinstance(trade_chance, FixedPoint):
            raise TypeError(f"{trade_chance=} must be of type `FixedPoint`")
        if not isinstance(risk_threshold, FixedPoint):
            raise TypeError(f"{risk_threshold=} must be of type `FixedPoint`")
        self.trade_chance = trade_chance
        self.risk_threshold = risk_threshold
        super().__init__(budget, rng, slippage_tolerance)

    def action(self, interface: HyperdriveInterface, wallet: HyperdriveWallet) -> list[Trade[HyperdriveMarketAction]]:
        """Implement a Long Louie user strategy

        Arguments
        ---------
        interface : HyperdriveInterface
            The trading market.
        wallet : HyperdriveWallet
            The agent's wallet.

        Returns
        -------
        action_list : list[MarketAction]
        """
        # Any trading at all is based on a weighted coin flip -- they have a trade_chance% chance of executing a trade
        gonna_trade = self.rng.choice([True, False], p=[float(self.trade_chance), 1 - float(self.trade_chance)])
        if not gonna_trade:
            return []
        action_list = []
        for long_time in wallet.longs:  # loop over longs # pylint: disable=consider-using-dict-items
            # if any long is mature
            # TODO: should we make this less time? they dont close before the agent runs out of money
            # how to intelligently pick the length? using PNL I guess.
            if (interface.current_block_time - FixedPoint(long_time)) >= interface.pool_config["positionDuration"]:
                trade_amount = wallet.longs[long_time].balance  # close the whole thing
                action_list += [
                    Trade(
                        market_type=MarketType.HYPERDRIVE,
                        market_action=HyperdriveMarketAction(
                            action_type=HyperdriveActionType.CLOSE_LONG,
                            trade_amount=trade_amount,
                            slippage_tolerance=self.slippage_tolerance,
                            wallet=wallet,
                            maturity_time=long_time,
                        ),
                    )
                ]
        long_balances = [long.balance for long in wallet.longs.values()]
        has_opened_long = bool(any(long_balance > 0 for long_balance in long_balances))
        # only open a long if the fixed rate is higher than variable rate
        if (interface.fixed_rate - interface.variable_rate) > self.risk_threshold and not has_opened_long:
            total_bonds_to_match_variable_apr = (
                interface.bonds_given_shares_and_rate(target_rate=interface.variable_rate)
            )
            # get the delta bond amount & convert units
            bond_reserves: FixedPoint = interface.pool_info["bondReserves"]
            new_bonds_to_match_variable_apr = (
                bond_reserves - total_bonds_to_match_variable_apr
            ) * interface.spot_price
            # new_base_to_match_variable_apr = interface.calc_shares_out_given_bonds_in(
            new_base_to_match_variable_apr = interface.get_out_for_in(new_bonds_to_match_variable_apr, shares_in=False)
            # get the maximum amount the agent can long given the market and the agent's wallet
            max_base = interface.get_max_long(wallet.balance.amount)
            # don't want to trade more than the agent has or more than the market can handle
            trade_amount = FixedPointMath.minimum(max_base, new_base_to_match_variable_apr)
            if trade_amount > WEI and wallet.balance.amount > WEI:
                action_list += [
                    Trade(
                        market_type=MarketType.HYPERDRIVE,
                        market_action=HyperdriveMarketAction(
                            action_type=HyperdriveActionType.OPEN_LONG,
                            trade_amount=trade_amount,
                            slippage_tolerance=self.slippage_tolerance,
                            wallet=wallet,
                        ),
                    )
                ]
        return action_list
