""" Defines a Rule class and a Rules helper class
"""

from typing import Iterable, Any, Union, Optional, Sequence

import numpy as np
import sympy

def isNonDefaultTargetArray(target_array:list[str]) -> bool:
    """ Checks if the provided target_array contains any non default (i.e. non None or "Any"/"any") target requirmments.
    Returns:
        bool: True if any none default target requirment in `target_array`, False otherwise.
    """
    for x in target_array:
        if not (x is None or x == "any" or x == "Any"):
            return True
    return False

def returnSympyClassVarsDict(classes:Iterable[str]) -> dict[str, sympy.Symbol]:
    symbols_str = ""
    for class_label in classes:
        symbols_str += class_label+" "
    symbols = sympy.symbols(symbols_str)
    if not isinstance(symbols, (list, tuple)):
        symbols = [symbols]
    symbols_dict = {class_label:symbols[index] 
                    for index, class_label in enumerate(classes)}
    return symbols_dict


class Rule:
    def __init__(self, rule_name:str, targets:Sequence[str]) -> None:
        """ 
        """
        self.rule_name = rule_name

        self.targets = targets
        # Stochiometries/propensities are with respect
        target_indices = range(len(targets))
        
        self.stoichiometies:        dict[int, Optional[Any]] = {i:None for i in target_indices}
        self.propensities:          dict[int, Optional[Any]] = {i:None for i in target_indices}
        self.stoichiometry_classes: dict[int, Optional[list[str]]] = {i:None for i in target_indices}
        self.propensity_classes:    dict[int, Optional[list[str]]] = {i:None for i in target_indices}

    def addLinearStoichiomety(self, target_indices:list[int], stoichiometies,
                              required_target_classes:list[list[str]]) -> None:
        assert(len(target_indices) == len(stoichiometies))
        for i, index in enumerate(target_indices):
            stoichiometry = stoichiometies[i]
            if not self.stoichiometies[index] is None:
                raise(ValueError(f"Overwriting already set stoichiomety is forbidden. Target compartment {self.targets[index]} at position {str(index+1)}"))
            elif isinstance(stoichiometry, (np.ndarray, list)):
                self.stoichiometies[index] = list(stoichiometry)
                self.stoichiometry_classes[index] = required_target_classes[i]
            else:
                raise(ValueError(f"Unrecognised stoichiomety of type {type(stoichiometies[i])}, for target index {index}"))
    
    def addSimplePropensityFunction(self, target_indices:list[int], values,
                                    required_target_classes:list[list[str]]) -> None:
        # Accepts matrix or constant values at the moment
        assert(len(target_indices) == len(values))
        for i, index in enumerate(target_indices):
            value = values[i]
            if not self.propensities[index] is None:
                raise(ValueError(f"Overwriting already set propensity is forbidden. Target compartment {self.targets[index]} at position {str(index+1)}"))

            if not isinstance(value, str):
                raise(ValueError(f"Unrecognised propensity function of type {type(values[i])}, for target index {index}"))

            self.propensity_classes[index] = required_target_classes[i]
            self.propensities[index] = value

    def validateFormula(self, formula, class_symbols:dict[str, sympy.Symbol],
                        safe_num:Union[float, int] = 1) -> bool:
        # Evaluate when all classes are 0
        subsitution_dict = {}
        for class_symbol in class_symbols.values():
            subsitution_dict[class_symbol] = safe_num
        res = formula.evalf(subs=subsitution_dict)
        # We require that a numerical result is outputted and no symbols are left over.
        assert(isinstance(res, (sympy.core.numbers.Float, sympy.core.numbers.Zero)))
        return True

    def checkRuleDefinition(self, builtin_class_symbols:dict[str, sympy.Symbol],
                            compartments_constant_symbols:dict[str, sympy.Symbol]) -> None:
        """ Perform the following validation on the rule definition:
            1. self.stoichiometies, self.propensities, self.propensity_classes are of the same length as the rule targets.
            2. each element of self.stoichiometies, self.propensities, self.propensity_classes are not None.
            3. each propensity at index i, in self.propensities, evaluates to a number when the builtin_class_symbols, compartments_constant_symbols and the propensity_classes[i] symbols are evaluated 
                as 1 (i.e. the propensity is a valid numerical formula).
        Args:
            builtin_class_symbols :
            compartments_constant_symbols :
        """
        for rule_arrays in (self.stoichiometies, self.propensities, self.propensity_classes, self.stoichiometry_classes):
            assert(len(rule_arrays) == len(self.targets))
        
        for i in range(len(self.targets)):
            if self.stoichiometies[i] is None:
                raise(ValueError(f"Incorrect rule definition for {self.rule_name}\nThe Compartment type {self.targets[i]} at rule position {str(i+1)} has no defined stochiometry."))
            elif self.propensities[i] is None or not isinstance(self.propensities[i], str):
                raise(ValueError(f"Incorrect rule definition for {self.rule_name}\nThe Compartment type {self.targets[i]} at rule position {str(i+1)} has no defined propensity."))
            elif self.propensity_classes[i] is None or not isinstance(self.propensity_classes[i], list):
                raise(ValueError(f"Incorrect rule definition for {self.rule_name}\nThe Compartment type {self.targets[i]} at rule position {str(i+1)} has no defined propensity class requirement."))
            elif self.stoichiometry_classes[i] is None or not isinstance(self.propensity_classes[i], list):
                raise(ValueError(f"Incorrect rule definition for {self.rule_name}\nThe Compartment type {self.targets[i]} at rule position {str(i+1)} has no defined stochiometry class requirement."))
            
        for index in range(len(self.propensities)):
            symbols = returnSympyClassVarsDict(self.propensity_classes[index]) | builtin_class_symbols | compartments_constant_symbols
            sympy_formula = sympy.parse_expr(self.propensities[index], local_dict=symbols)
            self.validateFormula(sympy_formula, symbols)
            
    def _mergeClassLists(self) -> None:
        """
        """
        # Maps new index to class label
        self.rule_classes = []
        for i, _ in enumerate(self.targets):
            sorted_classes = sorted(set(self.propensity_classes[i] + self.stoichiometry_classes[i]))
            tmp_rule_class_dict = dict(enumerate(sorted_classes))
            # Might be better to remap inputs for more complex functions rather than directly changing the definition of the function.
                # Use additive identity here
            new_stoichiometry = np.zeros(len(sorted_classes))
            for h, old_class in enumerate(self.stoichiometry_classes[i]):
                for j in range(len(tmp_rule_class_dict)):
                    if old_class == tmp_rule_class_dict[j]:
                        new_stoichiometry[j] = self.stoichiometies[i][h]
            self.stoichiometies[i] = list(new_stoichiometry)
            self.rule_classes.append(tmp_rule_class_dict)
        
    def returnRuleDict(self) -> dict[str,Any]:
        # Check performed in Rules class
        # self.checkRuleDefinition(builtin_class_symbols, compartments_constants)
        self._mergeClassLists()
        return {"name":self.rule_name,
                "target_types":self.targets,
                "required_classes":self.rule_classes,
                "stoichiometries":self.stoichiometies,
                "propensities":self.propensities
                }

class Rules:
    def __init__(self, defined_classes:Iterable[str], compartment_constants: Iterable[str]) -> None:
        self.rules:list[Rule] = []
        self.defined_classes = defined_classes
        self.model_prefix = "model_"
        self.compartment_prefix = "comp_"

        builtin_classes = []

        for classes in defined_classes:
            if self.model_prefix in classes:
                builtin_classes.append(classes)


        self.builtin_symbols = returnSympyClassVarsDict(builtin_classes)
        # DOESN'T CHECK FOR EXISTENCE OF CONSTANTS FOR EACH LOCATION - THIS IS DONE IN THE RULE MATCHING
        self.compartment_constants_symbols = returnSympyClassVarsDict(compartment_constants)
    
    def removeTypeRequirement(self, default_type:str = "any") -> None:
        """ Used to remove the user set (or unset) type requirements for all rules by setting to the default_type. Used for no-compartment models.
        Should not be used for any multi-compartmental models.
        """
        for rule in self.rules:
            if len(rule.targets) >= 2:
                raise(ValueError(f"ERROR: rule {rule.rule_name} has {len(rule.targets)} compartment targets for a compartmentless model (requires len(targets == 1))"))
            elif isNonDefaultTargetArray(rule.targets):
                print(f"Warning: rule {rule.rule_name} has non default (i.e not all elements are None or 'any') target list {rule.targets}")
                print("Ignoring type restrictions for no compartment models.")
            rule.targets = [default_type for _ in range(len(rule.targets))]

    def addRule(self, rule:Rule) -> None:
        if isinstance(rule, Rule):
            self.rules.append(rule)
        else:
            raise(TypeError(f"rule is not a child type of Rule base class (type: {type(rule)})"))
        
    def addRules(self, rules:Iterable[Rule]) -> None:
        for rule in rules:
            self.addRule(rule)
    
    def _checkRules(self) -> bool:
        for rule in self.rules:
            rule.checkRuleDefinition(self.builtin_symbols,
                                     self.compartment_constants_symbols)

            for propensity_class_index in range(len(rule.propensity_classes)):
                compartment_propensity_class = rule.propensity_classes[propensity_class_index]
                for comp_prop_class in compartment_propensity_class:
                    if not comp_prop_class in self.defined_classes:
                        raise ValueError(f"Class required for the propensity, {comp_prop_class}, not defined (Rule name: {rule.rule_name})")
                    
            for stoichiometry_class_index in range(len(rule.stoichiometry_classes)):
                compartment_stoichiometry_class = rule.stoichiometry_classes[stoichiometry_class_index]
                for comp_stoich_class in compartment_stoichiometry_class:
                    if not comp_stoich_class in self.defined_classes:
                        raise ValueError(f"Class required for the stoichiometry, {comp_stoich_class} not defined (Rule name: {rule.rule_name})")
        return True

    def returnMetaRuleDict(self) -> dict[str,dict[str,Any]]:
        self._checkRules()
        return {str(i):rule.returnRuleDict()
                for i, rule in enumerate(self.rules)}