"""
User strategy that opens a long position and then closes it after a certain amount of time has passed
"""
# pylint: disable=too-many-arguments

from elfpy.markets import Market
from elfpy.pricing_models import PricingModel
from elfpy.policies.basic import BasicPolicy


class Policy(BasicPolicy):
    """
    simple long
    only has one long open at a time
    """

    def __init__(self, wallet_address, budget=1000):
        """call basic policy init then add custom stuff"""
        self.amount_to_trade = 100
        super().__init__(wallet_address, budget)

    def action(self, market: Market, pricing_model: PricingModel):
        """Specify action"""
        can_open_long = (self.wallet.base_in_wallet >= self.amount_to_trade) and (
            market.share_reserves >= self.amount_to_trade
        )
        block_position_list = list(self.wallet.token_in_protocol.values())
        has_opened_long = bool(any((x < 0 for x in block_position_list)))
        action_list = []
        mint_times = list(self.wallet["token_in_wallet"].keys())
        if has_opened_long:
            mint_time = mint_times[-1]
            enough_time_has_passed = market.time - mint_time > 0.25
            if enough_time_has_passed:
                action_list.append(
                    self.create_agent_action(
                        action_type="close_long",
                        trade_amount=sum(block_position_list)
                        / (market.get_spot_price(pricing_model) * 0.99),  # assume 1% slippage
                        mint_time=mint_time,
                    )
                )
        elif (not has_opened_long) and can_open_long:
            action_list.append(self.create_agent_action(action_type="open_long", trade_amount=self.amount_to_trade))
        return action_list
