import numpy as np
import pyRBM.Simulation.State as State

class Solver:
    def __init__(self, use_cached_propensities:bool = True, no_rules_behaviour:str = "step", debug:bool = True):


        self.use_cached_propensities = use_cached_propensities
        
        # Either step or exit
        assert (no_rules_behaviour in ["step", "exit"])
        self.no_rules_behaviour = no_rules_behaviour
        self.default_step = 1
        self.debug = debug
    
    def initialize(self, locations, rules, matched_indices, model_state:State.ModelState, propensity_update_dict:dict = {}):
        self.locations = locations
        self.rules = rules
        self.matched_indices = matched_indices
        self.model_state = model_state
        self.propensity_update_dict = propensity_update_dict
        # Stats are throughout all runs

    
        self.reset()

    def reset(self):
        self.propensities = {}
        self.last_rule_index_set = None
        if self.use_cached_propensities:
            self.total_propensity = 0
        
        # Reset solver stats after a completed simulation
        if self.debug:
            self.current_stats = {}

    def simulateOneStep(self):
        raise(TypeError("Abstract class Solver, please use a concrete implementation."))
    
    # rules_and_matched_indices is used to determine which propensities to recompute, if None is provided this is all propensities.
    # returns total propensity

    def updateGivenPropensities(self, update_propensity_func, rules_and_matched_indices = None):
        model_state_values = list(self.model_state.returnModelClassesValues())

        if rules_and_matched_indices is None:
            for rule_i in range(len(self.matched_indices)):
                for index_set_i in range(len(self.matched_indices[rule_i])):
                    update_propensity_func(rule_i, index_set_i, model_state_values)
        else:
            for rule_i, index_set_i in rules_and_matched_indices:
                update_propensity_func(rule_i, index_set_i, model_state_values)


    def updateGivenPropensity(self, rule_i, index_set_i, model_state_values):
        rule = self.rules[rule_i]
        new_propensity = rule.returnPropensity(np.take(self.locations, self.matched_indices[rule_i][index_set_i]), model_state_values)
        if self.use_cached_propensities:
            propensity_diff = (new_propensity - self.propensities.get(f"{rule_i} {index_set_i}", 0.0))
            self.total_propensity += propensity_diff
        self.propensities[f"{rule_i} {index_set_i}"] = new_propensity

    def performPropensityUpdates(self, update_propensity_func):
        if not self.last_rule_index_set is None:
            rule_prop_update_set = self.propensity_update_dict[self.last_rule_index_set]
            changed_base_model_vars = self.model_state.returnChangedVars()
            if not len(changed_base_model_vars) == 0:
                rule_prop_update_set = rule_prop_update_set.copy()
                for changed_model_var in changed_base_model_vars:
                    rule_prop_update_set.update(self.propensity_update_dict.get(changed_model_var, set()))
            self.updateGivenPropensities(update_propensity_func, rule_prop_update_set)
        else:
            self.updateGivenPropensities(update_propensity_func)
    
    def collectStats(self, rule, index_set, total_propensity):
        assert(self.debug)
        self.current_stats["rule_triggered"] = str(rule)
        self.current_stats["rule_index_set"] = str(rule)+"_"+str(index_set)
        self.current_stats["total_propensity"] = float(total_propensity)

    # CACHE TOTAL PROPENSITY AND UPDATE USING DIFF BETWEEN OLD AND NEW CACHE VALUES.
    def returnTotalPropensity(self):
        if not self.use_cached_propensities:
            return sum(list(self.propensities.values()))
        else:
            return self.total_propensity
class GillespieSolver(Solver):
    def __init__(self, use_cached_propensities:bool = True, no_rules_behaviour:str = "step", debug:bool = True):
        super().__init__(use_cached_propensities, no_rules_behaviour, debug)
    
    def simulateOneStep(self, current_time):
        self.performPropensityUpdates(self.updateGivenPropensity)

        total_propensity = self.returnTotalPropensity()
        
        if total_propensity <= 0:
            if self.no_rules_behaviour == "end":
                print("Finishing model simulation early.\n No rules left to trigger - all rules have 0 propensity.")
                return
            elif self.no_rules_behaviour == "step":
                print(f"Stepping {self.default_step} ahead.\n No rules left to trigger - all rules have 0 propensity.")
                if self.debug:
                    self.collectStats(None, None, 0)
                    
                return current_time + self.default_step
        
        # Generate 0 to 1
        # Random rule
        u1, r2 = np.random.random_sample(2)
        u2 = -np.log(r2)*(1/total_propensity)
        # Random time
        cumulative_prop = 0
        selected_rule_index = None
        for rule_loc_key in list(self.propensities.keys()):
            cumulative_prop += self.propensities[rule_loc_key]
            if cumulative_prop > u1*total_propensity:
                selected_rule_index = rule_loc_key
                break
        # Only set the last rule used when using the caching for propensities.
        if self.use_cached_propensities:
            self.last_rule_index_set = selected_rule_index
        selected_rule, selected_locations = selected_rule_index.split(" ")
        assert (self.rules[int(selected_rule)].triggerAttemptedRuleChange(np.take(self.locations, self.matched_indices[int(selected_rule)][int(selected_locations)])))
        if self.debug:
            self.collectStats(int(selected_rule), int(selected_locations), total_propensity)
        return current_time + u2

class HKOSolver(Solver):
    def __init__(self, use_cached_propensities:bool = True, no_rules_behaviour:str = "step", debug:bool = True):
        super().__init__(use_cached_propensities, no_rules_behaviour, debug)
    
    def reset(self):
        super().reset()
        self.propensities = {str(rule_i):{str(matched_indices_i):0
                                          for matched_indices_i in range(len(self.matched_indices[rule_i]))}
                                            for rule_i in range(len(self.rules))}
        
        self.rule_propensities = {str(i):0 for i in range(len(self.rules))}
    
    def updateGivenPropensity(self, rule_i, index_set_i, model_state_values):
        rule = self.rules[rule_i]
        new_propensity = rule.returnPropensity(np.take(self.locations, self.matched_indices[rule_i][index_set_i]), model_state_values)
        if self.use_cached_propensities:
            propensity_diff = new_propensity - self.propensities[str(rule_i)].get(str(index_set_i), 0.0)
            self.rule_propensities[str(rule_i)] += propensity_diff
            self.total_propensity += propensity_diff
        self.propensities[str(rule_i)][str(index_set_i)] = new_propensity


    def simulateOneStep(self, current_time):
        self.performPropensityUpdates(self.updateGivenPropensity)

        total_propensity = self.returnTotalPropensity()
        
        if total_propensity <= 0:
            if self.no_rules_behaviour == "end":
                print("Finishing model simulation early.\n No rules left to trigger - all rules have 0 propensity.")
                return
            elif self.no_rules_behaviour == "step":
                print(f"Stepping {self.default_step} ahead.\n No rules left to trigger - all rules have 0 propensity.")
                return current_time + self.default_step
        
        # Generate 0 to 1
        # Random rule
        u1, r2 = np.random.random_sample(2)
        u2 = -np.log(r2)*(1/total_propensity)
        # Random time
        cumulative_rule_prop = 0
        
        selected_rule = None
        selected_index_set = None

        for rule_i in range(len(self.rules)):
            rule_propensity = self.rule_propensities[str(rule_i)]
            cumulative_rule_prop += rule_propensity
            if cumulative_rule_prop > u1*total_propensity:
                cumulative_rule_prop -= rule_propensity
                selected_rule = rule_i
                selected_rule_propensity_dict = self.propensities[str(rule_i)]
                for index_set_key in list(selected_rule_propensity_dict.keys()):
                    cumulative_rule_prop += selected_rule_propensity_dict[index_set_key]
                    if cumulative_rule_prop > u1*total_propensity:
                        selected_index_set = int(index_set_key)
                        break
                break
        # Only set the last rule used when using the caching for propensities.
        if self.use_cached_propensities:
            self.last_rule_index_set = f"{selected_rule} {selected_index_set}"
        assert (self.rules[int(selected_rule)].triggerAttemptedRuleChange(np.take(self.locations, self.matched_indices[int(selected_rule)][int(selected_index_set)])))

        if self.debug:
            self.collectStats(int(selected_rule), int(selected_index_set), total_propensity)
        
        return current_time + u2