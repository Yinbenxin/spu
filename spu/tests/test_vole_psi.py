import spu.pypsi as psi

import time
import os
import argparse
import threading
import random
import concurrent.futures
from spu.tests.gene_input import gen_sender_receiver_data
# import pygaialog

ROLE_SERVER = 0
ROLE_CLIENT = 1

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--role", type=int, default=-1, choices=[-1, 0, 1],
                    help="role, defalut value is -1, mean run all role")
parser.add_argument("-t", "--type", type=str, default="grpc", choices=["grpc", "mem"],
                    help="channel type, defalut value is grpc")
parser.add_argument("-m", "--max_packet_size", type=int,
                    default=1024 * 16, help="max packet size")
parser.add_argument("-d", "--data_size", type=int,

                    default=100000, help="test data size")
parser.add_argument("-e", "--enable_cv", type=int, default=1, choices=[0, 1],
                    help="use condition variables instead spinlock")

args = parser.parse_args()
print("args=", args)


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
    party, redis = get_server_from_env()  # add_meta={}, sysectbits=112, psi_type=0, log_dir=".", log_level=0, log_with_console=True, net_log_switch=False

    psi_params = dict(party=party, sysectbits=112, add_meta={},
                      redis=redis, log_dir=".", log_level=0,
                      server_output=True, use_redis=True,
                      log_with_console=True, net_log_switch=False, psi_type=3)
    print("psi_params = ", psi_params, "role = ", role)
    params = psi.PSIParameters_v2("psitask", role, **psi_params)
    psi_party = psi.PSIParty(params)
    res = psi_party.do_psi(inputs, element_size)
    print("role = ", role, ", psi res[:10]: ", res[:10])
    return res



def pressure_test():
    total_size = args.data_size
    total_size = 20000
    intersection_size = random.randint(0, total_size) % (total_size - 100)
    #intersection_size = 10
    print("intersection_size: ", intersection_size)
    recv_list, sender_list = gen_sender_receiver_data(total_size, receiver_size=total_size,
                                                      intersection_size=intersection_size)
    print("generate finished: ", intersection_size)
    
    element_size = len(recv_list[0].encode())
    recv_list_bytes = b''.join(map(lambda x: x.encode(), recv_list))
    sender_list_bytes = b''.join(map(lambda x: x.encode(), sender_list))
    start_time = time.time()
    print("sendser_size: {}, receiver_size: {}, intersection_size: {}", len(sender_list), len(recv_list), intersection_size);
    if args.role == -1:
        import multiprocess
        from multiprocess import Queue
        
        # 创建结果队列
        result_queue = Queue()
        
        def psi_party_with_queue(rank, inputs, element_size, queue):
            result = psi_party(rank, inputs, element_size)
            queue.put((rank, result))
        
        # 创建进程列表
        jobs = []
        input_data = {
            0: recv_list_bytes,    # ROLE_SERVER
            1: sender_list_bytes,  # ROLE_CLIENT
        }
        
        for rank in range(2):
            p = multiprocess.Process(
                target=psi_party_with_queue,
                args=(rank, input_data[rank], element_size, result_queue)
            )
            jobs.append(p)
        
        # 启动所有进程
        [job.start() for job in jobs]
        
        # 收集结果
        results = {}
        for _ in range(len(jobs)):
            rank, result = result_queue.get()
            results[rank] = result
            print(f"Role {rank} result length: {len(result)}")

            if rank == ROLE_CLIENT:
                assert len(result) == intersection_size, \
                    f"Intersection size mismatch: got {len(result)}, expected {intersection_size}"
        print("generate finished: ", intersection_size)
        
        # 等待所有进程完成
        for job in jobs:
            job.join()
   
    elif args.role == 0:
        old_psi(0, recv_list_bytes, element_size)
    elif args.role == 1:
        old_psi(1, sender_list_bytes, element_size)
    else:
        raise Exception("unknown role ...")
    end_time = time.time()
    print("use time :", end_time - start_time)

if __name__ == "__main__":

    pressure_intensity  = 1
    for i in range(pressure_intensity):
        pressure_test()
