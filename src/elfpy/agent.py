"""
Implements abstract classes that control agent behavior
"""

from __future__ import annotations  # types will be strings by default in 3.11
from typing import TYPE_CHECKING, Iterable
import logging
import numpy as np

from elfpy.utils.outputs import float_to_string
from elfpy.wallet import Long, Short, Wallet
from elfpy.types import MarketAction, MarketActionType, Quantity, TokenType

if TYPE_CHECKING:
    from elfpy.markets import Market


class Agent:
    """
    Implements a class that controls agent behavior agent has a budget that is a dict, keyed with a
    date value is an inte with how many tokens they have for that date

    Attributes
    ----------

    market : elfpy.markets.Market
        Market object that this Agent will be trading on.
    rng : numpy.random._generator.Generator
        Random number generator used for various simulation functions
    wallet_address : int
        Random ID used to identify this specific agent in the simulation
    budget : float
        Amount of assets that this agent has available for spending in the simulation
    last_update_spend : float
        Time relative to the market, in yearfracs, when this agent last made a trade. This is used to track PnL
    product_of_time_and_base : float
        Helper attribute used to track how an agent spends their assets over time
    wallet : elfpy.wallet.Wallet
        Wallet object which tracks the agent's asset balances

    Methods
    -------
    create_agent_action(action_type: MarketActionType, trade_amount: float, mint_time: float = 0) -> MarketAction
        Creates and returns a MarketAction object which represents a trade that this agent can make
    action(self) -> list[MarketAction]
        Execute the MarketAction implemented by a specific policy
    get_max_pt_short(self) -> float
        Returns an approximation of maximum amount of base that the agent can short given current market conditions
    get_trade_list(self) -> list[MarketAction]
        Helper function for computing a agent trade
    update_spend(self) -> None
        Track over time the agent's weighted average spend, for return calculation
    update_wallet(self, wallet_deltas: Wallet) -> None
        Update the agent's wallet
    get_liquidation_trades(self) -> list[MarketAction]
        Get final trades for liquidating positions
    log_status_report(self) -> None
        Logs user state
    log_final_report(self) -> None
        Logs a report of the agent's state

    """

    def __init__(self, wallet_address: int, budget: float):
        """
        Set up initial conditions
        """
        self.budget: float = budget
        self.last_update_spend: float = 0  # timestamp
        self.product_of_time_and_base: float = 0
        self.wallet: Wallet = Wallet(address=wallet_address, base=budget)

    def create_agent_action(
        self, action_type: MarketActionType, trade_amount: float, mint_time: float = 0
    ) -> MarketAction:
        """
        Creates and returns a MarketAction object which represents a trade that this agent can make

        Arguments
        ---------
        action_type : MarketActionType
            Type of action this function will execute. Must be one of the supported MarketActionTypes
        trade_amount : float
            Amount of assets that the agent will trade
        mint_time : float
            Time relative to the market at which the tokens relevant to this trade were minted, in yearfracs

        Returns
        -------
        MarketAction
            The MarketAction object that contains the details about the action to execute in the market
        """
        agent_action = MarketAction(
            # these two variables are required to be set by the strategy
            action_type=action_type,
            trade_amount=trade_amount,
            # next two variables are set automatically by the basic agent class
            wallet_address=self.wallet.address,
            mint_time=mint_time,
        )
        return agent_action

    def action(self, market: Market) -> list[MarketAction]:
        """Specify action from the policy"""
        """
        Abstract method meant to be implemented by the specific policy

        Specify action from the policy

        Arguments
        ---------
        market : Market
            The market on which this agent will be executing trades (MarketActions)
        Returns
        -------
        list[MarketAction]
            List of actions to execute in the market
        """
        raise NotImplementedError

    def get_max_long(self, market: Market) -> float:
        """
        Gets an approximation of the maximum amount of base the agent can use to
        enter into a long position.
        """
        (max_long, _) = market.pricing_model.get_max_long(
            market_state=market.market_state,
            fee_percent=market.fee_percent,
            time_remaining=market.position_duration,
        )
        return min(
            self.wallet.base,
            max_long,
        )

    def get_max_short(self, market: Market) -> float:
        """
        Gets an approximation of the maximum amount of bonds the agent can short.

        Arguments
        ---------
        market : Market
            The market on which this agent will be executing trades (MarketActions)
        Returns
        -------
        float
            Amount of base that the agent can short in the current market
        """
        # Get the market level max short.
        (max_short_max_loss, max_short) = market.pricing_model.get_max_short(
            market_state=market.market_state,
            fee_percent=market.fee_percent,
            time_remaining=market.position_duration,
        )

        # If the Agent's base balance can cover the max loss of the maximum
        # short, we can simply return the maximum short.
        if self.wallet.base >= max_short_max_loss:
            return max_short

        last_maybe_max_short = 0
        bond_percent = 1
        for step_size in [1 / (2 ** (x + 1)) for x in range(0, 25)]:
            # Compute the amount of base returned by selling the specified
            # amount of bonds.
            maybe_max_short = max_short * bond_percent
            trade_result = market.pricing_model.calc_out_given_in(
                in_=Quantity(amount=maybe_max_short, unit=TokenType.PT),
                market_state=market.market_state,
                fee_percent=market.fee_percent,
                time_remaining=market.position_duration,
            )

            # If the max loss is greater than the wallet's base, we need to
            # decrease the bond percentage. Otherwise, we may have found the
            # max short, and we should increase the bond percentage.
            max_loss = maybe_max_short - trade_result.user_result.d_base
            if max_loss > self.wallet.base:
                bond_percent -= step_size
            else:
                last_maybe_max_short = maybe_max_short
                if bond_percent == 1:
                    return last_maybe_max_short
                bond_percent += step_size

        return last_maybe_max_short

    def get_trade_list(self, market: Market) -> list:
        """
        Helper function for computing a agent trade
        direction is chosen based on this logic:
        when entering a trade (open long or short),
        we use calcOutGivenIn because we know how much we want to spend,
        and care less about how much we get for it.
        when exiting a trade (close long or short),
        we use calcInGivenOut because we know how much we want to get,
        and care less about how much we have to spend.
        we spend what we have to spend, and get what we get.

        Arguments
        ---------
        market : Market
            The market on which this agent will be executing trades (MarketActions)
        pricing_model : PricingModel
            The pricing model in use for this simulated market

        Returns
        -------
        list
            List of MarketAction objects that represent the trades to be made by this agent
        """
        action_list = self.action(market)  # get the action list from the policy
        for action in action_list:  # edit each action in place
            if action.mint_time is None:
                action.mint_time = market.time
        # TODO: Add safety checks
        # e.g. if trade amount > 0, whether there is enough money in the account
        return action_list

    def update_wallet(self, wallet_deltas: Wallet, market: Market) -> None:
        """
        Update the agent's wallet

        Arguments
        ---------
        wallet_deltas : Wallet
            The agent's wallet that tracks the amount of assets this agent holds
        market : Market
            The market on which this agent will be executing trades (MarketActions)

        This method has no returns. It updates the Agent's Wallet according to the passed parameters
        """
        # track over time the agent's weighted average spend, for return calculation
        new_spend = (market.time - self.last_update_spend) * (self.budget - self.wallet["base"])
        self.product_of_time_and_base += new_spend
        self.last_update_spend = market.time
        for key, value_or_dict in wallet_deltas.__dict__.items():
            if value_or_dict is None:
                continue
            if key in ["fees_paid", "address"]:
                continue
            # handle updating a value
            if key in ["base", "lp_tokens", "fees_paid"]:
                logging.debug(
                    "agent #%g %s pre-trade = %.0g\npost-trade = %1g\ndelta = %1g",
                    self.wallet.address,
                    key,
                    self.wallet[key],
                    self.wallet[key] + value_or_dict,
                    value_or_dict,
                )
                self.wallet[key] += value_or_dict
            # handle updating a dict, which have mint_time attached
            elif key == "longs":
                self._update_longs(value_or_dict.items())
            elif key == "shorts":
                self._update_shorts(value_or_dict.items())
            else:
                raise ValueError(f"wallet_key={key} is not allowed.")

    def _update_longs(self, longs: Iterable[tuple[float, Long]]) -> None:
        for mint_time, long in longs:
            if long.balance != 0:
                logging.debug(
                    "agent #%g trade longs, mint_time = %g\npre-trade amount = %s\ntrade delta = %s",
                    self.wallet.address,
                    mint_time,
                    self.wallet.longs,
                    long,
                )
                if mint_time in self.wallet.longs:  #  entry already exists for this mint_time, so add to it
                    self.wallet.longs[mint_time].balance += long.balance
                else:
                    self.wallet.longs.update({mint_time: long})
            if self.wallet.longs[mint_time].balance == 0:
                # Remove the empty long from the wallet.
                del self.wallet.longs[mint_time]

    def _update_shorts(self, shorts: Iterable[tuple[float, Short]]) -> None:
        for mint_time, short in shorts:
            if short.balance != 0:
                logging.debug(
                    "agent #%g trade shorts, mint_time = %g\npre-trade amount = %s\ntrade delta = %s",
                    self.wallet.address,
                    mint_time,
                    self.wallet.shorts,
                    short,
                )
                if mint_time in self.wallet.shorts:  #  entry already exists for this mint_time, so add to it
                    self.wallet.shorts[mint_time].balance += short.balance
                    self.wallet.shorts[mint_time].margin += short.margin
                else:
                    self.wallet.shorts.update({mint_time: short})
            if self.wallet.shorts[mint_time].balance == 0:
                # Add the remaining margin balance to the wallet's base.
                self.wallet.base += self.wallet.shorts[mint_time].margin
                # Remove the empty short from the wallet.
                del self.wallet.shorts[mint_time]

    def get_liquidation_trades(self, market: Market) -> list[MarketAction]:
        """
        Get final trades for liquidating positions

        Arguments
        ---------
        market : Market
            The market on which this agent will be executing trades or liquidations (MarketActions)

        Returns
        -------
        list[MarketAction]
            List of trades to execute in order to liquidate positions where applicable
        """
        action_list: list[MarketAction] = []
        for mint_time, long in self.wallet.longs.items():
            logging.debug("evaluating closing long: mint_time=%g, position=%s", mint_time, long)
            if long.balance > 0:
                action_list.append(
                    self.create_agent_action(
                        action_type=MarketActionType.CLOSE_LONG,
                        trade_amount=long.balance,
                        mint_time=mint_time,
                    )
                )
        for mint_time, short in self.wallet.shorts.items():
            logging.debug("evaluating closing short: mint_time=%g, position=%s", mint_time, short)
            if short.balance > 0:
                action_list.append(
                    self.create_agent_action(
                        action_type=MarketActionType.CLOSE_SHORT,
                        trade_amount=short.balance,
                        mint_time=mint_time,
                    )
                )
        if self.wallet.lp_tokens > 0:
            action_list.append(
                self.create_agent_action(
                    action_type=MarketActionType.REMOVE_LIQUIDITY,
                    trade_amount=self.wallet.lp_tokens,
                    mint_time=market.time,
                )
            )
        return action_list

    def log_status_report(self) -> None:
        """Logs the current user state"""
        logging.debug(
            "agent %g base = %1g and fees_paid = %1g",
            self.wallet.address,
            self.wallet.base,
            self.wallet.fees_paid if self.wallet.fees_paid else 0,
        )

    def log_final_report(self, market: Market, pricing_model: PricingModel) -> None:
        """
        Logs a report of the agent's state

        Arguments
        ---------
        market : Market
            The market on which this agent can execute trades (MarketActions)
        """
        # TODO: This is a HACK to prevent test_sim from failing on market shutdown
        # when the market closes, the share_reserves are 0 (or negative & close to 0) and several logging steps break
        if market.market_state.share_reserves > 0:
            price = market.spot_price
        else:
            price = 0
        base = self.wallet.base
        longs = list(self.wallet.longs.values())
        shorts = list(self.wallet.shorts.values())

        # Calculate the total pnl of the trader.
        longs_value = (sum(long.balance for long in longs) if len(longs) > 0 else 0) * price
        shorts_value = sum(short.margin - short.balance * price for short in shorts) if len(shorts) > 0 else 0
        total_value = base + longs_value + shorts_value
        profit_and_loss = total_value - self.budget

        # Calculated spending statistics.
        weighted_average_spend = self.product_of_time_and_base / market.time if market.time > 0 else 0
        spend = weighted_average_spend
        holding_period_rate = profit_and_loss / spend if spend != 0 else 0
        if market.time > 0:
            annual_percentage_rate = holding_period_rate / market.time
        else:
            annual_percentage_rate = np.nan

        # Log the trading report.
        lost_or_made = "lost" if profit_and_loss < 0 else "made"
        logging.info(
            (
                "agent #%g %s %s on $%s spent, APR = %g"
                " (%.2g in %s years), net worth = $%s"
                " from %s base, %s longs, and %s shorts at p = %g\n"
            ),
            self.wallet.address,
            lost_or_made,
            float_to_string(profit_and_loss),
            float_to_string(spend),
            annual_percentage_rate,
            holding_period_rate,
            float_to_string(market.time, precision=2),
            float_to_string(total_value),
            float_to_string(base),
            float_to_string(sum(long.balance for long in longs)),
            float_to_string(sum(short.balance for short in shorts)),
            price,
        )
