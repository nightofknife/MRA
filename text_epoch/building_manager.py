from .game_state import core_resources, building_modifiers # Relative import

buildings_data = {
    "granary": {
        "name": "Granary",
        "description": "Provides a steady supply of Food per cycle.",
        "production_cost_total": 50,
        "build_time_cycles": 5, 
        "prerequisites": [],
        "max_allowed": 2,
        "effect_description": "+10 Food/cycle per Granary",
        "apply_effect": lambda bm_ref, count: bm_ref.update({"food_per_cycle_bonus": bm_ref.get("food_per_cycle_bonus", 0) + 10 * count}),
    },
    "workshop": {
        "name": "Workshop",
        "description": "Generates Production points per cycle.",
        "production_cost_total": 80,
        "build_time_cycles": 8, 
        "prerequisites": [],
        "max_allowed": float('inf'), 
        "effect_description": "+5 Production/cycle per Workshop",
        "apply_effect": lambda bm_ref, count: bm_ref.update({"production_per_cycle_bonus": bm_ref.get("production_per_cycle_bonus", 0) + 5 * count}),
    },
    "communal_fields": { # This is a factor, so it should apply once if count >=1, or stack multiplicatively carefully
        "name": "Communal Fields",
        "description": "Increases Food production efficiency from population by 10%.",
        "production_cost_total": 100,
        "build_time_cycles": 10, 
        "prerequisites": ["basic_farming"], 
        "max_allowed": 1, # Max 1, so count will be 1 if present
        "effect_description": "+10% Food production efficiency from population",
        # For multiplicative stacking, if max_allowed > 1: (base_value * (modifier_per_building ** count))
        # But since it's max 1, it's simpler: if count > 0, apply 1.1, else 1.0.
        # The recalculate_all_building_effects will handle this by resetting to 1.0 first.
        "apply_effect": lambda bm_ref, count: bm_ref.update({"food_production_bonus_factor": bm_ref.get("food_production_bonus_factor", 1.0) * (1.1 if count > 0 else 1.0)}),
    },
    # --- New Buildings Start Here ---
    "improved_granary": {
        "name": "Improved Granary",
        "description": "Advanced storage reducing spoilage and increasing capacity.",
        "production_cost_total": 120,
        "build_time_cycles": 8,
        "prerequisites": ["basic_granaries"], # Tech prerequisite
        "max_allowed": 2,
        "effect_description": "+20 Food/cycle, +5% Food Production Factor (per building)",
        "apply_effect": lambda bm_ref, count: (
            bm_ref.update({"food_per_cycle_bonus": bm_ref.get("food_per_cycle_bonus", 0) + 20 * count}),
            # For multiplicative stacking: (base_value * (modifier_per_building ** count))
            # Here, if base is 1.0, it becomes 1.0 * (1.05^count).
            # This is handled by recalculate_all_building_effects resetting factor to 1.0 then applying.
            bm_ref.update({"food_production_bonus_factor": bm_ref.get("food_production_bonus_factor", 1.0) * (1.05**count)}) 
        )
    },
    "shrine": {
        "name": "Shrine",
        "description": "A dedicated space for rituals, bolstering cultural identity and societal stability.",
        "production_cost_total": 70,
        "build_time_cycles": 6,
        "prerequisites": ["storytelling"], # Tech prerequisite
        "max_allowed": 3,
        "effect_description": "+3 Culture/cycle, +0.2 Stability/cycle (per shrine)",
        "apply_effect": lambda bm_ref, count: (
            bm_ref.update({"culture_per_cycle_bonus": bm_ref.get("culture_per_cycle_bonus", 0) + 3 * count}),
            bm_ref.update({"stability_per_cycle_bonus": bm_ref.get("stability_per_cycle_bonus", 0) + 0.2 * count})
        )
    },
    "training_ground": {
        "name": "Training Ground",
        "description": "Basic military training improves discipline and offers a small stability boost.",
        "production_cost_total": 90,
        "build_time_cycles": 7,
        "prerequisites": [], 
        "max_allowed": 1,
        "effect_description": "+0.5 Stability/cycle. (Future: unlocks basic military units)",
        "apply_effect": lambda bm_ref, count: bm_ref.update({"stability_per_cycle_bonus": bm_ref.get("stability_per_cycle_bonus", 0) + 0.5 * count})
    },
    "stone_walls": {
        "name": "Stone Walls",
        "description": "Defensive walls providing security and a significant stability boost.",
        "production_cost_total": 200,
        "build_time_cycles": 15,
        "prerequisites": ["masonry"], # Tech prerequisite
        "max_allowed": 1, # Usually city walls are a single project
        "effect_description": "+2 Stability/cycle. (Future: defense modifier)",
        "apply_effect": lambda bm_ref, count: bm_ref.update({"stability_per_cycle_bonus": bm_ref.get("stability_per_cycle_bonus", 0) + 2.0 * count})
    },
    "library": {
        "name": "Library",
        "description": "A collection of scrolls and tablets, boosting Knowledge generation and research speed.",
        "production_cost_total": 150,
        "build_time_cycles": 10,
        "prerequisites": ["advanced_writing"], # Tech prerequisite
        "max_allowed": 1,
        "effect_description": "+10 Knowledge/cycle, +5% Knowledge Factor, +5% Research Speed Factor",
        "apply_effect": lambda bm_ref, count: (
            bm_ref.update({"knowledge_per_cycle_bonus": bm_ref.get("knowledge_per_cycle_bonus", 0) + 10 * count}),
            bm_ref.update({"knowledge_bonus_factor": bm_ref.get("knowledge_bonus_factor", 1.0) * (1.05**count)}),
            # Research speed from tech_modifiers, so this building's effect needs to be applied there.
            # This shows a limitation: building effects directly on tech_modifiers isn't standard.
            # For now, I'll assume research_speed_modifier is a direct effect on knowledge points for research tasks,
            # so +5% Knowledge Factor is a good proxy here. Or, it could add to a specific modifier if we had one.
            # Let's simplify: library boosts knowledge_bonus_factor primarily.
        )
    },
    "market_square": {
        "name": "Market Square",
        "description": "A central place for trade, boosting Production from population slightly.",
        "production_cost_total": 130,
        "build_time_cycles": 9,
        "prerequisites": ["trade_routes"], # Tech prerequisite
        "max_allowed": 1,
        "effect_description": "+5% Production Factor from population.",
        "apply_effect": lambda bm_ref, count: bm_ref.update({"production_bonus_factor": bm_ref.get("production_bonus_factor", 1.0) * (1.05**count)})
    },
    "basic_housing": {
        "name": "Basic Housing",
        "description": "Organized construction of simple dwellings. Increases max population and slightly improves growth.",
        "production_cost_total": 60,
        "build_time_cycles": 5,
        "prerequisites": [],
        "max_allowed": float('inf'), # Allow many
        "effect_description": "+10 Max Population, +2% Housing Quality (per unit)",
        "apply_effect": lambda bm_ref, count: (
             bm_ref.update({"max_population_bonus": bm_ref.get("max_population_bonus", 0) + 10 * count}),
             bm_ref.update({"housing_quality_modifier": bm_ref.get("housing_quality_modifier", 1.0) * (1.02**count)})
        )
    }
    # --- End of New Buildings ---
}

# Calculate production_cost_per_cycle for all buildings dynamically
# This loop must be AFTER the full buildings_data definition
for building_id_key, building_info_data in buildings_data.items():
    if building_info_data["build_time_cycles"] > 0:
        building_info_data["production_cost_per_cycle"] = round(building_info_data["production_cost_total"] / building_info_data["build_time_cycles"])
    else: 
        building_info_data["production_cost_per_cycle"] = building_info_data["production_cost_total"]


class BuildingManager:
    def __init__(self, buildings_config_dict, tech_tree_ref_obj): # core_resources is imported
        self.buildings_data = buildings_config_dict 
        self.tech_tree = tech_tree_ref_obj
        self.active_projects = [] 
        self.completed_buildings = {} # Stores {"granary": {"count": 2, "data": buildings_data["granary"]}, ...}

    def recalculate_all_building_effects(self):
        """Resets building_modifiers and re-applies effects from all completed buildings."""
        # Reset all relevant building_modifiers to their base values (0 for additive, 1.0 for multiplicative)
        building_modifiers.update({
            "food_per_cycle_bonus": 0, "production_per_cycle_bonus": 0,
            "knowledge_per_cycle_bonus": 0, "culture_per_cycle_bonus": 0,
            "stability_per_cycle_bonus": 0.0,
            "food_production_bonus_factor": 1.0, "production_bonus_factor": 1.0,
            "knowledge_bonus_factor": 1.0, "culture_bonus_factor": 1.0,
            "max_population_bonus": 0, "housing_quality_modifier": 1.0,
        })

        for building_id, building_info in self.completed_buildings.items():
            count = building_info["count"]
            building_definition = building_info["data"] # This is a reference to the entry in buildings_data
            
            if "apply_effect" in building_definition and callable(building_definition["apply_effect"]):
                # Pass the building_modifiers dict and the count of this specific building
                building_definition["apply_effect"](building_modifiers, count)

    def get_completed_building_counts(self):
        return {b_id: info["count"] for b_id, info in self.completed_buildings.items()}

    def get_constructible_buildings(self):
        constructible = {}
        current_completed_counts = self.get_completed_building_counts()

        for building_id, data in self.buildings_data.items(): # Uses self.buildings_data
            if current_completed_counts.get(building_id, 0) >= data["max_allowed"]:
                continue

            prerequisites_met = True
            for tech_prereq_id in data["prerequisites"]:
                # Accessing tech_tree object's technologies attribute
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
            return f"Error: Building '{building_id}' cannot be constructed (Reason unknown)."

        building_data = self.buildings_data[building_id]
        
        project = {
            "id": building_id,
            "name": building_data["name"],
            "remaining_cycles": building_data["build_time_cycles"],
            "cost_per_cycle": building_data["production_cost_per_cycle"]
        }
        self.active_projects.append(project)
        return f"Construction of {building_data['name']} started. It will take {building_data['build_time_cycles']} cycles and cost {project['cost_per_cycle']} Production per cycle."

    def update_construction(self): # core_resources is imported
        newly_completed_projects = []
        for project_idx, project in enumerate(self.active_projects): # Use enumerate if planning to modify list by index
            if core_resources["Production"] >= project["cost_per_cycle"]:
                core_resources["Production"] -= project["cost_per_cycle"]
                project["remaining_cycles"] -= 1
                # UI Leak: print statement
                print(f"Construction Progress: {project['name']} ({project['remaining_cycles']} cycles left). Used {project['cost_per_cycle']} Production.")

                if project["remaining_cycles"] <= 0:
                    newly_completed_projects.append(project)
            else:
                # UI Leak: print statement
                print(f"Construction Halted: {project['name']} paused. Needs {project['cost_per_cycle']} Production, have {core_resources['Production']:.0f}.")
        
        for proj_to_complete in newly_completed_projects:
            self.active_projects.remove(proj_to_complete) 
            b_id = proj_to_complete["id"]
            b_data = self.buildings_data[b_id]

            if b_id not in self.completed_buildings:
                self.completed_buildings[b_id] = {"count": 0, "data": b_data} # Store reference to master data
            self.completed_buildings[b_id]["count"] += 1
            
            self.recalculate_all_building_effects() # Recalculate all effects now that a new building is added
            
            # UI Leak: print statement
            print(f"\n--- Building Complete: {b_data['name']} (Total: {self.completed_buildings[b_id]['count']}) ---")
            print(f"Effect: {b_data['effect_description']}")
            # The specific impact of this completion is now part of the overall recalculation
            # and will be reflected in the next cycle's resource report.
