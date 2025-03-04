import unittest

# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
from lib.charms.mongodb_libs.v0 import machine_helpers


class TestCharm(unittest.TestCase):
    def test_auth_enabled_file_does_not_exist(self):
        machine_helpers.MONGOD_SERVICE_UPSTREAM_PATH = "/tmp/missing_file"

        self.assertEqual(machine_helpers.auth_enabled(), False)

    def test_auth_enabled(self):
        machine_helpers.MONGOD_SERVICE_UPSTREAM_PATH = "tests/unit/data/mongodb_auth.service"
        self.assertEqual(machine_helpers.auth_enabled(), True)

        machine_helpers.MONGOD_SERVICE_UPSTREAM_PATH = "tests/unit/data/mongodb.service"

        self.assertEqual(machine_helpers.auth_enabled(), False)

    def test_generate_service_args(self):
        service_args_auth = " ".join(
            [
                "ExecStart=/usr/bin/mongod",
                "--bind_ip",
                "localhost,1.1.1.1",
                "--replSet",
                "my_repl_set",
                "--auth",
                "--clusterAuthMode=keyFile",
                f"--keyFile={machine_helpers.KEY_FILE}",
                "\n",
            ]
        )
        self.assertEqual(
            machine_helpers.generate_service_args(True, "1.1.1.1", "my_repl_set"),
            service_args_auth,
        )

        service_args = " ".join(
            [
                "ExecStart=/usr/bin/mongod",
                # bind to localhost and external interfaces
                "--bind_ip",
                "localhost,1.1.1.1",
                # part of replicaset
                "--replSet",
                "my_repl_set",
                "\n",
            ]
        )
        self.assertEqual(
            machine_helpers.generate_service_args(False, "1.1.1.1", "my_repl_set"),
            service_args,
        )
