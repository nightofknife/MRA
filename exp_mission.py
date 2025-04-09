import json
import os
import runpy
import time

from control import control as CT


# todo

class Mission_related():
    """
    这段用于读取资源文件夹下的所有任务json文件
    """

    def __init__(self, mission_dir=None):
        self.mission_dict = {}
        self.enter_mission_list = []
        if not mission_dir:
            self.mission_dir: str = r"D:\bishe\code\res"
        self.control = CT(app_name="com.netease.cloudmusic")
        self.read_mission_json()

        # 以下的是用于表示当前状态的

    def set_mission_dir(self, new_mission_dir: str):
        self.mission_dir = new_mission_dir

    def return_mission_dic(self) -> dict:
        return self.mission_dict

    def read_mission_json(self) -> bool:
        if self.mission_dir == "":
            return False

        for filename in os.listdir(self.mission_dir):
            if not filename.endswith(".json"):
                continue
            file_path = os.path.join(self.mission_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for key, value in data.items():
                    if key not in self.mission_dict:
                        self.mission_dict[key] = value
                        if value.get("type", None) == 1:
                            self.enter_mission_list.append(key)
                    else:
                        print(rf"出现重复键值{key}")

    def show_enter_mission(self) -> list:
        return self.enter_mission_list

    def run_mission_list(self, start_mission_name, function=None):
        # 这里可能加一个检查是否已经链接到模拟器的部分
        for _ in range(5):
            if not self.control.is_connect_device:
                try:
                    self.control.device_connect()
                    break
                except:
                    if function:
                        function("未能连接到设备")
                    return False

        todo_mission_list = [start_mission_name]
        while todo_mission_list:
            # print("当前任务列表:", " ".join(todo_mission_list))
            if function:
                function(todo_mission_list[-1])
            next_mission_list = self._run_mission(todo_mission_list.pop())
            if next_mission_list is not None:
                todo_mission_list.extend(next_mission_list[::-1])
        if function:
            function("任务结束")

    def _run_mission(self, mission_name) -> list | None:
        print("正在执行:", mission_name, "任务")
        print(self.mission_dict)
        value = self.mission_dict.get(mission_name, None)
        if not value:
            print("无此任务")
            return None

        loc = value.get('loc', [0, 0])
        roi = value.get('roi', self.control.screen_size)  # todo 这里需要设定为屏幕大小
        template = value.get("template", None)
        input_text = value.get("input_text", None)
        ocr_text = value.get("ocr_text", None)
        match_text = value.get("match_text", None)
        next = value.get("next", None)
        retry = value.get("retry", 0)
        delay = value.get("delay", 1)
        error_next = value.get("error_next", None)
        offset = value.get("offset", None)
        threshold = value.get("threshold", 0.8)
        type = value.get("type", 2)
        other = value.get("other", None)
        action = value.get("action", "nothing")
        check_change = value.get("check_change", None)
        sub_mission = value.get("sub_mission", [])

        # 支持 retry 参数
        for attempt in range(retry + 1):  # 包括第一次执行
            if check_change is not None:
                befor_change_img = self.control.snapshot()

            # 对坐标进行更新
            print("对坐标进行更新")
            if ocr_text and roi != self.control.screen_size:
                if ocr_text in self.control.recognition_text_ocr(rect=roi):
                    loc = [int(roi[0] + roi[2] / 2), int(roi[1] + roi[3] / 2)]
            if match_text:
                if temp_loc := self.control.find_text_ocr(text=match_text, rect=roi):
                    loc = temp_loc
            if template:
                if temp_loc := self.control.match_template(template_path=template, rect=roi, threshold=threshold):
                    loc = temp_loc
            if offset:
                loc = [loc[0] + offset[0], loc[1] + offset[1]]

            # 根据要求实现行为
            print("实现行为")
            match action:
                case "nothing":
                    pass
                case "click":
                    self.control.touch(loc=[loc[0], loc[1]])
                case "swipe":
                    self.control.swipe(start=loc[:2], end=loc[2:])
                case action if action.endswith(".py"):
                    abs_path = os.path.abspath(action)
                    runpy.run_path(abs_path)
                case "startapp":
                    self.control.startup_app()
                case "closeapp":
                    self.control.close_app()
                case "input_text":
                    self.control.input_text(text=input_text, loc=loc, sure=True)
                case _:
                    print("未知的操作类型: %s", action)
                    return None

            time.sleep(delay)

            # 更新后续任务
            print("更新后续任务")

            if check_change is not None:
                after_change_img = self.control.snapshot()

                # 判断图片变换程度
                similarity = self.control.image_similarity_detection(image1=befor_change_img, image2=after_change_img)

                if (0 < check_change < similarity) or (check_change < 0 and similarity > abs(check_change)):
                    if attempt < retry:  # 如果还有重试机会，则继续重试
                        continue
                    return error_next

            # 支持 sub_mission 参数
            if sub_mission:
                for sub_task in sub_mission:
                    self.run_mission_list(sub_task)

        return next


if __name__ == "__main__":
    pass

    temp = Mission_related()
    temp.run_mission_list(start_mission_name='启动程序')
