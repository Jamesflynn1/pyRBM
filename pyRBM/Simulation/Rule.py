import re
from typing import Optional

import numpy as np
import sympy

from pyRBM.Simulation.Compartment import Compartment
from pyRBM.Core.StringUtilities import replaceVarName

class Rule:
    def __init__(self, propensity:list[str],
                 stoichiometry:list[np.ndarray],
                 rule_name:str, num_builtin_classes:int,
                 compartments:list[Compartment],
                 rule_index_sets:list[list[int]]) -> None:

        assert len(stoichiometry) == len(propensity)
        compartment_names = [compartment.name for compartment in compartments]
        if isinstance(propensity, (list)):
            self.lambda_propensities = []
            self.contains_compartment_constant = []
            self.contains_slot_match_constant = []
            self.sympy_formula = []
            comp_prop_dict = None

            for slot_i, formula_str in enumerate(propensity):
                symbol_string = ''.join([f"x{str(i)} "
                                         for i in range(len(stoichiometry[slot_i])+num_builtin_classes)])
                formula_symbols = sympy.symbols(symbol_string, real=True)
                # We only need one propensity function for this rule.
                if "comp_" not in formula_str and "slot_" not in formula_str:
                    formula = sympy.parse_expr(formula_str)
                    self.sympy_formula.append(formula)
                    comp_prop_dict=sympy.lambdify(formula_symbols, formula.simplify(), "numpy")
                    self.contains_compartment_constant.append(False)
                    self.contains_slot_match_constant.append(False)
                # We need multiple propensity functions for this rule as we have compartment specific information.
                elif "slot_" not in formula_str:
                    applicable_indices = self._findIndices(rule_index_sets, slot_i)
                    #formula_without_constants = self.subsituteConstants(formula_str, {key:"" for key in list(compartments[applicable_indices[0]].compartment_constants.keys())})
                    comp_prop_dict = {comp_index: sympy.lambdify(formula_symbols,
                                        sympy.parse_expr(self._subsituteConstants(formula_str, compartments[comp_index].compartment_constants,
                                                                                  None)).simplify(),
                                                        "numpy")
                                        for comp_index in applicable_indices}

                    # self.sympy_formula is used for precomputing rules only and uses an example set of locations - should not be used
                    # generally.
                    self.sympy_formula.append(sympy.parse_expr(self._subsituteConstants(formula_str,
                                                compartments[applicable_indices[0]].compartment_constants,
                                                None)))

                    self.contains_compartment_constant.append(True)
                    self.contains_slot_match_constant.append(False)

                else:
                    #formula_without_constants = self.subsituteConstants(formula_str, {key:"" for key in list(compartments[applicable_indices[0]].compartment_constants.keys())})
                    comp_prop_dict = {comp_index: sympy.lambdify(formula_symbols,
                                        sympy.parse_expr(self._subsituteConstants(formula_str, compartments[index_set[slot_i]].compartment_constants,
                                                                                  np.take(compartment_names, rule_index_sets[comp_index]))).simplify(),
                                                        "numpy")
                                        for comp_index, index_set in enumerate(rule_index_sets)}

                    # self.sympy_formula is used for precomputing rules only and uses an example set of locations - should not be used
                    # generally.
                    self.sympy_formula.append(sympy.parse_expr(self._subsituteConstants(formula_str,
                                                compartments[rule_index_sets[0][slot_i]].compartment_constants,
                                                np.take(compartment_names, rule_index_sets[0]))))

                    self.contains_compartment_constant.append(True)
                    self.contains_slot_match_constant.append(True)

                self.lambda_propensities.append(comp_prop_dict)
            # To remove
            #self.propensity_function = lambda x, comp : np.dot(x, self.propensity_matrix[comp])
        else:
            raise ValueError("Unsupported Propensity in Model Loading")
        self.rule_name = rule_name
        self.stoichiometry = stoichiometry
        self.contains_compartment_constant = np.array(self.contains_compartment_constant)
        self.contains_slot_match_constant = np.array(self.contains_slot_match_constant)

    def _subsituteConstants(self, formula_str:str, compartment_constants:Optional[dict], compartments_names:Optional[list]) -> str:
        # The slot to name substitution is performed prior to constant to value substitution,
        # to allow for constant with slot_ to be formed.
        if compartments_names is not None:
            for slots_i, compartment_name in enumerate(compartments_names):
                formula_str = formula_str.replace(f"slot_{slots_i}", compartment_name)
        
        out_formula = formula_str
        if compartment_constants is not None:
            for comp_constant in compartment_constants:
                # Use replaceVarName to exactly match comp_constant.
                out_formula = replaceVarName(out_formula, comp_constant,
                                             str(compartment_constants[comp_constant]),
                                             ignore_underscore = False)
        return out_formula

    def _findIndices(self, rule_index_sets:list[list[int]], slot_index:int) -> list[int]:
        possible_indices = set()

        for index_set in rule_index_sets:
            possible_indices.add(index_set[slot_index])

        return list(possible_indices)

    def _compartmentAttemptedCompartmentChange(self, class_values, compartment_index:int,
                                            times_triggered:int):
        new_values = class_values + times_triggered*self.stoichiometry[compartment_index]

        return new_values

    def returnPropensity(self, compartments, builtin_classes, index_set_i):
        assert(len(compartments) == len(self.stoichiometry))
        # Assume product operation.
        propensity = 1
        for comp_i, compartment in enumerate(compartments):
            # Apply thresholding here to ensure that no negative propensities are used.
            # print(self.lambda_propensities[comp_i](*compartment.class_values, *builtin_classes))
            if not self.contains_compartment_constant[comp_i]:
                propensity *= max(0, self.lambda_propensities[comp_i](*compartment.class_values,
                                                                     *builtin_classes))
            elif not self.contains_slot_match_constant[comp_i]:
                propensity *= max(0, self.lambda_propensities[comp_i][compartment.index](*compartment.class_values,
                                                                                     *builtin_classes))
            else:
                propensity *= max(0, self.lambda_propensities[comp_i][index_set_i](*compartment.class_values,
                                                                                     *builtin_classes))
                #print(self.lambda_propensities[comp_i][index_set_i](*compartment.class_values,
                 #                                                                    *builtin_classes))

        assert propensity >= 0
        return propensity

    # We expect pure Gillespie to have 0 propensity for negative rule changes, however with Tau leaping we may need
    # to check whether a series of rule changes leads to negative values.
    def triggerAttemptedRuleChange(self, compartments,
                                   times_triggered:int = 1,
                                   allow_negative:bool = True) -> bool:
        assert len(compartments) == len(self.stoichiometry)
        negative_vals = False
        new_class_values = []

        for comp_i, compartment in enumerate(compartments):
            new_compartment_values = self._compartmentAttemptedCompartmentChange(compartment.class_values,
                                                                           comp_i, times_triggered)
            if not allow_negative and np.any(new_compartment_values<0):
                negative_vals = True
                break
            else:
                new_class_values.append(new_compartment_values)
        if not negative_vals:
            for comp_i, compartment in enumerate(compartments):
                compartment.updateCompartmentValues(new_class_values[comp_i])
        return not negative_vals
        