from .game_state import core_resources, tech_modifiers # Relative import

# Original name in main.py was 'technologies', prompt used 'technologies_data'.
# Sticking to 'technologies' for now as it's used by the class.
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
    },
    # --- New Technologies Start Here ---
    "basic_granaries": {
        "name": "Basic Granaries",
        "description": "Learn to store food more effectively, reducing spoilage. Unlocks 'Improved Granary' building.",
        "cost": 40,
        "prerequisites": ["basic_farming"],
        "effect": lambda: tech_modifiers.update({"food_production_bonus_factor": tech_modifiers.get("food_production_bonus_factor", 1.0) * 1.05}), # Small bonus, main is unlock
        "unlocks_building": "improved_granary" 
    },
    "masonry": {
        "name": "Masonry",
        "description": "Understanding stone working allows for more durable constructions and 5% cheaper buildings. Unlocks 'Stone Walls'.",
        "cost": 70,
        "prerequisites": ["stone_tools"],
        "effect": lambda: tech_modifiers.update({"building_cost_modifier_production": tech_modifiers.get("building_cost_modifier_production", 1.0) * 0.95}),
        "unlocks_building": "stone_walls"
    },
    "animal_husbandry": {
        "name": "Animal Husbandry",
        "description": "Domesticating animals provides a steady source of food and +10% to overall food production.",
        "cost": 60,
        "prerequisites": ["basic_farming"],
        "effect": lambda: tech_modifiers.update({"food_production_bonus_factor": tech_modifiers.get("food_production_bonus_factor", 1.0) * 1.10}),
    },
    "storytelling": {
        "name": "Storytelling & Folklore",
        "description": "Developing traditions of storytelling increases Cultural generation by 15% and adds +1 Stability per cycle.",
        "cost": 50,
        "prerequisites": ["oral_tradition"],
        "effect": lambda: (
            tech_modifiers.update({"culture_generation_bonus_factor": tech_modifiers.get("culture_generation_bonus_factor", 1.0) * 1.15}),
            tech_modifiers.update({"stability_per_cycle_bonus": tech_modifiers.get("stability_per_cycle_bonus", 0.0) + 0.5}) # Reduced from +1 to +0.5 for balance
        )
    },
    "basic_herbalism": {
        "name": "Basic Herbalism",
        "description": "Understanding medicinal properties of plants slightly improves population growth (+5%) and stability (+0.5/cycle).",
        "cost": 45,
        "prerequisites": [],
        "effect": lambda: (
            tech_modifiers.update({"population_growth_modifier": tech_modifiers.get("population_growth_modifier", 1.0) * 1.05}),
            tech_modifiers.update({"stability_per_cycle_bonus": tech_modifiers.get("stability_per_cycle_bonus", 0.0) + 0.5})
        )
    },
    "specialized_tools": {
        "name": "Specialized Tools",
        "description": "Developing tools for specific tasks increases Production efficiency by an additional 15%.",
        "cost": 100,
        "prerequisites": ["stone_tools", "masonry"], # Example of multiple prereqs
        "effect": lambda: tech_modifiers.update({"production_bonus_factor": tech_modifiers.get("production_bonus_factor", 1.0) * 1.15}),
    },
    "calendrics": {
        "name": "Calendrics",
        "description": "Observing celestial cycles allows for better planning of agricultural activities, boosting food production by 10%. Improves research speed by 5%.",
        "cost": 80,
        "prerequisites": ["basic_farming", "oral_tradition"],
        "effect": lambda: (
            tech_modifiers.update({"food_production_bonus_factor": tech_modifiers.get("food_production_bonus_factor", 1.0) * 1.10}),
            tech_modifiers.update({"research_speed_modifier": tech_modifiers.get("research_speed_modifier", 1.0) * 1.05})
        )
    },
    "trade_routes": {
        "name": "Basic Trade Routes",
        "description": "Establishing rudimentary trade with nearby settlements slightly boosts Production (+5%) and Culture (+5%).",
        "cost": 90,
        "prerequisites": ["animal_husbandry"], # Need pack animals or similar
        "effect": lambda: (
            tech_modifiers.update({"production_bonus_factor": tech_modifiers.get("production_bonus_factor", 1.0) * 1.05}),
            tech_modifiers.update({"culture_generation_bonus_factor": tech_modifiers.get("culture_generation_bonus_factor", 1.0) * 1.05})
        ),
        "unlocks_policy": "establish_trade_posts" # Placeholder
    },
    "early_governance": {
        "name": "Early Governance",
        "description": "Basic forms of leadership and dispute resolution improve stability (+1/cycle). Unlocks 'Tribal Council' building.",
        "cost": 120,
        "prerequisites": ["storytelling", "early_writing"],
        "effect": lambda: tech_modifiers.update({"stability_per_cycle_bonus": tech_modifiers.get("stability_per_cycle_bonus", 0.0) + 1.0}),
        "unlocks_building": "tribal_council" # Placeholder
    },
    "advanced_writing": {
        "name": "Advanced Writing Systems",
        "description": "More complex writing systems improve research speed by 10% and knowledge generation by 15%.",
        "cost": 150,
        "prerequisites": ["early_writing", "calendrics"],
        "effect": lambda: (
            tech_modifiers.update({"research_speed_modifier": tech_modifiers.get("research_speed_modifier", 1.0) * 1.10}),
            tech_modifiers.update({"knowledge_generation_bonus_factor": tech_modifiers.get("knowledge_generation_bonus_factor", 1.0) * 1.15})
        )
    },
     "crop_rotation": {
        "name": "Crop Rotation",
        "description": "Improves soil fertility and food production by another 15%.",
        "cost": 130,
        "prerequisites": ["basic_farming", "calendrics"],
        "effect": lambda: tech_modifiers.update({"food_production_bonus_factor": tech_modifiers.get("food_production_bonus_factor", 1.0) * 1.15}),
    },
    "construction_techniques": {
        "name": "Construction Techniques",
        "description": "Improved methods make all future building projects 5% faster (effectively cheaper in total prod).",
        "cost": 110,
        "prerequisites": ["masonry", "specialized_tools"],
        "effect": lambda: tech_modifiers.update({"building_cost_modifier_production": tech_modifiers.get("building_cost_modifier_production", 1.0) * 0.95}),
    },
     "community_ethics": {
        "name": "Community Ethics",
        "description": "Shared values and ethics lead to a more harmonious society, increasing base stability by +1.5 per cycle.",
        "cost": 75,
        "prerequisites": ["storytelling"],
        "effect": lambda: tech_modifiers.update({"stability_per_cycle_bonus": tech_modifiers.get("stability_per_cycle_bonus", 0.0) + 1.5}),
    }
    # --- End of New Technologies ---
}

class TechTree:
    def __init__(self, technologies_data): # Parameter name from original, but uses global 'technologies'
        self.technologies = technologies_data # Should ideally use the passed in data

    def get_researched_techs(self):
        return {tech_id: data for tech_id, data in self.technologies.items() if data["researched"]}

    def get_available_research(self):
        available = {}
        for tech_id, data in self.technologies.items():
            if not data["researched"]:
                prerequisites_met = all(
                    # Ensure the prerequisite ID exists before checking 'researched'
                    self.technologies.get(prereq_id, {}).get("researched", False)
                    for prereq_id in data["prerequisites"]
                )
                if prerequisites_met:
                    available[tech_id] = data
        return available

    def research_tech(self, tech_id):
        # core_resources and tech_modifiers are imported from game_state
        available_techs = self.get_available_research()

        if tech_id not in available_techs:
            tech_data_for_name = self.technologies.get(tech_id)
            name = tech_data_for_name['name'] if tech_data_for_name else tech_id
            
            # Check prerequisite status for a more informative message
            if tech_data_for_name:
                missing_prereqs = [self.technologies.get(pr_id,{}).get('name', pr_id) for pr_id in tech_data_for_name.get("prerequisites", []) if not self.technologies.get(pr_id, {}).get("researched")]
                if missing_prereqs:
                    return f"Error: Cannot research '{name}'. Missing prerequisites: {', '.join(missing_prereqs)}."
                if tech_data_for_name.get("researched"):
                    return f"Error: Technology '{name}' has already been researched."

            return f"Error: Technology '{name}' is not available or does not exist."


        tech_data = self.technologies[tech_id]
        if core_resources["Knowledge"] < tech_data["cost"]:
            return f"Error: Not enough Knowledge to research {tech_data['name']}. Need {tech_data['cost']}, have {core_resources['Knowledge']:.0f}."

        core_resources["Knowledge"] -= tech_data["cost"]
        tech_data["researched"] = True # Modifies the global 'technologies' dict state
        if tech_data["effect"]:
            tech_data["effect"]() # Applies effect to global 'tech_modifiers'
        
        # UI Leak - this print should be handled by the UI module based on return value
        message = f"Technology Researched: {tech_data['name']}! Effect: {tech_data['description']}. Knowledge spent: {tech_data['cost']}. Remaining Knowledge: {core_resources['Knowledge']:.0f}"
        print(f"\n{message}") 
        return f"Successfully researched {tech_data['name']}."
