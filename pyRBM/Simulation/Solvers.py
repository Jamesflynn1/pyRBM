from typing import Optional, Callable, Union
from typing_extensions import override

import indexed_priority_queue
import numpy as np
from pyRBM.Simulation.State import ModelState
#from pyRBM.Simulation.WaitTimeDistributions import returnDistribFunctions

class Solver:
    def __init__(self, use_cached_propensities:bool = True,
                 no_rules_behaviour:str = "step", debug:bool = True,
                 random_generator=None, default_time_step=1) -> None:
        self.use_cached_propensities = use_cached_propensities

        # Either step or exit
        assert (no_rules_behaviour in ["step", "end"])
        self.no_rules_behaviour = no_rules_behaviour
        self.default_step = default_time_step
        self.debug = debug
        self._random_source = np.random.default_rng(random_generator)
    
    def processNoRuleEvent(self, current_time):
        if self.no_rules_behaviour == "end":
            print("Finishing model simulation early.\nNo rules left to trigger - all rules have 0 propensity.")
            return None
        elif self.no_rules_behaviour == "step":
            print(f"Stepping {self.default_step} ahead.\nNo rules left to trigger - all rules have 0 propensity.")
            if self.debug:
                self.collectStats(None, None, 0)

            return current_time + self.default_step
    
    def initialize(self, compartments, rules,
                   matched_indices, model_state:ModelState,
                   propensity_update_dict:Optional[dict] = None) -> None:
        self.compartments = compartments
        self.rules = rules
        self.matched_indices = matched_indices
        self.model_state = model_state

        # Read as propensity_update_dict if not None, otherwise a blank dictionary, avoids mutable default value
        self.propensity_update_dict = propensity_update_dict if propensity_update_dict is not None else {}


        self.reset()

    def reset(self) -> None:
        self.propensities = {}
        self.last_rule_index_set = []
        if self.use_cached_propensities:
            self.total_propensity = 0

        # Reset solver stats after a completed simulation
        if self.debug:
            self.current_stats = {}

    def simulateOneStep(self):
        raise(TypeError("Abstract class Solver, please use a concrete implementation."))

    # rules_and_matched_indices is used to determine which propensities to recompute, if None is provided this is all propensities.
    # returns total propensity

    def updateGivenPropensities(self, update_propensity_func:Callable[[int, int, list], None],
                                rules_and_matched_indices:Optional[tuple[int, int]] = None) -> None:
        model_state_values = list(self.model_state.returnModelClassesValues())

        if rules_and_matched_indices is None:
            for rule_i in range(len(self.matched_indices)):
                for index_set_i in range(len(self.matched_indices[rule_i])):
                    update_propensity_func(rule_i, index_set_i, model_state_values)
        else:
            for rule_i, index_set_i in rules_and_matched_indices:
                update_propensity_func(rule_i, index_set_i, model_state_values)


    def updateGivenPropensity(self, rule_i:int, index_set_i:int,
                              model_state_values:list) -> None:
        rule = self.rules[rule_i]
        new_propensity = rule.returnPropensity(np.take(self.compartments,
                                                       self.matched_indices[rule_i][index_set_i]),
                                                       model_state_values, index_set_i)
        if self.use_cached_propensities:
            propensity_diff = (new_propensity - self.propensities.get(f"{rule_i} {index_set_i}", 0.0))
            self.total_propensity += propensity_diff
        self.propensities[f"{rule_i} {index_set_i}"] = new_propensity

    def performPropensityUpdates(self, update_propensity_func:Callable[[int, int, list], None]) -> None:
        if self.use_cached_propensities and len(self.last_rule_index_set) > 0:
            rule_prop_update_set = {}
            for rule_index in self.last_rule_index_set:
                rule_prop_update_set = self.propensity_update_dict[rule_index]
            changed_model_vars = self.model_state.returnChangedVars()
            if len(changed_model_vars) > 0:
                rule_prop_update_set = rule_prop_update_set.copy()
                for changed_var in changed_model_vars:
                    rule_prop_update_set.update(self.propensity_update_dict[changed_var])

            self.updateGivenPropensities(update_propensity_func,
                                         rule_prop_update_set)
        else:
            self.updateGivenPropensities(update_propensity_func)

    def collectStats(self, rule:int, index_set:int, total_propensity) -> None:
        assert(self.debug)
        self.current_stats["rule_triggered"] = str(rule)
        self.current_stats["rule_index_set"] = str(rule)+"_"+str(index_set)
        self.current_stats["total_propensity"] = float(total_propensity)

    # CACHE TOTAL PROPENSITY AND UPDATE USING DIFF BETWEEN OLD AND NEW CACHE VALUES.
    def returnTotalPropensity(self) -> Union[float, int]:
        if not self.use_cached_propensities:
            return sum(list(self.propensities.values()))
        else:
            return self.total_propensity
        
class GillespieSolver(Solver):
    """ Gillespie Direct Method.
    Fastest implemented exact simulation algorithm and the most commonly used. 
    """
    def __init__(self, use_cached_propensities:bool = True,
                 no_rules_behaviour:str = "step", debug:bool = True) -> None:
        super().__init__(use_cached_propensities, no_rules_behaviour, debug)
        self.update_propensity_function = self.updateGivenPropensity

    def simulateOneStep(self, current_time):
        self.performPropensityUpdates(self.update_propensity_function)
        
        total_propensity = self.returnTotalPropensity()

        if total_propensity <= 0:
            return self.processNoRuleEvent(current_time)
        
        self.last_rule_index_set = []
        # Generate 0 to 1
        # Random rule
        u1, r2 = self._random_source.random(2)
        u2 = (-np.log(r2))/total_propensity
        # Random time
        cumulative_prop = 0
        selected_rule_index = None
        for rule_comp_key, rule_comp_propensity in self.propensities.items():
            cumulative_prop += rule_comp_propensity
            if cumulative_prop > u1*total_propensity:
               selected_rule_index = rule_comp_key
               break
        # No rule has been selected as even though total_propensity is non-zero, this is
        # likely due to numerical precision errors.
        if selected_rule_index is None:
            return self.processNoRuleEvent(current_time)

        # Only set the last rule used when using the caching for propensities.
        if self.use_cached_propensities:
            self.last_rule_index_set.append(selected_rule_index)
        selected_rule, selected_compartments = selected_rule_index.split(" ")
        assert (self.rules[int(selected_rule)].triggerAttemptedRuleChange(np.take(self.compartments,
                                                                                  self.matched_indices[int(selected_rule)]
                                                                                  [int(selected_compartments)])))
        if self.debug:
            self.collectStats(int(selected_rule), int(selected_compartments), total_propensity)
        return current_time + u2

class GillespieFRMSolver(Solver):
    """ Gillespie First Reaction method.
    Prefer the Gillespie Solver in almost all cases as the direct method is faster.
    """
    def __init__(self, use_cached_propensities:bool = True,
                 no_rules_behaviour:str = "step", debug:bool = True) -> None:
        super().__init__(use_cached_propensities, no_rules_behaviour, debug)
        self.update_propensity_function = self.updateGivenPropensity

    def simulateOneStep(self, current_time):
        self.performPropensityUpdates(self.update_propensity_function)

        # List of the rule/subrule pair that is triggered during this step.
        self.last_rule_index_set = []
        # Generate a random number for each subrule, this will be used to calculate the next event time
        r_i = -np.log(self._random_source.random(len(self.propensities)))

        min_time = None
        min_rule_index = None
        # Calculate the next event time and save the minimum event time and the rule/subrule index set that has that minimum time.
        for index, (rule_comp_key, rule_comp_propensity) in enumerate(self.propensities.items()):
            if rule_comp_propensity > 0:
                time = r_i[index]/rule_comp_propensity
                # If this is the first iteration, set the min_time = time, otherwise if time < min_time, update it.
                if min_time is None or time < min_time:
                    min_time = time
                    min_rule_index = rule_comp_key

        # No rule has been selected as even though total_propensity is non-zero, this is
        # likely due to numerical precision errors.
        if min_rule_index is None:
            return self.processNoRuleEvent(current_time)

        # Only set the last rule used when using the caching for propensities.
        if self.use_cached_propensities:
            self.last_rule_index_set.append(min_rule_index)
        selected_rule, selected_compartments = min_rule_index.split(" ")
        assert (self.rules[int(selected_rule)].triggerAttemptedRuleChange(np.take(self.compartments,
                                                                                  self.matched_indices[int(selected_rule)]
                                                                                  [int(selected_compartments)])))
        if self.debug:
            self.collectStats(int(selected_rule), int(selected_compartments), 0)
        return current_time + min_time

class GillespieNRMSolver(Solver):
    """ Gillespie Next Reaction Method.
    An improved version of the FRM method.
    """
    def __init__(self, no_rules_behaviour:str = "step", debug:bool = True) -> None:
        super().__init__(True, no_rules_behaviour, debug)
        self.update_propensity_function = self.updateGivenPropensityNRM

    def initialize(self, compartments, rules, matched_indices, model_state: ModelState, propensity_update_dict: dict | None = None) -> None:
        # Ensure that the rule index set updates itself, a new time will need to be generated
        # as the time was popped for that previous rule.
        super().initialize(compartments, rules, matched_indices, model_state, propensity_update_dict)
        for key in self.propensity_update_dict:
            try:
                self.propensity_update_dict[key].add(tuple(int(x) for x in key.split(" ")))
            except ValueError:
                continue

    def reset(self):
        super().reset()
        self.times = indexed_priority_queue.IndexedPriorityQueue()
        self.propensities = {f"{rule_i} {index_set_i}":0 for rule_i in range(len(self.matched_indices))
                             for index_set_i in range(len(self.matched_indices[rule_i]))}

    def updateGivenPropensityNRM(self, rule_i:int, index_set_i:int,
                              model_state_values:list) -> None:
        rule_index_string = f"{rule_i} {index_set_i}"
        rule = self.rules[rule_i]
        new_propensity = rule.returnPropensity(np.take(self.compartments,
                                                       self.matched_indices[rule_i][index_set_i]),
                                                       model_state_values, index_set_i)
        if new_propensity > 0:
            time_key = (rule_i, index_set_i)
            # If the rule has been triggered in the prior iteration.
            key_missing = False
            try:
                old_time = self.times.priority(time_key)
            except KeyError:
                key_missing = True
            time = None

            if rule_index_string in self.last_rule_index_set or key_missing:
            # Compute the new time by t + tau and save this rather than tau as in the FRM.
                time = self.current_time + ((-np.log(self._random_source.random(1)[0]))/new_propensity)
            else:
                old_propensity = self.propensities[rule_index_string]
                time = self.current_time + (old_propensity/new_propensity)*(old_time-self.current_time)

            if not key_missing:
                self.times.update((rule_i, index_set_i), new_priority=time)
            else:
                self.times.push((rule_i, index_set_i), priority=time)

        
        self.propensities[rule_index_string] = new_propensity


        # Reduce the storage size, will need to check pq size though.
        #else:
            #self.times.push((rule_i, index_set_i), priority=float("inf"))

    @override
    def updateGivenPropensities(self, update_propensity_func:Callable[[int, int, list], None],
                                rules_and_matched_indices:Optional[tuple[int, int]] = None) -> None:
        # Only change is self.updateTime calls and the computation of r_i for new times.
        model_state_values = list(self.model_state.returnModelClassesValues())

        if rules_and_matched_indices is None:
            for rule_i in range(len(self.matched_indices)):
                for index_set_i in range(len(self.matched_indices[rule_i])):
                    update_propensity_func(rule_i, index_set_i, model_state_values)
        else:
            for rule_i, index_set_i in rules_and_matched_indices:
                update_propensity_func(rule_i, index_set_i, model_state_values)
    @override
    def simulateOneStep(self, current_time):
        self.current_time = current_time
        self.performPropensityUpdates(self.update_propensity_function)

        # List of the rule/subrule pair that is triggered during this step.
        self.last_rule_index_set = []
        try:
            (selected_rule,selected_compartments), new_time  = self.times.pop()
        except IndexError:
            return self.processNoRuleEvent(current_time)

        # Only set the last rule used when using the caching for propensities.
        if self.use_cached_propensities:
            self.last_rule_index_set.append(f"{selected_rule} {selected_compartments}")
        assert (self.rules[int(selected_rule)].triggerAttemptedRuleChange(np.take(self.compartments,
                                                                                  self.matched_indices[int(selected_rule)]
                                                                                  [int(selected_compartments)])))
        if self.debug:
            self.collectStats(int(selected_rule), int(selected_compartments), 0)
        return new_time
class HKOSolver(Solver):
    def __init__(self, use_cached_propensities:bool = True,
                 no_rules_behaviour:str = "step",
                 debug:bool = True) -> None:
        super().__init__(use_cached_propensities,
                         no_rules_behaviour, debug)
    @override
    def reset(self) -> None:
        super().reset()
        # Rule index -> Subrule index -> subrule propensity
        # This overwrites the default rule index -> rule propensity map defined in super.reset()
        self.propensities = {str(rule_i):{str(matched_indices_i):0
                                          for matched_indices_i in range(len(self.matched_indices[rule_i]))}
                                            for rule_i in range(len(self.rules))}

        # Rule index -> rule propensity
        self.rule_propensities = {str(i):0 for i in range(len(self.rules))}

    @override
    def updateGivenPropensity(self, rule_i:int, index_set_i:int,
                              model_state_values:list) -> None:
        rule = self.rules[rule_i]

        # Return the propensity of the subrule given by rule_i triggered with index_set_i,
        # and the current global model state values.
        new_propensity = rule.returnPropensity(np.take(self.compartments,
                                                       self.matched_indices[rule_i][index_set_i]),
                                                       model_state_values, index_set_i)

        # We use the subrule propensity diff to update the stored propensity in rule_propensities and total_propensity
        propensity_diff = new_propensity - self.propensities[str(rule_i)].get(str(index_set_i), 0.0)

        self.rule_propensities[str(rule_i)] += propensity_diff

        if self.use_cached_propensities:
            self.total_propensity += propensity_diff
        self.propensities[str(rule_i)][str(index_set_i)] = new_propensity

    @override
    def simulateOneStep(self, current_time):
        # Update propensities for the rules affected by triggering the last_rule_index_set subrule.
        # Save these in self.rule_propensities, self.propensities.
        self.performPropensityUpdates(self.updateGivenPropensity)

        total_propensity = self.returnTotalPropensity()

        if total_propensity <= 0:
            return self.processNoRuleEvent(current_time)

        self.last_rule_index_set = []

        # Generate 0 to 1
        # Random rule
        u1, r2 = self._random_source.random(2)
        u2 = -np.log(r2)*(1/total_propensity)
        # Random time
        cumulative_rule_prop = 0

        selected_rule = None
        selected_index_set = None

        random_propensity = u1*total_propensity
        # Find which rule to trigger based on u1
        for rule_i in range(len(self.rules)):
            rule_propensity = self.rule_propensities[str(rule_i)]
            cumulative_rule_prop += rule_propensity
            if cumulative_rule_prop > random_propensity:
                # u1 lies between rule_i propensity interval
                selected_rule = rule_i
                # Start from the left hand side of rule_i's propensity interval
                cumulative_rule_prop -= rule_propensity
                selected_rule_propensity_dict = self.propensities[str(rule_i)]
                # Find which subrule (i.e. which compartments ("index set") triggered the rule)
                for index_set_key in selected_rule_propensity_dict:
                    cumulative_rule_prop += selected_rule_propensity_dict[index_set_key]
                    if cumulative_rule_prop > random_propensity:
                        selected_index_set = int(index_set_key)
                        break
                break
        # See dicussion of numerical precision in the Gillespie sovler.
        if selected_rule is None or selected_index_set is None:
            return self.processNoRuleEvent(current_time)
        
        # Only set the last rule used when using the caching for propensities.
        if self.use_cached_propensities:
            self.last_rule_index_set.append(f"{selected_rule} {selected_index_set}")
        assert (self.rules[int(selected_rule)].triggerAttemptedRuleChange(np.take(self.compartments,
                                                                                  self.matched_indices[int(selected_rule)]
                                                                                  [int(selected_index_set)])))

        if self.debug:
            self.collectStats(int(selected_rule),
                              int(selected_index_set),
                              total_propensity)

        return current_time + u2
class LaplaceGillespieSolver(GillespieSolver):
    def __init__(self, no_rules_behaviour:str = "step", debug:bool = True) -> None:
        # We require use of propensity caching as we only redraw when the update the propensity.
        super().__init__(True, no_rules_behaviour, debug)

        self.wait_time_distribs = returnDistribFunctions()

        self.update_propensity_function = self.updateLaplacePropensity

    def updateLaplacePropensity(self, rule_i:int, index_set_i:int,
                              model_state_values:list) -> None:
        rule = self.rules[rule_i]
        new_propensity = rule.returnPropensity(np.take(self.compartments,
                                                       self.matched_indices[rule_i][index_set_i]),
                                                       model_state_values, index_set_i)
        new_rate = self.wait_time_distribs[self.rule.wait_time_distribtion](new_propensity)
        if self.use_cached_propensities:
            rate_diff = (new_rate - self.propensities.get(f"{rule_i} {index_set_i}", 0.0))
            self.total_propensity += rate_diff
        self.propensities[f"{rule_i} {index_set_i}"] = new_rate

class TauLeapSolver(Solver):
    def __init__(self, time_step:float, use_cached_propensities:bool = False,
                 no_rules_behaviour:str = "step", debug:bool = True, negative_behaviour:str = "redraw") -> None:
        
        super().__init__(use_cached_propensities, no_rules_behaviour, debug, default_time_step=time_step)
        assert negative_behaviour in ["redraw", "ignore"]
        self.allow_negative = negative_behaviour == "ignore"

        # Use standard updateGivenPropensity derived from Solver class.
        self.update_propensity_function = self.updateGivenPropensity
        self.time_step = time_step

    def simulateOneStep(self, current_time):
        self.performPropensityUpdates(self.update_propensity_function)

        total_propensity = self.returnTotalPropensity()
        
        # No rule has been selected as even though total_propensity is non-zero, this could be due to numerical precision errors but is likely an issue with timestep.
        # Instead of checking whether a rule has been found, check that total_propensity differs from 0 more than machine tolerance.
        if total_propensity <= 1e-17:
            return self.processNoRuleEvent(current_time)

        for rule_comp_key, rule_comp_propensity in self.propensities.items():
            negative_valued = True
            while negative_valued:
                times_triggered = self._random_source.poisson(lam=rule_comp_propensity*self.time_step)
                selected_rule, selected_compartments = rule_comp_key.split(" ")

                if times_triggered > 0:
                    negative_valued = not self.rules[int(selected_rule)].triggerAttemptedRuleChange(np.take(self.compartments,
                                                                                  self.matched_indices[int(selected_rule)]
                                                                                  [int(selected_compartments)]), times_triggered, self.allow_negative)
                    if self.use_cached_propensities:
                        self.last_rule_index_set.append(rule_comp_key)
                    # Not collecting times_triggered here (should be!)
                    if self.debug:
                        self.collectStats(int(selected_rule), int(selected_compartments), total_propensity)
        return current_time + self.time_step