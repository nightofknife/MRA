import os

# --- Utility Functions ---
def clear_screen():
    """Clears the terminal screen."""
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')

def display_game_header(game_state_vars):
    print("====== Text Epoch ======")
    print(f"Year: {game_state_vars['current_cycle'] * 5} (Cycle: {game_state_vars['current_cycle']})")
    print("========================")

def display_core_resources(core_resources_dict): # Pass core_resources directly
    print("\n--- Core Resources ---")
    # Note: This display is simplified. The detailed change report is currently
    # printed directly by update_resources() in game_state.py.
    # A future refactor would have update_resources return data to be formatted here.
    for res, val in core_resources_dict.items():
        if isinstance(val, float):
            print(f"{res:<12}: {val:.2f}")
        elif isinstance(val, int) and res == "Stability":
             print(f"{res:<12}: {val}%")
        else:
            print(f"{res:<12}: {val}")
    print("----------------------")

def display_ongoing_activities(building_manager_obj):
    print("\n--- Ongoing Activities ---")
    print("Research Focus: (Techs research instantaneously in current model)") # Placeholder
    if building_manager_obj.active_projects:
        print("Under Construction:")
        for proj in building_manager_obj.active_projects:
            print(f"- {proj['name']}: {proj['remaining_cycles']} cycles left ({proj['cost_per_cycle']} Prod/cycle).")
    else:
        print("No active construction projects.")
    print("------------------------")

def display_recent_events(event_manager_obj, count=3):
    print(f"\n--- Recent Events (Last {count}) ---")
    if event_manager_obj.event_log:
        for log_entry in reversed(event_manager_obj.event_log[-count:]): 
            print(f"- {log_entry}")
    else:
        print("No significant events logged recently.")
    print("-----------------------------")

def display_pending_decision(event_manager_obj):
    if event_manager_obj.pending_decision_event:
        event = event_manager_obj.pending_decision_event
        print("\n--- !!! PENDING DECISION !!! ---")
        print(f"Event: {event['title']}")
        print(event['description'])
        for i, choice in enumerate(event['choices']):
            print(f"  {i+1}. {choice['choice_text']}")
        print("--------------------------------")
        return True # Indicates a decision is pending
    return False

def display_available_actions(tech_tree_obj, building_manager_obj):
    print("\n--- Available Actions ---")
    print("Research Options:")
    available_techs = tech_tree_obj.get_available_research()
    if available_techs:
        for tech_id, data in available_techs.items():
            print(f"- [{tech_id}] {data['name']} (Cost: {data['cost']} Knowledge). Effect: {data['description']}")
    else:
        print("  No new technologies available for research.")
    
    print("\nConstruction Options:")
    constructible_buildings = building_manager_obj.get_constructible_buildings()
    if constructible_buildings:
        for b_id, data in constructible_buildings.items():
            max_str = f"(Max: {data['max_allowed']})" if data['max_allowed'] != float('inf') else ""
            # Ensure production_cost_per_cycle is present, default to 0 if not (though it should be)
            cost_per_cycle = data.get('production_cost_per_cycle', data['production_cost_total'] / data['build_time_cycles'] if data['build_time_cycles'] > 0 else data['production_cost_total'])
            print(f"- [{b_id}] {data['name']} {max_str} (Cost: {data['production_cost_total']} Prod over {data['build_time_cycles']} cycles ({cost_per_cycle:.0f}/cycle)). Effect: {data['description']}")
    else:
        print("  No new buildings available for construction.")
    print("-------------------------")

def display_reference_info(tech_tree_obj, building_manager_obj):
    print("\n--- Reference ---")
    print("Researched Technologies:")
    researched_techs = tech_tree_obj.get_researched_techs()
    if researched_techs:
        print("  " + ", ".join([data['name'] for data in researched_techs.values()]))
    else:
        print("  None.")
    
    print("\nCompleted Buildings:")
    completed_building_counts = building_manager_obj.get_completed_building_counts()
    if completed_building_counts:
        building_strings = []
        for b_id_key, count in completed_building_counts.items():
            # Accessing buildings_data from the manager instance now
            building_info = building_manager_obj.buildings_data[b_id_key] 
            count_str = f" (x{count})" if count > 1 else ""
            building_strings.append(f"{building_info['name']}{count_str}")
        print("  " + ", ".join(building_strings))
    else:
        print("  None.")
    print("-----------------")

def get_player_input(is_decision_pending, decision_choices_count=0):
    if is_decision_pending:
        prompt = f"Enter your decision (1-{decision_choices_count}): "
        return input(prompt).strip().lower(), "decision"
    else:
        prompt = "\nEnter command ('next', 'research <id>', 'build <id>', 'log', 'quit'): "
        return input(prompt).strip().lower(), "command"

def display_full_event_log(event_manager_obj):
    clear_screen()
    print("\n--- Full Event Log (Oldest to Newest) ---")
    if event_manager_obj.event_log:
        for entry_idx, entry in enumerate(event_manager_obj.event_log):
            print(f"{entry_idx+1}. {entry}")
    else:
        print("Event log is empty.")
    print("------------------------------------------")
    input("Press Enter to return to the game...")

def print_action_result(message, error=False):
    """Prints result of an action and pauses if it wasn't an error, or if it was critical."""
    print(message)
    if not error or "Error:" in message: # Pause for errors or successful actions
        input("Press Enter to continue...")

def print_message(message):
    """Simple print for general messages, followed by a pause."""
    print(message)
    input("Press Enter to continue...")

def display_turn_summary(game_state_vars, core_resources_dict, building_manager_obj, event_manager_obj, tech_tree_obj):
    """Main function to display the entire game screen for a turn."""
    clear_screen()
    display_game_header(game_state_vars)
    display_core_resources(core_resources_dict) # Pass core_resources
    display_ongoing_activities(building_manager_obj)
    display_recent_events(event_manager_obj)

    is_decision_pending = display_pending_decision(event_manager_obj)
    
    if not is_decision_pending:
        display_available_actions(tech_tree_obj, building_manager_obj)
        display_reference_info(tech_tree_obj, building_manager_obj)
    
    return is_decision_pending # Return this status for the main loop to use for input handling
