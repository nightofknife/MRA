# --- Imports ---
# Assuming the 'text_epoch' directory is in the same directory as this main.py,
# or that text_epoch is in PYTHONPATH.
# For direct execution, Python might need to be run with 'python -m text_epoch.main' from parent dir
# or adjust sys.path. For now, using relative imports assuming it's run as part of a package.

# If running this file directly, and text_epoch is a subdir:
import sys
import os
# Add the parent directory of 'text_epoch' to sys.path if it's not already there
# This allows imports like from text_epoch.game_state import ...
# This is a common way to handle running files within a package structure directly.
current_dir = os.path.dirname(os.path.abspath(__file__))
# If main.py is at the root and text_epoch is a subdirectory:
package_dir = os.path.join(current_dir, "text_epoch")
if os.path.isdir(package_dir) and package_dir not in sys.path:
    # This structure assumes main.py is *outside* text_epoch dir.
    # If main.py is *inside* text_epoch dir, this path logic needs to change,
    # or we rely on Python's module resolution if text_epoch is installed or in PYTHONPATH.
    # For the prompt's structure 'text_epoch/main.py', this part is tricky.
    # The prompt implies text_epoch/main.py is the *new* main.
    # Let's assume this main.py is at the root for now, and it calls into the text_epoch package.
    # So, the imports should be:
    # from text_epoch.game_state import ...
    pass # sys.path modification might not be needed if run with `python -m main` from outside text_epoch


from text_epoch.game_state import (
    core_resources, game_state_vars, # tech_modifiers, building_modifiers are used by managers internally
    update_resources, update_stability # update_stability is used by event_manager internally
)
from text_epoch.tech_tree import TechTree, technologies
from text_epoch.building_manager import BuildingManager, buildings_data
from text_epoch.event_manager import EventManager, events_data
from text_epoch.autonomous_logic import make_autonomous_decision
from text_epoch.ui_console import (
    display_turn_summary, get_player_input,
    print_action_result, display_full_event_log, print_message
)
from text_epoch.utils import AUTONOMOUS_DECISION_THRESHOLD
from text_epoch.save_load_manager import save_game, load_game # New import
from text_epoch.policies import PolicyManager, policies_data # Policy system
from text_epoch import game_state as game_state_module # Import for PolicyManager


# --- Main Game Setup ---
def run_game():
    # Initialize Managers
    game_tech_tree = TechTree(technologies) # technologies is from tech_tree.py
    game_building_manager = BuildingManager(buildings_data, game_tech_tree) # buildings_data from building_manager.py
    
    # EventManager needs access to core_resources for trigger conditions and effects,
    # and other managers to check their state or apply effects.
    # update_stability is imported from game_state and passed if needed by events.
    game_event_manager = EventManager(events_data, game_tech_tree, game_building_manager)
    
    game_policy_manager = PolicyManager(policies_data, game_state_module, game_tech_tree, game_building_manager, game_event_manager)

    # --- Initial Load Option ---
    if os.path.exists("text_epoch_save.json"):
        initial_load_choice = input("Save file found. Load game? (yes/no): ").strip().lower()
        if initial_load_choice == 'yes':
            if load_game(game_tech_tree, game_building_manager, game_event_manager):
                print_message("Game loaded successfully. Continuing your adventure!", no_pause=False)
                # game_state_vars['current_cycle'] might have been loaded, so header will show correct cycle
            else:
                print_message("Failed to load game. Starting a new game.", no_pause=False)
                # Reset to ensure clean start if load failed partially (though load_game should handle this)
                # This part is tricky; load_game ideally leaves state untouched on failure or resets it.
                # Assuming load_game is robust enough not to corrupt state on fail.
        else:
            print_message("Starting a new game.", no_pause=False)
    else:
        print_message("Text Epoch game initialized. The adventure begins!", no_pause=False)


    # --- Main Game Loop ---
    running = True
    while running:
        game_state_vars["current_cycle"] += 1
        action_taken_by_player_this_turn = False # Reset for the new turn's input phase

        # --- Game Logic Phases ---
        # 1. Construction Phase (updates based on previous cycle's resources)
        if game_state_vars["current_cycle"] > 1:
            # This function currently prints directly (UI leak)
            game_building_manager.update_construction() 

        # 2. Policy Update Phase 
        game_policy_manager.update_active_policies() # Ticks down durations, handles expirations

        # 3. Resource Generation Phase
        # This function currently prints directly (UI leak)
        update_resources() # Operates on global core_resources, tech_modifiers, building_modifiers from game_state.py

        # 4. Event Phase
        if not game_event_manager.pending_decision_event:
            # This function currently prints directly (UI leak)
            game_event_manager.check_for_events() 

        # --- UI and Input Phase ---
        # Display current game state
        is_decision_pending = display_turn_summary(
            game_state_vars,
            core_resources,
            game_building_manager,
            game_event_manager,
            game_tech_tree
        )
        
        # Handle player input or pending decision
        if is_decision_pending:
            decision_choices_count = len(game_event_manager.pending_decision_event["choices"])
            user_input_str, _ = get_player_input(True, decision_choices_count)
            resolve_message = game_event_manager.resolve_decision_event(user_input_str)
            print_action_result(resolve_message, error=("Error:" in resolve_message))
            if "Error:" not in resolve_message:
                 action_taken_by_player_this_turn = True 
        else:
            user_input_str, _ = get_player_input(False)

            if user_input_str == 'quit':
                print_message("Exiting Text Epoch. Goodbye!", no_pause=True) # No pause before quit
                running = False # Exit loop
                continue # Skip to next iteration to exit
            elif user_input_str == 'save':
                action_taken_by_player_this_turn = True
                # save_game prints its own messages (UI leak)
                save_game(game_tech_tree, game_building_manager, game_event_manager)
                print_action_result("Save attempt complete (see messages above).", error=False) # Standard pause
            elif user_input_str == 'load':
                action_taken_by_player_this_turn = True
                print_message("Attempting to load game. Current state will be overwritten if successful.", no_pause=True)
                # load_game prints its own messages (UI leak)
                if load_game(game_tech_tree, game_building_manager, game_event_manager):
                    print_action_result("Game loaded. The world has changed around you!", error=False)
                    # Reset idle cycles as the game state has changed significantly
                    game_state_vars["idle_cycles_count"] = 0 
                    # Loop will continue, effectively restarting the turn display with loaded state
                else:
                    print_action_result("Failed to load game. Continuing with current game.", error=True)
            elif user_input_str.startswith("research "):
                action_taken_by_player_this_turn = True
                try:
                    tech_to_research = user_input_str.split(" ", 1)[1].strip()
                    # research_tech prints its own messages (UI leak)
                    research_message = game_tech_tree.research_tech(tech_to_research)
                    # We use print_action_result to standardize the pause, though research_tech also prints.
                    # Ideally, research_tech would return a status/message and UI would handle all printing.
                    # For now, we might see double prints for success.
                    print_action_result(research_message, error=("Error:" in research_message))
                except IndexError:
                    print_action_result("Invalid research command. Usage: research <tech_id>", error=True)
            elif user_input_str.startswith("build "):
                action_taken_by_player_this_turn = True
                try:
                    building_to_construct = user_input_str.split(" ", 1)[1].strip()
                    # start_project prints its own messages (UI leak)
                    build_message = game_building_manager.start_project(building_to_construct)
                    print_action_result(build_message, error=("Error:" in build_message))
                except IndexError:
                    print_action_result("Invalid build command. Usage: build <building_id>", error=True)
            elif user_input_str == 'log':
                action_taken_by_player_this_turn = True
                display_full_event_log(game_event_manager) # Handles its own clear and pause
            elif user_input_str == 'next' or user_input_str == "":
                game_state_vars["idle_cycles_count"] += 1
                # No message here, next cycle will start.
            else: # Unknown command
                action_taken_by_player_this_turn = True 
                print_action_result(f"Unknown command: '{user_input_str}'.", error=True)

            if action_taken_by_player_this_turn: # Any valid or invalid command attempt by player resets idle
                 game_state_vars["idle_cycles_count"] = 0

        # --- Autonomous Action Phase (if player was idle) ---
        if not action_taken_by_player_this_turn and \
           not is_decision_pending and \
           game_state_vars["idle_cycles_count"] >= AUTONOMOUS_DECISION_THRESHOLD:
            
            # make_autonomous_decision prints directly via event_manager.log_event (UI leak)
            print_message("--- Autonomous Civilization Focus ---", no_pause=True) # Header for AI action
            ai_took_action = make_autonomous_decision(
                game_tech_tree, 
                game_building_manager, 
                game_event_manager
            )
            if ai_took_action:
                game_state_vars["idle_cycles_count"] = 0
                print_action_result("Autonomous action taken and logged above.")
            else:
                # AI didn't find an action. It logs this itself.
                # No specific pause here, next cycle will just start unless player intervenes.
                pass


if __name__ == "__main__":
    # This structure assumes you run `python main.py` from the directory containing `main.py` and the `text_epoch` package.
    # If text_epoch is not found, Python's import system will raise an error.
    # Ensure the `text_epoch` directory has an `__init__.py` file.
    if not os.path.exists("text_epoch/__init__.py"):
        # Attempt to create it if missing, for ease of running if setup was partial.
        if not os.path.exists("text_epoch"):
            os.makedirs("text_epoch")
        with open("text_epoch/__init__.py", "w") as f:
            f.write("# This file makes text_epoch a package\n")
            print("Created text_epoch/__init__.py to ensure package recognition.")

    run_game()
