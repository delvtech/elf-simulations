"""Dataclasses for all structs in the IHyperdrive contract.

DO NOT EDIT.  This file was generated by pypechain.  See documentation at
https://github.com/delvtech/pypechain """

# super() call methods are generic, while our version adds values & types
# pylint: disable=arguments-differ
# contracts have PascalCase names
# pylint: disable=invalid-name
# contracts control how many attributes and arguments we have in generated code
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments
# unable to determine which imports will be used in the generated code
# pylint: disable=unused-import
# we don't need else statement if the other conditionals all have return,
# but it's easier to generate
# pylint: disable=no-else-return
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Fees:
    """Fees struct."""

    curve: int
    flat: int
    governanceLP: int
    governanceZombie: int


@dataclass
class PoolConfig:
    """PoolConfig struct."""

    baseToken: str
    linkerFactory: str
    linkerCodeHash: bytes
    initialVaultSharePrice: int
    minimumShareReserves: int
    minimumTransactionAmount: int
    positionDuration: int
    checkpointDuration: int
    timeStretch: int
    governance: str
    feeCollector: str
    fees: Fees


@dataclass
class Options:
    """Options struct."""

    destination: str
    asBase: bool
    extraData: bytes


@dataclass
class Checkpoint:
    """Checkpoint struct."""

    vaultSharePrice: int


@dataclass
class MarketState:
    """MarketState struct."""

    shareReserves: int
    bondReserves: int
    longExposure: int
    longsOutstanding: int
    shareAdjustment: int
    shortsOutstanding: int
    longAverageMaturityTime: int
    shortAverageMaturityTime: int
    isInitialized: bool
    isPaused: bool
    zombieBaseProceeds: int
    zombieShareReserves: int


@dataclass
class PoolInfo:
    """PoolInfo struct."""

    shareReserves: int
    shareAdjustment: int
    zombieBaseProceeds: int
    zombieShareReserves: int
    bondReserves: int
    lpTotalSupply: int
    vaultSharePrice: int
    longsOutstanding: int
    longAverageMaturityTime: int
    shortsOutstanding: int
    shortAverageMaturityTime: int
    withdrawalSharesReadyToWithdraw: int
    withdrawalSharesProceeds: int
    lpSharePrice: int
    longExposure: int


@dataclass
class WithdrawPool:
    """WithdrawPool struct."""

    readyToWithdraw: int
    proceeds: int


@dataclass
class PoolDeployConfig:
    """PoolDeployConfig struct."""

    baseToken: str
    linkerFactory: str
    linkerCodeHash: bytes
    minimumShareReserves: int
    minimumTransactionAmount: int
    positionDuration: int
    checkpointDuration: int
    timeStretch: int
    governance: str
    feeCollector: str
    fees: Fees
