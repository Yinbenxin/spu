import os
import json
import argparse
from psi_common import psi_party
# python run_psi.py -r 0
# python run_psi.py -r 1
def load_data(file_path):
    """从文件加载数据"""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines()]

def run_psi_role(role, data_dir):
    # 加载元数据
    metadata_path = os.path.join(data_dir, 'metadata.json')
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # 根据角色选择对应的数据文件
    data_file = os.path.join(data_dir, 'server_data.txt' if role == 0 else 'client_data.txt')
    data_list = load_data(data_file)
    
    # 准备输入数据
    element_size = metadata['element_size']
    data_bytes = b''.join(map(lambda x: x.encode(), data_list))
    
    # 执行PSI计算
    print(f"角色 {role} 开始PSI计算，数据大小: {len(data_list)}")
    result = psi_party(role, data_bytes, element_size)
    
    # 如果是客户端，验证结果
    if role == 1:  # 客户端
        true_intersection = load_data(os.path.join(data_dir, 'true_intersection.txt'))
        assert len(result) == len(true_intersection), \
            f"交集大小不匹配: 计算结果 {len(result)}, 预期 {len(true_intersection)}"
        print(f"PSI计算完成！交集大小: {len(result)}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description='运行PSI计算')
    parser.add_argument('-r', '--role', type=int, required=True, choices=[0, 1],
                        help='角色 (0: 服务端, 1: 客户端)')
    args = parser.parse_args()
    
    # 获取data目录路径
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"找不到数据目录: {data_dir}，请先运行 generate_psi_data.py 生成测试数据")
    
    run_psi_role(args.role, data_dir)

if __name__ == '__main__':
    main()