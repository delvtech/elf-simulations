"""Tests various interactive hyperdrive policies."""

import pytest
from ethpy.hyperdrive import HyperdriveReadInterface
from fixedpointmath import FixedPoint

from agent0.base import Trade
from agent0.hyperdrive import HyperdriveMarketAction, HyperdriveWallet
from agent0.hyperdrive.policies import HyperdriveBasePolicy, PolicyZoo

from .interactive_hyperdrive import InteractiveHyperdrive
from .interactive_hyperdrive_policy import InteractiveHyperdrivePolicy
from .local_chain import LocalChain


@pytest.mark.anvil
def test_policy_config_forgotten(chain: LocalChain):
    """The policy config is not passed in."""
    interactive_config = InteractiveHyperdrive.Config()
    interactive_hyperdrive = InteractiveHyperdrive(chain, interactive_config)
    alice = interactive_hyperdrive.init_agent(
        base=FixedPoint(10_000),
        name="alice",
        policy=PolicyZoo.random,
    )
    assert alice.agent.policy is not None


@pytest.mark.anvil
def test_policy_config_none_rng(chain: LocalChain):
    """The policy config has rng set to None."""
    interactive_config = InteractiveHyperdrive.Config()
    interactive_hyperdrive = InteractiveHyperdrive(chain, interactive_config)
    agent_policy = PolicyZoo.random.Config()
    agent_policy.rng = None
    alice = interactive_hyperdrive.init_agent(
        base=FixedPoint(10_000),
        name="alice",
        policy=PolicyZoo.random,
        policy_config=agent_policy,
    )
    assert alice.agent.policy.rng is not None


@pytest.mark.anvil
def test_snapshot_policy_state(chain: LocalChain):
    """Tests proper saving/loading of policy state during snapshotting."""

    # Define dummy class for deep state copy
    class _InnerState:
        inner_var: int

        def __init__(self):
            self.inner_var = 1
            self.inner_list = [1]

    class _SubPolicy(HyperdriveBasePolicy):
        inner_state: _InnerState
        outer_var: int

        def __init__(self, policy_config: HyperdriveBasePolicy.Config):
            self.inner_state = _InnerState()
            self.outer_var = 2
            self.outer_list = [2]
            super().__init__(policy_config)

        def action(
            self, interface: HyperdriveReadInterface, wallet: HyperdriveWallet
        ) -> tuple[list[Trade[HyperdriveMarketAction]], bool]:
            # pylint: disable=missing-return-doc
            return [], False

    # Initialize agent with sub policy
    interactive_hyperdrive = InteractiveHyperdrive(chain)
    agent = interactive_hyperdrive.init_agent(policy=_SubPolicy)
    # Snapshot state
    chain.save_snapshot()

    # Sanity check and type narrowing
    assert isinstance(agent.agent.policy, InteractiveHyperdrivePolicy)
    assert agent.agent.policy.sub_policy is not None
    assert isinstance(agent.agent.policy.sub_policy, _SubPolicy)
    assert agent.agent.policy.sub_policy.outer_var == 2
    assert agent.agent.policy.sub_policy.outer_list == [2]
    assert agent.agent.policy.sub_policy.inner_state.inner_var == 1
    assert agent.agent.policy.sub_policy.inner_state.inner_list == [1]

    # Change inner state variables
    agent.agent.policy.sub_policy.outer_var = 22
    agent.agent.policy.sub_policy.outer_list.append(222)
    agent.agent.policy.sub_policy.inner_state.inner_var = 11
    agent.agent.policy.sub_policy.inner_state.inner_list.append(111)
    assert agent.agent.policy.sub_policy.outer_var == 22
    assert agent.agent.policy.sub_policy.outer_list == [2, 222]
    assert agent.agent.policy.sub_policy.inner_state.inner_var == 11
    assert agent.agent.policy.sub_policy.inner_state.inner_list == [1, 111]

    # Load snapshot
    chain.load_snapshot()

    # Ensure inner states were restored
    assert agent.agent.policy.sub_policy.outer_var == 2
    assert agent.agent.policy.sub_policy.outer_list == [2]
    assert agent.agent.policy.sub_policy.inner_state.inner_var == 1
    assert agent.agent.policy.sub_policy.inner_state.inner_list == [1]
