import random # May be needed for some policy effects

# Import game state components that policies might affect or depend on
from .game_state import core_resources, tech_modifiers, building_modifiers, game_state_vars

# It's cleaner if policies modify their own dedicated modifier dictionary
policy_modifiers = {
    "culture_per_cycle_policy_bonus": 0, # Example for Festival of Abundance
    "production_bonus_factor_policy": 1.0, # Example for Forced Labor
    "population_growth_modifier_policy": 1.0, # Example for Forced Labor
    "knowledge_generation_bonus_factor_policy": 1.0, # Example for Knowledge Sharing
    "culture_per_cycle_policy_cost": 0, # Example for Knowledge Sharing ongoing cost
    "stability_policy_bonus": 0, # Flat stability bonus from policies
}

# --- Policy Definitions ---
policies_data = {
    "festival_abundance": {
        "policy_id": "festival_abundance",
        "name": "Festival of Abundance",
        "description": "Host a grand festival to celebrate recent successes, boosting morale and cultural cohesion for a time.",
        "cost_to_enact": {"Food": 50, "Culture": 20},
        "prerequisites": {"min_population": 50, "min_stability": 40},
        "duration": 5, # cycles
        "type": "timed_active", # one_time_enactment might be better if effects are instant + a timed modifier
        "effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            pol_mods_ref.update({"stability_policy_bonus": pol_mods_ref.get("stability_policy_bonus", 0) + 10}),
            pol_mods_ref.update({"culture_per_cycle_policy_bonus": pol_mods_ref.get("culture_per_cycle_policy_bonus", 0) + int(core_res_ref.get("Population",0) * 0.05)}) # +5% of pop as culture
            # Note: stability_policy_bonus needs to be applied by update_stability or similar
        ),
        "remove_effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            pol_mods_ref.update({"stability_policy_bonus": pol_mods_ref.get("stability_policy_bonus", 0) - 10}),
            pol_mods_ref.update({"culture_per_cycle_policy_bonus": pol_mods_ref.get("culture_per_cycle_policy_bonus", 0) - int(core_res_ref.get("Population",0) * 0.05)})
        ),
        "cooldown": 15
    },
    "forced_labor_quotas": {
        "policy_id": "forced_labor_quotas",
        "name": "Forced Labor Quotas",
        "description": "Implement strict work quotas to maximize production output, at the cost of public happiness and growth.",
        "cost_to_enact": {"Stability": 5}, # Direct cost to stability
        "prerequisites": {"tech": ["specialized_tools"]}, # Placeholder, assumes "specialized_tools" exists
        "duration": 10,
        "type": "timed_active",
        "effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            pol_mods_ref.update({"production_bonus_factor_policy": pol_mods_ref.get("production_bonus_factor_policy", 1.0) * 1.15}),
            pol_mods_ref.update({"population_growth_modifier_policy": pol_mods_ref.get("population_growth_modifier_policy", 1.0) * 0.95})
        ),
        "remove_effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            pol_mods_ref.update({"production_bonus_factor_policy": pol_mods_ref.get("production_bonus_factor_policy", 1.0) / 1.15}),
            pol_mods_ref.update({"population_growth_modifier_policy": pol_mods_ref.get("population_growth_modifier_policy", 1.0) / 0.95})
        ),
        "cooldown": 20
    },
    "knowledge_sharing_initiative": {
        "policy_id": "knowledge_sharing_initiative",
        "name": "Knowledge Sharing Initiative",
        "description": "Promote the open exchange of ideas and learning, boosting research at a small cultural cost.",
        # Ongoing cost handled by effects directly modifying resource rates or a specific modifier
        "cost_to_enact": {}, 
        "prerequisites": {"tech": ["advanced_writing"]},
        "duration": None, # Toggleable
        "type": "toggleable_active",
        "effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            pol_mods_ref.update({"knowledge_generation_bonus_factor_policy": pol_mods_ref.get("knowledge_generation_bonus_factor_policy", 1.0) * 1.10}),
            pol_mods_ref.update({"culture_per_cycle_policy_cost": pol_mods_ref.get("culture_per_cycle_policy_cost", 0) + 1}) # Cost 1 culture per cycle
        ),
        "remove_effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            pol_mods_ref.update({"knowledge_generation_bonus_factor_policy": pol_mods_ref.get("knowledge_generation_bonus_factor_policy", 1.0) / 1.10}),
            pol_mods_ref.update({"culture_per_cycle_policy_cost": pol_mods_ref.get("culture_per_cycle_policy_cost", 0) - 1})
        ),
        "cooldown": 5 # Cooldown after toggling off
    },
    "water_management_edict": {
        "policy_id": "water_management_edict",
        "name": "Water Management Edict",
        "description": "Invest in irrigation and water distribution, boosting food production from farms.",
        "cost_to_enact": {"Production": 75},
        "prerequisites": {"tech": ["basic_farming"], "buildings_completed": {"communal_fields": 1}}, # Example: requires 1 communal_fields
        "duration": None, # Permanent once enacted
        "type": "one_time_enactment", # Passive permanent bonus
        "effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            # This policy might affect building_modifiers if it targets specific building outputs,
            # or tech_modifiers if it's a general bonus. Let's make it a general food prod bonus.
            t_mods_ref.update({"food_production_bonus_factor": t_mods_ref.get("food_production_bonus_factor", 1.0) * 1.05})
        ),
        # No remove_effects for one_time_enactment typically, unless it's replaced by another policy.
        "cooldown": None
    },
    "elder_council_support": {
        "policy_id": "elder_council_support",
        "name": "Elder Council Support",
        "description": "Provide additional resources and recognition to the council of elders, improving stability.",
        "cost_to_enact": {"Culture": 25, "Production": 25},
        "prerequisites": {"tech": ["early_governance"]},
        "duration": 10, 
        "type": "timed_active",
        "effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            pol_mods_ref.update({"stability_policy_bonus": pol_mods_ref.get("stability_policy_bonus", 0) + 2})
        ),
        "remove_effects": lambda gs_vars_ref, t_mods_ref, b_mods_ref, core_res_ref, pol_mods_ref: (
            pol_mods_ref.update({"stability_policy_bonus": pol_mods_ref.get("stability_policy_bonus", 0) - 2})
        ),
        "cooldown": 15
    }
}


class PolicyManager:
    def __init__(self, policies_data_ref, game_state_module_ref, tech_tree_ref_obj, building_manager_ref_obj, event_manager_ref_obj):
        self.policies_definitions = policies_data_ref # This is the policies_data dict from this module
        self.game_state_module = game_state_module_ref # To access core_resources, game_state_vars, modifiers
        self.tech_tree = tech_tree_ref_obj
        self.building_manager = building_manager_ref_obj
        self.event_manager = event_manager_ref_obj # For logging

        self.active_policies = {} # E.g., {"policy_id": {"remaining_duration": 10, "enacted_cycle": 150, "type": "timed_active"}}
        self.policies_on_cooldown = {} # E.g., {"policy_id": ends_on_cycle_X}
        
        # Initialize policy_modifiers in game_state if not already present (defensive)
        if not hasattr(self.game_state_module, 'policy_modifiers'):
            self.game_state_module.policy_modifiers = policy_modifiers.copy()
        else: # Merge with existing to ensure all keys are present
            for k,v in policy_modifiers.items():
                self.game_state_module.policy_modifiers.setdefault(k,v)


    def get_enactable_policies(self):
        enactable = {}
        current_cycle = self.game_state_module.game_state_vars["current_cycle"]

        for policy_id, policy in self.policies_definitions.items():
            if policy_id in self.active_policies:
                continue # Already active
            if policy_id in self.policies_on_cooldown and self.policies_on_cooldown[policy_id] > current_cycle:
                continue # On cooldown

            # Check prerequisites
            prereqs_met = True
            # Tech prerequisites
            for tech_req in policy.get("prerequisites", {}).get("tech", []):
                if not self.tech_tree.technologies.get(tech_req, {}).get("researched", False):
                    prereqs_met = False
                    break
            if not prereqs_met: continue

            # Resource prerequisites (for enacting)
            for resource, amount in policy.get("cost_to_enact", {}).items():
                if resource == "Stability": # Special case for stability cost
                    if self.game_state_module.core_resources.get(resource, 0) < amount:
                        prereqs_met = False; break
                elif self.game_state_module.core_resources.get(resource, 0) < amount:
                    prereqs_met = False; break
            if not prereqs_met: continue
            
            # Min game state prerequisites (e.g. stability, population)
            if self.game_state_module.core_resources.get("Stability",0) < policy.get("prerequisites",{}).get("min_stability",0):
                prereqs_met = False
            if self.game_state_module.core_resources.get("Population",0) < policy.get("prerequisites",{}).get("min_population",0):
                prereqs_met = False
            
            # Building prerequisites
            for building_req_id, count_req in policy.get("prerequisites", {}).get("buildings_completed", {}).items():
                if self.building_manager.get_completed_building_counts().get(building_req_id, 0) < count_req:
                    prereqs_met = False; break
            if not prereqs_met: continue


            if prereqs_met:
                enactable[policy_id] = policy
        return enactable

    def enact_policy(self, policy_id):
        enactable_policies = self.get_enactable_policies()
        if policy_id not in enactable_policies:
            # Try to find out why for a better message
            if policy_id not in self.policies_definitions: return f"Error: Policy '{policy_id}' does not exist."
            if policy_id in self.active_policies: return f"Error: Policy '{self.policies_definitions[policy_id]['name']}' is already active."
            if policy_id in self.policies_on_cooldown and self.policies_on_cooldown[policy_id] > self.game_state_module.game_state_vars["current_cycle"]:
                return f"Error: Policy '{self.policies_definitions[policy_id]['name']}' is on cooldown until cycle {self.policies_on_cooldown[policy_id]}."
            # Add more specific prerequisite failure messages here if desired
            return f"Error: Cannot enact '{self.policies_definitions[policy_id]['name']}'. Prerequisites not met or insufficient resources."

        policy = self.policies_definitions[policy_id]

        # Deduct enactment costs
        for resource, amount in policy.get("cost_to_enact", {}).items():
            self.game_state_module.core_resources[resource] -= amount
        
        # Apply effects
        if "effects" in policy and callable(policy["effects"]):
            policy["effects"](
                self.game_state_module.game_state_vars, 
                self.game_state_module.tech_modifiers, 
                self.game_state_module.building_modifiers, 
                self.game_state_module.core_resources,
                self.game_state_module.policy_modifiers # Pass the policy_modifiers dict
            )

        self.active_policies[policy_id] = {
            "remaining_duration": policy.get("duration"), # None for permanent/toggleable
            "enacted_cycle": self.game_state_module.game_state_vars["current_cycle"],
            "type": policy["type"]
        }
        
        self.event_manager.log_event(f"Policy Enacted: '{policy['name']}'. {policy['description']}", is_major=True)
        return f"Policy '{policy['name']}' enacted."

    def revoke_policy(self, policy_id):
        if policy_id not in self.active_policies:
            return f"Error: Policy '{self.policies_definitions.get(policy_id, {}).get('name', policy_id)}' is not active."
        
        policy_def = self.policies_definitions[policy_id]
        active_policy_info = self.active_policies[policy_id]

        if active_policy_info["type"] != "toggleable_active":
            return f"Error: Policy '{policy_def['name']}' is not toggleable and cannot be revoked manually."

        if "remove_effects" in policy_def and callable(policy_def["remove_effects"]):
            policy_def["remove_effects"](
                self.game_state_module.game_state_vars, 
                self.game_state_module.tech_modifiers, 
                self.game_state_module.building_modifiers, 
                self.game_state_module.core_resources,
                self.game_state_module.policy_modifiers
            )
        
        del self.active_policies[policy_id]
        if policy_def.get("cooldown"):
            self.policies_on_cooldown[policy_id] = self.game_state_module.game_state_vars["current_cycle"] + policy_def["cooldown"]
        
        self.event_manager.log_event(f"Policy Revoked: '{policy_def['name']}'.", is_major=True)
        return f"Policy '{policy_def['name']}' revoked."

    def update_active_policies(self):
        current_cycle = self.game_state_module.game_state_vars["current_cycle"]
        expired_this_cycle = []

        # Update durations and check for expirations
        for policy_id, policy_info in self.active_policies.items():
            if policy_info["type"] == "timed_active" and policy_info["remaining_duration"] is not None:
                policy_info["remaining_duration"] -= 1
                if policy_info["remaining_duration"] <= 0:
                    expired_this_cycle.append(policy_id)
        
        # Process expired policies
        for policy_id in expired_this_cycle:
            policy_def = self.policies_definitions[policy_id]
            self.event_manager.log_event(f"Policy Expired: '{policy_def['name']}'.", is_major=True)
            if "remove_effects" in policy_def and callable(policy_def["remove_effects"]):
                policy_def["remove_effects"](
                    self.game_state_module.game_state_vars, 
                    self.game_state_module.tech_modifiers, 
                    self.game_state_module.building_modifiers, 
                    self.game_state_module.core_resources,
                    self.game_state_module.policy_modifiers
                )
            del self.active_policies[policy_id]
            if policy_def.get("cooldown"):
                self.policies_on_cooldown[policy_id] = current_cycle + policy_def["cooldown"]

        # Clear ended cooldowns
        ended_cooldowns = [pid for pid, end_cycle in self.policies_on_cooldown.items() if current_cycle >= end_cycle]
        for pid in ended_cooldowns:
            del self.policies_on_cooldown[pid]
            self.event_manager.log_event(f"Policy '{self.policies_definitions[pid]['name']}' is now off cooldown.", is_major=False)

        # Apply ongoing effects of active policies (e.g. per-cycle costs)
        # This is better handled by having update_resources check policy_modifiers
        # For "Knowledge Sharing Initiative" culture cost:
        # self.game_state_module.core_resources["Culture"] -= self.game_state_module.policy_modifiers.get("culture_per_cycle_policy_cost",0)
        # This direct modification is okay if policies are few and simple.
        # For more complex ongoing effects, integrating into update_resources via policy_modifiers is better.
        # The current lambdas for knowledge sharing already set a value in policy_modifiers.
        # update_resources should be modified to use it.
        pass # No direct per-cycle application here; handled by modifiers or specific calls in main loop if needed.
