# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.8
#   kernelspec:
#     display_name: Python 3.10.2 64-bit
#     language: python
#     name: python3
# ---

# %%
import numpy as np
import time, os, numbers
import pandas as pd
import matplotlib.pyplot as plt
import sys  
import seaborn as sns
sns.set()
sys.path.insert(0, './scripts')
from PricingModels import Element_Pricing_Model, Market, YieldsSpacev2_Pricing_model

# %%
token_price = 3
token_supply = 1*1e7
market_value = token_price * token_supply
growth_rate = 0.5 # 50% annualized growth rate
funding_need = market_value/1 # 6 million per year ($200k/yr for 30 staff or $100k/yr for 60 staff)

columns = ['token_price', 'token_supply', 'market_value', 'growth_rate', 'new_tokens', 'funding_acquired', 'old_token_price', 'new_token_price']
df = pd.DataFrame(data=[[token_price, token_supply, market_value, growth_rate, np.nan, np.nan, 0, 0]]
    ,columns=columns)
for t in range(1,11):
    growth_rate = growth_rate*0.8
    market_value = market_value * (1 + growth_rate)
    old_token_price = market_value/token_supply
    new_tokens = funding_need/old_token_price
    funding_acquired = 0
    token_price = old_token_price
    # print('{} tokens needed, price from {}→{} diff={}'.format(new_tokens,token_price,market_value/(token_supply+new_tokens),funding_need - funding_acquired))
    while funding_acquired - funding_need < -1:
        token_price = market_value/(token_supply+new_tokens)
        new_tokens = funding_need/token_price # update tokens being printed
        funding_acquired = token_price * new_tokens
        print('{} tokens needed, price from {}→{} diff={}'.format(new_tokens,old_token_price,market_value/(token_supply+new_tokens),funding_acquired - funding_need))
    token_supply += new_tokens
    df = pd.concat([df,pd.DataFrame(data=[[token_price, token_supply, market_value, growth_rate, new_tokens, funding_acquired, old_token_price, token_price]], columns=columns, index=[t])])
display(df.style.format({'token_supply': '{:,.0f}', 'market_value': '{:,.0f}', 'growth_rate': '{:,.0%}', 'new_tokens': '{:,.0f}', 'funding_acquired': '{:,.0f}'}))

# %%
numPlots = 2
fig, ax = plt.subplots(ncols=1, nrows=numPlots,gridspec_kw = {'wspace':0, 'hspace':0.1, 'height_ratios':np.ones(numPlots)}, sharex=True)
fig.patch.set_facecolor('white')   # set fig background color to white

currentPlot = 0
df.plot(use_index=True, y=['funding_acquired','new_tokens'], figsize=(10,5*numPlots), ax=ax[currentPlot]\
    , title='Have to print more to fund same amount of ${:,.0f} million...'.format(funding_need/1e6))
ax[currentPlot].grid(visible=True,linestyle='--', linewidth='1', color='grey',which='both', alpha=0.5)
# display(token_price)
# display(np.ceil(token_price))
# display(np.arange(0,np.ceil(token_price)+1,1))
ax[currentPlot].set_yticks(np.arange(0,np.ceil(new_tokens/1e7)*1e7+1e7,1e7))

currentPlot = 1
df.plot(use_index=True, y='token_price', figsize=(10,5*numPlots), ax=ax[currentPlot], title='... that causes number go down')
ax[currentPlot].grid(visible=True,linestyle='--', linewidth='1', color='grey',which='both', alpha=0.5)

#for final plot
ax[currentPlot].set_xlabel('Time (years)')
plt.xticks(df.index)
plt.show()
