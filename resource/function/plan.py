import time
import logging
from typing import Dict, Any, Optional


class AutomationEngine:
    def __init__(self):
        from control import control
        self.ctrl = control()  # 实例化底层控制对象
        self.screen_width = self.ctrl.region[2]  # 默认分辨率，实际应动态获取
        self.screen_height = self.ctrl.region[3]
        self.logger = logging.getLogger('AutomationEngine')

    def execute_command(self, command: Dict[str, Any]) -> bool:
        """执行单条命令的入口方法"""
        try:
            # 预处理参数
            processed_params = self._preprocess_params(command.get('params', {}))

            # 执行条件检查
            if not self._check_conditions(command.get('conditions', [])):
                self.logger.warning("Condition check failed, aborting command")
                return False

            # 分发执行
            action_type = command['action']
            if action_type == 'click':
                return self._execute_click(processed_params)
            elif action_type == 'ocr_find_and_click':
                return self._execute_ocr_click(processed_params)
            elif action_type == 'key_press':
                return self._execute_key_press(processed_params)
            elif action_type == 'drag':
                return self._execute_drag(processed_params)
            # 添加其他动作类型...
            else:
                raise ValueError(f"Unknown action type: {action_type}")

        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            return False

    def _preprocess_params(self, params: Dict) -> Dict:
        """参数预处理"""
        processed = {}
        for key, value in params.items():
            if key.endswith('_rel'):  # 处理相对坐标
                abs_key = key.replace('_rel', '')
                processed[abs_key] = self._convert_relative_coord(value)
            else:
                processed[key] = value
        return processed

    def _convert_relative_coord(self, coord) -> tuple:
        """将相对坐标(0.0-1.0)转换为绝对坐标"""
        if isinstance(coord, (list, tuple)):
            return (
                int(coord[0] * self.screen_width),
                int(coord[1] * self.screen_height)
            )
        return coord

    def _check_conditions(self, conditions: list) -> bool:
        """检查前置条件"""
        for condition in conditions:
            cond_type = condition['type']
            if cond_type == 'template_match':
                if not self._check_template_match(condition):
                    return False
            elif cond_type == 'ocr_text':
                if not self._check_ocr_text(condition):
                    return False
            # 可扩展其他条件类型...
        return True

    def _check_template_match(self, condition: Dict) -> bool:
        """模板匹配条件检查"""
        template = condition['template']
        region = condition.get('region', [0, 0, self.screen_width, self.screen_height])
        threshold = condition.get('threshold', 0.8)

        screenshot = self.ctrl.capture(rect=region)
        match_result = self.ctrl.match_template(template, screenshot, threshold=threshold)
        return match_result is not False

    def _check_ocr_text(self, condition: Dict) -> bool:
        """OCR文本条件检查"""
        text = condition['text']
        region = condition.get('region', None)
        screenshot = self.ctrl.capture(rect=region) if region else None
        return self.ctrl.find_text_ocr(img=screenshot, text=text, rect=region) is not False

    def _execute_click(self, params: Dict) -> bool:
        """执行点击操作"""
        x = params.get('x', 0)
        y = params.get('y', 0)
        key = params.get('key', 1)
        self.ctrl.win32_click(x, y, key)
        return True

    def _execute_ocr_click(self, params: Dict) -> bool:
        """OCR查找并点击"""
        text = params['text']
        region = params.get('region', None)
        max_retry = params.get('max_retry', 3)

        for _ in range(max_retry):
            screenshot = self.ctrl.capture(rect=region)
            pos = self.ctrl.find_text_ocr(img=screenshot, text=text, rect=region)
            if pos:
                self.ctrl.win32_click(pos[0], pos[1])
                return True
            time.sleep(1)
        return False

    def _execute_key_press(self, params: Dict) -> bool:
        """执行按键操作"""
        key = params['key']
        duration = params.get('duration', 0.1)
        self.ctrl.keyboard.keyboard_key_down_and_up(key)
        time.sleep(duration)
        return True

    def _execute_drag(self, params: Dict) -> bool:
        """执行拖拽操作"""
        start = params['start']
        end = params['end']
        key = params.get('key', 1)
        self.ctrl.win32_dragfromto_mouse(
            start_x=start[0],
            start_y=start[1],
            end_x=end[0],
            end_y=end[1],
            key=key
        )
        return True

    def execute_task(self, task: Dict) -> bool:
        """执行完整任务"""
        for command in task['steps']:
            success = self.execute_command(command)
            if not success and not command.get('ignore_failure', False):
                self.logger.error(f"Task aborted due to command failure: {command}")
                return False
        return True