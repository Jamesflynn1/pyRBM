import numpy as np
import pyRBM.Simulation.State as State

class Solver:
    def __init__(self, locations, rules, matched_indices, model_state:State.ModelState, use_cached_propensities:bool = True, no_rules_behaviour:str = "step", propensity_update_dict:dict = {}):
        self.locations = locations
        self.rules = rules
        self.matched_indices = matched_indices
        self.model_state = model_state

        self.use_cached_propensities = use_cached_propensities

        self.last_rule_index_set = None

        self.propensities = {}
        if self.use_cached_propensities:
            self.total_propensity = 0
        self.propensity_update_dict = propensity_update_dict
        # Either step or exit
        assert (no_rules_behaviour in ["step", "exit"])
        self.no_rules_behaviour = no_rules_behaviour
        self.default_step = 1

    def simulateOneStep(self):
        raise(TypeError("Abstract class Solver, please use a concrete implementation."))
    
    # rules_and_matched_indices is used to determine which propensities to recompute, if None is provided this is all propensities.
    # returns total propensity
    def updateGivenPropensities(self, rules_and_matched_indices = None):
        model_state_values = list(self.model_state.returnModelClassesValues())

        if rules_and_matched_indices is None:
            for rule_i in range(len(self.matched_indices)):
                rule = self.rules[rule_i]
                for index_set_i in range(len(self.matched_indices[rule_i])):
                    new_propensity = rule.returnPropensity(np.take(self.locations, self.matched_indices[rule_i][index_set_i]),
                                                   model_state_values)
                    if self.use_cached_propensities:
                        self.total_propensity += (new_propensity - self.propensities.get(f"{rule_i} {index_set_i}", 0.0))
                    self.propensities[f"{rule_i} {index_set_i}"] = new_propensity
        else:
            for rule_i, index_set_i in rules_and_matched_indices:
                rule = self.rules[rule_i]
                new_propensity = rule.returnPropensity(np.take(self.locations, self.matched_indices[rule_i][index_set_i]),
                                                                                     model_state_values)
                if self.use_cached_propensities:
                    self.total_propensity += (new_propensity - self.propensities.get(f"{rule_i} {index_set_i}", 0.0))
                self.propensities[f"{rule_i} {index_set_i}"] = new_propensity

    def performPropensityUpdates(self):
        if not self.last_rule_index_set is None:
            rule_prop_update_set = self.propensity_update_dict[self.last_rule_index_set]
            changed_base_model_vars = self.model_state.returnChangedVars()
            if not len(changed_base_model_vars) == 0:
                rule_prop_update_set = rule_prop_update_set.copy()
                for changed_model_var in changed_base_model_vars:
                    rule_prop_update_set.update(self.propensity_update_dict.get(changed_model_var, set()))
            self.updateGivenPropensities(rule_prop_update_set)
        else:
            self.updateGivenPropensities()
    
    def reset(self):
        self.propensities = {}
        self.last_rule_index_set = None

    # CACHE TOTAL PROPENSITY AND UPDATE USING DIFF BETWEEN OLD AND NEW CACHE VALUES.
    def returnTotalPropensity(self):
        if not self.use_cached_propensities:
            return np.sum(list(self.propensities.values()))
        else:
            return self.total_propensity
class GillespieSolver(Solver):
    def __init__(self, locations, rules, matched_indices, model_state:State.ModelState, use_cached_propensities:bool = True, no_rules_behaviour:str = "step", propensity_update_dict:dict = {}):
        super().__init__(locations, rules, matched_indices, model_state, use_cached_propensities, no_rules_behaviour, propensity_update_dict)
    
    def simulateOneStep(self, current_time):
        self.performPropensityUpdates()

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
        cumulative_prop = 0
        selected_rule = None
        for rule_loc_key in list(self.propensities.keys()):
            cumulative_prop += self.propensities[rule_loc_key]
            if cumulative_prop > u1*total_propensity:
                selected_rule = rule_loc_key
                break
        # Only set the last rule used when using the caching for propensities.
        if self.use_cached_propensities:
            self.last_rule_index_set = selected_rule
        selected_rule, selected_locations = selected_rule.split(" ")
        assert (self.rules[int(selected_rule)].triggerAttemptedRuleChange(np.take(self.locations, self.matched_indices[int(selected_rule)][int(selected_locations)])))
        return current_time + u2

class TauLeapingGillespieSolver(Solver):
    def __init__(self, locations, rules, matched_indices, model_state, use_cached_propensities:bool = True, no_rules_behaviour:str = "step"):
        super().__init__(locations, rules, matched_indices, model_state, use_cached_propensities, no_rules_behaviour)
    
    def simulateOneStep(self, current_time):
        total_propensity = 0
        propensities = []


        for rule_i in range(len(self.matched_indices)):
            rule = self.rules[rule_i]
            for index_set_I in range(len(self.matched_indices[rule_i])):
                propensity = rule.returnPropensity(np.take(self.locations, self.matched_indices[rule_i][index_set_I]), 
                                                   list(self.model_state.returnModelClassesValues()))
                total_propensity+= propensity
                # First element the propensity, second element the rule index, index element pair.
                propensities.append([propensity, [rule_i, index_set_I]])
                
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
        cumulative_prop = 0
        selected_rule = None
        for rule_index, propensity in enumerate(propensities):
            if cumulative_prop+propensity[0] > u1*total_propensity:
                selected_rule = rule_index
                break
            else:
                cumulative_prop += propensity[0]
        selected_rule, selected_locations = propensities[selected_rule][1]
        assert (self.rules[selected_rule].triggerAttemptedRuleChange(np.take(self.locations, self.matched_indices[selected_rule][selected_locations])))
        return current_time + u2
