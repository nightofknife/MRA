import random
from .game_state import core_resources, update_stability # Relative import

# --- Event Definitions ---
# events_data will be passed to the EventManager instance,
# but we define it here for modularity as per the prompt.
# The EventManager class itself won't directly use this global events_data,
# but expects a similar structure from its 'events_config' parameter.
# To make this runnable directly if this module was the main one (for testing),
# one might assign events_data to a variable inside the class or pass it explicitly.
# For this refactor, it's assumed main.py will pass the global events_data from this module.

events_data = {
    "bumper_harvest": {
        "event_id": "bumper_harvest",
        "type": "random",
        "title": "Unexpected Bumper Harvest",
        "description": "Favorable weather and unexpected fertility have led to an unusually large harvest.",
        "probability": 0.05,
        "trigger_conditions": lambda cr, techs: True,
        "effects": lambda event_manager_ref: ( # Pass event_manager_ref for logging
            core_resources.update({"Food": core_resources["Food"] + 50 + int(core_resources["Population"] * 0.5)}),
            core_resources.update({"Stability": min(100, core_resources["Stability"] + 5)}),
            event_manager_ref.log_event("Outcome: Food increased significantly (+50, +0.5/Pop). Stability improved (+5%).")
        )
    },
    "rodent_infestation": {
        "event_id": "rodent_infestation",
        "type": "random",
        "title": "Rodent Infestation",
        "description": "Rodents have infested food stores, leading to significant losses.",
        "probability": 0.03,
        "trigger_conditions": lambda cr, techs: cr["Food"] > 20,
        "effects": lambda event_manager_ref: (
            core_resources.update({"Food": max(0, core_resources["Food"] - int(core_resources["Food"] * 0.15))}),
            core_resources.update({"Stability": max(0, core_resources["Stability"] - 3)}),
            event_manager_ref.log_event("Outcome: Food decreased by 15%. Stability slightly worsened (-3%).")
        )
    },
    "strange_lights": {
        "event_id": "strange_lights",
        "type": "decision",
        "title": "Strange Lights in the Sky",
        "description": "Elderly members of the tribe speak of strange, fleeting lights observed in the night sky. Some are fearful, others curious.",
        "probability": 0.02,
        "trigger_conditions": lambda cr, techs: cr["Knowledge"] > 30,
        "player_choices": [
            {
                "choice_text": "Dismiss them as ill omens. Focus on earthly matters and appease the spirits with work.",
                "choice_effects": lambda event_manager_ref: (
                    core_resources.update({"Culture": core_resources["Culture"] + 10}),
                    core_resources.update({"Knowledge": max(0, core_resources["Knowledge"] - 5)}),
                    core_resources.update({"Stability": min(100, core_resources["Stability"] + 2)}),
                    event_manager_ref.log_event("Choice Outcome: Culture +10, Knowledge -5, Stability +2.")
                )
            },
            {
                "choice_text": "Order the wisest to observe and interpret them. Knowledge is paramount.",
                "choice_effects": lambda event_manager_ref: (
                    core_resources.update({"Knowledge": core_resources["Knowledge"] + 20}),
                    core_resources.update({"Culture": max(0, core_resources["Culture"] - 5)}),
                    core_resources.update({"Stability": max(0, core_resources["Stability"] - random.randint(0,3))}),
                    event_manager_ref.log_event("Choice Outcome: Knowledge +20, Culture -5. Stability may have slightly decreased due to unease.")
                )
            },
            {
                "choice_text": "Proclaim them a sign from the ancient spirits! Hold a grand ritual to seek guidance.",
                "choice_effects": lambda event_manager_ref: (
                    core_resources.update({"Culture": core_resources["Culture"] + 30}),
                    core_resources.update({"Stability": min(100, core_resources["Stability"] + 5)}),
                    core_resources.update({"Production": max(0, core_resources["Production"] - 15)}),
                    core_resources.update({"Food": max(0, core_resources["Food"] - 20)}),
                    event_manager_ref.log_event("Choice Outcome: Culture +30, Stability +5. Production -15, Food -20 due to ritual preparations.")
                )
            }
        ]
    },
    # --- New Events Start Here ---
    "fertile_soil_discovery": {
        "event_id": "fertile_soil_discovery",
        "type": "random",
        "title": "Fertile Soil Discovered!",
        "description": "Scouts have found a nearby valley with exceptionally fertile soil, promising bountiful harvests.",
        "probability": 0.02, # Lowered from example for balance
        "trigger_conditions": lambda gs, tt, bm, em: gs.core_resources["Population"] > 30 and tt.technologies.get("basic_farming", {}).get("researched"),
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Food": rs["Food"] + 100 + int(rs["Population"] * 0.2)}),
            tm.update({"food_production_bonus_factor": tm.get("food_production_bonus_factor", 1.0) * 1.03}),
            em_ref.log_event("Outcome: Significant food bonus received (+100, +0.2/Pop). Food production factor slightly increased (+3%).", is_major=False)
        ),
        "one_time": True
    },
    "tool_scarcity": { # Renamed from example for clarity
        "event_id": "tool_scarcity",
        "type": "decision",
        "title": "Tool Scarcity",
        "description": "Many tools have broken recently, and artisans report a shortage of quality materials for replacements. Production is slowing.",
        "probability": 0.03,
        "trigger_conditions": lambda gs, tt, bm, em: gs.core_resources["Production"] < (gs.core_resources["Population"] * 0.4) and gs.core_resources["Population"] > 40 and not tt.technologies.get("specialized_tools",{}).get("researched"),
        "player_choices": [
            {
                "choice_text": "Organize a village-wide effort to find new material sources. (Cost: 30 Food, 10 Production. Chance of success).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Food": rs["Food"] - 30 if rs["Food"] >= 30 else 0}),
                    rs.update({"Production": rs["Production"] - 10 if rs["Production"] >= 10 else 0}),
                    (lambda: (
                        tm.update({"production_bonus_factor": tm.get("production_bonus_factor", 1.0) * 1.10}), 
                        em_ref.log_event("Choice Outcome: Material search successful! Production efficiency permanently increased by 10%.", is_major=False)
                    ))() if random.random() < 0.6 else em_ref.log_event("Choice Outcome: The search for new materials was arduous but yielded little. Resources spent.", is_major=False)
                )
            },
            {
                "choice_text": "Implement stricter rationing of existing tools. (Stability -5. Production efficiency -10% for this cycle, then recovers).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Stability": rs["Stability"] - 5}),
                    # This is an immediate effect for the current cycle's calculation in update_resources if it checks this.
                    # A temporary effect system would be better. For now, this implies a one-cycle hit that then reverts.
                    # The actual revert needs to be handled by the game logic if not truly permanent.
                    # For simplicity, we'll make it a smaller permanent hit.
                    tm.update({"production_bonus_factor": tm.get("production_bonus_factor", 1.0) * 0.95}), # Simplified to permanent small hit
                    em_ref.log_event("Choice Outcome: Tools rationed. Stability -5. Production efficiency slightly reduced (-5% permanently as proxy for temporary effect).", is_major=False)
                )
            },
            {
                "choice_text": "Do nothing; the current tools must suffice. (Risk of further production loss).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    (lambda: (
                        tm.update({"production_bonus_factor": tm.get("production_bonus_factor", 1.0) * 0.90}), 
                        em_ref.log_event("Choice Outcome: Ignoring the scarcity led to more breakages. Production efficiency worsened (-10%).", is_major=False)
                    ))() if random.random() < 0.33 else em_ref.log_event("Choice Outcome: The people grumble, but production continues, for now.", is_major=False)
                )
            }
        ]
    },
    "new_song_inspires": {
        "event_id": "new_song_inspires",
        "type": "random",
        "title": "A New Song Inspires!",
        "description": "A traveling bard (or perhaps a local talent) has composed a song that resonates deeply with the people, lifting spirits.",
        "probability": 0.04,
        "trigger_conditions": lambda gs, tt, bm, em: gs.core_resources["Culture"] > 20,
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Culture": rs["Culture"] + 20 + int(rs["Population"] * 0.1)}),
            rs.update({"Stability": min(100, rs["Stability"] + 7)}),
            em_ref.log_event("Outcome: The new song brings joy! Culture increased (+20, +0.1/Pop), Stability significantly improved (+7%).", is_major=False)
        )
    },
    "dispute_among_elders": {
        "event_id": "dispute_among_elders",
        "type": "decision",
        "title": "Dispute Among Elders",
        "description": "A heated disagreement has broken out among the council of elders regarding the interpretation of recent omens.",
        "probability": 0.03,
        "trigger_conditions": lambda gs, tt, bm, em: gs.core_resources["Stability"] < 60 and tt.technologies.get("oral_tradition", {}).get("researched") and not tt.technologies.get("early_governance",{}).get("researched"),
        "player_choices": [
            {
                "choice_text": "Side with Elder Theron's conservative interpretation. (Stability +5, Culture -10)",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Stability": min(100, rs["Stability"] + 5)}),
                    rs.update({"Culture": rs["Culture"] - 10 if rs["Culture"] >= 10 else 0}),
                    em_ref.log_event("Choice Outcome: Sided with Elder Theron. Stability +5, Culture -10.", is_major=False)
                )
            },
            {
                "choice_text": "Support Elder Lyra's progressive view. (Knowledge +15, Stability -3)",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Knowledge": rs["Knowledge"] + 15}),
                    rs.update({"Stability": rs["Stability"] - 3}),
                    em_ref.log_event("Choice Outcome: Sided with Elder Lyra. Knowledge +15, Stability -3.", is_major=False)
                )
            },
            {
                "choice_text": "Urge mediation and compromise. (Cost: 10 Production. Chance of greater unity or further division).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Production": rs["Production"] - 10 if rs["Production"] >= 10 else 0}),
                    (lambda: (rs.update({"Stability": min(100, rs["Stability"] + 10)}), rs.update({"Culture": rs["Culture"] + 10}), em_ref.log_event("Choice Outcome: Mediation successful! Stability +10, Culture +10.", is_major=False)))() if random.random() < 0.5 
                    else (lambda: (rs.update({"Stability": rs["Stability"] - 7}), em_ref.log_event("Choice Outcome: Mediation failed, deepening the rift. Stability -7.", is_major=False)))()
                )
            }
        ]
    },
    "scouts_return_empty": {
        "event_id": "scouts_return_empty",
        "type": "random",
        "title": "Scouts Return Empty-Handed",
        "description": "The latest scouting party found no new resources or notable discoveries. Some whisper it's a bad omen.",
        "probability": 0.05,
        "trigger_conditions": lambda gs, tt, bm, em: True, 
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Stability": rs["Stability"] - 1}),
            em_ref.log_event("Outcome: Scouts found nothing of note. A slight dip in morale (Stability -1).", is_major=False)
        )
    },
    "ancient_ruins_found": {
        "event_id": "ancient_ruins_found",
        "type": "decision",
        "title": "Ancient Ruins Discovered!",
        "description": "Scouts stumbled upon crumbling ruins of an unknown civilization in a remote area.",
        "probability": 0.015,
        "trigger_conditions": lambda gs, tt, bm, em: tt.technologies.get("calendrics", {}).get("researched"),
        "one_time": True,
        "player_choices": [
            {
                "choice_text": "Send an expedition. (Cost: 50 Food, 20 Prod. Gain Knowledge, chance of Culture or research boost).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Food": rs["Food"] - 50 if rs["Food"] >= 50 else 0}),
                    rs.update({"Production": rs["Production"] - 20 if rs["Production"] >= 20 else 0}),
                    rs.update({"Knowledge": rs["Knowledge"] + random.randint(30, 60)}),
                    (lambda: (rs.update({"Culture": rs["Culture"] + random.randint(20,40)}), em_ref.log_event("Choice Outcome: Expedition sent. Knowledge gained. Ruins yielded cultural insights!", is_major=False)))() if random.random() < 0.5 
                    else (lambda: (tm.update({"research_speed_modifier": tm.get("research_speed_modifier", 1.0) * 1.05}), em_ref.log_event("Choice Outcome: Expedition sent. Knowledge gained. Study of ruins slightly boosted research speed!", is_major=False)))()
                )
            },
            {
                "choice_text": "Declare the ruins taboo. (Stability +3, Culture +5).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Stability": min(100, rs["Stability"] + 3)}),
                    rs.update({"Culture": rs["Culture"] + 5}),
                    em_ref.log_event("Choice Outcome: Ruins declared taboo. Stability +3, Culture +5.", is_major=False)
                )
            },
            {
                "choice_text": "Salvage materials. (Gain Production, risk instability).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Production": rs["Production"] + random.randint(40, 100)}),
                    (lambda: (rs.update({"Stability": rs["Stability"] - random.randint(5,10)}), em_ref.log_event("Choice Outcome: Salvaging was fruitful but disturbed spirits. Production gained, Stability lost.", is_major=False)))() if random.random() < 0.4
                    else em_ref.log_event("Choice Outcome: Salvaging yielded useful materials without incident.", is_major=False)
                )
            }
        ]
    },
    "localized_flood": {
        "event_id": "localized_flood",
        "type": "random",
        "title": "Localized Flood",
        "description": "Heavy rains caused a nearby river to flood, damaging some farmlands and workshops.",
        "probability": 0.025,
        "trigger_conditions": lambda gs, tt, bm, em: bm.get_completed_building_counts().get("communal_fields", 0) > 0 or bm.get_completed_building_counts().get("workshop", 0) > 0,
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Food": max(0, rs["Food"] - int(rs["Food"]*0.05))}), 
            rs.update({"Production": max(0, rs["Production"] - int(rs["Production"]*0.05))}), 
            rs.update({"Stability": rs["Stability"] - 2}),
            em_ref.log_event("Outcome: Minor flood damage. Food -5%, Production -5%, Stability -2.", is_major=False)
        )
    },
    "mild_winter": {
        "event_id": "mild_winter",
        "type": "random",
        "title": "Mild Winter",
        "description": "The winter was surprisingly mild, leading to lower food consumption and general contentment.",
        "probability": 0.04,
        "trigger_conditions": lambda gs, tt, bm, em: True,
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Food": rs["Food"] + int(gs.core_resources["Population"] * gs.FOOD_CONSUMPTION_PER_CAPITA * 0.2)}), # Access game_state.FOOD_CONSUMPTION_PER_CAPITA
            rs.update({"Stability": min(100, rs["Stability"] + 4)}),
            em_ref.log_event("Outcome: A mild winter eases food burden and lifts spirits. Food bonus, Stability +4.", is_major=False)
        )
    },
    "prophetic_dream": {
        "event_id": "prophetic_dream",
        "type": "decision",
        "title": "A Prophetic Dream",
        "description": "One of the mystics reports a powerful dream, believed to be a message from the ancestors.",
        "probability": 0.02,
        "trigger_conditions": lambda gs, tt, bm, em: tt.technologies.get("storytelling", {}).get("researched") and gs.core_resources["Culture"] > 40,
        "player_choices": [
            {
                "choice_text": "Heed the dream: Focus efforts on spiritual matters. (Culture +25, Knowledge -10)",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Culture": rs["Culture"] + 25}),
                    rs.update({"Knowledge": rs["Knowledge"] - 10 if rs["Knowledge"] >= 10 else 0}),
                    em_ref.log_event("Choice Outcome: Spiritual focus. Culture +25, Knowledge -10.", is_major=False)
                )
            },
            {
                "choice_text": "Interpret the dream as a call for innovation. (Knowledge +25, Culture -10)",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Knowledge": rs["Knowledge"] + 25}),
                    rs.update({"Culture": rs["Culture"] - 10 if rs["Culture"] >= 10 else 0}),
                    em_ref.log_event("Choice Outcome: Innovation focus. Knowledge +25, Culture -10.", is_major=False)
                )
            },
            {
                "choice_text": "The dream is merely a dream. Ignore it. (Small chance of minor stability loss later).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    (lambda: (rs.update({"Stability": rs["Stability"] - 3}), em_ref.log_event("Choice Outcome: Ignoring the dream caused some unease. Stability -3.", is_major=False)))() if random.random() < 0.25
                    else em_ref.log_event("Choice Outcome: The dream was dismissed without consequence.", is_major=False)
                )
            }
        ]
    },
    "unexpected_ally_visit": { # Renamed from example
        "event_id": "unexpected_ally_visit",
        "type": "random",
        "title": "Unexpected Visitors",
        "description": "A small, friendly nomadic group passes through, offering a small gift of rare herbs and sharing tales.",
        "probability": 0.015,
        "trigger_conditions": lambda gs, tt, bm, em: tt.technologies.get("trade_routes", {}).get("researched"),
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Food": rs["Food"] + 20}),
            rs.update({"Culture": rs["Culture"] + 10}),
            tm.update({"population_growth_modifier": tm.get("population_growth_modifier", 1.0) * 1.02}), # Slight, temporary boost
            gsv.update({"temporary_effects": gsv.get("temporary_effects", []) + [{"modifier": "population_growth_modifier", "original_value": tm.get("population_growth_modifier", 1.0) / 1.02, "duration": 3, "change": 0.02, "type": "factor"}]}), # Experimental
            em_ref.log_event("Outcome: Friendly nomads gifted rare herbs. Food +20, Culture +10. Population growth slightly encouraged (temp effect for 3 cycles).", is_major=False)
        )
    },
    "disease_outbreak_minor": {
        "event_id": "disease_outbreak_minor",
        "type": "random",
        "title": "Minor Sickness Spreads",
        "description": "A common sickness is affecting a small part of the population, reducing productivity.",
        "probability": 0.03,
        "trigger_conditions": lambda gs, tt, bm, em: gs.core_resources["Population"] > 50 and not tt.technologies.get("basic_herbalism", {}).get("researched"),
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Population": rs["Population"] - int(rs["Population"] * 0.02)}), 
            tm.update({"production_bonus_factor": tm.get("production_bonus_factor", 1.0) * 0.95}), # Temp 5% prod loss
            rs.update({"Stability": rs["Stability"] - 4}),
            gsv.update({"temporary_effects": gsv.get("temporary_effects", []) + [{"modifier": "production_bonus_factor", "original_value": tm.get("production_bonus_factor", 1.0) / 0.95, "duration": 3, "change": -0.05, "type": "factor"}]}), # Experimental
            em_ref.log_event("Outcome: Minor sickness outbreak! Population -2%, Production temporarily -5% (3 cycles), Stability -4.", is_major=False)
        )
    },
     "philosopher_emerges": {
        "event_id": "philosopher_emerges",
        "type": "random",
        "title": "A Philosopher Emerges",
        "description": "An individual begins to question the nature of things, sparking new ways of thinking.",
        "probability": 0.01,
        "trigger_conditions": lambda gs, tt, bm, em: tt.technologies.get("advanced_writing", {}).get("researched") and gs.core_resources["Knowledge"] > 100,
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Knowledge": rs["Knowledge"] + 50}),
            rs.update({"Culture": rs["Culture"] + 30}),
            tm.update({"research_speed_modifier": tm.get("research_speed_modifier", 1.0) * 1.1}), 
            em_ref.log_event("Outcome: A new philosopher inspires new thought! Knowledge +50, Culture +30, Research Speed +10%.", is_major=False)
        ),
        "one_time": True
    },
    "artisans_inspired_work": {
        "event_id": "artisans_inspired_work",
        "type": "random",
        "title": "Artisans' Inspired Work",
        "description": "A period of unusual creativity leads to exceptionally well-made goods and art.",
        "probability": 0.025,
        "trigger_conditions": lambda gs, tt, bm, em: gs.core_resources["Culture"] > 50 and bm.get_completed_building_counts().get("workshop", 0) > 0,
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            rs.update({"Production": rs["Production"] + 75}),
            rs.update({"Culture": rs["Culture"] + 40}),
            rs.update({"Stability": min(100, rs["Stability"] + 3)}),
            em_ref.log_event("Outcome: Inspired artisans create masterpieces! Production +75, Culture +40, Stability +3.", is_major=False)
        )
    },
    "bandit_activity_low": {
        "event_id": "bandit_activity_low",
        "type": "random",
        "title": "Bandit Activity Low",
        "description": "Recent patrols or perhaps just luck has meant very little trouble from bandits or raiders.",
        "probability": 0.04,
        "trigger_conditions": lambda gs, tt, bm, em: gs.core_resources["Stability"] > 50, # More likely if stable
        "effects": lambda rs, tm, bm_mods, gsv, em_ref: (
            # Small bonus to production (less disruption) and stability
            tm.update({"production_bonus_factor": tm.get("production_bonus_factor", 1.0) * 1.02}),
            rs.update({"Stability": min(100, rs["Stability"] + 2)}),
            em_ref.log_event("Outcome: Low bandit activity. Production efficiency +2%, Stability +2.", is_major=False)
        )
    },
    "valuable_mineral_vein": {
        "event_id": "valuable_mineral_vein",
        "type": "decision",
        "title": "Valuable Mineral Vein Discovered",
        "description": "Miners have struck a rich vein of a curious, glittering mineral. It seems valuable, but also difficult to extract.",
        "probability": 0.01,
        "trigger_conditions": lambda gs, tt, bm, em: tt.technologies.get("specialized_tools", {}).get("researched") and bm.get_completed_building_counts().get("workshop",0) > 0,
        "one_time": True,
        "player_choices": [
            {
                "choice_text": "Invest heavily in its extraction. (Cost: 100 Production, 50 Food. Gain large amount of Production later, or valuable resource for trade).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Production": rs["Production"] - 100 if rs["Production"] >= 100 else 0}),
                    rs.update({"Food": rs["Food"] - 50 if rs["Food"] >= 50 else 0}),
                    # Set a flag for a future event or a delayed bonus
                    gsv.update({"mineral_extraction_underway": gsv.get("mineral_extraction_underway",0) + 1, "mineral_extraction_timer": gsv.get("current_cycle",0) + 10}), # Ready in 10 cycles
                    em_ref.log_event("Choice Outcome: Major effort to extract minerals begins. Resources committed. (Results in ~10 cycles)", is_major=False)
                )
            },
            {
                "choice_text": "Study the mineral first. (Cost: 30 Knowledge. May unlock new tech or understanding).",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    rs.update({"Knowledge": rs["Knowledge"] - 30 if rs["Knowledge"] >= 30 else 0}),
                    (lambda: (rs.update({"Knowledge": rs["Knowledge"] + 100}), tm.update({"research_speed_modifier": tm.get("research_speed_modifier", 1.0) * 1.05}), em_ref.log_event("Choice Outcome: Study reveals insights! Knowledge +100, Research Speed +5%.", is_major=False)))() if random.random() < 0.6
                    else em_ref.log_event("Choice Outcome: The mineral is puzzling, study yields little for now.", is_major=False)
                )
            },
            {
                "choice_text": "It's too dangerous or difficult. Leave it be.",
                "choice_effects": lambda rs, tm, bm_mods, gsv, em_ref: (
                    em_ref.log_event("Choice Outcome: The mineral vein was left undisturbed.", is_major=False)
                )
            }
        ]
    }
    # --- End of New Events ---
}

class EventManager:
    def __init__(self, events_config, tech_tree_ref, building_manager_ref): # core_resources, update_stability are imported
        self.events_data = events_config # This will be the events_data dict from this module, passed in by main.py
        self.tech_tree = tech_tree_ref
        self.building_manager = building_manager_ref
        # self.update_stability_func = update_stability # Imported, can be called directly
        self.pending_decision_event = None
        self.event_log = [] 

    def log_event(self, message, is_major=False):
        prefix = "EVENT: "
        if is_major:
            prefix = "MAJOR EVENT: "
        
        log_entry = f"{prefix}{message}"
        # UI Leak: This print should be handled by a UI module
        print(log_entry) 
        self.event_log.append(log_entry)
        if len(self.event_log) > 30:
            self.event_log.pop(0)

    def apply_effects(self, effects_lambda):
        if effects_lambda:
            effects_lambda(self) # Pass self (event_manager_ref) to the lambda

    def check_for_events(self):
        if self.pending_decision_event:
            return 

        triggered_event_this_cycle = False
        # Iterate over a copy if modification during iteration is possible (e.g. one_time events)
        for event_id, event_data in list(self.events_data.items()): 
            if event_data.get("triggered_this_session", False) and event_data.get("one_time", False):
                continue

            conditions_met = True
            if "trigger_conditions" in event_data:
                # Pass core_resources and tech_tree.technologies to condition lambdas
                if not event_data["trigger_conditions"](core_resources, self.tech_tree.technologies):
                    conditions_met = False
            
            if not conditions_met:
                continue

            if random.random() < event_data.get("probability", 0.0):
                self.trigger_event(event_id, event_data)
                triggered_event_this_cycle = True
                if self.pending_decision_event or event_data.get("stops_further_events_this_cycle", False):
                    break 
        
        if not triggered_event_this_cycle:
            # UI Leak: This print should be handled by a UI module
            print("No significant events occurred this cycle.")


    def trigger_event(self, event_id, event_data):
        self.log_event(f"{event_data['title']} - {event_data['description']}", is_major=True)
        
        if event_data.get("one_time", False):
             self.events_data[event_id]["triggered_this_session"] = True # Mark as triggered

        if event_data["type"] == "decision":
            self.pending_decision_event = {
                "id": event_id, 
                "title": event_data["title"],
                "description": event_data["description"],
                "choices": event_data["player_choices"] 
            }
        elif event_data["type"] == "random": 
            if "effects" in event_data:
                self.apply_effects(event_data["effects"])
        
    def resolve_decision_event(self, choice_input):
        if not self.pending_decision_event:
            return "Error: No pending decision to resolve."

        try:
            choice_idx = int(choice_input) - 1 
            if not 0 <= choice_idx < len(self.pending_decision_event["choices"]):
                return "Error: Invalid choice number."
        except ValueError:
            return "Error: Choice must be a number."

        chosen_option = self.pending_decision_event["choices"][choice_idx]
        self.log_event(f"For '{self.pending_decision_event['title']}', you chose: '{chosen_option['choice_text']}'", is_major=True)
        
        if "choice_effects" in chosen_option:
            self.apply_effects(chosen_option["choice_effects"])

        self.pending_decision_event = None 
        return f"Decision '{chosen_option['choice_text']}' has been made."
