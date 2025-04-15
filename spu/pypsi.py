"""TenSEAL is a library for doing homomorphic encryption operation on tensors.
"""
import os

# try:
#     import _pypsi_cpp as _psi_cpp
# except ImportError:
#     import pypsi._pypsi_cpp as _psi_cpp



# from pypsi.version import __version__
# import pygaialog as logger
# import pygaiachannel
import uuid
import json
import pandas as pd
import numpy as np
from google.protobuf import json_format
from tempfile import TemporaryDirectory

import spu.psi as psi
import spu.libspu.link as link
from spu.tests.utils import create_link_desc, wc_count,get_free_port
import logging

class PSIParameters_v2:
    def __init__(self, taskid, role, party, redis, add_meta={}, sysectbits=112, psi_type=1, log_dir=".", log_level=2,
                 log_with_console=True, net_log_switch=False, server_output=True, use_redis=True, chl_type='mem'):
        self.taskid = taskid
        self.party = party #address
        self.role = role
        self.redis = redis
        self.sysectbits = sysectbits
        self.log_dir = log_dir
        self.log_level = log_level
        self.psi_type = psi_type
        self.net_log_switch = net_log_switch
        self.add_meta = add_meta
        self.log_with_console = log_with_console
        self.server_output = server_output
        self.use_redis = use_redis
        self.chl_type = chl_type # mem or grpc
class PSIParty:
    def __init__(self, parameters_v2, channel=None):
        self.parameters = parameters_v2
        self.tempdir_ = TemporaryDirectory()
        
    def tearDown(self) -> None:
        self.tempdir_.cleanup()
        return super().tearDown()

    def do_psi(self, input: bytes, element_size: int):
        # logger.info(f"role: {self.parameters.role}, taskid:, {self.parameters.taskid}, p_address: {self.parameters.party}, redis: {self.parameters.redis} element_size: {element_size}")
        # 创建PSI_data目录

        # link_desc = create_link_desc(2)
        link_desc = link.Desc()
        link_desc.add_party("alice", f"127.0.0.1:{get_free_port()}")
        link_desc.add_party("bob", f"127.0.0.1:{get_free_port()}")
        link_ctx = link.create_grpc(link_desc, self.parameters.role, False, self.parameters.taskid, self.parameters.chl_type, self.parameters.party, self.parameters.redis )
        #产生uuid
        uuid_str = str(uuid.uuid4())
        csv_path_input_self = f"{self.tempdir_.name}/{self.parameters.taskid}_{self.parameters.role}_input.csv"
        csv_path_output_self = f"{self.tempdir_.name}/{self.parameters.taskid}_{self.parameters.role}_output.csv"
        data = np.frombuffer(input, dtype=np.uint8)
        elements = []
        
        # 按照element_size分割数据
        for i in range(0, len(data), element_size):
            element = data[i:i+element_size].tobytes().hex()
            elements.append(element)
        print("开始写入文件", csv_path_input_self)
        # 创建DataFrame并保存为CSV
        df = pd.DataFrame(elements, columns=['id'])
        df.to_csv(csv_path_input_self, index=False)

        role ="ROLE_RECEIVER" if self.parameters.role == 0 else "ROLE_SENDER"

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
        configs = json_format.ParseDict(json.loads(config_json), psi.PsiConfig())
        logging.info('开始PSI')

        try:
            psi.psi(configs, link_ctx)
        except Exception as e:
            logging.info(e)
        logging.info('完成PSI')
        
        # link_ctx.del_gaia_net()
        df = pd.read_csv(csv_path_output_self)
        result = df['id'].values
        
        return result
