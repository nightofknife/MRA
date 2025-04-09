import os
import runpy
import time

import yaml
from typing import Dict, List, Optional, Any
from resource.function.control import control as CT
from typing import List, Dict, Any


class MissionRunner:
    """
    这个类用于解析任务，运行任务，留出端口用于承接更高层的调用请求
    """

    def __init__(self, yaml_path: str):
        self.yaml_path = None
        self.missions = self._parse_yaml(yaml_path)
        self.control = CT(window_name="雷索纳斯")
        self.mission_dict = self.parse_missions()  # 存储任务变量
        self.running_mission = None

    def parse_missions(self, yaml_path: str | bool = None) -> dict[Any, Dict]:
        """
        解析 spl.yaml 文件，提取所有 mission 到列表中
        参数:
            yaml_path: spl.yaml 文件路径
        返回:
            List[Dict]: 包含所有 mission 的列表，维持原始结构
        """
        if yaml_path is None:
            yaml_path = self.yaml_path

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        missions = {}

        if isinstance(data, list):
            # 处理顶层直接是 mission 列表的情况
            for mission_entry in data:
                if 'mission' in mission_entry:
                    missions[mission_entry['mission']['mission_name']] = (mission_entry['mission'])
        self.mission_dict = missions
        return missions

    def Run_Mission(self, mission_name: str) -> bool:

        todo_mission_list = [mission_name]
        while todo_mission_list:
            print("当前任务列表:", " ".join(todo_mission_list))

            next_mission_list = self.Run_sigle_Mission(todo_mission_list.pop())
            if next_mission_list is not False:
                todo_mission_list.extend(next_mission_list[::-1])

    def Run_sigle_Mission(self, mission_name: str) -> bool:
        print("正在执行:", mission_name, "任务")
        mission_value: Dict = self.mission_dict.get(mission_name, None)
        if not mission_value:
            print("无此任务")
            return False

        # 支持 retry 参数
        for _ in range(mission_value['retry_time'] + 1):  # 包括第一次执行
            for steps in mission_value['step']:

                # 对坐标进行更新
                roi = steps.get('recognition').get('region_rel', self.control.region)  # 这里的默认值应该是屏幕大小
                # 根据要求实现行为
                print("实现行为")
                match steps.get('action').get('type', None):
                    case "nothing":
                        pass
                    case "click":

                        if ocr_text := steps.get('recognition').get('ocr_text', None):
                            if ocr_text in self.control.recognition_text_ocr(rect=roi):
                                loc = [int(roi[0] + roi[2] / 2), int(roi[1] + roi[3] / 2)]
                        if find_text := steps.get('recognition').get('find_text', None):
                            if temp_loc := self.control.find_text_ocr(text=find_text, rect=roi):
                                loc = temp_loc
                        if template := steps.get('recognition').get('template', None):
                            if temp_loc := self.control.match_template(aim=,img=,
                                                                       threshold=steps.get('recognition').get('threshold', 0.8)):
                                loc = temp_loc
                        if click_loc := steps.get('action').get('click', None):
                            loc = click_loc

                        if offset := steps.get('action').get('offset', None):
                            loc = [loc[0] + offset[0], loc[1] + offset[1]]

                        self.control.touch(loc=[loc[0], loc[1]])

                    case "swipe":
                        if swipe_loc := steps.get('action').get('swipe_loc', None):
                            loc = swipe_loc

                        if offset := steps.get('action').get('offset', None):
                            loc = [loc[0] + offset[0], loc[1] + offset[1], loc[2] + offset[2], loc[3] + offset[3]]

                        self.control.swipe(start=loc[:2], end=loc[2:])

                    case action if action.endswith(".py"):
                        abs_path = os.path.abspath(action)
                        runpy.run_path(abs_path)

                    case "startapp":
                        if app_name:= steps.get('action').get('app_name', None):
                            self.control.startup_app(app_name)

                    case "closeapp":
                        if app_name := steps.get('action').get('app_name', None):
                            self.control.app_name(app_name)

                    case _:
                        print("未知的操作类型: %s", action)
                        return False

                time.sleep(steps.get('delay',0))

            # 更新后续任务
            print("更新后续任务")

        return next
