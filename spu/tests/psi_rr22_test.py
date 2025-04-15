# Copyright 2024 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import unittest
from tempfile import TemporaryDirectory

import multiprocess
from google.protobuf import json_format

import spu.libspu.link as link
import spu.psi as psi

from spu.tests.utils import create_link_desc, wc_count, get_free_port


class UnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir_ = TemporaryDirectory()
        return super().setUp()

    def tearDown(self) -> None:
        self.tempdir_.cleanup()
        return super().tearDown()

    def test_psi(self):
        # link_desc = create_link_desc(2)


        def wrap(rank):
            link_desc = link.Desc()
            link_desc.add_party("alice", f"127.0.0.1:{get_free_port()}")
            link_desc.add_party("bob", f"127.0.0.1:{get_free_port()}")
            role ="ROLE_RECEIVER" if rank == 0 else "ROLE_SENDER"
            csv_path_input_self = "spu/tests/data/alice.csv" if rank == 0 else "spu/tests/data/bob.csv"
            csv_path_output_self = f"{self.tempdir_.name}/spu_test_psi_alice_psi_ouput.csv" if rank == 0 else f"{self.tempdir_.name}/spu_test_psi_bob_psi_ouput.csv"    
            config_json = f'''
                {{
                    "protocol_config": {{
                        "protocol": "PROTOCOL_RR22",
                        "ecdh_config": {{
                            "curve": "CURVE_25519"
                        }},
                        "role": "{role}",
                        "broadcast_result": true
                    }},
                    "input_config": {{
                        "type": "IO_TYPE_FILE_CSV",
                        "path": "{csv_path_input_self}"
                    }},
                    "output_config": {{
                        "type": "IO_TYPE_FILE_CSV",
                        "path": "{csv_path_output_self}"
                    }},
                    "keys": [
                        "id"
                    ],
                    "skip_duplicates_check": true,
                    "disable_alignment": true
                }}
                '''

            link_ctx = link.create_grpc(link_desc, rank, False, 'psi_rr22_test')
            configs = json_format.ParseDict(json.loads(config_json), psi.PsiConfig())

            psi.psi(configs, link_ctx)

        jobs = [
            multiprocess.Process(
                target=wrap,
                args=(rank, ),
            )
            for rank in range(2)
        ]
        [job.start() for job in jobs]

        for job in jobs:
            job.join()

        self.assertEqual(
            wc_count(f"{self.tempdir_.name}/spu_test_psi_alice_psi_ouput.csv"),
            wc_count(f"{self.tempdir_.name}/spu_test_psi_bob_psi_ouput.csv"),
        )


if __name__ == '__main__':
    unittest.main()
