#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os

import pytest
from helpers import (
    APP_NAME,
    PORT,
    UNIT_IDS,
    count_primaries,
    find_unit,
    get_password,
    unit_uri,
)
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from pytest_operator.plugin import OpsTest
from tenacity import RetryError

logger = logging.getLogger(__name__)

ANOTHER_DATABASE_APP_NAME = "another-database-a"


@pytest.mark.skipif(
    os.environ.get("PYTEST_SKIP_DEPLOY", False),
    reason="skipping deploy, model expected to be provided.",
)
@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest) -> None:
    """Build and deploy one unit of MongoDB."""
    my_charm = await ops_test.build_charm(".")
    await ops_test.model.deploy(my_charm, num_units=len(UNIT_IDS))
    await ops_test.model.wait_for_idle()


@pytest.mark.abort_on_fail
async def test_status(ops_test: OpsTest) -> None:
    """Verifies that the application and unit are active."""
    await ops_test.model.wait_for_idle(apps=[APP_NAME], status="active", timeout=1000)
    assert len(ops_test.model.applications[APP_NAME].units) == len(UNIT_IDS)


@pytest.mark.parametrize("unit_id", UNIT_IDS)
async def test_unit_is_running_as_replica_set(ops_test: OpsTest, unit_id: int) -> None:
    """Tests that mongodb is running as a replica set for the application unit."""
    # connect to mongo replica set
    unit = ops_test.model.applications[APP_NAME].units[unit_id]
    connection = unit.public_address + ":" + str(PORT)
    client = MongoClient(connection, replicaset="mongodb")

    # check mongo replica set is ready
    try:
        client.server_info()
    except ServerSelectionTimeoutError:
        assert False, "server is not ready"

    # close connection
    client.close()


async def test_leader_is_primary_on_deployment(ops_test: OpsTest) -> None:
    """Tests that right after deployment that the primary unit is the leader."""
    # grab leader unit
    leader_unit = await find_unit(ops_test, leader=True)

    # verify that we have a leader
    assert leader_unit is not None, "No unit is leader"

    # connect to mongod
    password = await get_password(ops_test)
    client = MongoClient(unit_uri(leader_unit.public_address, password), directConnection=True)

    # verify primary status
    assert client.is_primary, "Leader is not primary"
    client.close()


async def test_exactly_one_primary(ops_test: OpsTest) -> None:
    """Tests that there is exactly one primary in the deployed units."""
    try:
        password = await get_password(ops_test)
        number_of_primaries = count_primaries(ops_test, password)
    except RetryError:
        number_of_primaries = 0

    # check that exactly of the units is the leader
    assert number_of_primaries == 1, "Expected one unit to be a primary: {} != 1".format(
        number_of_primaries
    )


async def test_get_primary_action(ops_test: OpsTest) -> None:
    """Tests that action get-primary outputs the correct unit with the primary replica."""
    # determine which unit is the primary
    expected_primary = None
    for unit in ops_test.model.applications[APP_NAME].units:
        # connect to mongod
        password = await get_password(ops_test)
        client = MongoClient(unit_uri(unit.public_address, password), directConnection=True)

        # check primary status
        if client.is_primary:
            expected_primary = unit.name
            break

    # verify that there is a primary
    assert expected_primary

    # check if get-primary returns the correct primary unit regardless of
    # which unit the action is run on
    for unit in ops_test.model.applications[APP_NAME].units:
        # use get-primary action to find primary
        action = await unit.run_action("get-primary")
        action = await action.wait()
        identified_primary = action.results["replica-set-primary"]

        # assert get-primary returned the right primary
        assert identified_primary == expected_primary

async def test_exactly_one_primary_reported_by_juju(ops_test: OpsTest) -> None:
    primary = []
    
    def check():
        for unit in ops_test.model.applications[app].units:
            if self.unit.status = "Replica set primary"
            primary.append(unit)
        assert len(primary) == 1, "Multiple replica set primaries detected"

    check()

    # kill the replica set primary
    await kill_unit_process(ops_test, primary[0], kill_code="SIGKILL")

    # wait for re-election, sleep for twice the median election time
    time.sleep(MEDIAN_REELECTION_TIME * 2)

    check()

    # remove killed unit
    await ops_test.model.destroy_unit(primary[0])
