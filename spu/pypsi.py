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
import json
import pandas as pd
import numpy as np
from google.protobuf import json_format

import spu.psi as psi
import spu.libspu.link as link
from spu.tests.utils import create_link_desc, wc_count

class LicenceException(Exception):
    pass

class PSIParameters:
    def __init__(self, taskid, role, input, inindexfilename="", outfilename="result.csv", nelements=0, dt=1, elementbylen=40,
                  sysectbits=112, type=1, ot_type=0, log_dir="logs", false_positive_probability=1e-8,
                  address="0.0.0.0:7766", client_address="0.0.0.0:6379", bin_input=False, read_from_file=True,
                  server_output=False, use_redis=True, add_meta={}, thread_count=4):
        self.taskid = taskid
        self.role = role
        self.input = input
        self.inindexfilename = inindexfilename
        self.outfilename = outfilename
        self.nelements = nelements
        self.elementbylen = elementbylen
        self.sysectbits = sysectbits
        self.psi_type = type
        self.log_dir = log_dir
        self.address = address
        self.redis = client_address
        self.bin_input = bin_input
        self.read_from_file = read_from_file
        self.server_output = server_output
        self.use_redis = use_redis
        self.add_meta = add_meta
        assert(thread_count>0)
        self.thread_count = thread_count

class PSIParameters_v2:
    def __init__(self, taskid, role, party, redis, add_meta={}, sysectbits=112, psi_type=1, log_dir=".", log_level=2,
                 log_with_console=True, net_log_switch=False, server_output=True, use_redis=True):
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

class PSIParty:
    def __init__(self, parameters_v2, channel=None):
        self.parameters = parameters_v2


        if channel:
            self.chl = channel

        else:
            self.chl = channel

    def do_psi(self, input: bytes, element_size: int):
        # logger.info(f"role: {self.parameters.role}, taskid:, {self.parameters.taskid}, p_address: {self.parameters.party}, redis: {self.parameters.redis} element_size: {element_size}")
        # 创建PSI_data目录

        #产生uuid

        csv_path_input_self = f"PSI_data/{self.parameters.taskid}_{self.parameters.role}_input.csv"
        csv_path_output_self = f"PSI_data/{self.parameters.taskid}_{self.parameters.role}_output.csv"
        # 将input写入csv文件，每个元素大小为element_size，列名为id
        print("开始写入文件", csv_path_input_self)
        if os.path.exists(csv_path_output_self):
            os.remove(csv_path_output_self)
        if not os.path.exists("PSI_data"):
            os.makedirs("PSI_data")
        # 将bytes类型的input转换为numpy数组
        data = np.frombuffer(input, dtype=np.uint8)
        elements = []
        
        # 按照element_size分割数据
        for i in range(0, len(data), element_size):
            element = data[i:i+element_size].tobytes().hex()
            elements.append(element)
            
        # 创建DataFrame并保存为CSV
        df = pd.DataFrame(elements, columns=['id'])
        df.to_csv(csv_path_input_self, index=False)


        link_desc = create_link_desc(2)

        receiver_config_json = f'''
        {{
            "protocol_config": {{
                "protocol": "PROTOCOL_RR22",
                "ecdh_config": {{
                    "curve": "CURVE_25519"
                }},
                "role": "ROLE_RECEIVER",
                "broadcast_result": true
            }},
            "input_config": {{
                "type": "IO_TYPE_FILE_CSV",
                "path": "PSI_data/{self.parameters.taskid}_0_input.csv"
            }},
            "output_config": {{
                "type": "IO_TYPE_FILE_CSV",
                "path": "PSI_data/{self.parameters.taskid}_0_output.csv"
            }},
            "keys": [
                "id"
            ],
            "skip_duplicates_check": true,
            "disable_alignment": true
        }}
        '''

        sender_config_json = f'''
        {{
            "protocol_config": {{
                "protocol": "PROTOCOL_RR22",
                "ecdh_config": {{
                    "curve": "CURVE_25519"
                }},
                "role": "ROLE_SENDER",
                "broadcast_result": true
            }},
            "input_config": {{
                "type": "IO_TYPE_FILE_CSV",
                "path": "PSI_data/{self.parameters.taskid}_1_input.csv"
            }},
            "output_config": {{
                "type": "IO_TYPE_FILE_CSV",
                "path": "PSI_data/{self.parameters.taskid}_1_output.csv"
            }},
            "keys": [
                "id"
            ],
            "skip_duplicates_check": true,
            "disable_alignment": true
        }}
        '''

        configs = [
            json_format.ParseDict(json.loads(receiver_config_json), psi.PsiConfig()),
            json_format.ParseDict(json.loads(sender_config_json), psi.PsiConfig()),
        ]
        print("self.parameters.role", self.parameters.role)
        link_ctx = link.create_grpc(link_desc, self.parameters.role)
        # gaia_net = link.create_gaia_channel(self.parameters.role, self.parameters.taskid)
        link_ctx.add_gaia_net()
        psi.psi(configs[self.parameters.role], link_ctx)

        df = pd.read_csv(csv_path_output_self)
        result = df['id'].values

        os.remove(csv_path_output_self)
        # link_ctx.add_gaia_net()
        # gaia_net.destroy()

        return result
