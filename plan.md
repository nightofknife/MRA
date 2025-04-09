class TaskNode:
    TYPE_ACTION = "action"    # 执行命令
    TYPE_CONDITION = "condition"  # 条件分支
    TYPE_LOOP = "loop"       # 循环执行
    TYPE_PARALLEL = "parallel" # 并行执行
    TYPE_SET_VAR = "set_var" # 设置变量


# 任务结构示例
task_id: combat_001
variables:
  min_hp: 30
  target_enemy: "boss"
steps:
  - type: "action"
    name: "check_status"
    command: "get_player_status"
    output: ["current_hp", "current_mp"]
  
  - type: "condition"
    condition: "current_hp < min_hp"
    true_branch:
      - type: "action"
        name: "use_potion"
        command: "use_item"
        args: {"item_id": "hppotion"}
    false_branch:
      - type: "action"
        name: "attack"
        command: "skill_attack"
        args: {"skill_id": "fireball"}
  
  - type: "parallel"
    branches:
      - steps:
          - type: "loop"
            condition: "target_enemy.exists"
            steps:
              - type: "action"
                command: "basic_attack"
      - steps:
          - type: "action"
            command: "monitor_escape"