# Core Resources
core_resources = {
    "Population": 100,
    "Food": 100,
    "Production": 50,
    "Knowledge": 0,
    "Culture": 0,
    "Stability": 75  # Represented as a percentage (0-100)
}

# Game State
game_state = {
    "current_cycle": 0,
    "idle_cycles_count": 0,
}

# --- Game Constants ---
AUTONOMOUS_DECISION_THRESHOLD = 4 # Cycles of player inaction to trigger AI

# --- Technology System ---
DEFAULT_FOOD_PRODUCTION_PER_CAPITA = 1.1
DEFAULT_PRODUCTION_PER_CAPITA = 0.5
DEFAULT_KNOWLEDGE_PER_CAPITA = 0.1
DEFAULT_CULTURE_PER_CAPITA = 0.05

# Global Modifiers - these will be updated by technologies
tech_modifiers = {
    "food_production_bonus_factor": 1.0, # Multiplicative bonus to food production
    "production_bonus_factor": 1.0,    # Multiplicative bonus to general production
    "knowledge_generation_bonus_factor": 1.0, # Multiplicative bonus to knowledge generation
    "culture_generation_bonus_factor": 1.0, # Multiplicative bonus to culture generation
}

technologies = {
    "stone_tools": {
        "name": "Improved Stone Tools",
        "description": "Increases Production efficiency by 20%.",
        "cost": 20,
        "prerequisites": [],
        "researched": False,
        "effect": lambda: tech_modifiers.update({"production_bonus_factor": tech_modifiers["production_bonus_factor"] * 1.2})
    },
    "basic_farming": {
        "name": "Basic Farming Techniques",
        "description": "Increases Food production efficiency by 20%.",
        "cost": 30,
        "prerequisites": [],
        "researched": False,
        "effect": lambda: tech_modifiers.update({"food_production_bonus_factor": tech_modifiers["food_production_bonus_factor"] * 1.2})
    },
    "oral_tradition": {
        "name": "Oral Tradition",
        "description": "Increases Knowledge generation by 10%.",
        "cost": 15,
        "prerequisites": [],
        "researched": False,
        "effect": lambda: tech_modifiers.update({"knowledge_generation_bonus_factor": tech_modifiers["knowledge_generation_bonus_factor"] * 1.1})
    },
    "early_writing": {
        "name": "Early Writing",
        "description": "Increases Knowledge generation by another 20% and Culture by 10%.",
        "cost": 50,
        "prerequisites": ["oral_tradition"],
        "researched": False,
        "effect": lambda: (
            tech_modifiers.update({"knowledge_generation_bonus_factor": tech_modifiers["knowledge_generation_bonus_factor"] * 1.2}),
            tech_modifiers.update({"culture_generation_bonus_factor": tech_modifiers["culture_generation_bonus_factor"] * 1.1})
        )
    }
}

class TechTree:
    def __init__(self, technologies_data):
        self.technologies = technologies_data

    def get_researched_techs(self):
        return {tech_id: data for tech_id, data in self.technologies.items() if data["researched"]}

    def get_available_research(self):
        available = {}
        for tech_id, data in self.technologies.items():
            if not data["researched"]:
                prerequisites_met = all(
                    self.technologies[prereq_id]["researched"] for prereq_id in data["prerequisites"]
                )
                if prerequisites_met:
                    available[tech_id] = data
        return available

    def research_tech(self, tech_id):
        global core_resources
        available_techs = self.get_available_research()

        if tech_id not in available_techs:
            return f"Error: Technology '{tech_id}' is not available or does not exist."

        tech_data = self.technologies[tech_id]
        if core_resources["Knowledge"] < tech_data["cost"]:
            return f"Error: Not enough Knowledge to research {tech_data['name']}. Need {tech_data['cost']}, have {core_resources['Knowledge']:.0f}."

        core_resources["Knowledge"] -= tech_data["cost"]
        tech_data["researched"] = True
        if tech_data["effect"]:
            tech_data["effect"]() # Apply the effect
        
        print(f"\nTechnology Researched: {tech_data['name']}!")
        print(f"Effect: {tech_data['description']}")
        print(f"Knowledge spent: {tech_data['cost']}. Remaining Knowledge: {core_resources['Knowledge']:.0f}")
        return f"Successfully researched {tech_data['name']}."

import random # Needed for event probabilities
import os

# --- Autonomous Decision Making ---
def make_autonomous_decision(resources, tech_tree_obj, building_manager_obj, event_manager_obj):
    """
    Makes a single autonomous decision for the civilization based on simple priorities.
    Returns True if an action was taken, False otherwise.
    """
    action_taken = False
    reason = "No specific crisis or opportunity identified."

    # 1. Food Security
    # Estimate food consumption: current pop * base consumption. Tech/building effects are included in actual Food changes.
    # This is a rough estimate for AI planning.
    estimated_food_consumption_per_cycle = resources["Population"] * FOOD_CONSUMPTION_PER_CAPITA
    if estimated_food_consumption_per_cycle <= 0: estimated_food_consumption_per_cycle = 1 # Avoid div by zero

    food_cycles_remaining = resources["Food"] / estimated_food_consumption_per_cycle if estimated_food_consumption_per_cycle > 0 else float('inf')
    
    # Attempt to calculate net food production (very simplified, doesn't account for future pop growth this cycle)
    # This relies on the fact that update_resources() has just run and values are current.
    # A more robust way would be to simulate next cycle's food production.
    # For now, we'll use a proxy: if food is low or dropping significantly.
    # We can't easily get "net food change" without re-running parts of update_resources or storing its detailed output.
    # So, let's focus on food reserves and available improvements.

    if food_cycles_remaining < 5 or resources["Food"] < 20 : # Less than 5 cycles of food or less than 20 food units
        reason = "Low food reserves."
        # Try to research food tech
        available_techs = tech_tree_obj.get_available_research()
        food_techs = {tid: tdata for tid, tdata in available_techs.items() if "Food" in tdata["description"] and resources["Knowledge"] >= tdata["cost"]}
        if food_techs:
            cheapest_food_tech_id = min(food_techs, key=lambda tid: food_techs[tid]["cost"])
            msg = tech_tree_obj.research_tech(cheapest_food_tech_id)
            event_manager_obj.log_event(f"Autonomous Focus: {reason} Researching '{tech_tree_obj.technologies[cheapest_food_tech_id]['name']}'. Outcome: {msg}")
            action_taken = "Error:" not in msg
            return action_taken

        # Else, try to build food building
        available_buildings = building_manager_obj.get_constructible_buildings()
        food_buildings = {bid: bdata for bid, bdata in available_buildings.items() 
                          if ("Food" in bdata["description"] or "food" in bdata["effect_description"].lower()) and 
                             (resources["Production"] >= bdata["production_cost_per_cycle"] or bdata["build_time_cycles"] == 0) # Check if can afford first cycle
                         }
        if food_buildings:
            # Prioritize buildings that give flat bonuses if food is critically low, then percentage
            # This is a simple heuristic. A more complex one might look at cost/benefit.
            best_food_building_id = None
            if any("per_cycle_bonus" in building_modifiers and bm_key == "food_per_cycle_bonus" for bm_key in building_modifiers): # A bit of a hacky check
                 # Find one with food_per_cycle_bonus if possible
                for bid, bdata in food_buildings.items():
                    # This check is very indirect. A better way would be to have tags or direct effect values in building_data
                    if "provides" in bdata["description"].lower() and "food" in bdata["description"].lower(): # Heuristic for flat bonus
                        best_food_building_id = bid
                        break
            if not best_food_building_id: # Fallback to any food building, cheapest first
                 best_food_building_id = min(food_buildings, key=lambda bid: food_buildings[bid]["production_cost_total"])

            if best_food_building_id:
                msg = building_manager_obj.start_project(best_food_building_id)
                event_manager_obj.log_event(f"Autonomous Focus: {reason} Constructing '{building_manager_obj.buildings_data[best_food_building_id]['name']}'. Outcome: {msg}")
                action_taken = "Error:" not in msg
                return action_taken
    
    # 2. Stability Crisis (Placeholder logic)
    if resources["Stability"] < 30:
        reason = "Low societal stability."
        # No direct stability techs/buildings defined yet. AI might prioritize food if that's a known cause.
        # For now, just log that it's a concern.
        event_manager_obj.log_event(f"Autonomous Concern: {reason}. No direct action defined for AI yet.")
        # action_taken remains False, other priorities will be checked.

    # 3. Knowledge Generation
    available_techs = tech_tree_obj.get_available_research()
    if resources["Knowledge"] > 20 and available_techs: # Have some knowledge, and techs are available
        reason = "Surplus knowledge and available research."
        cheapest_tech_id = min(available_techs, key=lambda tid: available_techs[tid]["cost"])
        if resources["Knowledge"] >= available_techs[cheapest_tech_id]["cost"]:
            msg = tech_tree_obj.research_tech(cheapest_tech_id)
            event_manager_obj.log_event(f"Autonomous Focus: {reason} Researching cheapest tech '{tech_tree_obj.technologies[cheapest_tech_id]['name']}'. Outcome: {msg}")
            action_taken = "Error:" not in msg
            return action_taken

    # 4. Production Utilization
    available_buildings = building_manager_obj.get_constructible_buildings()
    if resources["Production"] > 30 and available_buildings: # Have some production, and buildings can be started
        reason = "Surplus production and available construction projects."
        # Pick cheapest building that can be afforded for at least one cycle
        affordable_buildings = {bid: bdata for bid, bdata in available_buildings.items() if resources["Production"] >= bdata["production_cost_per_cycle"]}
        if affordable_buildings:
            cheapest_building_id = min(affordable_buildings, key=lambda bid: affordable_buildings[bid]["production_cost_total"])
            msg = building_manager_obj.start_project(cheapest_building_id)
            event_manager_obj.log_event(f"Autonomous Focus: {reason} Constructing cheapest building '{building_manager_obj.buildings_data[cheapest_building_id]['name']}'. Outcome: {msg}")
            action_taken = "Error:" not in msg
            return action_taken

    if not action_taken:
        event_manager_obj.log_event(f"Autonomous Focus: Civilization is stable or lacks immediate actions. Current reason checked: {reason}")

    return action_taken


# --- Utility Functions ---
def clear_screen():
    """Clears the terminal screen."""
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For macOS and Linux
    else:
        _ = os.system('clear')

# --- Event Definitions ---
events_data = {
    "bumper_harvest": {
        "event_id": "bumper_harvest",
        "type": "random", # Can be 'random' or 'decision'
        "title": "Unexpected Bumper Harvest",
        "description": "Favorable weather and unexpected fertility have led to an unusually large harvest.",
        "probability": 0.05, # 5% chance per cycle to trigger
        "trigger_conditions": lambda cr, techs: True, # No special conditions for this one yet
        "effects": lambda: (
            core_resources.update({"Food": core_resources["Food"] + 50 + int(core_resources["Population"] * 0.5)}), # Flat +50 food + 0.5 per pop
            core_resources.update({"Stability": min(100, core_resources["Stability"] + 5)}),
            game_event_manager.log_event("Outcome: Food increased significantly (+50, +0.5/Pop). Stability improved (+5%).")
        )
    },
    "rodent_infestation": {
        "event_id": "rodent_infestation",
        "type": "random",
        "title": "Rodent Infestation",
        "description": "Rodents have infested food stores, leading to significant losses.",
        "probability": 0.03,
        "trigger_conditions": lambda cr, techs: cr["Food"] > 20, # Only if there's some food to infest
        "effects": lambda: (
            core_resources.update({"Food": max(0, core_resources["Food"] - int(core_resources["Food"] * 0.15))}), # Lose 15% of food
            core_resources.update({"Stability": max(0, core_resources["Stability"] - 3)}),
            game_event_manager.log_event("Outcome: Food decreased by 15%. Stability slightly worsened (-3%).")
        )
    },
    "strange_lights": {
        "event_id": "strange_lights",
        "type": "decision",
        "title": "Strange Lights in the Sky",
        "description": "Elderly members of the tribe speak of strange, fleeting lights observed in the night sky. Some are fearful, others curious.",
        "probability": 0.02,
        "trigger_conditions": lambda cr, techs: cr["Knowledge"] > 30, # Only if Knowledge > 30
        "player_choices": [
            {
                "choice_text": "Dismiss them as ill omens. Focus on earthly matters and appease the spirits with work.",
                "choice_effects": lambda: (
                    core_resources.update({"Culture": core_resources["Culture"] + 10}),
                    core_resources.update({"Knowledge": max(0, core_resources["Knowledge"] - 5)}),
                    core_resources.update({"Stability": min(100, core_resources["Stability"] + 2)}), # Slight stability from decisive (even if dismissive) leadership
                    game_event_manager.log_event("Choice Outcome: Culture +10, Knowledge -5, Stability +2.")
                )
            },
            {
                "choice_text": "Order the wisest to observe and interpret them. Knowledge is paramount.",
                "choice_effects": lambda: (
                    core_resources.update({"Knowledge": core_resources["Knowledge"] + 20}),
                    core_resources.update({"Culture": max(0, core_resources["Culture"] - 5)}),
                    core_resources.update({"Stability": max(0, core_resources["Stability"] - random.randint(0,3))}), # Fear of unknown
                    game_event_manager.log_event("Choice Outcome: Knowledge +20, Culture -5. Stability may have slightly decreased due to unease.")
                )
            },
            {
                "choice_text": "Proclaim them a sign from the ancient spirits! Hold a grand ritual to seek guidance.",
                "choice_effects": lambda: (
                    core_resources.update({"Culture": core_resources["Culture"] + 30}),
                    core_resources.update({"Stability": min(100, core_resources["Stability"] + 5)}),
                    core_resources.update({"Production": max(0, core_resources["Production"] - 15)}), # Rituals take effort
                    core_resources.update({"Food": max(0, core_resources["Food"] - 20)}), # Feasting for ritual
                    game_event_manager.log_event("Choice Outcome: Culture +30, Stability +5. Production -15, Food -20 due to ritual preparations.")
                )
            }
        ]
    }
}


class EventManager:
    def __init__(self, events_config, resources_ref, tech_tree_ref, building_manager_ref, stability_update_func_ref=None):
        self.events_data = events_config
        self.core_resources = resources_ref
        self.tech_tree = tech_tree_ref
        self.building_manager = building_manager_ref
        self.update_stability_func = stability_update_func_ref 
        self.pending_decision_event = None
        self.event_log = [] # Stores strings describing triggered events and choices

    def log_event(self, message, is_major=False):
        prefix = "EVENT: "
        if is_major:
            prefix = "MAJOR EVENT: "
        
        log_entry = f"{prefix}{message}"
        print(log_entry) # For immediate visibility
        self.event_log.append(log_entry)
        if len(self.event_log) > 30: # Limit log size
            self.event_log.pop(0)

    def apply_effects(self, effects_lambda):
        if effects_lambda:
            effects_lambda() 

    def check_for_events(self):
        if self.pending_decision_event:
            return # Player needs to resolve the current decision first

        triggered_event_this_cycle = False
        for event_id, event_data in self.events_data.items():
            if event_data.get("triggered_this_session", False) and event_data.get("one_time", False): # For one-time events
                continue

            conditions_met = True
            if "trigger_conditions" in event_data:
                if not event_data["trigger_conditions"](self.core_resources, self.tech_tree.technologies):
                    conditions_met = False
            
            if not conditions_met:
                continue

            if random.random() < event_data.get("probability", 0.0):
                self.trigger_event(event_id, event_data)
                triggered_event_this_cycle = True
                if self.pending_decision_event or event_data.get("stops_further_events_this_cycle", False):
                    break # Only one major event or decision event per cycle usually
        
        if not triggered_event_this_cycle:
            print("No significant events occurred this cycle.")


    def trigger_event(self, event_id, event_data):
        self.log_event(f"{event_data['title']} - {event_data['description']}", is_major=True)
        
        if event_data.get("one_time", False):
             self.events_data[event_id]["triggered_this_session"] = True


        if event_data["type"] == "decision":
            self.pending_decision_event = {
                "id": event_id, # Store event_id for reference if needed
                "title": event_data["title"],
                "description": event_data["description"],
                "choices": event_data["player_choices"] # Contains text and effect lambdas
            }
        elif event_data["type"] == "random": # Direct effect
            if "effects" in event_data:
                self.apply_effects(event_data["effects"])
                # Specific outcomes are logged by the effect lambda itself via game_event_manager.log_event
        # Potentially add 'triggered' event type here later that might not be random

    def resolve_decision_event(self, choice_input):
        if not self.pending_decision_event:
            return "Error: No pending decision to resolve."

        try:
            choice_idx = int(choice_input) - 1 # Player input is 1-based
            if not 0 <= choice_idx < len(self.pending_decision_event["choices"]):
                return "Error: Invalid choice number."
        except ValueError:
            return "Error: Choice must be a number."

        chosen_option = self.pending_decision_event["choices"][choice_idx]
        self.log_event(f"For '{self.pending_decision_event['title']}', you chose: '{chosen_option['choice_text']}'", is_major=True)
        
        if "choice_effects" in chosen_option:
            self.apply_effects(chosen_option["choice_effects"])
            # Specific outcomes logged by the choice_effect lambda

        self.pending_decision_event = None # Clear the pending event
        return f"Decision '{chosen_option['choice_text']}' has been made."


# --- Building System ---
building_modifiers = {
    "food_per_cycle_bonus": 0,          # Flat bonus to food per cycle
    "production_per_cycle_bonus": 0,    # Flat bonus to production per cycle
    "knowledge_per_cycle_bonus": 0,     # Flat bonus to knowledge per cycle
    "culture_per_cycle_bonus": 0,       # Flat bonus to culture per cycle
    "food_production_bonus_factor": 1.0, # Multiplicative bonus to food from population
}

buildings_data = {
    "granary": {
        "name": "Granary",
        "description": "Provides a steady supply of +10 Food per cycle.",
        "production_cost_total": 50,
        "build_time_cycles": 5, # production_cost_per_cycle will be 10
        "prerequisites": [],
        "max_allowed": 2,
        "effect_description": "+10 Food/cycle",
        "apply_effect": lambda: building_modifiers.update({"food_per_cycle_bonus": building_modifiers["food_per_cycle_bonus"] + 10}),
        "remove_effect": lambda: building_modifiers.update({"food_per_cycle_bonus": building_modifiers["food_per_cycle_bonus"] - 10}),
    },
    "workshop": {
        "name": "Workshop",
        "description": "Generates +5 Production points per cycle.",
        "production_cost_total": 80,
        "build_time_cycles": 8, # production_cost_per_cycle will be 10
        "prerequisites": [],
        "max_allowed": float('inf'), 
        "effect_description": "+5 Production/cycle",
        "apply_effect": lambda: building_modifiers.update({"production_per_cycle_bonus": building_modifiers["production_per_cycle_bonus"] + 5}),
        "remove_effect": lambda: building_modifiers.update({"production_per_cycle_bonus": building_modifiers["production_per_cycle_bonus"] - 5}),
    },
    "communal_fields": {
        "name": "Communal Fields",
        "description": "Increases Food production efficiency from population by 10%.",
        "production_cost_total": 100,
        "build_time_cycles": 10, # production_cost_per_cycle will be 10
        "prerequisites": ["basic_farming"], 
        "max_allowed": 1,
        "effect_description": "+10% Food production efficiency from population",
        "apply_effect": lambda: building_modifiers.update({"food_production_bonus_factor": building_modifiers["food_production_bonus_factor"] * 1.1}),
        "remove_effect": lambda: building_modifiers.update({"food_production_bonus_factor": building_modifiers["food_production_bonus_factor"] / 1.1}),
    }
}

# Calculate production_cost_per_cycle for all buildings dynamically
for b_id, data in buildings_data.items():
    if data["build_time_cycles"] > 0:
        data["production_cost_per_cycle"] = round(data["production_cost_total"] / data["build_time_cycles"])
    else: 
        data["production_cost_per_cycle"] = data["production_cost_total"]


class BuildingManager:
    def __init__(self, buildings_config, resources_ref, tech_tree_ref):
        self.buildings_data = buildings_config
        self.core_resources = resources_ref
        self.tech_tree = tech_tree_ref
        self.active_projects = [] 
        self.completed_buildings = {}

    def get_completed_building_counts(self):
        return {b_id: info["count"] for b_id, info in self.completed_buildings.items()}

    def get_constructible_buildings(self):
        constructible = {}
        current_completed_counts = self.get_completed_building_counts()

        for building_id, data in self.buildings_data.items():
            if current_completed_counts.get(building_id, 0) >= data["max_allowed"]:
                continue

            prerequisites_met = True
            for tech_prereq_id in data["prerequisites"]:
                tech_entry = self.tech_tree.technologies.get(tech_prereq_id)
                if not tech_entry or not tech_entry["researched"]:
                    prerequisites_met = False
                    break
            if not prerequisites_met:
                continue
            
            constructible[building_id] = data
        return constructible

    def start_project(self, building_id):
        available_to_build = self.get_constructible_buildings()
        if building_id not in available_to_build:
            if building_id not in self.buildings_data:
                return f"Error: Building ID '{building_id}' is unknown."
            data = self.buildings_data[building_id]
            if self.get_completed_building_counts().get(building_id, 0) >= data["max_allowed"]:
                 return f"Error: Cannot start {data['name']}. Maximum number ({data['max_allowed']}) already built."
            missing_prereqs = []
            for tech_prereq_id in data["prerequisites"]:
                 tech_info = self.tech_tree.technologies.get(tech_prereq_id)
                 if not tech_info or not tech_info["researched"]:
                    missing_prereqs.append(tech_info['name'] if tech_info else tech_prereq_id)
            if missing_prereqs:
                return f"Error: Cannot start {data['name']}. Missing technology prerequisites: {', '.join(missing_prereqs)}."
            return f"Error: Building '{building_id}' cannot be constructed (Reason unknown, check logs if any)."

        building_data = self.buildings_data[building_id]
        
        project = {
            "id": building_id,
            "name": building_data["name"],
            "remaining_cycles": building_data["build_time_cycles"],
            "cost_per_cycle": building_data["production_cost_per_cycle"]
        }
        self.active_projects.append(project)
        return f"Construction of {building_data['name']} started. It will take {building_data['build_time_cycles']} cycles and cost {project['cost_per_cycle']} Production per cycle."

    def update_construction(self):
        newly_completed_projects = []
        for project_idx, project in enumerate(self.active_projects):
            if self.core_resources["Production"] >= project["cost_per_cycle"]:
                self.core_resources["Production"] -= project["cost_per_cycle"]
                project["remaining_cycles"] -= 1
                print(f"Construction Progress: {project['name']} ({project['remaining_cycles']} cycles left). Used {project['cost_per_cycle']} Production.")

                if project["remaining_cycles"] <= 0:
                    newly_completed_projects.append(project)
            else:
                print(f"Construction Halted: {project['name']} paused. Needs {project['cost_per_cycle']} Production, have {self.core_resources['Production']:.0f}.")
        
        for proj_to_complete in newly_completed_projects:
            self.active_projects.remove(proj_to_complete) # remove by value, works if dicts are unique enough
            b_id = proj_to_complete["id"]
            b_data = self.buildings_data[b_id]

            if b_id not in self.completed_buildings:
                self.completed_buildings[b_id] = {"count": 0, "data": b_data.copy()} # Store a copy of building data
            self.completed_buildings[b_id]["count"] += 1
            
            if b_data.get("apply_effect"): 
                b_data["apply_effect"]()
            
            print(f"\n--- Building Complete: {b_data['name']} ---")
            print(f"Effect Acquired: {b_data['effect_description']}")

# Constants for resource calculations
POPULATION_GROWTH_RATE_BASE = 0.01  # Base growth rate if food is abundant
FOOD_CONSUMPTION_PER_CAPITA = 1.0
# FOOD_PRODUCTION_PER_CAPITA is now DEFAULT_FOOD_PRODUCTION_PER_CAPITA and modified by tech_modifiers
# PRODUCTION_PER_CAPITA is now DEFAULT_PRODUCTION_PER_CAPITA and modified by tech_modifiers
# KNOWLEDGE_PER_CAPITA is now DEFAULT_KNOWLEDGE_PER_CAPITA and modified by tech_modifiers
# CULTURE_PER_CAPITA is now DEFAULT_CULTURE_PER_CAPITA and modified by tech_modifiers
STARVATION_PENALTY_RATIO = 0.1 # Percentage of population lost to starvation if food is 0
MIN_POPULATION = 2

# Stability constants
STABILITY_FOOD_SHORTAGE_THRESHOLD = 0.1 # If food per capita is below this, stability might drop
STABILITY_STARVATION_PENALTY = 5 # Flat penalty to stability if starvation occurs
STABILITY_LOW_THRESHOLD = 40 # Below this, stability tends to decrease
STABILITY_LOW_DRAIN_RATE = 2 # How much stability drops if below STABILITY_LOW_THRESHOLD
STABILITY_HIGH_THRESHOLD = 80 # Above this, stability has positive momentum
STABILITY_HIGH_BOOST_RATE = 1 # How much stability increases if above STABILITY_HIGH_THRESHOLD
STABILITY_FOOD_PENALTY_NO_STARVATION = 2 # Stability penalty if food is zero but no one starved (yet)


def update_stability(food_is_zero, starvation_occurred):
    """
    Calculates and updates stability for the current cycle.
    Returns the change in stability.
    """
    global core_resources
    prev_stability = core_resources["Stability"]
    stability_change = 0

    # 1. Food Shortages
    if starvation_occurred:
        stability_change -= STABILITY_STARVATION_PENALTY
        print(f"Stability impacted by starvation: -{STABILITY_STARVATION_PENALTY}%")
    elif food_is_zero: # Food is zero, but no one starved (e.g. population is already at MIN_POPULATION)
        stability_change -= STABILITY_FOOD_PENALTY_NO_STARVATION
        print(f"Stability impacted by critical food shortage: -{STABILITY_FOOD_PENALTY_NO_STARVATION}%")


    # 2. Low Stability Drain
    if prev_stability < STABILITY_LOW_THRESHOLD:
        stability_change -= STABILITY_LOW_DRAIN_RATE
        print(f"Stability below {STABILITY_LOW_THRESHOLD}%, further decrease: -{STABILITY_LOW_DRAIN_RATE}%")


    # 3. High Stability Boost
    if prev_stability > STABILITY_HIGH_THRESHOLD:
        stability_change += STABILITY_HIGH_BOOST_RATE
        print(f"Stability above {STABILITY_HIGH_THRESHOLD}%, slight boost: +{STABILITY_HIGH_BOOST_RATE}%")

    core_resources["Stability"] += stability_change
    core_resources["Stability"] = max(0, min(100, core_resources["Stability"])) # Clamp between 0 and 100

    # Placeholder for stability-triggered events
    if core_resources["Stability"] < 20:
        print("CRITICAL: Stability is dangerously low! Risk of major negative events.")
    elif core_resources["Stability"] < STABILITY_LOW_THRESHOLD:
        print("Warning: Stability is low.")


    return core_resources["Stability"] - prev_stability


def update_resources():
    """
    Updates all core resources based on game logic for one cycle.
    Prints changes for each resource.
    """
    global core_resources

    prev_pop = core_resources["Population"]
    prev_food = core_resources["Food"]
    prev_prod = core_resources["Production"]
    prev_know = core_resources["Knowledge"]
    prev_cult = core_resources["Culture"]
    # prev_stability = core_resources["Stability"] # Stability is handled by its own function

    starvation_this_cycle = False # Flag to pass to update_stability

    # Apply building flat bonuses first for the cycle
    # These are resources generated directly by buildings, not modifying population output
    core_resources["Food"] += building_modifiers["food_per_cycle_bonus"]
    core_resources["Production"] += building_modifiers["production_per_cycle_bonus"]
    core_resources["Knowledge"] += building_modifiers["knowledge_per_cycle_bonus"]
    core_resources["Culture"] += building_modifiers["culture_per_cycle_bonus"]
    
    # Store amounts generated by population for detailed report
    food_from_pop = 0
    prod_from_pop = 0
    know_from_pop = 0
    cult_from_pop = 0

    # 1. Food Consumption (based on current population)
    food_consumed = core_resources["Population"] * FOOD_CONSUMPTION_PER_CAPITA
    core_resources["Food"] -= food_consumed

    # 2. Population changes
    population_change = 0
    if core_resources["Food"] < 0: # Starvation
        # Population loss proportional to how much food is missing, up to STARVATION_PENALTY_RATIO
        food_deficit_ratio = -core_resources["Food"] / (food_consumed if food_consumed > 0 else 1) # how bad is the deficit
        actual_starvation_penalty = min(STARVATION_PENALTY_RATIO, STARVATION_PENALTY_RATIO * food_deficit_ratio * 2) # Scale penalty with deficit severity
        starvation_loss = int(core_resources["Population"] * actual_starvation_penalty)
        population_change = -starvation_loss
        if starvation_loss > 0:
            starvation_this_cycle = True
        core_resources["Food"] = 0 # Food cannot be negative
        print(f"Warning: Starvation! Population decreased by {starvation_loss} due to food deficit.")
    else: # Growth if there's surplus food
        # Growth is proportional to surplus food, scaled by POPULATION_GROWTH_RATE_BASE
        # Simple model: growth is a percentage of current population, influenced by food surplus
        # Max growth capped by POPULATION_GROWTH_RATE_BASE * 2 (e.g. very abundant food)
        food_surplus_factor = 1 + (core_resources["Food"] / (core_resources["Population"] * FOOD_CONSUMPTION_PER_CAPITA + 1)) # +1 to avoid div by zero
        effective_growth_rate = min(POPULATION_GROWTH_RATE_BASE * food_surplus_factor, POPULATION_GROWTH_RATE_BASE * 2)
        population_growth = int(core_resources["Population"] * effective_growth_rate)
        population_change = population_growth

    core_resources["Population"] += population_change
    if core_resources["Population"] < MIN_POPULATION:
        # Check if it's a game over condition or just clamp
        if prev_pop >= MIN_POPULATION : # Only set to min if it just dropped below
             core_resources["Population"] = MIN_POPULATION
        # If it was already below MIN_POPULATION and drops further, it might be a game over state (handled elsewhere)


    # 3. Food Production by Population (after population changes for the cycle have been determined)
    effective_food_prod_factor = tech_modifiers["food_production_bonus_factor"] * building_modifiers["food_production_bonus_factor"]
    current_food_pop_production_per_capita = DEFAULT_FOOD_PRODUCTION_PER_CAPITA * effective_food_prod_factor
    food_from_pop = core_resources["Population"] * current_food_pop_production_per_capita
    core_resources["Food"] += food_from_pop
    core_resources["Food"] = max(0, core_resources["Food"]) 

    # 4. Production by Population
    current_prod_pop_per_capita = DEFAULT_PRODUCTION_PER_CAPITA * tech_modifiers["production_bonus_factor"] # Buildings add flat, not factor here
    prod_from_pop = core_resources["Population"] * current_prod_pop_per_capita
    core_resources["Production"] += prod_from_pop
    core_resources["Production"] = max(0, core_resources["Production"])

    # 5. Knowledge by Population
    current_know_pop_per_capita = DEFAULT_KNOWLEDGE_PER_CAPITA * tech_modifiers["knowledge_generation_bonus_factor"] # Buildings add flat
    know_from_pop = core_resources["Population"] * current_know_pop_per_capita
    core_resources["Knowledge"] += know_from_pop
    core_resources["Knowledge"] = max(0, core_resources["Knowledge"])

    # 6. Culture by Population
    current_cult_pop_per_capita = DEFAULT_CULTURE_PER_CAPITA * tech_modifiers["culture_generation_bonus_factor"] # Buildings add flat
    cult_from_pop = core_resources["Population"] * current_cult_pop_per_capita
    core_resources["Culture"] += cult_from_pop
    core_resources["Culture"] = max(0, core_resources["Culture"])

    # Stability Update
    stability_change = update_stability(food_is_zero=(core_resources["Food"] == 0), starvation_occurred=starvation_this_cycle) # food_is_zero refers to net food after all production/consumption
    stability_change_str = f"{stability_change:+.0f}%"
    
    # Report changes
    pop_change_str = f"{core_resources['Population'] - prev_pop:+.0f}"
    
    total_food_produced_this_cycle = food_from_pop + building_modifiers["food_per_cycle_bonus"]
    food_tech_bonus_perc = (tech_modifiers["food_production_bonus_factor"] - 1) * 100
    food_bldg_factor_perc = (building_modifiers["food_production_bonus_factor"] - 1) * 100
    food_change_str = f"{core_resources['Food'] - prev_food:+.0f} (Consumed: {food_consumed:.0f}; Produced: {total_food_produced_this_cycle:.0f} [Pop: {food_from_pop:.0f}, Bldgs: {building_modifiers['food_per_cycle_bonus']:.0f}]; Pop Bonus Factors [Tech: {food_tech_bonus_perc:.0f}%, Bldgs: {food_bldg_factor_perc:.0f}%])"

    total_prod_generated_this_cycle = prod_from_pop + building_modifiers["production_per_cycle_bonus"]
    prod_tech_bonus_perc = (tech_modifiers["production_bonus_factor"] - 1) * 100
    prod_change_str = f"{core_resources['Production'] - prev_prod:+.0f} (Generated: {total_prod_generated_this_cycle:.0f} [Pop: {prod_from_pop:.0f}, Bldgs: {building_modifiers['production_per_cycle_bonus']:.0f}]; Pop Bonus Factors [Tech: {prod_tech_bonus_perc:.0f}%])"

    total_know_generated_this_cycle = know_from_pop + building_modifiers["knowledge_per_cycle_bonus"]
    know_tech_bonus_perc = (tech_modifiers["knowledge_generation_bonus_factor"] - 1) * 100
    know_change_str = f"{core_resources['Knowledge'] - prev_know:+.2f} (Generated: {total_know_generated_this_cycle:.2f} [Pop: {know_from_pop:.2f}, Bldgs: {building_modifiers['knowledge_per_cycle_bonus']:.2f}]; Pop Bonus Factors [Tech: {know_tech_bonus_perc:.0f}%])"

    total_cult_generated_this_cycle = cult_from_pop + building_modifiers["culture_per_cycle_bonus"]
    cult_tech_bonus_perc = (tech_modifiers["culture_generation_bonus_factor"] - 1) * 100
    cult_change_str = f"{core_resources['Culture'] - prev_cult:+.2f} (Generated: {total_cult_generated_this_cycle:.2f} [Pop: {cult_from_pop:.2f}, Bldgs: {building_modifiers['culture_per_cycle_bonus']:.2f}]; Pop Bonus Factors [Tech: {cult_tech_bonus_perc:.0f}%])"

    print("\n--- Resource Report ---")
    print(f"Population: {core_resources['Population']:.0f} ({pop_change_str})")
    print(f"Food:       {core_resources['Food']:.0f} ({food_change_str})")
    print(f"Production: {core_resources['Production']:.0f} ({prod_change_str})")
    print(f"Knowledge:  {core_resources['Knowledge']:.2f} ({know_change_str})")
    print(f"Culture:    {core_resources['Culture']:.2f} ({cult_change_str})")
    print(f"Stability:  {core_resources['Stability']:.0f}% ({stability_change_str})")
    print("----------------------")


if __name__ == "__main__":
    game_tech_tree = TechTree(technologies) 
    game_building_manager = BuildingManager(buildings_data, core_resources, game_tech_tree)
    game_event_manager = EventManager(events_data, core_resources, game_tech_tree, game_building_manager, update_stability)

    print("Text Epoch game initialized. (Initial screen will be cleared)")
    # Initial resource print (will be cleared by the first cycle's clear_screen)
    # print("\n--- Initial Resources ---") 
    # for resource, value in core_resources.items():
    #     if resource == "Stability":
    #         print(f"{resource}: {value}%")
    #     elif isinstance(value, float):
    #         print(f"{resource}: {value:.2f}")
    #     else:
    #         print(f"{resource}: {value}")
    # print("----------------------")
    input("Press Enter to begin the first cycle...")
    for resource, value in core_resources.items():
        if resource == "Stability":
            print(f"{resource}: {value}%")
        elif isinstance(value, float):
            print(f"{resource}: {value:.2f}")
        else:
            print(f"{resource}: {value}")
    print("----------------------")

    while True:
        game_state["current_cycle"] += 1
        
        # --- PHASES OF THE GAME CYCLE ---
        # 1. Construction Phase (consumes Production from *last* cycle's income)
        #    Outputs from this phase are immediate prints for now (e.g. "Construction Progress...")
        #    These are helpful for the player to see what just happened due to their prior commands.
        if game_state["current_cycle"] > 1: # No construction updates before first real cycle processing
             print("\n-- Construction Phase --") # This header might be removed if clear_screen is effective
             game_building_manager.update_construction()
        
        # 2. Resource Generation Phase
        update_resources() # This function now contains its own "Resource Report" print block.
                           # The report shows changes based on *this* cycle's calculations.

        # 3. Event Phase
        #    Event occurrences and outcomes are logged by EventManager.log_event()
        #    which prints them immediately.
        if not game_event_manager.pending_decision_event:
            game_event_manager.check_for_events()


        # --- DISPLAY ROUTINE (Clears and redraws screen) ---
        clear_screen()
        print("====== Text Epoch ======")
        print(f"Year: {game_state['current_cycle'] * 5} (Cycle: {game_state['current_cycle']})") # Assuming 5 years per cycle for flavor
        print("========================")

        # Core Resources Overview (Uses the detailed report from update_resources)
        # The update_resources() function already prints a detailed report.
        # For this new UI, we will call a dedicated display function for resources.
        # For now, let's re-iterate core_resources for summary, assuming update_resources still prints its detailed block.
        # Ideally, update_resources would *return* the changes, and then a display function would format it.
        # For this iteration, we'll just re-print the summary from core_resources.
        # The detailed breakdown (like "+50 prod / -30 cons") is already in update_resources's print statements.
        print("\n--- Core Resources ---")
        for res, val in core_resources.items():
            # We need previous values to show change here, which update_resources had.
            # This simple loop won't show changes unless we store them globally or pass them.
            # For now, it will just be current values. The detailed report from update_resources shows changes.
            if isinstance(val, float):
                print(f"{res:<12}: {val:.2f}")
            elif isinstance(val, int) and res == "Stability":
                 print(f"{res:<12}: {val}%")
            else:
                print(f"{res:<12}: {val}")
        print("----------------------")
        # Note: The detailed per-resource change string (e.g., "Food: 120 (+15)...") is printed within update_resources().
        # This section is a quick summary. We could enhance this to show changes if update_resources() returns them.

        print("\n--- Ongoing Activities ---")
        # Current Research: (The current system researches techs instantly)
        # For now, we can list researched techs as a proxy, or leave this for future if research takes time.
        print("Research Focus: (Instantaneous in current model)")
        # Active Construction:
        if game_building_manager.active_projects:
            print("Under Construction:")
            for proj in game_building_manager.active_projects:
                print(f"- {proj['name']}: {proj['remaining_cycles']} cycles left ({proj['cost_per_cycle']} Prod/cycle).")
        else:
            print("No active construction projects.")
        print("------------------------")

        print("\n--- Recent Events (Last 3) ---")
        if game_event_manager.event_log:
            for log_entry in reversed(game_event_manager.event_log[-3:]): 
                print(f"- {log_entry}")
        else:
            print("No significant events logged recently.")
        print("-----------------------------")
        
        # Player Input and Available Actions Section
        # This section will either show a pending decision or the list of available actions + command prompt.

        if game_event_manager.pending_decision_event:
            event = game_event_manager.pending_decision_event
            print("\n--- !!! PENDING DECISION !!! ---")
            print(f"Event: {event['title']}")
            print(event['description'])
            for i, choice in enumerate(event['choices']):
                print(f"  {i+1}. {choice['choice_text']}")
            print("--------------------------------")
            user_choice_input = input(f"Enter your decision (1-{len(event['choices'])}): ").strip()
            resolve_message = game_event_manager.resolve_decision_event(user_choice_input)
            print(resolve_message) 
            if "Error:" not in resolve_message : # If decision was made, pause to let user read
                 input("Press Enter to continue...")
        else:
            print("\n--- Available Actions ---")
            # Available Research:
            print("Research Options:")
            available_techs = game_tech_tree.get_available_research()
            if available_techs:
                for tech_id, data in available_techs.items():
                    print(f"- [{tech_id}] {data['name']} (Cost: {data['cost']} Knowledge). Effect: {data['description']}")
            else:
                print("  No new technologies available for research.")
            
            # Constructible Buildings:
            print("\nConstruction Options:")
            constructible_buildings = game_building_manager.get_constructible_buildings()
            if constructible_buildings:
                for b_id, data in constructible_buildings.items():
                    max_str = f"(Max: {data['max_allowed']})" if data['max_allowed'] != float('inf') else ""
                    print(f"- [{b_id}] {data['name']} {max_str} (Cost: {data['production_cost_total']} Prod over {data['build_time_cycles']} cycles). Effect: {data['description']}")
            else:
                print("  No new buildings available for construction.")
            print("-------------------------")

            # Completed Techs and Buildings (Reference)
            print("\n--- Reference ---")
            print("Researched Technologies:")
            researched_techs = game_tech_tree.get_researched_techs()
            if researched_techs:
                print("  " + ", ".join([data['name'] for data in researched_techs.values()]))
            else:
                print("  None.")
            
            print("\nCompleted Buildings:")
            completed_building_counts = game_building_manager.get_completed_building_counts()
            if completed_building_counts:
                building_strings = []
                for b_id_key, count in completed_building_counts.items():
                    building_info = game_building_manager.buildings_data[b_id_key] 
                    count_str = f" (x{count})" if count > 1 else ""
                    building_strings.append(f"{building_info['name']}{count_str}")
                print("  " + ", ".join(building_strings))
            else:
                print("  None.")
            print("-----------------")


            command_prompt = "\nEnter command ('next', 'research <id>', 'build <id>', 'log', 'quit'): "
            user_input = input(command_prompt).strip().lower()
            
            if user_input == 'quit':
                print("Exiting Text Epoch. Goodbye!")
                break
            elif user_input.startswith("research "):
                game_state["idle_cycles_count"] = 0 # Player action
                try:
                    tech_to_research = user_input.split(" ", 1)[1].strip()
                    research_message = game_tech_tree.research_tech(tech_to_research)
                    print(research_message) 
                    if "Error:" not in research_message: input("Press Enter to continue...")
                except IndexError:
                    print("Invalid research command. Usage: research <tech_id>")
                    input("Press Enter to continue...")
            elif user_input.startswith("build "):
                game_state["idle_cycles_count"] = 0 # Player action
                try:
                    building_to_construct = user_input.split(" ", 1)[1].strip()
                    build_message = game_building_manager.start_project(building_to_construct)
                    print(build_message) 
                    if "Error:" not in build_message: input("Press Enter to continue...")
                except IndexError:
                    print("Invalid build command. Usage: build <building_id>")
                    input("Press Enter to continue...")
            elif user_input == 'log':
                game_state["idle_cycles_count"] = 0 # Player action (viewing log counts)
                clear_screen()
                print("\n--- Full Event Log (Oldest to Newest) ---")
                if game_event_manager.event_log:
                    for entry_idx, entry in enumerate(game_event_manager.event_log):
                        print(f"{entry_idx+1}. {entry}")
                else:
                    print("Event log is empty.")
                print("------------------------------------------")
                input("Press Enter to return to the game...")
            elif user_input == 'next' or user_input == "":
                game_state["idle_cycles_count"] += 1
                print(f"Advancing to next cycle. Idle cycles: {game_state['idle_cycles_count']}")
                # No specific "Press Enter to continue" here, as the screen will refresh.
            else:
                game_state["idle_cycles_count"] = 0 # Unknown command also counts as interaction attempt
                print(f"Unknown command: '{user_input}'. Type 'next', 'research <id>', 'build <id>', 'log', or 'quit'.")
                input("Press Enter to continue...")
        
        # Autonomous Decision Making, if triggered
        if game_state["idle_cycles_count"] >= AUTONOMOUS_DECISION_THRESHOLD:
            if game_event_manager.pending_decision_event:
                print("Autonomous action deferred: Player decision pending.")
            else:
                print("\n--- Autonomous Civilization Focus ---")
                action_taken = make_autonomous_decision(core_resources, game_tech_tree, game_building_manager, game_event_manager)
                if action_taken:
                    game_state["idle_cycles_count"] = 0
                    input("Autonomous action taken. Press Enter to continue...") 
                else:
                    # If AI couldn't find anything to do, it might remain idle or player needs to intervene.
                    # We can let idle_cycles_count continue to rise or reset it. For now, let it be.
                    # This means if AI is stuck, player must take over or it will keep trying.
                    print("Civilization pondered but found no immediate autonomous action to take.")
                    # Potentially increment a different counter for "AI_could_not_act" to prevent log spam if AI is truly stuck.
                    # For now, idle_cycles_count won't reset if AI does nothing. Player command will reset it.

        # Auto-pause at end of cycle if an action or decision resolution didn't already pause.
        # This is tricky because many paths already have an input().
        # The goal is to ensure user sees messages before clear_screen().
        # The "Press Enter to continue..." prompts after specific actions (build, research, log, decision) handle most cases.
        # If 'next' was chosen, or AI ran, the screen redraws. If AI took action, it pauses.
        # If AI did NOT take action, or if it was just 'next', no extra pause here is ideal.
