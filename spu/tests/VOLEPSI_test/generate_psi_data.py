import os
import random
import json
from gene_input import gen_sender_receiver_data

def generate_and_save_data(total_size=20000, intersection_size=None):
    # 创建data目录（如果不存在）
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 如果未指定交集大小，随机生成一个
    if intersection_size is None:
        intersection_size = random.randint(0, total_size) % (total_size - 100)
    
    print(f"生成数据集 - 总大小: {total_size}, 交集大小: {intersection_size}")
    
    # 生成数据集
    recv_list, sender_list = gen_sender_receiver_data(
        total_size,
        receiver_size=total_size,
        intersection_size=intersection_size
    )
    
    # 找到真实交集
    recv_set = set(recv_list)
    sender_set = set(sender_list)
    true_intersection = list(recv_set.intersection(sender_set))
    
    # 保存数据到文件
    data_files = {
        'server_data.txt': recv_list,
        'client_data.txt': sender_list,
        'true_intersection.txt': true_intersection
    }
    
    saved_files = {}
    for filename, data in data_files.items():
        file_path = os.path.join(data_dir, filename)
        with open(file_path, 'w') as f:
            f.write('\n'.join(data))
        saved_files[filename] = file_path
        print(f"已保存{filename}，包含 {len(data)} 条数据")
    
    # 保存元数据
    metadata = {
        'total_size': total_size,
        'intersection_size': len(true_intersection),
        'element_size': len(recv_list[0].encode()),
        'files': saved_files
    }
    
    metadata_path = os.path.join(data_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

if __name__ == '__main__':
    metadata = generate_and_save_data()
    print("\n数据生成完成！元数据已保存到 metadata.json")