import spu.py_psi as psi
import os
import argparse

ROLE_SERVER = 0
ROLE_CLIENT = 1

def get_server_from_env() -> (str, str):
    """
    get grpc and redis server from env
    :return:
    """
    grpc_server = os.getenv("GRPC_SERVER", "0.0.0.0:9900")
    redis_server = os.getenv("REDIS_SERVER", "tcp://redis123@127.0.0.1:6379")
    print("grpc server ", grpc_server)
    return grpc_server, redis_server

def psi_party(role, inputs, element_size):
    party, redis = get_server_from_env()

    psi_params = dict(party=party, sysectbits=112, add_meta={},
                      redis=redis, log_dir=".", log_level=0,
                      server_output=True, use_redis=True,
                      log_with_console=True, net_log_switch=False, psi_type=3)
    print("psi_params = ", psi_params, "role = ", role)
    params = psi.PSIParameters_v2("psitask123", role, **psi_params)
    psi_party = psi.PSIParty(params)
    res = psi_party.do_psi(inputs, element_size)
    print("role = ", role, ", psi res[:10]: ", res[:10])
    return res

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", type=str, default="grpc", choices=["grpc", "mem"],
                        help="channel type, defalut value is grpc")
    parser.add_argument("-m", "--max_packet_size", type=int,
                        default=1024 * 16, help="max packet size")
    parser.add_argument("-d", "--data_size", type=int,
                        default=100000, help="test data size")
    parser.add_argument("-e", "--enable_cv", type=int, default=1, choices=[0, 1],
                        help="use condition variables instead spinlock")
    return parser.parse_args()