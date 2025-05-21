from .game_state import core_resources, FOOD_CONSUMPTION_PER_CAPITA, building_modifiers # For the hacky check, will improve

# Note: TechTree, BuildingManager, EventManager objects are passed as arguments, so no direct import of those classes needed here.

def make_autonomous_decision(tech_tree_obj, building_manager_obj, event_manager_obj):
    """
    Makes a single autonomous decision for the civilization based on simple priorities.
    Returns True if an action was taken, False otherwise.
    Directly uses 'core_resources' imported from game_state.
    """
    action_taken = False
    reason = "No specific crisis or opportunity identified."

    # 1. Food Security
    estimated_food_consumption_per_cycle = core_resources["Population"] * FOOD_CONSUMPTION_PER_CAPITA
    if estimated_food_consumption_per_cycle <= 0: estimated_food_consumption_per_cycle = 1 

    food_cycles_remaining = core_resources["Food"] / estimated_food_consumption_per_cycle if estimated_food_consumption_per_cycle > 0 else float('inf')
    
    if food_cycles_remaining < 5 or core_resources["Food"] < 20 : 
        reason = "Low food reserves."
        available_techs = tech_tree_obj.get_available_research()
        # Filter for techs that mention "Food" or "food" in description and are affordable
        food_techs = {
            tid: tdata for tid, tdata in available_techs.items() 
            if ("Food" in tdata["description"] or "food" in tdata["description"]) and core_resources["Knowledge"] >= tdata["cost"]
        }
        if food_techs:
            cheapest_food_tech_id = min(food_techs, key=lambda tid: food_techs[tid]["cost"])
            msg = tech_tree_obj.research_tech(cheapest_food_tech_id) # research_tech uses global core_resources
            event_manager_obj.log_event(f"Autonomous Focus: {reason} Researching '{tech_tree_obj.technologies[cheapest_food_tech_id]['name']}'. Outcome: {msg}")
            action_taken = "Error:" not in msg
            if action_taken: return True # Action taken

        available_buildings = building_manager_obj.get_constructible_buildings()
        food_buildings = {
            bid: bdata for bid, bdata in available_buildings.items() 
            if ("Food" in bdata["description"] or "food" in bdata["effect_description"].lower()) and 
               (core_resources["Production"] >= bdata["production_cost_per_cycle"] or bdata["build_time_cycles"] == 0)
        }
        if food_buildings:
            best_food_building_id = None
            # Heuristic: prioritize flat bonus if "provides" is in description
            for bid, bdata in food_buildings.items():
                if "provides" in bdata["description"].lower() and "food" in bdata["description"].lower():
                    best_food_building_id = bid
                    break
            if not best_food_building_id: # Fallback to cheapest
                 best_food_building_id = min(food_buildings, key=lambda bid: food_buildings[bid]["production_cost_total"])

            if best_food_building_id:
                msg = building_manager_obj.start_project(best_food_building_id) # start_project uses global core_resources
                event_manager_obj.log_event(f"Autonomous Focus: {reason} Constructing '{building_manager_obj.buildings_data[best_food_building_id]['name']}'. Outcome: {msg}")
                action_taken = "Error:" not in msg
                if action_taken: return True # Action taken
    
    if core_resources["Stability"] < 30:
        reason = "Low societal stability."
        event_manager_obj.log_event(f"Autonomous Concern: {reason}. No direct AI action defined to improve stability yet.")
        # No action taken for stability alone yet

    available_techs = tech_tree_obj.get_available_research()
    if core_resources["Knowledge"] > 20 and available_techs: 
        reason = "Surplus knowledge and available research."
        # Filter for affordable techs
        affordable_techs = {tid: tdata for tid, tdata in available_techs.items() if core_resources["Knowledge"] >= tdata["cost"]}
        if affordable_techs:
            cheapest_tech_id = min(affordable_techs, key=lambda tid: affordable_techs[tid]["cost"])
            msg = tech_tree_obj.research_tech(cheapest_tech_id)
            event_manager_obj.log_event(f"Autonomous Focus: {reason} Researching cheapest tech '{tech_tree_obj.technologies[cheapest_tech_id]['name']}'. Outcome: {msg}")
            action_taken = "Error:" not in msg
            if action_taken: return True # Action taken

    available_buildings = building_manager_obj.get_constructible_buildings()
    if core_resources["Production"] > 30 and available_buildings: 
        reason = "Surplus production and available construction projects."
        affordable_buildings = {
            bid: bdata for bid, bdata in available_buildings.items() 
            if core_resources["Production"] >= bdata["production_cost_per_cycle"] or bdata["build_time_cycles"] == 0
        }
        if affordable_buildings:
            cheapest_building_id = min(affordable_buildings, key=lambda bid: affordable_buildings[bid]["production_cost_total"])
            msg = building_manager_obj.start_project(cheapest_building_id)
            event_manager_obj.log_event(f"Autonomous Focus: {reason} Constructing cheapest building '{building_manager_obj.buildings_data[cheapest_building_id]['name']}'. Outcome: {msg}")
            action_taken = "Error:" not in msg
            if action_taken: return True # Action taken

    if not action_taken:
        event_manager_obj.log_event(f"Autonomous Focus: Civilization is stable or lacks immediate actions. Last reason checked: {reason}")

    return action_taken
