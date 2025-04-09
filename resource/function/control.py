import re

import time
from ctypes import windll, c_long, c_ulong, Structure, Union, c_int, POINTER, sizeof, CDLL
from os import path
import win32api
import win32con
import win32gui
import cv2
import win32ui
from paddleocr import PaddleOCR
import logging
import numpy as np
import ctypes
from enum import Enum
import screeninfo
import ctypes
import threading

MapVirtualKey = ctypes.windll.user32.MapVirtualKeyA

logging.disable(logging.DEBUG)  # 关闭DEBUG日志的打印
logging.disable(logging.WARNING)

basedir = path.dirname(path.abspath(__file__))
dlldir = path.join(basedir, r'lg_dll\ghub_mouse.dll')
LONG = c_long
DWORD = c_ulong
ULONG_PTR = POINTER(DWORD)
gm = CDLL(dlldir)
gmok = gm.mouse_open()


class MOUSEINPUT(Structure):
    _fields_ = (('dx', LONG),
                ('dy', LONG),
                ('mouseData', DWORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))


class _INPUTunion(Union):
    _fields_ = (('mi', MOUSEINPUT), ('mi', MOUSEINPUT))


class INPUT(Structure):
    _fields_ = (('type', DWORD),
                ('union', _INPUTunion))


def SendInput(*inputs):
    nInputs = len(inputs)
    LPINPUT = INPUT * nInputs
    pInputs = LPINPUT(*inputs)
    cbSize = c_int(sizeof(INPUT))
    return windll.user32.SendInput(nInputs, pInputs, cbSize)


def Input(structure):
    return INPUT(0, _INPUTunion(mi=structure))


def MouseInput(flags, x, y, data):
    return MOUSEINPUT(x, y, data, flags, 0, None)


def Mouse(flags, x=0, y=0, data=0):
    return Input(MouseInput(flags, x, y, data))


def _convert_bitmap_to_np(bitmap):
    """将Win32位图转换为numpy数组"""
    bmpinfo = bitmap.GetInfo()
    bmpstr = bitmap.GetBitmapBits(True)
    return np.frombuffer(bmpstr, dtype=np.uint8).reshape(
        (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)
    )


class match():

    def __init__(self):
        self.template = None
        # 初始化特征检测器（使用ORB算法）
        self.detector = cv2.ORB_create(nfeatures=1000)
        # 初始化BF匹配器
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def _prepare_image(self, img):
        """通用图像预处理方法"""
        if isinstance(img, str):
            image = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
        elif isinstance(img, np.ndarray):
            image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            raise ValueError("不支持的图像类型")
        return image

    def feature_match_single(self, aim, img, min_matches=10, reproj_thresh=4.0):
        """
        基于特征点的单目标识别
        :param aim: 目标图像（路径或numpy数组）
        :param img: 待搜索图像（路径或numpy数组）
        :param min_matches: 最小匹配点数阈值
        :param reproj_thresh: RANSAC重投影阈值
        :return: 目标中心坐标 (x, y) 或 False
        """
        try:
            # 预处理图像
            img1 = self._prepare_image(aim)
            img2 = self._prepare_image(img)

            # 检测关键点和描述子
            kp1, des1 = self.detector.detectAndCompute(img1, None)
            kp2, des2 = self.detector.detectAndCompute(img2, None)

            if des1 is None or des2 is None:
                return False

            # 特征匹配
            matches = self.bf.match(des1, des2)
            if len(matches) < min_matches:
                return False

            # 提取匹配点坐标
            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

            # 使用RANSAC计算单应性矩阵
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, reproj_thresh)
            if H is None:
                return False

            # 获取目标角点
            h, w = img1.shape
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, H)

            # 计算中心点
            center = np.mean(dst, axis=0).ravel()
            return (int(center[0]), int(center[1]))

        except Exception as e:
            print(f"特征匹配出错: {str(e)}")
            return False

    def feature_match_multiple(self, aim, img, min_matches=10, reproj_thresh=4.0):
        """
        基于特征点的多目标识别
        :param aim: 目标图像（路径或numpy数组）
        :param img: 待搜索图像（路径或numpy数组）
        :param min_matches: 每个目标的最小匹配点数
        :param reproj_thresh: RANSAC重投影阈值
        :return: 多个目标中心坐标列表 或 False
        """
        try:
            img1 = self._prepare_image(aim)
            img2 = self._prepare_image(img)

            kp1, des1 = self.detector.detectAndCompute(img1, None)
            kp2, des2 = self.detector.detectAndCompute(img2, None)

            if des1 is None or des2 is None:
                return False

            # 使用knn匹配提高召回率
            matches = self.bf.knnMatch(des1, des2, k=2)

            # 应用比率测试（Lowe's ratio test）
            good = []
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    good.append(m)

            if len(good) < min_matches:
                return False

            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            # 使用DBSCAN聚类检测多个目标
            clustering = cv2.DBSCAN(eps=50, min_samples=min_matches).fit(dst_pts)
            labels = clustering.labels_

            centers = []
            for label in set(labels):
                if label == -1:
                    continue  # 忽略噪声点
                class_mask = (labels == label)
                cluster_pts = dst_pts[class_mask.flatten()]

                # 计算聚类中心
                center = np.mean(cluster_pts, axis=0).ravel()
                centers.append((int(center[0]), int(center[1])))

            return centers if centers else False

        except Exception as e:
            print(f"多目标匹配出错: {str(e)}")
            return False

    def match_template(self, aim: np.ndarray | str, img: np.ndarray | str, mask: np.ndarray = None, threshold=0.8):
        match_img = self._prepare_image(img)
        match_aim = self._prepare_image(aim)

        result = cv2.matchTemplate(image=match_img, templ=match_aim, method=cv2.TM_CCOEFF_NORMED, mask=mask)

        (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)
        if maxVal > threshold:
            # print(maxLoc, maxVal)
            return maxLoc
        else:
            # print('匹配度不够：',maxVal)
            return False

    def match_all_template(self, aim: np.ndarray | str, img: np.ndarray | str, mask: np.ndarray = None, threshold=0.8):
        match_img = self._prepare_image(img)
        match_aim = self._prepare_image(aim)

        # 执行模板匹配
        result = cv2.matchTemplate(image=match_img, templ=match_aim, method=cv2.TM_CCOEFF_NORMED, mask=mask)

        # 找到所有匹配度大于阈值的位置
        loc = np.where(result >= threshold)

        # 将匹配到的坐标转换为列表形式
        matches = list(zip(*loc[::-1]))  # 转换为(x, y)坐标

        if len(matches) > 0:
            return matches
        else:
            print('未找到匹配度大于阈值的坐标')
            return []


class ocr():
    """
    使用PaddleOCR库进行文字识别的类，提供查找特定文本、识别文本列表等功能。
    """

    def __init__(self):
        """
        初始化OCR实例，设置使用角度分类和中文语言。
        """
        # self.ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        self.ocr = PaddleOCR(use_angle_cls=True, lang="ch",
                             det_model_dir=r"C:\Users\356\Desktop\auto\MMA\MMA\resource\model\ch_PP-OCRv4_det_server_infer",
                             rec_model_dir=r"C:\Users\356\Desktop\auto\MMA\MMA\resource\model\ch_PP-OCRv4_rec_server_infer",
                             cls_model_dir=r"C:\Users\356\Desktop\auto\MMA\MMA\resource\model\ch_ppocr_mobile_v2.0_cls_slim_infer",
                             )

        self.__rect_size = [0, 0, 1297, 760]

    def _crop_image(self, img, rect):
        if rect:
            return img[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
        return img

    def find_text_ocr(self, img=None, text="", rect=None):
        """
        在指定图像区域内搜索特定的文本。

        :param img: 待识别的图像。
        :param text: 要搜索的文本。
        :param rect: 指定的搜索区域，格式为[x, y, width, height]。
        :return: 返回找到的文本坐标，如果未找到则返回False。
        """
        screen = self._crop_image(img, rect)
        if not rect:
            rect = self.__rect_size

        print("搜索文本：", text, "搜索范围", rect)

        result = self.ocr.ocr(screen, cls=True)
        if not result:
            return False
        for idx in range(len(result)):
            res = result[idx]
            print(res)
            if not res:
                continue
            if not result:
                return False
            for line in res:
                if line[1][0] == text:
                    loc = [(line[0][0][0] + line[0][1][0]) // 2, (line[0][1][1] + line[0][2][1]) // 2]
                    return [loc[0] + rect[0], loc[1] + rect[1]]
        return False

    def find_text_include_ocr(self, img=None, text="", rect=None):
        """
        在指定图像区域内搜索包含特定文本的字符串。

        :param img: 待识别的图像。
        :param text: 要搜索的文本。
        :param rect: 指定的搜索区域，格式为[x, y, width, height]。
        :return: 返回找到的包含文本的坐标，如果未找到则返回False。
        """
        screen = self._crop_image(img, rect)
        if not rect:
            rect = self.__rect_size

        print("搜索文本：", text, "搜索范围", rect)

        result = self.ocr.ocr(screen, cls=True)
        if not result:
            return False
        for idx in range(len(result)):
            res = result[idx]
            if not res:
                continue
            if not result:
                return False
            for line in res:
                if text in line[1][0]:
                    loc = [(line[0][0][0] + line[0][1][0]) // 2, (line[0][1][1] + line[0][2][1]) // 2]
                    return [int(loc[0] + rect[0]), int(loc[1] + rect[1])]
        return False

    def find_text_exist_ocr(self, img=None, textlist=None, rect=None):
        """
        在指定图像区域内搜索是否存在文本列表中的任意文本。

        :param img: 待识别的图像。
        :param textlist: 要搜索的文本列表。
        :param rect: 指定的搜索区域，格式为[x, y, width, height]。
        :return: 返回找到的文本及其坐标，如果未找到则返回False。
        """

        if not textlist:
            print("空参数")
            return False
        print("搜索文本")
        screen = self._crop_image(img, rect)
        if not rect:
            rect = self.__rect_size

        print("搜索文本列表：", textlist, "搜索范围", rect)

        result = self.ocr.ocr(screen, cls=True)
        for idx in range(len(result)):
            res = result[idx]
            # if not rect:
            #     continue
            for line in res:
                if line[1][0] in textlist:
                    loc = [(line[0][0][0] + line[0][1][0]) // 2, (line[0][1][1] + line[0][2][1]) // 2]
                    return line[1][0], [int(loc[0] + rect[0]), int(loc[1] + rect[1])]
        return False

    def find_textlist_ocr(self, img=None, textlist=None, rect=None):
        """
        在指定图像区域内搜索文本列表中的所有文本。

        :param img: 待识别的图像。
        :param textlist: 要搜索的文本列表。
        :param rect: 指定的搜索区域，格式为[x, y, width, height]。
        :return: 返回找到的所有文本及其坐标的列表，如果未找到则返回False。
        """
        if not textlist:
            print("空参数")
            return False
        print("搜索文本")
        screen = self._crop_image(img, rect)
        if not rect:
            rect = self.__rect_size

        print("搜索文本列表：", textlist, "搜索范围", rect)

        result = self.ocr.ocr(screen, cls=True)
        resultloc = []
        for idx in range(len(result)):
            res = result[idx]
            if not rect:
                continue
            for line in res:
                if line[1][0] in textlist:
                    loc = [(line[0][0][0] + line[0][1][0]) // 2, (line[0][1][1] + line[0][2][1]) // 2]
                    resultloc.append([line[1][0], [loc[0] + rect[0], loc[1] + rect[1]]])
        return resultloc if resultloc != [] else False

    # todo 这个函数还未测试过
    def find_retext_ocr(self, img=None, text="", rect=None):
        """
        在指定图像区域内搜索符合正则表达式的文本，并返回匹配的文本坐标列表。

        :param img: 待识别的图像。
        :param text: 正则表达式字符串，用于匹配图像中的文本。
        :param rect: 指定的搜索区域，格式为[x, y, width, height]。
        :return: 返回匹配到的文本坐标列表。
        """
        screen = self._crop_image(img, rect)
        if not rect:
            rect = self.__rect_size

        # cv2.imshow("image", img)
        # cv2.waitKey(0)

        result = self.ocr.ocr(screen, cls=False)
        print(result)
        matched_texts = []

        for line in result[0]:
            if line:
                text_content = line[1][0]
                try:
                    # 尝试编译正则表达式
                    regex = re.compile(text)
                    # 使用正则表达式匹配文本
                    print(text_content)
                    matches = True if regex.search(text_content) else False
                except re.error:
                    # 如果编译失败，说明pattern不是一个正则表达式
                    # 直接检查pattern是否为text的子串
                    matches = True if text in text_content else False

                if matches:
                    start_x, start_y = line[0][0]
                    end_x, end_y = line[0][2]
                    matched_texts.append([
                        (start_x + end_x) // 2 + rect[0],  # 计算文本中心的x坐标
                        (start_y + end_y) // 2 + rect[1]  # 计算匹配文本的y坐标
                    ])
        print(matched_texts)
        return matched_texts

    def recognition_text_ocr(self, img=None, rect=None):
        """
        识别指定图像区域内的文本，并返回置信度最高的文本。

        :param img: 待识别的图像。
        :param rect: 指定的识别区域，格式为[x, y, width, height]。
        :return: 返回置信度最高的文本。
        """
        screen = self._crop_image(img, rect)
        if not rect:
            rect = self.__rect_size

        result_list = self.ocr.ocr(screen, cls=True, det=True, rec=True)
        max = 0
        result = ""
        if result_list[0] is None:
            return False
        for idx in result_list:
            for i in idx:
                if i[1][1] > max:
                    result = i[1][0]
                    max = i[1][1]
        return result

    def recognition_textlist_ocr(self, img=None, rect: list = None):
        """
        识别指定图像区域内的所有文本，并返回一个列表。

        :param img: 待识别的图像。
        :param rect: 指定的识别区域列表，每个区域格式为[x, y, width, height]。
        :return: 返回识别到的文本列表。
        """

        if rect is None:
            print("空参数运行")
            return False
        result = []
        print("识别文本范围列表", rect)
        for i in rect:
            newscreen = img[i[1]:i[1] + i[3], i[0]:i[0] + i[2]]
            # cv2.imshow("rect", newscreen)
            # cv2.waitKey(0)

            resultlist = self.ocr.ocr(newscreen, cls=True, rec=True, det=False)
            max = 0
            print(resultlist)
            for idx in resultlist:
                for j in idx:
                    if j[1] > max:
                        max = j[1]
                        result.append(j[0])
        print("识别到：", result)
        return result


class screenshot:
    def __init__(self, window_name="LocalSend"):
        self.screens = list(screeninfo.get_monitors())
        self.current_screen_idx = 0
        self.hwnd = None
        self.region = (0, 0, 1920, 1080)
        self.window_name = window_name
        self._update_window_rect()
    def _update_window_rect(self):
        """更新窗口位置并适配显示器"""
        try:
            self.hwnd = win32gui.FindWindow(None, self.window_name)
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            self.region = (left, top, right - left, bottom - top)
        except:
            self.region = (0, 0, 1920, 1080)

        # 确定窗口所在的显示器
        for i, screen in enumerate(self.screens):
            if (left >= screen.x and left < screen.x + screen.width) and \
                    (top >= screen.y and top < screen.y + screen.height):
                self.current_screen_idx = i
                break
        else:
            self.current_screen_idx = 0

        # 调整region为相对于显示器坐标的坐标
        screen = self.screens[self.current_screen_idx]
        self.region_relative = (
            self.region[0] - screen.x,
            self.region[1] - screen.y,
            self.region[2],
            self.region[3]
        )
        return self.region_relative

    def _grab_with_bitblt(self, rect=None):
        """使用BitBlt截图（后台窗口）"""
        rect_global = self.region  # 使用全局坐标
        left, top, width, height = rect_global
        x1 = left
        y1 = top
        x2 = x1 + rect_global[2]
        y2 = y1 + rect_global[3]

        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, rect[2]-15, rect[3]-35)
        save_dc.SelectObject(bitmap)

        windll.user32.PrintWindow(self.hwnd, save_dc.GetSafeHdc(), 3)
        img = _convert_bitmap_to_np(bitmap)

        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwnd_dc)
        return img

    def capture(self, rect=None):
        self._update_window_rect()
        rect_global = rect or self.region
        img = self._grab_with_bitblt(rect_global)
        return img


class mouse():

    def __init__(self):
        self.mouse_key_down_list = []
        self.mouse_loc = [0, 0]

    def win32_get_mouse_loc(self):
        """
        获取当前鼠标的位置。

        :return: 返回一个包含鼠标x, y坐标的元组。
        """
        self.mouse_loc = win32api.GetCursorPos()
        return self.mouse_loc

    def win32_mouse_moveto_xy(self, x=0, y=0):
        """
        将鼠标移动到屏幕上的指定位置。

        :param x: 目标x坐标。
        :param y: 目标y坐标。
        """
        win32api.SetCursorPos((x, y))
        SendInput(
            Mouse(win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_VIRTUALDESK | win32con.MOUSEEVENTF_ABSOLUTE))

    def win32_mouse_move_xy(self, x=0, y=0):
        """
        相对当前位置移动鼠标。

        :param x: 相对x坐标偏移量，正为右移。
        :param y: 相对y坐标偏移量，正为下移。
        """
        old_x, old_y = self.win32_get_mouse_loc()
        win32api.SetCursorPos((old_x - x, old_y - y))

    def win32_mouse_roll(self, x=None, y=None, offset=0, speed=0.5):
        """
        滚动鼠标滚轮
        注意滚轮滚动的第一次不会动，应该是滚轮的防误触功能

        :param y:
        :param speed:
        :param offset: 滚轮滚动量，正为向上滚动，负为向下滚动。
        """
        if x and y:
            win32api.SetCursorPos((x, y))
        for _ in range(abs(offset)):
            direction = 120 if offset > 0 else -120
            SendInput(Mouse(win32con.MOUSEEVENTF_WHEEL, 0, 0, direction))
            time.sleep(speed)

    def win32_mouse_key_down(self, key=1):
        """
        模拟鼠标按键按下。

        :param key: 鼠标按键类型，1为左键，2为右键，3为中键。
        """

        if key == 1:
            SendInput(Mouse(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0))
        elif key == 2:
            SendInput(Mouse(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0))
        self.mouse_key_down_list.append(key)

    def win32_mouse_key_up(self, key=1):
        """
        模拟鼠标按键释放。

        :param key: 鼠标按键类型，1为左键，2为右键，3为中键。
        """
        if key == 1:
            SendInput(Mouse(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0))
        elif key == 2:
            SendInput(Mouse(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0))
        self.mouse_key_down_list.remove(key)

    def win32_mouse_key_up_and_down(self, key=1):
        """
        模拟鼠标按键的按下和释放（点击）。

        :param key: 鼠标按键类型，1为左键，2为右键。
        """
        if key == 1:
            SendInput(Mouse(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0))
            # time.sleep(0.01)
            SendInput(Mouse(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0))
        elif key == 2:
            SendInput(Mouse(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0))
            # time.sleep(0.01)
            SendInput(Mouse(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0))

    def win32_up_mouse_key(self):
        """
        释放所有按下的鼠标按键。
        """
        for i in self.mouse_key_down_list:
            if i == 1:
                SendInput(Mouse(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0))
            elif i == 2:
                SendInput(Mouse(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0))
        self.mouse_key_down_list = []

    def win32_click(self, x, y, key=1):
        """
        在指定屏幕上的坐标进行鼠标点击。

        :param x: 点击的x坐标。
        :param y: 点击的y坐标。
        :param key: 鼠标按键类型，1为左键。
        """
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        # 判断x和y是否为浮点数
        if isinstance(x, float) or isinstance(y, float):
            # 计算按比例缩放的坐标
            actual_x = int(x * screen_width)
            actual_y = int(y * screen_height)
        else:
            # x和y为整数，直接使用
            actual_x = x
            actual_y = y
        self.win32_mouse_moveto_xy(actual_x, actual_y)
        self.win32_mouse_key_up_and_down(key=key)

    def win32_dragto_mouse(self, x, y, key=None):
        """
        将鼠标拖拽到屏幕上的指定位置。

        :param x: 目标x坐标。
        :param y: 目标y坐标。
        :param key: 鼠标按键，如果为None则不进行点击操作。
        """
        if key is not None:
            self.win32_mouse_key_down(key=key)
        while True:
            mouse_loc = self.win32_get_mouse_loc()
            offset_x = x - mouse_loc[0]
            offset_y = y - mouse_loc[1]
            if abs(offset_x) + abs(offset_y) < 5:
                break
            self.win32_mouse_move_xy(x=-1 if offset_x > 0 else 1, y=-1 if offset_y > 0 else 1)
            time.sleep(0.001)
        if key is not None:
            self.win32_mouse_key_up(key=key)

    def win32_drag_mouse(self, x, y, key=None):
        """
        相对当前位置拖拽鼠标。

        :param x: 相对x坐标偏移量。
        :param y: 相对y坐标偏移量。
        :param key: 鼠标按键，如果为None则不进行点击操作。
        """
        if key is not None:
            self.win32_mouse_key_down(key=key)
        aim_x = self.win32_get_mouse_loc()[0] + x
        aim_y = self.win32_get_mouse_loc()[1] + y
        while True:
            mouse_loc = self.win32_get_mouse_loc()
            offset_x = aim_x - mouse_loc[0]
            offset_y = aim_y - mouse_loc[1]
            if abs(offset_x) + abs(offset_y) < 5:
                break
            self.win32_mouse_move_xy(x=-1 if offset_x > 0 else 1, y=-1 if offset_y > 0 else 1)
            time.sleep(0.001)
        if key is not None:
            self.win32_mouse_key_up(key=key)

    def win32_dragfromto_mouse(self, start_x=None, start_y=None, end_x=None, end_y=None, relative=False, key=None):
        """
        从起始坐标拖拽鼠标到目标坐标。

        :param start_x: 起始x坐标，如果为None则使用当前鼠标位置。
        :param start_y: 起始y坐标，如果为None则使用当前鼠标位置。
        :param end_x: 目标x坐标。
        :param end_y: 目标y坐标。
        :param relative: 是否使用相对坐标。
        :param key: 鼠标按键，如果为None则不进行点击操作。
        """

        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        mouse_loc = self.win32_get_mouse_loc()

        # 如果提供了起始坐标，并且需要按比例缩放坐标
        if end_x is not None and end_y is not None:
            if isinstance(end_x, float):
                end_x = int(end_x * screen_width)
            if isinstance(end_y, float):
                end_y = int(end_y * screen_height)

        if start_x is not None and start_y is not None:
            if isinstance(end_x, float):
                start_x = int(start_x * screen_width)
            if isinstance(start_y, float):
                start_y = int(start_y * screen_height)

        if relative:
            # 如果是相对移动，计算相对坐标
            end_x += mouse_loc[0]
            end_y += mouse_loc[1]
        else:
            self.win32_mouse_moveto_xy(x=start_x, y=start_y)

        if key is not None:
            self.win32_mouse_key_down(key=key)

        # 移动到目标坐标
        while True:
            mouse_loc = self.win32_get_mouse_loc()
            offset_x = end_x - mouse_loc[0]
            offset_y = end_y - mouse_loc[1]
            if abs(offset_x) + abs(offset_y) < 5:
                break
            self.win32_mouse_move_xy(x=-1 if offset_x > 0 else 1, y=-1 if offset_y > 0 else 1)
            time.sleep(0.001)

        if key is not None:
            self.win32_mouse_key_up(key=key)

    def lg_mouse_move_xy(self, x, y):  # for import
        """
        使用Logitech Gaming Software API移动鼠标。

        :param x: 相对x坐标偏移量。
        :param y: 相对y坐标偏移量。
        """
        if gmok:
            return gm.moveR(self, x, y)
        return SendInput(Mouse(0x0001, x, y))

    def lg_mouse_down(self, key=1):
        """
        使用Logitech Gaming Software API按下鼠标按键。

        :param key: 鼠标按键类型。
        """
        if gmok:
            return gm.press(key)
        if key == 1:
            return SendInput(Mouse(0x0002))
        elif key == 2:
            return SendInput(Mouse(0x0008))
        elif key == 3:
            return SendInput(Mouse(0x0020))

    def lg_mouse_up(self, key=1):
        """
        使用Logitech Gaming Software API释放鼠标按键。

        :param key: 鼠标按键类型。
        """

        if gmok:
            return gm.release()
        if key == 1:
            return SendInput(Mouse(0x0004))
        elif key == 2:
            return SendInput(Mouse(0x0010))
        elif key == 3:
            return SendInput(Mouse(0x0040))

    def lg_mouse_close(self):  # for import
        """
        关闭Logitech Gaming Software API。
        """
        if gmok:
            return gm.mouse_close()

    def lg_mouse_up_and_down(self, key=1):
        """
        使用Logitech Gaming Software API进行鼠标点击。

        :param key: 鼠标按键类型。
        """

        self.lg_mouse_down(key=key)
        time.sleep(0.01)
        self.lg_mouse_up(key=key)

    def lg_mouse_move_left(self, num=1):
        """
        使用Logitech Gaming Software API向左移动鼠标。

        :param num: 移动的步数。
        """
        for _ in range(num):
            self.lg_mouse_move_xy(-100, 0)
            time.sleep(0.02)

    def lg_mouse_move_right(self, num=1):
        """
        使用Logitech Gaming Software API向右移动鼠标。

        :param num: 移动的步数。
        """
        for _ in range(num):
            self.lg_mouse_move_xy(100, 0)
            time.sleep(0.02)

    def lg_mouse_move_up(self, num=1):
        """
        使用Logitech Gaming Software API向上移动鼠标。

        :param num: 移动的步数。
        """

        for _ in range(num):
            self.lg_mouse_move_xy(0, -100)
            time.sleep(0.02)

    def lg_mouse_move_down(self, num=1):
        """
        使用Logitech Gaming Software API向下移动鼠标。

        :param num: 移动的步数。
        """

        for _ in range(num):
            self.lg_mouse_move_xy(0, 100)
            time.sleep(0.02)


class keyboard():
    MapVirtualKey = ctypes.windll.user32.MapVirtualKeyA

    keyboard_key_down_list = []

    class key(Enum):
        A = 0x41
        B = 0x42
        C = 0x43
        D = 0x44
        E = 0x45
        F = 0x46
        G = 0x47
        H = 0x48
        I = 0x49
        J = 0x4A
        K = 0x4B
        L = 0x4C
        M = 0x4D
        N = 0x4E
        O = 0x4F
        P = 0x50
        Q = 0x51
        R = 0x52
        S = 0x53
        T = 0x54
        U = 0x55
        V = 0x56
        W = 0x57
        X = 0x58
        Y = 0x59
        Z = 0X5A

        Shift = 0x10
        Space = 0x20
        LeftCtrl = 0x11
        Esc = 0x1B
        Alt = 0x12
        Enter = 0x13

        Main_0 = 0x30
        Main_1 = 0x31
        Main_2 = 0x32
        Main_3 = 0x33
        Main_4 = 0x34
        Main_5 = 0x35
        Main_6 = 0x36
        Main_7 = 0x37
        Main_8 = 0x38
        Main_9 = 0x39

        f1 = 0x70
        f2 = 0x71
        f3 = 0x72
        f4 = 0x73
        f5 = 0x74

    def keyboard_key_down(self, key=None):
        if not key:
            return None
        win32api.keybd_event(key, MapVirtualKey(key, 0), 0, 0)
        self.keyboard_key_down_list.append(key)

    def keyboard_key_up(self, key=None):
        if not key:
            return None
        win32api.keybd_event(key, MapVirtualKey(key, 0), win32con.KEYEVENTF_KEYUP, 0)
        self.keyboard_key_down_list.remove(key)

    def keyboard_key_down_and_up(self, key=None):  # 0x41是a
        if not key:
            return None
        # win32api.keybd_event(虚拟码，扫描码(游戏必填)，按下与抬起的标识，0）
        win32api.keybd_event(key, MapVirtualKey(key, 0), 0, 0)
        time.sleep(0.02)
        win32api.keybd_event(key, MapVirtualKey(key, 0), win32con.KEYEVENTF_KEYUP, 0)

    def up_keyboard_key(self):
        while len(self.keyboard_key_down_list) > 0:
            self.keyboard_key_up(key=self.keyboard_key_down_list[0])
        self.keyboard_key_down_list = []


class control(match, ocr, screenshot, mouse, keyboard):
    def __init__(self, window_name="LocalSend"):
        match.__init__(self)
        ocr.__init__(self)
        screenshot.__init__(self, window_name=window_name)
        mouse.__init__(self)
        keyboard.__init__(self)

    # 新基本函数

    def win32_windows_set_top(self, hwnd=None):
        """
        将指定句柄窗口置顶
        :param hwnd: 窗口句柄
        """
        if hwnd is None:
            hwnd = self.hwnd

        # 检查窗口是否处于最小化状态
        window_placement = win32gui.GetWindowPlacement(hwnd)
        if window_placement[1] == win32con.SW_SHOWMINIMIZED:
            # 恢复窗口到正常状态
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)


        # 设置窗口为最顶层
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        # 取消固定置顶，恢复正常的Z序管理
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

        return True



    def win32_mouse_get_loc_rect(self):
        self.mouse_loc = win32api.GetCursorPos()
        self._update_window_rect()
        return [self.mouse_loc[0] - self.window_rect[0], self.mouse_loc[1] - self.window_rect[1]]

    # 重写函数部分
    def win32_mouse_moveto_xy(self, x=0, y=0):
        rect = self._update_window_rect()
        win32api.SetCursorPos((rect[0] + x, rect[1] + y))

    def win32_mouse_roll(self, x=None, y=None, offset=0, speed=0.5):
        """
                滚动鼠标滚轮
                注意滚轮滚动的第一次不会动，应该是滚轮的防误触功能

                :param offset: 滚轮滚动量，正为向上滚动，负为向下滚动。
                """
        if x and y:
            rect = self._update_window_rect()
            win32api.SetCursorPos((rect[0] + x, rect[1] + y))
        for i in range(abs(offset)):
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, 120 if offset > 0 else -120)

            time.sleep(speed)

    def win32_dragfromto_mouse(self, start_x=None, start_y=None, end_x=None, end_y=None, relative=False, key=None,
                               delay=0):
        """

        :param start_x:
        :param start_y:
        :param end_x:
        :param end_y:
        :param relative:
        :param key:
        :param delay:
        :return:
        """
        temp_windows_rect = self._update_window_rect()

        screen_width = temp_windows_rect[2]
        screen_height = temp_windows_rect[3]

        mouse_loc = self.win32_mouse_get_loc_rect()

        # 如果提供了起始坐标，并且需要按比例缩放坐标
        if start_x is not None and start_y is not None:
            if isinstance(end_x, float):
                end_x = int(end_x * screen_width) + temp_windows_rect[0]
            if isinstance(end_y, float):
                end_y = int(end_y * screen_height) + temp_windows_rect[1]

        if start_x is not None and start_y is not None:
            if isinstance(start_x, float):
                start_x = int(start_x * screen_width) + temp_windows_rect[0]
            if isinstance(start_y, float):
                start_y = int(start_y * screen_height) + temp_windows_rect[1]

        if relative:
            # 如果是相对移动，计算相对坐标
            end_x += mouse_loc[0]
            end_y += mouse_loc[1]
        else:
            self.win32_mouse_moveto_xy(x=start_x, y=start_y)
            time.sleep(2)

        if key is not None:
            self.win32_mouse_key_down(key=key)
        # print(start_x,start_y,end_x,end_y)
        # 移动到目标坐标
        while True:
            mouse_loc = self.win32_mouse_get_loc_rect()
            offset_x = end_x - mouse_loc[0]
            offset_y = end_y - mouse_loc[1]
            # print(offset_x,offset_y)
            if abs(offset_x) + abs(offset_y) < 5:
                break
            self.win32_mouse_move_xy(x=-1 if offset_x > 0 else 1, y=-1 if offset_y > 0 else 1)
            time.sleep(0.001)

        time.sleep(delay)

        if key is not None:
            self.win32_mouse_key_up(key=key)

    def win32_click(self, x, y, key=1):

        temp_windows_rect = self._update_window_rect()

        screen_width = temp_windows_rect[2]
        screen_height = temp_windows_rect[3]

        # 判断x和y是否为浮点数
        if isinstance(x, float) or isinstance(y, float):
            # 计算按比例缩放的坐标
            actual_x = int(x * screen_width)
            actual_y = int(y * screen_height)
        else:
            # x和y为整数，直接使用
            actual_x = x
            actual_y = y
        self.win32_mouse_moveto_xy(actual_x, actual_y)
        self.win32_mouse_key_up_and_down(key=key)

    def win32_dragto_mouse(self, x, y, key=None):
        if key is not None:
            self.win32_mouse_key_down(key=key)
        while True:
            mouse_loc = self.win32_get_mouse_loc()
            offset_x = x - mouse_loc[0]
            offset_y = y - mouse_loc[1]
            if abs(offset_x) + abs(offset_y) < 4:
                break
            self.win32_mouse_move_xy(x=-1 if offset_x > 0 else 1, y=-1 if offset_y > 0 else 1)
            time.sleep(0.001)
        if key is not None:
            self.win32_mouse_key_up(key=key)


def main():
    window_name = "雷索纳斯"  # 替换为你的实际窗口名称
    scr = screenshot(window_name)

    try:
        while True:
            # 实时获取窗口位置并截图
            frame = scr.capture()  # 全屏截图

            # 显示实时画面
            cv2.imshow("Real-time Screenshot", frame)

            # 检测退出指令（按'q'退出）
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.01)  # 防止CPU占用过高

    finally:
        # 释放资源
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
