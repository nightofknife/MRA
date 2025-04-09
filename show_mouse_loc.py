import ctypes.wintypes
import time

def get_mouse_position() -> tuple[int, int]:
    """获取当前鼠标全局坐标（虚拟屏幕坐标系）"""
    pt = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)


def start_tracking(interval: float = 0.5):
    """实时跟踪并打印鼠标坐标（按interval秒间隔）"""
    try:
        while True:
            x, y = get_mouse_position()
            print(f"当前坐标：全局({x},{y})")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("跟踪已停止。")

if __name__ == "__main__":

    # 开始实时跟踪（按Ctrl+C停止）
    start_tracking(interval=0.5)
