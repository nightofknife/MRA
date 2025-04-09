import os
import cv2
import time
import psutil


if __name__ == "__main__":
    import control

if __name__ == "game_action":
    import resource.function.control as control


"""
这个类别准备改成启动和关闭游戏的
"""
class game_action(control.control):
    game_start: bool = False
    gema_path = r"D:\game\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe"
    game_name_CN = '鸣潮  '
    game_name_EN = 'Wuthering Waves.exe'

    def __init__(self, game_path=None):
        self.check_game_state()
        control.control.__init__(self)
        self.start_camera_cut()

    def mouse_click(self, x, y, key=1):
        offset = self.window_rect[:2]
        self.win32_click(x=x + offset[0], y=y + offset[1], key=1)

    def check_game_state(self):
        pl = psutil.pids()
        for pid in pl:
            if psutil.Process(pid).name() == 'Wuthering Waves.exe':
                print("程序正在运行")
                self.game_start = True
                return True
        print("程序未在运行")
        self.game_start = False
        return False

    def search_game_path(self):
        return None

    def open_game(self):
        os.startfile(self.gema_path)

    def start_game(self):
        self.open_game()
        while True:
            if self.check_game_state():
                break
            print('!')
            time.sleep(1)
        time.sleep(10)
        self.start_camera_cut()
        start_time = time.time()
        new_time = time.time()
        while new_time - start_time < 3600:
            img = self.latest_frame_rect()
            result = self.find_text_include_ocr(text="特征码", img=img)
            if result:
                print("已经在游戏中")
                return True
            self.lg_mouse_up_and_down()
            time.sleep(1)
        return False

    def close_game(self):
        pass

    def temp_daily_mission_get(self):
        self.open_course_interface()

        time.sleep(2)
        while True:
            if result := self.find_text_include_ocr(text="领取", img=self.latest_frame_rect()):
                print(result)
                self.mouse_click(x=result[0], y=result[1], key=1)
            else:
                break
            time.sleep(1)
        while True:
            if result := self.match_template(
                    aim=cv2.imread(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\template\daily.jpg"),
                    img=self.latest_frame_rect()):
                print(result)
                self.mouse_click(x=result[0] + 24, y=result[1] + 40, key=1)
            else:
                break
            time.sleep(1)
        print("领取完成")

        if result := self.find_text_include_ocr(text="点击空白区域关闭", img=self.latest_frame_rect()):
            print(result)
            self.mouse_click(x=result[0], y=result[1], key=1)

        while True:
            if self.match_template(
                    aim=cv2.imread(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\template\mian.jpg"),
                    img=self.latest_frame_rect(), threshold=0.9):
                break
            self.keyboard_key_down_and_up(key=self.key.Esc.value)
            time.sleep(2)

    def temp_pass_mission_get(self):
        self.open_pass_interface()

        time.sleep(2)
        while True:
            if result := self.match_template(
                    aim=r"C:\Users\356\Desktop\auto\MMA\MMA\resource\template\pass_mission.jpg",
                    img=self.latest_frame_rect(), threshold=0.6):
                print(result)
                self.mouse_click(x=result[0], y=result[1], key=1)
                break
            time.sleep(1)
        if result := self.find_text_include_ocr(text="一键领取", img=self.latest_frame_rect()):
            print(result)
            self.mouse_click(x=result[0], y=result[1], key=1)
            time.sleep(2)
        while True:
            if result := self.match_template(
                    aim=cv2.imread(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\template\pass_gift.jpg"),
                    img=self.latest_frame_rect(), threshold=0.9):
                print(result)
                self.mouse_click(x=result[0] + 24, y=result[1] + 40, key=1)
                break
            time.sleep(1)
        if result := self.find_text_include_ocr(text="一键领取", img=self.latest_frame_rect()):
            print(result)
            self.mouse_click(x=result[0], y=result[1], key=1)
            time.sleep(2)
        if result := self.find_text_include_ocr(text="点击空白区域关闭", img=self.latest_frame_rect()):
            print(result)
            self.mouse_click(x=result[0], y=result[1], key=1)
        while True:
            if self.match_template(
                    aim=cv2.imread(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\template\mian.jpg"),
                    img=self.latest_frame_rect(), threshold=0.9):
                break
            self.keyboard_key_down_and_up(key=self.key.Esc.value)
            time.sleep(2)

    def temp_backpack_(self):
        self.open_package_interface()


if __name__ == "__main__":
    temp = game_action()
    temp.temp_daily_mission_get()
    temp.temp_pass_mission_get()
