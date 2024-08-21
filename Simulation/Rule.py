from typing import Any
import numpy as np
import sympy
import matplotlib.pyplot as plt

class Rule:
    def __init__(self, propensity, stoichiometry, rule_name, num_builtin_classes, locations, rule_index_sets) -> None:
        assert (len(stoichiometry) == len(propensity))
        if isinstance(propensity, (list)):
            self.lambda_propensities = []
            self.contains_location_constant = []
            self.sympy_formula = []

            for slot_i, formula_str in enumerate(propensity):
                symbol_string = ''.join([f'x{str(i)} ' for i in range(len(stoichiometry[slot_i])+num_builtin_classes)])
                formula_symbols = sympy.symbols(symbol_string, real=True)

                #symbols = sympy.symbols("".join([f"x{i} " for i in range(len(stoichiometry[loc_i]))]) , real=True)
                #M = sympy.IndexedBase('x', shape=(dim))
            
                #symbols = [f"x{i}" for i in range(len(stoichiometry[loc_i]))]

                if not "loc_" in formula_str:
                    formula = sympy.parse_expr(formula_str)
                    self.sympy_formula.append(formula)
                    f=sympy.lambdify(formula_symbols, formula.simplify(), "numpy")
                    self.contains_location_constant.append(False)
                else:
                    applicable_indices = self.findIndices(rule_index_sets, slot_i)
                    #formula_without_constants = self.subsituteConstants(formula_str, {key:"" for key in list(locations[applicable_indices[0]].location_constants.keys())})

                    f = {loc_index: sympy.lambdify(formula_symbols, sympy.parse_expr(self.subsituteConstants(formula_str, locations[loc_index].location_constants)).simplify(), "numpy") for loc_index in applicable_indices}

                    self.sympy_formula.append(sympy.parse_expr(self.subsituteConstants(formula_str, locations[applicable_indices[0]].location_constants)))

                    self.contains_location_constant.append(True)

                self.lambda_propensities.append(f)
            self.propensity_function = lambda x, loc : np.dot(x, self.propensity_matrix[loc])
        else:
            raise(ValueError("Unsupported Propensity in Model Loading"))
        self.rule_name = rule_name
        self.stoichiometry = stoichiometry
        self.contains_location_constant = np.array(self.contains_location_constant)
    
    def subsituteConstants(self, formula_str:str, location_constants:dict):
        out_formula = formula_str
        for loc_constant in list(location_constants.keys()):
            out_formula = out_formula.replace(loc_constant, str(location_constants[loc_constant]))
        return out_formula

    def findIndices(self, rule_index_sets, slot_index):
        possible_indices = set([])

        for index_set in rule_index_sets:
            possible_indices.add(index_set[slot_index])

        return list(possible_indices)
    def locationAttemptedCompartmentChange(self, class_values, location_index, times_triggered):
        new_values = class_values + times_triggered*self.stoichiometry[location_index]

        return new_values
    
    def returnPropensity(self, locations, builtin_classes):
        assert(len(locations) == len(self.stoichiometry))
        # Assume product operation.
        propensity = 1
        for loc_i, location in enumerate(locations):
            # Apply thresholding here to ensure that no negative propensities are used.
            # print(self.lambda_propensities[loc_i](*location.class_values, *builtin_classes))
            if not self.contains_location_constant[loc_i]:
                propensity *= max(0, self.lambda_propensities[loc_i](*location.class_values, *builtin_classes))
            else:
                propensity *= max(0, self.lambda_propensities[loc_i][location.index](*location.class_values, *builtin_classes))

        assert (propensity >= 0)
        return propensity
    
    # We expect pure Gillespie to have 0 propensity for negative rule changes, however with Tau leaping we may need
    # to check whether a series of rule changes lead 
    def triggerAttemptedRuleChange(self, locations, times_triggered = 1):
        assert(len(locations) == len(self.stoichiometry))
        negative = False
        new_class_values = []

        for loc_i, location in enumerate(locations):
            new_location_values = self.locationAttemptedCompartmentChange(location.class_values, loc_i, times_triggered)
            # CHANGE TODO
            if np.any(new_location_values<-1):
                negative = True
                break
            else:
                new_class_values.append(new_location_values)
        if not negative:
            for loc_i, location in enumerate(locations):
                location.updateCompartmentValues(new_class_values[loc_i])
        return not negative
        