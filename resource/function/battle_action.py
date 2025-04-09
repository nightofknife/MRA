# 这里需要完善战斗系统
import time

import control


class battle(control.control):
    character_list = ["漂泊者", "今汐", "安可"]
    ban_list = [1, 1, 0]  #1用0否
    action_list = [[1, {'a': 3, 'q': 1, 'e': 1, 'r': 1}],
                   [2, {'a': 3, 'q': 1, 'e': 1, 'r': 1}],
                   [3, {'a': 3, 'q': 1, 'e': 1, 'r': 1}]]

    def __init__(self, character=None, ban=None):
        if character:
            self.character_list = character
        if ban:
            self.ban_list = ban

        control.control.__init__(self)

    def fight(self):
        for i in self.action_list:
            self.lg_mouse_up_and_down(key=3)
            if self.ban_list[i[0]-1] == 0:
                continue
            eval(rf"self.keyboard_key_down_and_up(key=self.key.Main_{i[0]}.value)")
            for _ in range(3):
                for j in range(i[1]['a']):
                    self.lg_mouse_up_and_down(key=1)
                    time.sleep(0.5)
                for j in range(i[1]['q']):
                    self.keyboard_key_down_and_up(key=self.key.Q.value)
                    time.sleep(0.2)
                for j in range(i[1]['e']):
                    self.keyboard_key_down_and_up(key=self.key.E.value)
                    time.sleep(0.5)
                for j in range(i[1]['r']):
                    self.keyboard_key_down_and_up(key=self.key.R.value)
                    time.sleep(0.5)
                self.lg_mouse_down(key=1)
                time.sleep(0.5)
                self.lg_mouse_up(key=1)
            self.lg_mouse_up_and_down(key=3)


if __name__ == "__main__":
    time.sleep(3)
    temp = battle()
    for _ in range(5):
        temp.fight()