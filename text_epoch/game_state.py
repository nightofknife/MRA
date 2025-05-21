# Core Resources
core_resources = {
    "Population": 100,
    "Food": 100,
    "Production": 50,
    "Knowledge": 0,
    "Culture": 0,
    "Stability": 75  # Represented as a percentage (0-100)
}

# Game State dictionary
game_state_vars = { # Renamed from game_state to avoid conflict with module name
    "current_cycle": 0,
    "idle_cycles_count": 0,
}

# Global Modifiers from Techs - these will be updated by technologies
tech_modifiers = {
    "food_production_bonus_factor": 1.0,
    "production_bonus_factor": 1.0,
    "knowledge_generation_bonus_factor": 1.0,
    "culture_generation_bonus_factor": 1.0,
    "stability_per_cycle_bonus": 0.0, # Additive bonus to stability each cycle
    "population_growth_modifier": 1.0, # Multiplicative, e.g., for health improvements
    "building_cost_modifier_production": 1.0, # Multiplicative, e.g., 0.9 for 10% cheaper
    "research_speed_modifier": 1.0, # Multiplicative, effectively makes knowledge points more valuable or reduces costs
    # (This might be implemented by dividing tech costs by this modifier, or multiplying knowledge gain)
    # For now, assume it modifies effective knowledge gain for research.
}

# Global Modifiers from Buildings
building_modifiers = {
    "food_per_cycle_bonus": 0,
    "production_per_cycle_bonus": 0,
    "knowledge_per_cycle_bonus": 0,
    "culture_per_cycle_bonus": 0,
    "food_production_bonus_factor": 1.0, # Multiplicative factor for food produced by population
    "production_bonus_factor": 1.0, # Multiplicative factor for production by population (if ever needed, usually flat)
    "knowledge_bonus_factor": 1.0, # Multiplicative factor for knowledge by population
    "culture_bonus_factor": 1.0,   # Multiplicative factor for culture by population
    "stability_per_cycle_bonus": 0.0, # Additive bonus to stability each cycle (can also be from buildings)
    "max_population_bonus": 0, # Additive, increases max population cap (if such a cap exists)
    "housing_quality_modifier": 1.0, # Factor, could influence pop growth or stability
}

# Global Modifiers from Policies (this is the authoritative one, ensuring it matches policies.py initial definition)
# This dictionary is modified by PolicyManager.
policy_modifiers = {
    "culture_per_cycle_policy_bonus": 0,
    "production_bonus_factor_policy": 1.0,
    "population_growth_modifier_policy": 1.0,
    "knowledge_generation_bonus_factor_policy": 1.0,
    "culture_per_cycle_policy_cost": 0, 
    "stability_policy_bonus": 0, 
    "food_per_cycle_policy_bonus": 0,
    "production_per_cycle_policy_bonus": 0,
    "knowledge_per_cycle_policy_bonus": 0
}

# --- Game Constants ---
# Resource Calculation Constants
DEFAULT_FOOD_PRODUCTION_PER_CAPITA = 1.1
DEFAULT_PRODUCTION_PER_CAPITA = 0.5
DEFAULT_KNOWLEDGE_PER_CAPITA = 0.1
DEFAULT_CULTURE_PER_CAPITA = 0.05

POPULATION_GROWTH_RATE_BASE = 0.01
FOOD_CONSUMPTION_PER_CAPITA = 1.0
STARVATION_PENALTY_RATIO = 0.1
MIN_POPULATION = 2

# Stability Constants
STABILITY_FOOD_SHORTAGE_THRESHOLD = 0.1
STABILITY_STARVATION_PENALTY = 5
STABILITY_LOW_THRESHOLD = 40
STABILITY_LOW_DRAIN_RATE = 2
STABILITY_HIGH_THRESHOLD = 80
STABILITY_HIGH_BOOST_RATE = 1
STABILITY_FOOD_PENALTY_NO_STARVATION = 2

# Autonomous Decision Constants (though AUTONOMOUS_DECISION_THRESHOLD will be in main.py or a general logic module)
# For now, keeping it simple.

def update_stability(food_is_zero, starvation_occurred):
    """
    Calculates and updates stability for the current cycle.
    Returns the change in stability.
    Assumes core_resources is accessible globally within this module.
    """
    prev_stability = core_resources["Stability"]
    stability_change = 0

    if starvation_occurred:
        stability_change -= STABILITY_STARVATION_PENALTY
        print(f"Stability impacted by starvation: -{STABILITY_STARVATION_PENALTY}%") # UI Leak
    elif food_is_zero:
        stability_change -= STABILITY_FOOD_PENALTY_NO_STARVATION
        print(f"Stability impacted by critical food shortage: -{STABILITY_FOOD_PENALTY_NO_STARVATION}%") # UI Leak

    if prev_stability < STABILITY_LOW_THRESHOLD:
        stability_change -= STABILITY_LOW_DRAIN_RATE
        print(f"Stability below {STABILITY_LOW_THRESHOLD}%, further decrease: -{STABILITY_LOW_DRAIN_RATE}%") # UI Leak
    
    if prev_stability > STABILITY_HIGH_THRESHOLD:
        stability_change += STABILITY_HIGH_BOOST_RATE
        print(f"Stability above {STABILITY_HIGH_THRESHOLD}%, slight boost: +{STABILITY_HIGH_BOOST_RATE}%") # UI Leak

    core_resources["Stability"] += stability_change
    core_resources["Stability"] = max(0, min(100, core_resources["Stability"]))

    if core_resources["Stability"] < 20:
        print("CRITICAL: Stability is dangerously low! Risk of major negative events.") # UI Leak
    elif core_resources["Stability"] < STABILITY_LOW_THRESHOLD:
        print("Warning: Stability is low.") # UI Leak
    
    return core_resources["Stability"] - prev_stability

def update_resources():
    """
    Updates all core resources based on game logic for one cycle.
    Prints changes for each resource. (This printing is a UI leak and should be refactored later)
    Assumes core_resources, tech_modifiers, building_modifiers and constants are accessible globally within this module.
    """
    prev_pop = core_resources["Population"]
    prev_food = core_resources["Food"]
    prev_prod = core_resources["Production"]
    prev_know = core_resources["Knowledge"]
    prev_cult = core_resources["Culture"]

    starvation_this_cycle = False

    # Apply flat bonuses from buildings and policies
    # Apply flat bonuses from buildings and policies (ensure .get for safety)
    core_resources["Food"] += building_modifiers.get("food_per_cycle_bonus", 0) + policy_modifiers.get("food_per_cycle_policy_bonus", 0)
    core_resources["Production"] += building_modifiers.get("production_per_cycle_bonus", 0) + policy_modifiers.get("production_per_cycle_policy_bonus", 0)
    core_resources["Knowledge"] += building_modifiers.get("knowledge_per_cycle_bonus", 0) + policy_modifiers.get("knowledge_per_cycle_policy_bonus", 0)
    core_resources["Culture"] += building_modifiers.get("culture_per_cycle_bonus", 0) + policy_modifiers.get("culture_per_cycle_policy_bonus", 0)
    
    # Apply ongoing policy costs that directly deduct from resources
    culture_cost_from_policies = policy_modifiers.get("culture_per_cycle_policy_cost", 0) # Cost is positive in definition
    core_resources["Culture"] -= culture_cost_from_policies
    if core_resources["Culture"] < 0: core_resources["Culture"] = 0
    # (Add other direct resource costs from policies here if any)
    
    food_from_pop = 0
    prod_from_pop = 0
    know_from_pop = 0
    cult_from_pop = 0

    food_consumed = core_resources["Population"] * FOOD_CONSUMPTION_PER_CAPITA
    core_resources["Food"] -= food_consumed

    population_change = 0
    if core_resources["Food"] < 0:
        food_deficit_ratio = -core_resources["Food"] / (food_consumed if food_consumed > 0 else 1)
        actual_starvation_penalty = min(STARVATION_PENALTY_RATIO, STARVATION_PENALTY_RATIO * food_deficit_ratio * 2)
        starvation_loss = int(core_resources["Population"] * actual_starvation_penalty)
        population_change = -starvation_loss
        if starvation_loss > 0:
            starvation_this_cycle = True
        core_resources["Food"] = 0
        print(f"Warning: Starvation! Population decreased by {starvation_loss} due to food deficit.") # UI Leak
    else: # Growth if there's surplus food
        base_growth_rate_modified = POPULATION_GROWTH_RATE_BASE * \
                                    tech_modifiers.get("population_growth_modifier", 1.0) * \
                                    building_modifiers.get("housing_quality_modifier", 1.0) * \
                                    policy_modifiers.get("population_growth_modifier_policy", 1.0)
        
        food_surplus_factor = 1 + (core_resources["Food"] / (core_resources["Population"] * FOOD_CONSUMPTION_PER_CAPITA + 1))
        effective_growth_rate = min(base_growth_rate_modified * food_surplus_factor, base_growth_rate_modified * 2) # Cap growth rate relative to modified base
        population_growth = int(core_resources["Population"] * effective_growth_rate)
        population_change = population_growth
    
    core_resources["Population"] += population_change
    if core_resources["Population"] < MIN_POPULATION:
        if prev_pop >= MIN_POPULATION:
             core_resources["Population"] = MIN_POPULATION

    effective_food_prod_factor = tech_modifiers.get("food_production_bonus_factor", 1.0) * \
                                 building_modifiers.get("food_production_bonus_factor", 1.0) # Policies usually give flat food or affect growth, not this factor
    current_food_pop_production_per_capita = DEFAULT_FOOD_PRODUCTION_PER_CAPITA * effective_food_prod_factor
    food_from_pop = core_resources["Population"] * current_food_pop_production_per_capita
    core_resources["Food"] += food_from_pop
    core_resources["Food"] = max(0, core_resources["Food"]) 

    effective_prod_factor = tech_modifiers.get("production_bonus_factor", 1.0) * \
                            building_modifiers.get("production_bonus_factor", 1.0) * \
                            policy_modifiers.get("production_bonus_factor_policy", 1.0)
    current_prod_pop_per_capita = DEFAULT_PRODUCTION_PER_CAPITA * effective_prod_factor
    prod_from_pop = core_resources["Population"] * current_prod_pop_per_capita
    core_resources["Production"] += prod_from_pop
    core_resources["Production"] = max(0, core_resources["Production"])

    effective_know_factor = tech_modifiers.get("knowledge_generation_bonus_factor", 1.0) * \
                            building_modifiers.get("knowledge_bonus_factor", 1.0) * \
                            policy_modifiers.get("knowledge_generation_bonus_factor_policy", 1.0)
    current_know_pop_per_capita = DEFAULT_KNOWLEDGE_PER_CAPITA * effective_know_factor
    know_from_pop = core_resources["Population"] * current_know_pop_per_capita
    core_resources["Knowledge"] += know_from_pop
    core_resources["Knowledge"] = max(0, core_resources["Knowledge"])

    effective_cult_factor = tech_modifiers.get("culture_generation_bonus_factor", 1.0) * \
                           building_modifiers.get("culture_bonus_factor", 1.0) # Policies give flat culture or have direct cost
    current_cult_pop_per_capita = DEFAULT_CULTURE_PER_CAPITA * effective_cult_factor
    cult_from_pop = core_resources["Population"] * current_cult_pop_per_capita
    core_resources["Culture"] += cult_from_pop
    core_resources["Culture"] = max(0, core_resources["Culture"])

    # Stability Update (incorporating flat policy and tech bonuses before percentage calculations)
    prev_stability_for_report_calc = core_resources["Stability"] # Store stability before any direct additions this cycle for reporting
    
    core_resources["Stability"] += policy_modifiers.get("stability_policy_bonus", 0) + \
                                 tech_modifiers.get("stability_per_cycle_bonus", 0) + \
                                 building_modifiers.get("stability_per_cycle_bonus", 0)
    core_resources["Stability"] = max(0, min(100, core_resources["Stability"])) # Clamp before update_stability internal logic
    
    stability_change_from_events_food = update_stability(food_is_zero=(core_resources["Food"] == 0), starvation_occurred=starvation_this_cycle)
    
    total_stability_change_for_report = core_resources["Stability"] - prev_stability # prev_stability is from start of update_resources
    stability_change_str_report = f"{total_stability_change_for_report:+.1f}%"
        
    pop_growth_mods_total_perc = (tech_modifiers.get("population_growth_modifier", 1.0) * \
                                 building_modifiers.get("housing_quality_modifier", 1.0) * \
                                 policy_modifiers.get("population_growth_modifier_policy", 1.0) - 1) * 100
    pop_change_str_report = f"{core_resources['Population'] - prev_pop:+.0f} (Growth Mod: {pop_growth_mods_total_perc:.0f}%)"

    total_food_produced_this_cycle = food_from_pop + building_modifiers.get("food_per_cycle_bonus", 0) + policy_modifiers.get("food_per_cycle_policy_bonus", 0)
    food_total_factor_perc_report = (effective_food_prod_factor - 1) * 100
    food_change_str_report = f"{core_resources['Food'] - prev_food:+.0f} (Consumed: {food_consumed:.0f}; Produced: {total_food_produced_this_cycle:.0f} [Pop: {food_from_pop:.0f}, Bldgs: {building_modifiers.get('food_per_cycle_bonus',0):.0f}, Policies: {policy_modifiers.get('food_per_cycle_policy_bonus',0):.0f}]; Pop Bonus Factors: {food_total_factor_perc_report:.0f}%)"

    total_prod_generated_this_cycle = prod_from_pop + building_modifiers.get("production_per_cycle_bonus", 0) + policy_modifiers.get("production_per_cycle_policy_bonus", 0)
    prod_total_factor_perc_report = (effective_prod_factor - 1) * 100
    prod_change_str_report = f"{core_resources['Production'] - prev_prod:+.0f} (Generated: {total_prod_generated_this_cycle:.0f} [Pop: {prod_from_pop:.0f}, Bldgs: {building_modifiers.get('production_per_cycle_bonus',0):.0f}, Policies: {policy_modifiers.get('production_per_cycle_policy_bonus',0):.0f}]; Pop Bonus Factors: {prod_total_factor_perc_report:.0f}%)"

    total_know_generated_this_cycle = know_from_pop + building_modifiers.get("knowledge_per_cycle_bonus", 0) + policy_modifiers.get("knowledge_per_cycle_policy_bonus", 0)
    know_total_factor_perc_report = (effective_know_factor - 1) * 100
    know_change_str_report = f"{core_resources['Knowledge'] - prev_know:+.2f} (Generated: {total_know_generated_this_cycle:.2f} [Pop: {know_from_pop:.2f}, Bldgs: {building_modifiers.get('knowledge_per_cycle_bonus',0):.2f}, Policies: {policy_modifiers.get('knowledge_per_cycle_policy_bonus',0):.2f}]; Pop Bonus Factors: {know_total_factor_perc_report:.0f}%)"

    total_cult_generated_this_cycle = cult_from_pop + building_modifiers.get("culture_per_cycle_bonus", 0) + policy_modifiers.get("culture_per_cycle_policy_bonus", 0)
    cult_total_factor_perc_report = (effective_cult_factor - 1) * 100
    cult_cost_from_policies_report = policy_modifiers.get("culture_per_cycle_policy_cost", 0)
    cult_change_str_report = f"{core_resources['Culture'] - prev_cult:+.2f} (Generated: {total_cult_generated_this_cycle:.2f} [Pop: {cult_from_pop:.2f}, Bldgs: {building_modifiers.get('culture_per_cycle_bonus',0):.2f}, Policies(bonus): {policy_modifiers.get('culture_per_cycle_policy_bonus',0):.2f}]; Costs [Policies: {cult_cost_from_policies_report:.2f}]; Pop Bonus Factors: {cult_total_factor_perc_report:.0f}%)"

    # This print block is a UI leak and should be handled by a dedicated UI module
    print("\n--- Resource Report ---") # This line is the same
    print(f"Population: {core_resources['Population']:.0f} ({pop_change_str_report})")
    print(f"Food:       {core_resources['Food']:.0f} ({food_change_str_report})")
    print(f"Production: {core_resources['Production']:.0f} ({prod_change_str_report})")
    print(f"Knowledge:  {core_resources['Knowledge']:.2f} ({know_change_str_report})")
    # cult_change_str_report already includes calculation of policy cost in its net change.
    print(f"Culture:    {core_resources['Culture']:.2f} ({cult_change_str_report})") 
    print(f"Stability:  {core_resources['Stability']:.0f}% ({stability_change_str_report})")
    print("----------------------")
