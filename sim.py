import numpy as np
import pandas as pd

class YieldSimulator(object):
    def __init__(self, **kwargs):
        self.step_size = kwargs.get('step_size') # time resolution
        self.min_fee = kwargs.get('min_fee') # percentage of the slippage we take as a fee
        self.max_fee = kwargs.get('max_fee')
        self.t_min = kwargs.get('t_min') # minimum time (usually 0 or step_size)
        self.t_max = kwargs.get('t_max') # maximum time (must be <= 1)
        self.tokens = kwargs.get('tokens') # list of strings
        self.min_target_liquidity = kwargs.get('min_target_liquidity')
        self.max_target_liquidity = kwargs.get('max_target_liquidity')
        self.min_target_volume = kwargs.get('min_target_volume')
        self.max_target_volume = kwargs.get('max_target_volume')
        self.min_apy = kwargs.get('min_apy')
        self.max_apy = kwargs.get('max_apy')
        self.min_vault_age = kwargs.get('min_vault_age')
        self.max_vault_age = kwargs.get('max_vault_age')
        self.min_vault_apy = kwargs.get('min_vault_apy')
        self.max_vault_apy = kwargs.get('max_vault_apy')
        self.min_pool_age = kwargs.get('min_pool_age')
        self.max_pool_age = kwargs.get('max_pool_age')
        self.base_asset_price = kwargs.get('base_asset_price')
        self.precision = kwargs.get('precision')
        self.pricing_model_name = str(kwargs.get('pricing_model_name'))
        self.trade_direction = kwargs.get('trade_direction')
        self.days_until_maturity = kwargs.get('days_until_maturity')
        self.num_trading_days = kwargs.get('num_trading_days')
        self.num_steps = self.t_max // self.step_size
        self.times = np.arange(self.t_min, self.t_max + self.step_size, self.step_size)
        self.num_times = len(self.times)
        self.current_time_index = 0
        analysis_keys = [
            'model_name',
            'time_until_end',
            't_stretch',
            'target_liquidity',
            'target_daily_volume',
            'start_apy',
            'current_apy',
            'fee_percent',
            'init_vault_age',
            'vault_apy',
            'pool_age',
            'x_reserves',
            'y_reserves',
            'total_supply',
            'token_in',
            'token_out',
            'direction',
            'trade_amount',
            'conversion_rate',
            'normalizing_constant',
            'out_without_fee_slippage',
            'out_with_fee',
            'out_without_fee',
            'fee',
            'days_until_maturity',
            'num_trading_days',
            'day',
            'spot_price',
            'num_orders',
        ]
        self.analysis_dict = {key:[] for key in analysis_keys}
        self.sim_params_set = False

    def set_sim_params(self):
        self.target_liquidity = np.random.uniform(self.min_target_liquidity, self.max_target_liquidity)
        self.target_daily_volume = np.random.uniform(self.min_target_volume, self.max_target_volume)
        self.start_apy = np.random.uniform(self.min_apy, self.max_apy)
        self.fee_percent = np.random.uniform(self.min_fee, self.max_fee)
        # determine real-world parameters for estimating u and c (vault and pool details)
        self.init_vault_age = np.random.uniform(self.min_vault_age, self.max_vault_age) # in years
        self.vault_apy = np.random.uniform(self.min_vault_apy, self.max_vault_apy) / 100 # as a decimal
        self.pool_age = np.random.uniform(min(self.init_vault_age, self.min_pool_age), self.max_pool_age) # in years
        self.sim_params_set = True

    def set_random_time(self):
        self.current_time_index = np.random.randint(0, self.num_times)

    def increment_time(self):
        self.current_time_index += 1

    def get_current_time(self):
        return self.times[self.current_time_index]

    def run_simulation(self, override_dict=None):
        # Update parameters if the user provided new ones
        assert self.sim_params_set, ('ERROR: You must run simulator.set_sim_params() before running the simulation')
        if override_dict is not None:
            for key in override_dict.keys():
                if hasattr(self, key):
                    setattr(self, key, override_dict[key])
        if override_dict is not None and 'conversion_rate' in override_dict.keys():
            self.conversion_rate = override_dict['conversion_rate']
        else:
            self.conversion_rate = np.around((1 + self.vault_apy)**self.init_vault_age, self.precision) # c variable in the paper
        if override_dict is not None and 'normalizing_constant' in override_dict.keys():
            self.normalizing_constant = override_dict['normalizing_constant']
        else:
            self.normalizing_constant = np.around((1 + self.vault_apy)**self.pool_age, self.precision) # \mu variable in the paper
        # Initiate pricing model
        if self.pricing_model_name.lower() == 'yieldspace':
            self.pricing_model = YieldSpacev2PricingModel()
        elif self.pricing_model_name.lower() == 'yieldspaceminfee':
            self.pricing_model = YieldSpacev2MinFeePricingModel()
        elif self.pricing_model_name.lower() == 'element':
            self.pricing_model = ElementPricingModel()
        else:
            raise ValueError(f'pricing_model_name must be "YieldSpace", "YieldSpaceMinFee", or "Element", not {self.pricing_model_name}')
        self.t_stretch = self.pricing_model.calc_time_stretch(self.start_apy) # determine time stretch
        self.time = self.get_current_time()

        (x_reserves, y_reserves, liquidity) = self.pricing_model.calc_liquidity(
            self.target_liquidity,
            self.base_asset_price,
            self.start_apy,
            self.days_until_maturity,
            self.t_stretch,
            self.normalizing_constant,
            self.conversion_rate)
        total_supply = x_reserves + y_reserves
        spot_price = self.pricing_model.calc_spot_price(
            x_reserves,
            y_reserves,
            total_supply,
            self.time / self.t_stretch,
            self.normalizing_constant,
            self.conversion_rate)
        # TODO: Do we want to calculate & store this?
        #resulting_apy = self.pricing_model.apy(spot_price, self.days_until_maturity)

        self.market = Market(
            x_reserves, y_reserves, self.fee_percent,
            self.days_until_maturity / (365 * self.t_stretch),
            total_supply,
            self.pricing_model,
            self.conversion_rate,
            self.normalizing_constant)

        for day in range(self.num_trading_days):
            self.day = day
            self.current_vault_age = self.init_vault_age + self.day / 365
            # TODO: this is probably wrong? z is observable and should be calculated within the sim. c should be calculated from z and x.
            self.market.c += self.vault_apy / 100 / 365 * self.market.u

            # TODO: adjustable target daily volume that is a function of the day
            todays_num_trades = 0
            day_trading_volume = 0
            while day_trading_volume < self.target_daily_volume:
                # TODO: simplify market price conversion (not necessary) & allow for different trade amounts
                #self.trade_amount = np.random.uniform(0, (liquidity / self.base_asset_price) / 5)
                self.trade_amount = np.random.normal(self.target_daily_volume / 10, self.target_daily_volume / 10 / 10) / self.base_asset_price

                # TODO: improve trading distribution (e.g. actual historical trades or a fit to historical trades)
                token_index = np.random.randint(0, 2) # 0 or 1
                self.token_in = self.tokens[token_index]
                self.token_out = self.tokens[1-token_index]

                (self.without_fee_or_slippage, self.with_fee, self.without_fee, self.fee) = self.market.swap(
                    self.trade_amount, # in units of base asset
                    self.trade_direction,
                    self.token_in,
                    self.token_out)
                self.update_analysis_dict()

                day_trading_volume += self.trade_amount * self.base_asset_price
            self.market.tick(self.step_size)

    def update_analysis_dict(self):
        self.analysis_dict['model_name'].append(self.pricing_model.model_name())
        self.analysis_dict['time_until_end'].append(self.market.t)
        self.analysis_dict['t_stretch'].append(self.t_stretch)
        self.analysis_dict['target_liquidity'].append(self.target_liquidity)
        self.analysis_dict['target_daily_volume'].append(self.target_daily_volume)
        self.analysis_dict['start_apy'].append(self.start_apy)
        self.analysis_dict['current_apy'].append(self.market.apy(self.days_until_maturity - self.day + 1))
        self.analysis_dict['fee_percent'].append(self.fee_percent)
        self.analysis_dict['init_vault_age'].append(self.init_vault_age)
        self.analysis_dict['vault_apy'].append(self.vault_apy)
        self.analysis_dict['pool_age'].append(self.pool_age)
        self.analysis_dict['x_reserves'].append(self.market.x)
        self.analysis_dict['y_reserves'].append(self.market.y)
        self.analysis_dict['total_supply'].append(self.market.total_supply)
        self.analysis_dict['token_in'].append(self.token_in)
        self.analysis_dict['token_out'].append(self.token_out)
        self.analysis_dict['direction'].append(self.trade_direction)
        self.analysis_dict['trade_amount'].append(self.trade_amount)
        self.analysis_dict['conversion_rate'].append(self.market.c)
        self.analysis_dict['normalizing_constant'].append(self.market.u)
        self.analysis_dict['out_without_fee_slippage'].append(self.without_fee_or_slippage)
        self.analysis_dict['out_with_fee'].append(self.with_fee)
        self.analysis_dict['out_without_fee'].append(self.without_fee)
        self.analysis_dict['fee'].append(self.fee)
        self.analysis_dict['days_until_maturity'].append(self.days_until_maturity)
        self.analysis_dict['num_trading_days'].append(self.num_trading_days)
        self.analysis_dict['day'].append(self.day)
        self.analysis_dict['spot_price'].append(self.market.spot_price())
        self.analysis_dict['num_orders'].append(self.market.x_orders + self.market.y_orders)


class Market(object):
    def __init__(self, x, y, g, t, total_supply, pricing_model, c=1, u=1, verbose=False):
        #TODO: Rename these variables to be more descriptive
        self.x=x
        self.y=y
        self.total_supply = total_supply
        self.g=g
        self.t=t
        self.c=c # conversion rate
        self.u=u # normalizing constant
        self.pricing_model=pricing_model
        self.x_orders = 0
        self.y_orders = 0
        self.x_volume = 0
        self.y_volume = 0
        self.cum_y_slippage=0
        self.cum_x_slippage=0
        self.cum_y_fees=0
        self.cum_x_fees=0
        self.starting_fyt_price=self.spot_price()
        self.verbose = verbose

    def apy(self, days_until_maturity):
        price = self.pricing_model.calc_spot_price(self.x, self.y, self.total_supply, self.t, self.u, self.c)
        return self.pricing_model.apy(price, days_until_maturity)

    def spot_price(self):
        return self.pricing_model.calc_spot_price(self.x, self.y, self.total_supply, self.t, self.u, self.c)

    def tick(self, step_size):
        self.t -= step_size

    def swap(self, amount, direction, token_in, token_out):
        if direction == "in":
            if token_in == "fyt" and token_out == "base":
                in_reserves = self.y + self.total_supply
                out_reserves = self.x
                (without_fee_or_slippage, output_with_fee, output_without_fee, fee) = \
                        self.pricing_model.calc_in_given_out(
                                amount, in_reserves, out_reserves, token_in, self.g, self.t, self.u, self.c)
                dx = -output_with_fee
                dy = amount
            elif token_in == "base" and token_out == "fyt":
                in_reserves = self.x
                out_reserves = self.y + self.total_supply
                (without_fee_or_slippage, output_with_fee, output_without_fee, fee) = \
                        self.pricing_model.calc_in_given_out(
                                amount, in_reserves, out_reserves, token_in, self.g, self.t, self.u, self.c)
                dx = amount
                dy = -output_with_fee
            else:
                raise ValueError(
                        f'token_in and token_out must be unique and in the set ("base", "fyt"), not in={token_in} and out={token_out}')
        elif direction == "out":
            if token_in == "fyt" and token_out == "base":
                in_reserves = self.y + self.total_supply
                out_reserves = self.x
                (without_fee_or_slippage, output_with_fee, output_without_fee, fee) = \
                        self.pricing_model.calc_out_given_in(
                                amount, in_reserves, out_reserves, token_out, self.g, self.t, self.u, self.c)
                dx = -output_with_fee
                dy = amount
            elif token_in == "base" and token_out == "fyt":
                in_reserves = self.x
                out_reserves = self.y + self.total_supply
                (without_fee_or_slippage, output_with_fee, output_without_fee, fee) = \
                        self.pricing_model.calc_out_given_in(
                                amount, in_reserves, out_reserves, token_out, self.g, self.t, self.u, self.c)
                dx = amount
                dy = -output_with_fee
        else:
            raise ValueError(f'direction argument must be "in" or "out", not {direction}')
        if fee > 0:
            self.x += dx
            self.y += dy
            self.cum_x_slippage += abs(without_fee_or_slippage - output_without_fee)
            self.cum_y_fees += fee
            self.x_orders += 1
            self.x_volume += output_with_fee
        if self.verbose and self.x_orders + self.y_orders < 10:
            print('conditional one')
            print([amount, self.y + self.total_supply, self.x / self.c, token_in, self.g, self.t, self.u, self.c])
            print([without_fee_or_slippage, output_with_fee, output_without_fee, fee])
        if self.verbose and any([isinstance(output_with_fee, complex), isinstance(output_without_fee, complex), isinstance(fee, complex)]):
            print([amount, self.y + self.total_supply, self.x, token_in, self.g, self.t, self.u, self.c])
            print([(without_fee_or_slippage, output_with_fee, output_without_fee, fee)])
        return (without_fee_or_slippage, output_with_fee, output_without_fee, fee)


class PricingModel(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    @staticmethod
    def model_name():
        raise NotImplementedError

    @staticmethod
    def calc_in_given_out(out, in_reserves, out_reserves, token_in, g, t, u, c):
        raise NotImplementedError

    @staticmethod
    def calc_out_given_in(in_, in_reserves, out_reserves, token_out, g, t, u, c):
        raise NotImplementedError

    @staticmethod
    def calc_time_stretch(apy):
        return 3.09396 / (0.02789 * apy)

    @staticmethod
    def calc_max_trade(in_reserves, out_reserves, t):
        k = in_reserves**(1 - t) + out_reserves**(1 - t)
        return k**(1 / (1 - t)) - in_reserves

    @staticmethod
    def calc_tokens_in_given_lp_out(lp_out, x_reserves, y_reserves, total_supply):
        # Check if the pool is initialized
        if total_supply == 0:
            x_needed = lp_out
            y_needed = 0
        else:
            # solve for y_needed: lp_out = ((x_reserves / y_reserves) * y_needed * total_supply)/x_reserves
            y_needed = (lp_out * x_reserves) / ((x_reserves / y_reserves) * total_supply)
            # solve for x_needed: x_reserves / y_reserves = x_needed / y_needed
            x_needed = (x_reserves / y_reserves) * y_needed
        return (x_needed, y_needed)

    @staticmethod
    def calc_lp_out_given_tokens_in(x_in, y_in, x_reserves, y_reserves, total_supply):
        # Check if the pool is initialized
        if total_supply == 0:
            # When uninitialized we mint exactly the underlying input in LP tokens
            lp_out = x_in
            x_needed = x_in
            y_needed = 0
        else:
            # calc the number of x needed for the y_in provided
            x_needed = (x_reserves / y_reserves) * y_in
            # if there isn't enough x_in provided
            if x_needed > x_in:
                lp_out = (x_in * total_supply) / x_reserves
                # use all the x_in
                x_needed = x_in
                # solve for: x_reserves/y_reserves = x_needed/y_needed
                y_needed = x_needed/(x_reserves/y_reserves)
            else:
                # We calculate the percent increase in the reserves from contributing all of the bond
                lp_out = (x_needed * total_supply)/x_reserves
                y_needed = y_in
        return (x_needed, y_needed, lp_out)

    @staticmethod
    def calc_lp_in_given_tokens_out(min_x_out, min_y_out, x_reserves, y_reserves, total_supply):
        # calc the number of x needed for the y_out provided
        x_needed = (x_reserves / y_reserves) * min_y_out
        # if there isn't enough x_out provided
        if min_x_out > x_needed:
            lp_in = (min_x_out * total_supply)/x_reserves
            # use all the x_out
            x_needed = min_x_out
            # solve for: x_reserves/y_reserves = x_needed/y_needed
            y_needed = x_needed/(x_reserves/y_reserves)
        else:
            y_needed = min_y_out
            lp_in = (y_needed * total_supply)/y_reserves
        return (x_needed, y_needed, lp_in)

    @staticmethod
    def calc_tokens_out_for_lp_in(lp_in, x_reserves, y_reserves, total_supply):
        # solve for y_needed: lp_out = ((x_reserves / y_reserves) * y_needed * total_supply)/x_reserves
        y_needed = (lp_in * x_reserves) / ((x_reserves / y_reserves) * total_supply)
        # solve for x_needed: x_reserves/y_reserves = x_needed/y_needed
        x_needed = (x_reserves / y_reserves) * y_needed
        return (x_needed, y_needed)

    def calc_x_reserves(self, apy, y_reserves, days_until_maturity, time_stretch, u, c):
        raise NotImplementedError

    def apy(self, price, days_until_maturity):
        T = days_until_maturity / 365
        return (1 - price) / price / T * 100 # APYW

    def calc_spot_price(self, x_reserves, y_reserves, total_supply, t, u, c):
        return 1 / pow(c * (y_reserves + total_supply) / (u * x_reserves), t)

    def calc_apy_from_reserves(self, x_reserves, y_reserves, total_supply, t, t_stretch, u, c):
        spot_price = self.calc_spot_price(x_reserves, y_reserves, total_supply, t, u, c)
        days_until_maturity = t * 365 * t_stretch
        return self.apy(spot_price, days_until_maturity)

    def calc_spot_price_from_apy(self, apy, days_until_maturity):
        T = days_until_maturity / 365
        return 1 - apy * T / 100

    def calc_liquidity(self, target_liquidity, market_price, apy, days_until_maturity, time_stretch, u, c):
        spot_price = self.calc_spot_price_from_apy(apy, days_until_maturity)
        t = days_until_maturity / (365 * time_stretch)
        y_reserves = target_liquidity / market_price / 2 / (1 - apy / 100 * t)
        x_reserves = self.calc_x_reserves(
                apy, y_reserves, days_until_maturity, time_stretch, u, c)
        scaleUpFactor = target_liquidity / (x_reserves * market_price + y_reserves * market_price * spot_price)
        y_reserves = y_reserves * scaleUpFactor
        x_reserves = x_reserves * scaleUpFactor
        liquidity = x_reserves * market_price + y_reserves * market_price * spot_price
        actual_apy = self.calc_apy_from_reserves(
                x_reserves, y_reserves, x_reserves + y_reserves, t, time_stretch, u, c)
        if self.verbose:
            print('x={} y={} total={} apy={}'.format(x_reserves,y_reserves,liquidity,actual_apy))
        return (x_reserves, y_reserves, liquidity)


class ElementPricingModel(PricingModel):
    @staticmethod
    def model_name():
        return "ElementPricingModel"

    @staticmethod
    def calc_in_given_out(out, in_reserves, out_reserves, token_in, g, t, u, c):
        k = in_reserves**(1 - t) + out_reserves**(1 - t)
        without_fee = pow(k - pow(out_reserves - out, 1 - t), 1 / (1 - t)) - in_reserves
        if token_in == "base":
            fee = (out - without_fee) * g
        elif token_in == "fyt":
            fee = (without_fee - out) * g
        with_fee = without_fee + fee
        without_fee_or_slippage = out * (in_reserves / out_reserves)**t
        return (without_fee_or_slippage, with_fee, without_fee, fee)

    @staticmethod
    def calc_out_given_in(in_, in_reserves, out_reserves, token_out, g, t, u, c):
        k = in_reserves**(1 - t) + out_reserves**(1 - t)
        without_fee = out_reserves - pow(k - pow(in_reserves + in_, 1 - t), 1 / (1 - t))
        if token_out == "base":
            fee = (in_ - without_fee) * g
        elif token_out == "fyt":
            fee = (without_fee - in_) * g
        with_fee = without_fee - fee
        without_fee_or_slippage = 1 / pow(in_reserves / out_reserves, t) * in_
        return (without_fee_or_slippage, with_fee, without_fee, fee)

    def calc_x_reserves(self, apy, y_reserves, days_until_maturity, time_stretch, u=1, c=1):
        t = days_until_maturity / (365 * time_stretch)
        T = days_until_maturity / 365
        r = apy / 100
        return 2 * y_reserves / ((-1 / (r * T - 1))**(1 / t) - 1)

    def calc_spot_price(self, x_reserves, y_reserves, total_supply, t):
        super(ElementPricingModel, self).calc_spot_price(x_reserves, y_reserves, total_supply, t, u=1, c=1)

    def calc_apy_from_reserves(self, x_reserves, y_reserves, total_supply, t, t_stretch, u, c):
        super(ElementPricingModel, self).calc_apy_from_reserves(x_reserves, y_reserves, total_supply, t, t_stretch, u=1, c=1)

    def calc_apy_from_reserves(self, x_reserves, y_reserves, total_supply, t, t_stretch):
        super(ElementPricingModel, self).calc_apy_from_reserves(x_reserves, y_reserves, total_supply, t, t_stretch, u=1, c=1)


class YieldSpacev2PricingModel(PricingModel):
    @staticmethod
    def model_name():
        return "YieldsSpacev2"

    @staticmethod
    def calc_in_given_out(out, in_reserves, out_reserves, token_in, g, t, u, c):
        scale = c / u
        if token_in == "base": # calc shares in for fyt out
            dy = out
            z = in_reserves / c # convert from x to z (x=cz)
            y = out_reserves
            k = scale * (u * z)**(1 - t) + y**(1 - t)
            without_fee = (1 / u * ((k - (y - dy)**(1 - t)) / scale)**(1 / (1 - t)) - z) * c
            fee = (out - without_fee) * g
            with_fee = without_fee + fee
            without_fee_or_slippage = (in_reserves / (c / u * out_reserves))**t * out
        elif token_in == "fyt": # calc fyt in for shares out
            dz = out / c
            z = out_reserves / c # convert from x to z (x=cz)
            y = in_reserves
            k = scale * (u * z)**(1 - t) + y**(1 - t)
            without_fee = (k - scale * (u * z - u * dz)**(1 - t))**(1 / (1 - t)) - y
            fee =  (without_fee - out) * g
            with_fee = without_fee + fee
            without_fee_or_slippage = (c / u * in_reserves / out_reserves)**t * out
        return (without_fee_or_slippage, with_fee, without_fee, fee)

    @staticmethod
    def calc_out_given_in(in_, in_reserves, out_reserves, token_out, g, t, u, c):
        if token_out == "base": # calc shares out for fyt in
            scale = c / u
            dy = in_
            z = out_reserves / c # convert from x to z (x=cz)
            y = in_reserves
            k = scale * (u * z)**(1 - t) + y**(1 - t)
            without_fee = (z - 1 / u * ((k - (y + dy)**(1 - t)) / scale)**(1 / (1 - t))) * c
            fee = (in_ - without_fee) * g
            with_fee = without_fee - fee
            without_fee_or_slippage = 1 / ((c / u * in_reserves) / out_reserves)**t * in_
        elif token_out == "fyt": # calc fyt out for shares in
            scale = c / u
            dz = in_ / c # convert from x to z (x=cz)
            z = in_reserves / c # convert from x to z (x=cz)
            y = out_reserves
            k = scale * (u * z)**(1 - t) + y**(1 - t)
            without_fee = y - (k - scale * (u * z + u * dz)**(1 - t))**(1 / (1 - t))
            fee = (without_fee - in_) * g
            with_fee = without_fee - fee
            without_fee_or_slippage = 1 / (in_reserves / (c / u * out_reserves))**t * in_
        return (without_fee_or_slippage, with_fee, without_fee, fee)

    def calc_x_reserves(self, apy, y_reserves, days_until_maturity, time_stretch, u, c):
        t = days_until_maturity / (365 * time_stretch)
        T = days_until_maturity / 365
        r = apy / 100
        result = 2 * c * y_reserves / (-c + u * (-1 / (r * T - 1))**(1 / t))
        if self.verbose:
            print(f'calc_x_reserves result: {result}')
        return result



class YieldSpacev2MinFeePricingModel(YieldSpacev2PricingModel):
    @staticmethod
    def model_name():
        return "YieldsSpacev2_MinFee"

    @staticmethod
    def calc_out_given_in(in_, in_reserves, out_reserves, token_out, g, t, u, c):
        scale = c / u
        if token_out == "base": # calc shares out for fyt in
            dy = in_
            z = out_reserves / c # convert from x to z (x=cz)
            y = in_reserves
            k = scale * (u * z)**(1 - t) + y**(1 - t)
            without_fee = z - 1 / u * ((k - (y + dy)**(1 - t)) / scale)**(1 / (1 - t))
            without_fee = without_fee * c # convert from z to x (x=cz)
            fee =  (in_ - without_fee) * g
            if fee / in_ < 5 / 100 / 100:
                fee = in_ * 5/ 100 / 100
            with_fee = without_fee - fee
            without_fee_or_slippage = 1 / ((c / u * in_reserves) / out_reserves)**t * in_
        elif token_out == "fyt": # calc fyt out for shares in
            dz = in_ / c # convert from x to z (x=cz)
            z = in_reserves / c # convert from x to z (x=cz)
            y = out_reserves
            k = scale * (u * z)**(1 - t) + y**(1 - t)
            without_fee = y - (k - scale * (u * z + u * dz)**(1 - t))**(1 / (1 - t))
            fee =  (without_fee - in_) * g
            if fee / in_ < 5 / 100 / 100:
                fee = in_ * 5 / 100 / 100
            with_fee = without_fee - fee
            without_fee_or_slippage = 1 / (in_reserves / (c / u * out_reserves))**t * in_
        return (without_fee_or_slippage, with_fee, without_fee, fee)
