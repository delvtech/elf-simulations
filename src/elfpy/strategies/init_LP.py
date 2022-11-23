from elfpy.strategies.basic import BasicPolicy


class Policy(BasicPolicy):
    """
    simple LP
    only has one LP open at a time
    """

    def __init__(self, market, rng, wallet_address, budget=1000, amount_to_LP=100, pt_to_short=100, verbose=False):
        """call basic policy init then add custom stuff"""
        super().__init__(market=market, rng=rng, wallet_address=wallet_address, budget=budget, verbose=verbose)
        self.amount_to_LP = amount_to_LP
        self.pt_to_short = pt_to_short
        self.status_update()

    def action(self):
        """
        implement user strategy
        LP if you can, but only do it once
        short if you can, but only do it once
        """
        self.status_update()
        action_list = []
        if not self.has_LPd and self.can_LP:
            action_list.append(
                self.create_user_action(
                    action_type="add_liquidity",
                    trade_amount=self.amount_to_LP
                )
            )
        if (not self.has_opened_short) and self.can_open_short:
            action_list.append(
                self.create_user_action(
                    action_type="open_short",
                    trade_amount=self.pt_to_short
                    )
                )
        return action_list

    def status_update(self):
        self.has_LPd = self.wallet.lp_in_wallet > 0
        self.can_LP = self.wallet.base_in_wallet >= self.amount_to_LP
        self.position_list = list(self.wallet.token_in_protocol.values())
        self.mint_times = list(self.wallet.token_in_protocol.keys())
        self.has_opened_short = True if any([x < -1 for x in self.position_list]) else False
        self.can_open_short = self.get_max_pt_short(self.market.time) >= self.pt_to_short