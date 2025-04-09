import math
from PIL import Image, ImageDraw
import heapq
from collections import deque


def a_star_pathfinding(image_path, start, end, dis=5, dir=False):
    def heuristic(a, b):
        # 曼哈顿距离作为启发函数
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # 读取并处理地图
    img = Image.open(image_path).convert('L')
    width, height = img.size
    pixels = img.load()

    # 预计算每个点到最近障碍物的距离
    distance = [[float('inf') for _ in range(height)] for _ in range(width)]
    queue = []
    for x in range(width):
        for y in range(height):
            if pixels[x, y] <= 128:  # 障碍物
                distance[x][y] = 0
                queue.append((x, y))
    # BFS遍历
    directions_bfs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if dir:
        directions_bfs += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    visited = [[False] * height for _ in range(width)]
    q = deque(queue)
    for x, y in queue:
        visited[x][y] = True
    while q:
        x, y = q.popleft()
        for dx, dy in directions_bfs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not visited[nx][ny]:
                if distance[nx][ny] > distance[x][y] + 1:
                    distance[nx][ny] = distance[x][y] + 1
                    q.append((nx, ny))
                    visited[nx][ny] = True

    # 坐标有效性检查
    if not (0 <= start[0] < width and 0 <= start[1] < height) or not (0 <= end[0] < width and 0 <= end[1] < height):
        raise ValueError("坐标超出地图范围")
    if pixels[start[0], start[1]] < 128 or pixels[end[0], end[1]] < 128:
        raise ValueError("起点或终点位于障碍物上")
    if distance[start[0]][start[1]] < dis or distance[end[0]][end[1]] < dis:
        raise ValueError(f"起点或终点距离障碍物不足{dis}单位")

    # 初始化A*算法结构
    open_list = []
    heapq.heappush(open_list, (0, start))
    came_from = {start: None}
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}

    while open_list:
        current = heapq.heappop(open_list)[1]
        if current == end:
            break
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if dir:
            directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < width and 0 <= neighbor[1] < height:
                # 新增距离约束检查
                if (pixels[neighbor[0], neighbor[1]] > 128 and
                        distance[neighbor[0]][neighbor[1]] >= dis):
                    new_g = g_score[current] + 1
                    if (neighbor not in g_score or new_g < g_score[neighbor]):
                        g_score[neighbor] = new_g
                        f_score[neighbor] = new_g + heuristic(neighbor, end)
                        heapq.heappush(open_list, (f_score[neighbor], neighbor))
                        came_from[neighbor] = current

    # 路径回溯
    path = []
    current = end
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()

    # 绘制路径
    img_color = Image.open(image_path)
    draw = ImageDraw.Draw(img_color)
    for i in range(len(path) - 1):
        draw.line([path[i], path[i + 1]], fill="red", width=2)

    output_path = image_path.replace('.jpg', '_path.jpg')
    img_color.save(output_path)
    return path, output_path


if __name__ == "__main__":
    # 示例用法
    path, output = a_star_pathfinding(
        image_path=r"C:\Users\356\Desktop\auto\MMA\MMA\train.jpg",
        start=(400, 100),
        end=(100, 880),
        dis=5,
        dir=True
    )
    print(path)
    print(f"路径已保存至：{output}")
