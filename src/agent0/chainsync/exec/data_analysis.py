"""Script to format on-chain hyperdrive pool, config, and transaction data post-processing."""

from __future__ import annotations

import logging
import time
from typing import Callable

from eth_typing import ChecksumAddress
from sqlalchemy.orm import Session

from agent0.chainsync import PostgresConfig
from agent0.chainsync.analysis import data_to_analysis
from agent0.chainsync.db.base import initialize_session
from agent0.chainsync.db.hyperdrive import (
    PoolInfo,
    get_latest_block_number_from_analysis_table,
    get_latest_block_number_from_table,
    get_pool_config,
)
from agent0.ethpy.hyperdrive import HyperdriveReadInterface

_SLEEP_AMOUNT = 1


# TODO cleanup
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
def data_analysis(
    start_block: int = 0,
    interfaces: list[HyperdriveReadInterface] | None = None,
    rpc_uri: str | None = None,
    hyperdrive_addresses: list[ChecksumAddress] | None = None,
    db_session: Session | None = None,
    postgres_config: PostgresConfig | None = None,
    exit_on_catch_up: bool = False,
    exit_callback_fn: Callable[[], bool] | None = None,
    suppress_logs: bool = False,
    calc_pnl: bool = True,
):
    """Execute the data acquisition pipeline.

    Arguments
    ---------
    start_block: int
        The starting block to filter the query on
    interfaces: list[HyperdriveReadInterface] | None, optional
        A collection of Hyperdrive interface objects, each connected to a pool.
        If not set, will initialize one based on rpc_uri and hyperdrive_address.
    rpc_uri: str, optional
        The URI for the web3 provider to initialize the interface with. Not used if an interface
        is provided.
    hyperdrive_addresses: list[ChecksumAddress] | None, optional
        A collection of Hyperdrive address, each pointing to an initialized pool.
        Not used if a list of interfaces is provided.
    db_session: Session | None
        Session object for connecting to db. If None, will initialize a new session based on
        postgres.env.
    postgres_config: PostgresConfig | None = None,
        PostgresConfig for connecting to db. If none, will set from postgres.env.
    exit_on_catch_up: bool
        If True, will exit after catching up to current block
    exit_callback_fn: Callable[[], bool] | None, optional
        A function that returns a boolean to call to determine if the script should exit.
        The function should return False if the script should continue, or True if the script should exit.
        Defaults to not set.
    suppress_logs: bool, optional
        If true, will suppress info logging from this function. Defaults to False.
    calc_pnl: bool
        Whether to calculate pnl. Defaults to True.
    """
    # TODO implement logger instead of global logging to suppress based on module name.

    ## Initialization
    if interfaces is None:
        if hyperdrive_addresses is None or rpc_uri is None:
            # TODO when we start deploying the registry, this case should look for existing
            # pools in the registry and use those.
            raise ValueError("hyperdrive_address and rpc_uri must be provided if not providing interface")
        interfaces = [
            HyperdriveReadInterface(hyperdrive_address, rpc_uri) for hyperdrive_address in hyperdrive_addresses
        ]

    # postgres session
    db_session_init = False
    if db_session is None:
        db_session_init = True
        db_session = initialize_session(postgres_config=postgres_config, ensure_database_created=True)

    ## Get starting point for restarts
    analysis_latest_block_number = get_latest_block_number_from_analysis_table(db_session)

    # Using max of latest block in database or specified start block
    curr_start_write_block = max(start_block, analysis_latest_block_number + 1)

    # Get pool config
    # TODO this likely should return a pd.Series, not dataframe
    pool_config_df = None
    # Wait for pool config on queries to db to exist to ensure acquire_data is up and running
    for _ in range(10):
        pool_config_df = get_pool_config(db_session, coerce_float=False)
        pool_config_len = len(pool_config_df)
        if pool_config_len == 0:
            time.sleep(_SLEEP_AMOUNT)
        else:
            break
    if pool_config_df is None:
        raise ValueError("Error in getting pool config from db")

    # Main data loop
    # monitor for new blocks & add pool info per block
    if not suppress_logs:
        logging.info("Monitoring database for updates...")
    while True:
        latest_data_block_number = get_latest_data_block(db_session)
        # Only execute if we are on a new block
        if latest_data_block_number < curr_start_write_block:
            exit_callable = False
            if exit_callback_fn is not None:
                exit_callable = exit_callback_fn()
            if exit_on_catch_up or exit_callable:
                break
            time.sleep(_SLEEP_AMOUNT)
            continue
        # Does batch analysis on range(analysis_start_block, latest_data_block_number) blocks
        # i.e., [start_block, end_block)
        # TODO do regular batching to sample for wallet information
        analysis_start_block = curr_start_write_block
        analysis_end_block = latest_data_block_number + 1
        if not suppress_logs:
            logging.info("Running batch %s to %s", analysis_start_block, analysis_end_block)
        data_to_analysis(analysis_start_block, analysis_end_block, pool_config_df, db_session, interfaces, calc_pnl)
        curr_start_write_block = latest_data_block_number + 1

    # Clean up resources on clean exit
    # If this function made the db session, we close it here
    if db_session_init:
        db_session.close()


def get_latest_data_block(db_session: Session) -> int:
    """Gets the latest block the data pipeline has written
    Since there are multiple tables that analysis reads from,
    we query the latest block from all read tables and select the minimum
    block from the list.

    Arguments
    ---------
    db_session: Session
        The initialized db session.

    Returns
    -------
    int
        The latest block number from the PoolInfo table.
    """
    # Note to avoid race condition, we add pool info as the last update for the block
    latest_pool_info = get_latest_block_number_from_table(PoolInfo, db_session)

    return latest_pool_info
