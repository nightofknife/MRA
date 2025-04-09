import yaml
from typing import List, Dict, Any


def parse_missions(yaml_path: str) -> dict[Any, Any]:
    """
    解析 spl.yaml 文件，提取所有 mission 到列表中
    参数:
        yaml_path: spl.yaml 文件路径
    返回:
        List[Dict]: 包含所有 mission 的列表，维持原始结构
    """
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    missions = {}

    if isinstance(data, list):
        # 处理顶层直接是 mission 列表的情况
        for mission_entry in data:
            if 'mission' in mission_entry:
                missions[mission_entry['mission']['mission_name']] = (mission_entry['mission'])

    return missions


# 示例用法
if __name__ == "__main__":
    missions = parse_missions(r"C:\Users\356\Desktop\auto\MMA\MMA\project\Resonance\mission.yaml")
    print(missions)
    print(f"共解析到 {len(missions)} 个任务")

