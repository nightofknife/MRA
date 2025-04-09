import json
import requests
import math
import random


class web_action():
    url = f'https://web-static.kurobbs.com/mcmap/position/position.json?%20t=1723019685974'

    header = {'user-agent': 'Mozilla/5.0 (Windows NT 10 .0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/112.0.0.0 Safari/537.36',
              'cookie': 'Hm_lvt_2daceab856bc69f2063edab16d1c2ca1=1716710102,1719301484'}

    object_loc = None

    def __init__(self):
        self.object_loc = self.web_update_object_loc()

    def web_update_object_loc(self):
        response = requests.get(self.url, headers=self.header).json()

        new_json = []
        for i in response:
            temp_loc = []
            for j in i["location"]:
                temp_loc.append({'id': j["id"], 'x': int(j["x"] / 100), 'y': int(j["y"] / 100)})
            new_json.append({'name': i["name"], 'location': temp_loc})
        with open(r"C:\Users\356\Desktop\auto\MMA\MMA\resource\data\object_loc.json", 'w', encoding='utf-8') as f:
            json.dump(new_json, f, ensure_ascii=False)
            self.object_loc = new_json
        return new_json

    def web_get_object_loc(self, object_name: str = None) -> list:
        if not object_name:
            return []
        for i in self.object_loc:
            if i["name"] == object_name:
                location = []
                for j in i["location"]:
                    location.append((j["id"], j["x"], j["y"]))

                return location

    def web_planning_path(self, object_name=None, start_loc=(0, 0)):
        if start_loc:
            start_point_id = ("0", start_loc[0], start_loc[1])
        else:
            start_point_id = ("0", 0, 0)
        if object_name:
            points = self.web_get_object_loc(object_name=object_name)
        else:
            points = self.web_get_object_loc(object_name="先行公约")
        points.append(start_point_id)
        path = greedy_tsp(points, start_point_id[0])
        return path


def greedy_tsp(points, start_point_id):
    start_point = next(point for point in points if point[0] == start_point_id)
    unvisited = [point for point in points if point[0] != start_point_id]

    path = [start_point]
    current_point = start_point

    while unvisited:
        next_point = min(unvisited, key=lambda point: calculate_distance(current_point, point))
        path.append(next_point)
        unvisited.remove(next_point)
        current_point = next_point

    path.append(start_point)  # 回到起点
    return path


def calculate_distance(point1, point2):
    return math.sqrt((point1[1] - point2[1]) ** 2 + (point1[2] - point2[2]) ** 2)


# 贪心算法


if __name__ == "__main__":
    temp = web_action()
    loc_list = temp.web_get_object_loc("游弋蝶")
    loc_list.append(('0', 0, 0))

    best_path = temp.web_planning_path(points=loc_list, start_point_id="0")
    print("Best Path:", [point for point in best_path])
