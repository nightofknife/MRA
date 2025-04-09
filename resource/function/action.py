import time

import cv2

from control import control

"""
这个类应该实现游戏中各种基础操作
先实现一个有用的
1：识别声骸信息保存并判断有无升级必要，有就升级，没有就跳过
"""


class base_action(control):

    def __init__(self):
        control.__init__(self)


    # 日常任务用函数
    def choose_daily_mission(self):
        """
        这个函数用于点击切换到日常任务的任务界面
        :return:
        """

    def choose_daily_award(self):
        """
        这个函数用于点击切换到日常任务的奖励界面
        :return:
        """

    def get_daily_mission(self):
        """
        这个是用于领取完成的任务
        :return:
        """
        while True:
            if result := self.find_text_include_ocr(text="领取", img=self.latest_frame_rect()):
                print(result)
                self.win32_click(x=result[0], y=result[1], key=1)
            else:
                break
            time.sleep(1)

    def get_daily_reward(self):
        """
        这个是用于领取每日奖励的
        :return:
        """
        while True:
            if result := self.match_template(
                    aim=cv2.imread(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\template\daily.jpg"),
                    img=self.latest_frame_rect()):
                print(result)
                self.win32_click(x=result[0] + 24, y=result[1] + 40, key=1)
            else:
                break
            time.sleep(1)

    def get_daily(self):
        """
        这个函数是用于完整的收取每日奖励的
        :return:
        """

    # 通行证用的函数
    def choose_pass_mission(self):
        """
        这个函数用于点击切换到通行证的任务界面
        :return:
        """

    def choose_pass_award(self):
        """
        这个函数用于切换到通行证的奖励界面
        :return:
        """

    # 这里用于切换仓库中不同的类别
    def choose_warehouse_monster(self):
        """
        这个是用于切换到声骸类别的
        :return:
        """
    def choose_warehouse_type2(self):
        pass
    def choose_warehouse_type3(self):
        pass
    def choose_warehouse_type4(self):
        pass
    def choose_warehouse_type5(self):
        pass
    def choose_warehouse_type6(self):
        pass

    # 这里用于切换任务列表的类别

    def choose_mission_type1(self):
        pass
    def choose_mission_type2(self):
        pass
    def choose_mission_type3(self):
        pass
    def choose_mission_type4(self):
        pass
    def choose_mission_type5(self):
        pass

    # 这里是临时用的用于声骸参数识别的部分
    def temp_choose_monster(self):
        """
        这里是点击声骸
        :return:
        """

    def temp_identification_data(self):
        """
        这里是用于读取生骸信息的
        :return:
        """

    def temp_calculated_value(self):
        """
        这里是计算声骸价值的
        :return:
        """

    def temp_upgrade_monster(self):
        """
        这里用于升级声骸
        :return:
        """
        def temp_enter_monster():
            """
            这里是进入声骸信息界面（如果有
            :return:
            """

    def temp_all_monster(self):
        """
        这里是总体的用于读取声骸信息并升级的部分
        :return:
        """




















