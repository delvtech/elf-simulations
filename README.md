[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![testing: pytest](https://img.shields.io/badge/testing-pytest-blue.svg)](https://docs.pytest.org/en/latest/contents.html)
[![license: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-lightgrey)](http://www.apache.org/licenses/LICENSE-2.0)
[![DELV - Terms of Service](https://img.shields.io/badge/DELV-Terms_of_Service-orange)](https://delv-public.s3.us-east-2.amazonaws.com/delv-terms-of-service.pdf)

[![testing: coverage](https://codecov.io/gh/delvtech/agent0/branch/main/graph/badge.svg?token=1S60MD42ZP)](https://app.codecov.io/gh/delvtech/agent0?displayType=list)
[![docs: build](https://readthedocs.org/projects/agent0/badge/?version=latest)](https://agent0.readthedocs.io/en/latest/?badge=latest)

<img src="https://raw.githubusercontent.com/delvtech/agent0/main/icons/agent0-dark.svg" width="800" alt="agent0"><br>

# A Framework for Hyperdrive Trading Strategies

This repo by [DELV](https://delv.tech) contains tools for you to deploy automated trading agents, perform market simulations, and conduct trading research. Read on for more info or jump to the [quickstart guide](https://agent0.readthedocs.io/en/latest/#quickstart-examples).
This docs page can be found via [https://agent0.readthedocs.io/en/latest/](https://agent0.readthedocs.io/en/latest/).

<br><a href="https://app.codecov.io/gh/delvtech/agent0?displayType=list"><img height="100px" src="https://codecov.io/gh/delvtech/agent0/graphs/sunburst.svg?token=1S60MD42ZP"></a> 

## Hyperdrive Background

Hyperdrive is an automated market maker (AMM) protocol that enables fixed-rate markets to be built on top of arbitrary yield sources. It deploys assets into those yield sources and wraps them as Hyperdrive positions represented as hy[Tokens] that trade at a discount (%) and can be redeemed for their full face value at maturity. Since the hy[Token]’s initial cost and value at maturity are known upfront, this discounted purchase represents a fixed rate of return.

Abstracting interest rate dynamics into a single price opens up interesting Market Dynamics while giving users the freedom to employ a number of Trading Strategies.

To ensure that a balanced market exists where the market price can be increased and decreased by supply and demand, the AMM supports three basic operations:

* Opening Longs, which provides exposure to the fixed rate by purchasing hy[Tokens] at a discount to their face value for the price of forgoing the variable rate. Longs pay trading fees to the pool.

* Opening Shorts, which provides exposure to the variable rate generated by the capital that backs hy[Tokens] for the price of paying the fixed rate. Shorts pay trading fees to the pool.

* Providing Liquidity, which facilitates Long and Short trading by automatically taking the other side of user positions, and charges trading fees. Part of the pool's fees may go to a governance address.

Read more at [docs.hyperdrive.box](https://docs.hyperdrive.box/)

## What is Agent0?

Agent0 is DELV's Python-based library for testing, analyzing, and interacting with Hyperdrive's smart contracts. It provides ready-for-use trading policies as well as a framework for building smart agents that act according to policies that can be strictly user-designed, AI-powered, or a combination. These agents are deployable to execute trades on-chain or can be coupled with a simulated environment to test trading strategies, understand Hyperdrive, and explore integrations or deployment configurations.

When running Hyperdrive on a local blockchain, agent0 also provides a managed database delivered to you as Pandas dataframes via an API as well as a visualization dashboard to enable analysis and understanding.

Read more about [how agent0 works](https://docs.hyperdrive.box/hyperdrive-trading-bots/how-agent0-works) in our [docs](https://docs.hyperdrive.box/).

## Quickstart Examples

This repo contains general purpose code for interacting with Ethereum smart contracts.
However, it was built for the primary use case of trading on [Hyperdrive](https://hyperdrive.delv.tech) markets.

First, install [Foundry](https://book.getfoundry.sh/getting-started/installation) and [Docker](https://docs.docker.com/engine/install/).

Next, using a Python 3.10 environment, you can install agent0 via [uv](https://github.com/astral-sh/uv):

```sh
uv pip install --upgrade agent0
```

You're ready to go! You can use agent0 to do datascience, automate trading, or simulate trading strategies. Below are some quick examples to get you started. When you're ready, check out our [examples folder](https://github.com/delvtech/agent0/tree/main/examples/) for more information, including details on executing trades on remote chains.

### Execute Hyperdrive trades in a simulated blockchain environment

```python
import datetime
from fixedpointmath import FixedPoint
from agent0 import LocalHyperdrive, LocalChain

# Initialize.
chain = LocalChain()
hyperdrive = LocalHyperdrive(chain)
hyperdrive_agent0 = chain.init_agent(base=FixedPoint(100_000), eth=FixedPoint(10), pool=hyperdrive)

# Run trades.
chain.advance_time(datetime.timedelta(weeks=1))
open_long_event = hyperdrive_agent0.open_long(base=FixedPoint(100))
chain.advance_time(datetime.timedelta(weeks=5))
close_event = hyperdrive_agent0.close_long(
    maturity_time=open_long_event.args.maturity_time, bonds=open_long_event.args.bond_amount
)

# Analyze.
pool_info = hyperdrive.get_pool_info(coerce_float=True)
pool_info.plot(x="block_number", y="longs_outstanding", kind="line")
trade_ticker = hyperdrive_agent0.get_trade_events()
positions = hyperdrive_agent0.get_positions(show_closed_positions=True)

# Shut down the chain.
chain.cleanup()
```

### Query all positions

```python
import os
from agent0 import Chain, Hyperdrive

# We recommend you use env variables for sensitive information.
PUBLIC_ADDRESS = os.getenv("PUBLIC_ADDRESS")
RPC_URI = os.getenv("RPC_URI")

# Address of the Hyperdrive registry (this is for Sepolia).
REGISTRY_ADDRESS = "0x4ba58147e50e57e71177cfedb1fac0303f216104"

# View open and closed positions across all pools.
with Chain(RPC_URI) as chain:
    agent = chain.init_agent(public_address=PUBLIC_ADDRESS)
    registered_pools = Hyperdrive.get_hyperdrive_pools_from_registry(
        chain,
        registry_address = REGISTRY_ADDRESS,
    )
    all_positions = agent.get_positions(
        pool_filter=registered_pools,
        show_closed_positions=True,
    )
    print(all_positions)
```

### Automate withdrawing mature positions

```python
import os
from agent0 import Chain, Hyperdrive

# We recommend you use env variables for sensitive information.
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URI = os.getenv("RPC_URI")

# Address of the Hyperdrive registry (this is for Sepolia).
REGISTRY_ADDRESS = "0x4ba58147e50e57e71177cfedb1fac0303f216104"
chain = Chain(RPC_URI)
registered_pools = Hyperdrive.get_hyperdrive_pools_from_registry(
    chain,
    registry_address = REGISTRY_ADDRESS,
)

agent = chain.init_agent(private_key=PRIVATE_KEY)
for pool in registered_pools:
    # Close all mature longs.
    for long in agent.get_longs(pool=pool):
        if long.maturity_time <= chain.block_time():
            agent.close_long(
                maturity_time=long.maturity_time,
                bonds=long.balance,
                pool=pool,
            )
    # Close all mature shorts.
    for short in agent.get_shorts(pool=pool):
        if short.maturity_time <= chain.block_time():
            agent.close_short(
                maturity_time=short.maturity_time,
                bonds=short.balance,
                pool=pool,
            )

# Shut down the chain.
chain.cleanup()
```

## Advanced Install

Please refer to [INSTALL.md](https://github.com/delvtech/agent0/tree/main/INSTALL.md) for more advanced install options.

## Deployment

Please refer to [BUILD.md](https://github.com/delvtech/agent0/tree/main/BUILD.md).

## Testing and Contributions

Please refer to [CONTRIBUTING.md](https://github.com/delvtech/agent0/tree/main/CONTRIBUTING.md).

## Number format

We frequently use 18-decimal [fixed-point precision numbers](https://github.com/delvtech/fixedpointmath#readme) for arithmetic.

## Disclaimer

This project is a work-in-progress.
The language used in this code and documentation is not intended to, and does not, have any particular financial, legal, or regulatory significance.

---

Copyright © 2024  DELV

Licensed under the Apache License, Version 2.0 (the "OSS License").

By accessing or using this code, you signify that you have read, understand and agree to be bound by and to comply with the [OSS License](http://www.apache.org/licenses/LICENSE-2.0) and [DELV's Terms of Service](https://delv-public.s3.us-east-2.amazonaws.com/delv-terms-of-service.pdf). If you do not agree to those terms, you are prohibited from accessing or using this code.

Unless required by applicable law or agreed to in writing, software distributed under the OSS License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the OSS License and the DELV Terms of Service for the specific language governing permissions and limitations.
