# 这个文件用于实现角色定向移动到某个坐标
import resource.function.control

if __name__ == "move_action":
    import control
    import cv2
    import numpy as np
    import math
    import time

if __name__ == "__main__":
    import control
    import cv2
    import numpy as np
    import math
    import time
    from matplotlib import pyplot as plt
    import json


# 规定坐标，x轴 y轴顺序均以游戏内顺序处理

class move(control.control):
    old_loc = [0, 0, 0]
    direction = 0
    map = cv2.imread(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\template\map_temp.jpg")
    angle_template = cv2.imread(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\template\direction.jpg")

    def __init__(self):
        control.control.__init__(self)
        with open(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\data\transport_loc.json", 'r+', encoding='utf-8') as f:
            self.transport_loc = json.load(f)
        self.start_camera_cut()

    def move_to_xy(self, aim_loc):
        # new_loc = self.map_reset_base_loc()
        new_loc = (0, 0)

        # 这里需要计算最近的传送点是哪个
        nest_transport_id, nest_transport_dis, nest_transport_loc = self.transport_to_nest_xy(aim_loc)

        # 这里需要计算直接过去近还是传送近
        # if self.calculated_distance(start=new_loc,end=aim_loc) < nest_transport_inf[1]:
        #     # 如果跑过去更好
        #     self.run_to_xy(aim_loc=aim_loc)
        #     return
        # 这里点开地图拖动到传送点传送
        ## 这里开始截取终点地图部分用于后续拖动地图

        transport_map_loc = self.transform_loc(type="ttm", loc=nest_transport_loc)
        aim_img = self.map[transport_map_loc[1] - 160:transport_map_loc[1] + 160,
                  transport_map_loc[0] - 160:transport_map_loc[0] + 160]
        # cv2.imshow("1", aim_img)
        # cv2.waitKey(0)

        ## 这里开始计算游戏地图移动方向
        offset = (j - i for i, j in zip(new_loc, nest_transport_loc))

        # self.keyboard_key_down_and_up(self.key.M.value)

        # 重置角色坐标，导航到目的地

    def transport_to_nest_xy(self, aim_loc):
        aim_loc_xy = aim_loc[:2]
        min_dis = 114514
        min_loc = (0, 0)
        id = None
        for i in self.transport_loc:
            for j in i['location']:
                dis = self.calculated_distance(start=(j['x'], j['y']), end=aim_loc_xy)
                if dis < min_dis:
                    min_dis = dis
                    min_loc = (j['x'], j['y'])
                    id = j['id']
        print(id, min_loc)

        return id, min_dis, min_loc

    def run_to_xy(self, aim_loc, start_xy=None):
        if start_xy is None:
            self.map_reset_base_loc()

        while True:

            self.up_keyboard_key()
            time.sleep(0.5)

            new_loc = self.map_recognize_loc()

            if dis := self.calculated_distance(start=new_loc, end=aim_loc) < 20:
                break

            aim_angle = self.aim_direction(start=new_loc, end=aim_loc)

            self.turn(aim_angle)

            self.run_straight()
            time.sleep(1)
            self.keyboard_key_down_and_up(self.key.Space.value)
            time.sleep(4 if dis > 50 else 2)
        self.up_keyboard_key()

    def turn(self, aim_angle):
        while True:
            self.up_keyboard_key()
            true_angle = self.move_angle()
            offset = aim_angle - true_angle

            print("\n目标方向为：", aim_angle, "°")
            print("当前方向为：", true_angle, "°")
            print("偏移角度为", offset, "°\n")

            if offset < -180:
                offset = 360 + offset
            elif offset > 180:
                offset = -360 + offset
            if offset > 10:
                if offset < 25:
                    self.lg_mouse_move_right(1)
                elif offset < 40:
                    self.lg_mouse_move_right(1)
                elif offset < 55:
                    self.lg_mouse_move_right(2)
                elif offset < 70:
                    self.lg_mouse_move_right(4)
                else:
                    self.lg_mouse_move_right(6)
            elif offset < -10:
                if offset > -25:
                    self.lg_mouse_move_left(1)
                elif offset > -40:
                    self.lg_mouse_move_left(1)
                elif offset > -55:
                    self.lg_mouse_move_left(2)
                elif offset > -70:
                    self.lg_mouse_move_left(4)
                else:
                    self.lg_mouse_move_left(6)
            else:
                break
            self.walk_straight()
            time.sleep(0.5)

    def calculated_distance(self, start=None, end=None):
        if not (start and end):
            start = self.old_loc
            end = self.map_reset_base_loc()
        return math.sqrt((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2)

    def move_angle(self):
        angle = self.detect_angle()
        return int(angle)

    def aim_direction(self, start=None, end=None):
        if start is None or end is None:
            start = self.map_reset_base_loc()
            end = [2663, 3117, 13]

        direction = [end[0] - start[0], start[1] - end[1]]

        andle = self.deviation_angle_calculation(direction)
        print("这里是计算偏移角度部分\n起始坐标", start)
        print("目标坐标", end)
        print("坐标差距", direction)
        print("目标角度", andle)
        print("\n")
        return int(andle)

    def map_recognize_loc(self, old_loc=None):
        if not old_loc:
            old_loc = self.old_loc
        pic_loc = self.transform_loc(type="ttm", loc=old_loc, offset=320)

        self.keyboard_key_down_and_up(key=self.key.M.value)
        time.sleep(1.5)

        aim = self.latest_frame_rect(rect=(410, 150, 480, 480))
        img = self.map[pic_loc[1]:pic_loc[1] + 640, pic_loc[0]:pic_loc[0] + 640]
        cv2.imwrite(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\log\aim.jpg", aim)
        cv2.imwrite(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\log\img.jpg", img)
        result = cv2.matchTemplate(img, aim, cv2.TM_CCORR_NORMED)
        (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)
        print("小地图坐标识别度", maxVal)
        if maxVal < 0.9:  # 如果匹配置信度低于0.9 合理怀疑压根没识别对地方，重新全图匹配一下
            # todo 这里可能需要抽一下逻辑，把进地图的和识别的拆一下，减少无用重复操作
            self.keyboard_key_down_and_up(key=self.key.M.value)
            time.sleep(1)
            transform_loc = self.map_reset_base_loc()
        else:
            loc = [maxLoc[0] + pic_loc[0], maxLoc[1] + pic_loc[1]]
            transform_loc = self.transform_loc(type="mtt", loc=loc, offset=240)
            self.keyboard_key_down_and_up(key=self.key.M.value)
        time.sleep(1)

        self.old_loc = [transform_loc[0], transform_loc[1], 0]
        print("\n这里是获取到的角色实际坐标位置", self.old_loc, "\n")
        return [transform_loc[0], transform_loc[1], 0]

    def map_reset_base_loc(self):
        self.keyboard_key_down_and_up(key=self.key.M.value)
        time.sleep(1)
        aim = self.latest_frame_rect(rect=(410, 150, 480, 480))

        result = cv2.matchTemplate(self.map, aim, cv2.TM_CCORR_NORMED)
        (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)

        # loc = reversed(maxLoc)
        transform_loc = self.transform_loc(type="mtt", loc=maxLoc, offset=240)

        self.keyboard_key_down_and_up(key=self.key.M.value)
        time.sleep(1)

        self.old_loc = [transform_loc[0], transform_loc[1], 0]
        print("\n这里是重设到的角色实际坐标位置", self.old_loc, "\n")
        return [transform_loc[0], transform_loc[1], 0]

    def transform_loc(self, type=None, loc=None, offset=0):
        if not (type and loc):
            print("此处缺少参数")
            return False
        if type == "ttm":
            transform_loc = [int((loc[0] + 2132) * 1.25 - offset),
                             int((loc[1] + 1637) * 1.25 - offset)]
        elif type == "mtt":
            transform_loc = [int((loc[0] + offset) * 0.8) - 2132,
                             int((loc[1] + offset) * 0.8) - 1637]
        else:
            return False
        return transform_loc

    def detect_angle(self):
        # 初始化SIFT检测器
        sift = cv2.SIFT_create()
        while True:
            image = self.latest_frame_rect(rect=(72, 95, 35, 40))

            # gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 检测关键点和描述符
            kp1, des1 = sift.detectAndCompute(self.angle_template, None)
            kp2, des2 = sift.detectAndCompute(image, None)

            # 使用FLANN匹配器
            index_params = dict(algorithm=1, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            matches = flann.knnMatch(des1, des2, k=2)

            # 过滤匹配点
            good_matches = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)

            # 计算旋转角度
            angle = 0
            try:
                if len(good_matches) > 0:
                    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    M, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts)
                    angle = -np.degrees(np.arctan2(M[0, 1], M[0, 0]))

                if angle is not np.nan:
                    self.direction = angle
                    return int(angle)
            except:
                pass
            self.lg_mouse_move_left(6)

    def deviation_angle_calculation(self, loc):
        # 计算角度（以弧度为单位）
        angle_rad = math.atan2(loc[1], loc[0])
        # 将弧度转换为角度
        angle_deg = math.degrees(angle_rad)
        # 计算相对于竖直向上的角度差值
        vertical_angle_difference = angle_deg
        # 确保角度在 -180 到 180 度之间
        vertical_angle_difference = -(vertical_angle_difference - 90)
        if vertical_angle_difference > 180:
            vertical_angle_difference = vertical_angle_difference - 360

        return vertical_angle_difference


if __name__ == "__main__":
    temp = move()
    # temp.run_to_xy(aim_loc=(-757, 1274, 50))
    temp.run_to_xy(aim_loc=(-757, 1274))

    # while True:
    #     time.sleep(0.5)
    # test = temp.calculated_distance(start=[-1005, 1430, 0], end=(-970, 1407, 7))
    # print(test)
    # temp.deviation_angle_calculation(loc=[100,-200])

# 14 -758
# 2685 1100
#
# 3045 3269
# 6472 6133
