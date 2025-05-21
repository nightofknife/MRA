import json
import os

# Import game state variables and data definitions directly for saving
from .game_state import (
    core_resources, game_state_vars, tech_modifiers, building_modifiers
)
from .tech_tree import technologies as technologies_data # Rename to avoid conflict if class was also named technologies
from .building_manager import buildings_data as all_buildings_data # Data for all buildings
from .event_manager import events_data as all_events_data # Data for all events

# Note: Manager instances themselves are not saved directly. Their relevant state is extracted.
# The ui_console.print_message cannot be directly used here as it might create circular dependencies
# or is not appropriate for a non-UI module. For now, save/load will print directly.
# A better approach would be for save/load to return status messages for the UI to display.

def save_game(game_tech_tree, game_building_manager, game_event_manager, filename="text_epoch_save.json"):
    """
    Collects all necessary game state data, serializes it to JSON, and writes to a file.
    """
    try:
        # 1. Collect Game State
        save_data = {
            "core_resources": core_resources.copy(),
            "game_state_vars": game_state_vars.copy(),
            "tech_modifiers": tech_modifiers.copy(),
            "building_modifiers": building_modifiers.copy(),
            
            # Tech Tree: Save the 'researched' status for each technology
            "technologies_researched_state": {
                tech_id: tech.get("researched", False) 
                for tech_id, tech in game_tech_tree.technologies.items() # Use the live state from the manager
            },
            
            # Building Manager: Active projects and completed buildings counts
            "building_manager_active_projects": [project.copy() for project in game_building_manager.active_projects],
            "building_manager_completed_buildings": {
                 # Save count and any other relevant non-lambda state if buildings had more dynamic state
                b_id: {"count": info["count"]} 
                for b_id, info in game_building_manager.completed_buildings.items()
            },
            
            # Event Manager: Event log and any pending decision
            "event_manager_event_log": list(game_event_manager.event_log), # Ensure it's a list
            "event_manager_pending_decision_event": (
                game_event_manager.pending_decision_event.copy() 
                if game_event_manager.pending_decision_event else None
            ),
            # We also need to save one-time event triggered status
            "events_triggered_state": {
                event_id: event.get("triggered_this_session", False)
                for event_id, event in game_event_manager.events_data.items() # Use manager's copy
                if event.get("one_time", False) 
            }
        }

        # 2. Serialization and Writing to File
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=4)
        
        print(f"Game saved successfully to {filename}") # UI Leak
        return True

    except Exception as e:
        print(f"Error saving game: {e}") # UI Leak
        return False

def load_game(game_tech_tree, game_building_manager, game_event_manager, filename="text_epoch_save.json"):
    """
    Reads game state from a JSON file, deserializes it, and restores the game state.
    Returns True if loading was successful, False otherwise.
    """
    if not os.path.exists(filename):
        print(f"Save file '{filename}' not found.") # UI Leak
        return False

    try:
        with open(filename, 'r') as f:
            loaded_data = json.load(f)

        # Restore Game State
        # Direct restoration for simple dicts/vars
        core_resources.clear()
        core_resources.update(loaded_data["core_resources"])
        
        game_state_vars.clear()
        game_state_vars.update(loaded_data["game_state_vars"])
        
        tech_modifiers.clear()
        tech_modifiers.update(loaded_data["tech_modifiers"])
        
        building_modifiers.clear()
        building_modifiers.update(loaded_data["building_modifiers"])

        # Tech Tree: Restore 'researched' status
        # We are updating the 'technologies_data' which is used by TechTree instance
        # This assumes TechTree either uses this global dict or is re-initialized with it.
        # The current TechTree class takes 'technologies_data' in __init__ but then uses the global.
        # For this to work robustly, TechTree should operate on the dict it's given.
        # For now, we update the manager's dictionary.
        loaded_tech_researched_state = loaded_data["technologies_researched_state"]
        for tech_id, tech_instance_data in game_tech_tree.technologies.items():
            tech_instance_data["researched"] = loaded_tech_researched_state.get(tech_id, False)
        
        # Building Manager: Restore active projects and completed buildings
        game_building_manager.active_projects = [project.copy() for project in loaded_data["building_manager_active_projects"]]
        game_building_manager.completed_buildings.clear()
        # We need to restore the 'data' part of completed_buildings correctly, pointing to master building definitions
        for b_id, info in loaded_data["building_manager_completed_buildings"].items():
            if b_id in all_buildings_data: # Ensure building definition exists
                 game_building_manager.completed_buildings[b_id] = {
                     "count": info["count"],
                     "data": all_buildings_data[b_id] # Link to the master definition
                 }

        # Event Manager: Restore event log and pending decision
        game_event_manager.event_log = list(loaded_data["event_manager_event_log"])
        pending_event_data = loaded_data.get("event_manager_pending_decision_event")
        if pending_event_data:
            # Ensure choices are correctly structured if they were modified for serialization (not an issue with JSON)
            game_event_manager.pending_decision_event = pending_event_data
        else:
            game_event_manager.pending_decision_event = None
        
        # Restore one-time event triggered states
        loaded_events_triggered = loaded_data.get("events_triggered_state", {})
        for event_id, event_instance_data in game_event_manager.events_data.items():
            if event_instance_data.get("one_time", False):
                event_instance_data["triggered_this_session"] = loaded_events_triggered.get(event_id, False)


        # CRITICAL: Re-apply effects based on loaded state
        # 1. Clear current modifiers (already done by .clear() and .update() above for tech_modifiers and building_modifiers)
        #    But let's be explicit for safety if .update didn't fully replace.
        tech_modifiers.clear()
        tech_modifiers.update({ # Reset to defaults before re-applying
            "food_production_bonus_factor": 1.0, "production_bonus_factor": 1.0,
            "knowledge_generation_bonus_factor": 1.0, "culture_generation_bonus_factor": 1.0,
        })
        building_modifiers.clear()
        building_modifiers.update({ # Reset to defaults
            "food_per_cycle_bonus": 0, "production_per_cycle_bonus": 0,
            "knowledge_per_cycle_bonus": 0, "culture_per_cycle_bonus": 0,
            "food_production_bonus_factor": 1.0,
        })

        # 2. Re-apply tech effects
        for tech_id, tech_instance_data in game_tech_tree.technologies.items():
            if tech_instance_data["researched"] and tech_instance_data.get("effect"):
                tech_instance_data["effect"]() # Lambdas directly modify imported tech_modifiers

        # 3. Re-apply building effects
        for b_id, info in game_building_manager.completed_buildings.items():
            building_def = info["data"] # This now correctly points to master building_data
            if building_def.get("apply_effect"):
                # Effects are applied per instance. If a granary gives +10, 2 granaries give +20.
                # The apply_effect lambda should be defined to add to the existing modifier.
                # So, if we have 2 granaries, we call apply_effect twice.
                for _ in range(info["count"]):
                    building_def["apply_effect"]() # Lambdas directly modify imported building_modifiers
        
        print(f"Game loaded successfully from {filename}") # UI Leak
        return True

    except Exception as e:
        print(f"Error loading game: {e}. The save file might be corrupted or incompatible.") # UI Leak
        return False
