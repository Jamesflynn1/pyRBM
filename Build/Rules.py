import numpy as np
import sympy
import json

def returnSympyClassVarsDict(classes):
    symbols_str = ""
    for class_label in classes:
        symbols_str += class_label+" "
    symbols = sympy.symbols(symbols_str)
    if not isinstance(symbols, (list, tuple)):
        symbols = [symbols]
    symbols_dict = {class_label:symbols[index] for index, class_label in enumerate(classes)}
    return symbols_dict


class Rule:
    def __init__(self, rule_name:str, targets:list):

        self.rule_name = rule_name

        self.targets = targets
        # Stochiometries/propensities are with respect
        self.stoichiometies = {i:None for i in range(len(targets))}
        self.propensities = {i:None for i in range(len(targets))}

        self.rule_classes = {i:None for i in range(len(targets))}
        self.stoichiometry_classes = {i:None for i in range(len(targets))}
        self.propensity_classes = {i:None for i in range(len(targets))}

    def addLinearStoichiomety(self, target_indices, stoichiometies, required_target_classes):
        assert(len(target_indices) == len(stoichiometies))
        for i, index in enumerate(target_indices):
            stoichiometry = stoichiometies[i]
            if not self.stoichiometies[index] is None:
                raise(ValueError(f"Overwriting already set stoichiomety is forbidden. Target location {self.targets[index]} at position {str(index+1)}"))
            elif isinstance(stoichiometry, (np.ndarray, list)):
                self.stoichiometies[index] = list(stoichiometry)
                self.stoichiometry_classes[index] = required_target_classes[i]
            else:
                raise(ValueError(f"Unrecognised stoichiomety of type {type(stoichiometies[i])}, for target index {index}"))
    
    def addSimplePropensityFunction(self, target_indices, values, required_target_classes):
        # Accepts matrix or constant values at the moment
        assert(len(target_indices) == len(values))
        for i, index in enumerate(target_indices):
            value = values[i]
            print(f"{value}")
            if not self.propensities[index] is None:
                raise(ValueError(f"Overwriting already set propensity is forbidden. Target location {self.targets[index]} at position {str(index+1)}"))

            if not isinstance(value, str):
                raise(ValueError(f"Unrecognised propensity function of type {type(values[i])}, for target index {index}"))

            self.propensity_classes[index] = required_target_classes[i]
            self.propensities[index] = value

    def validateFormula(self, formula, class_symbols, safe_num = 1):
        # Evaluate when all classes are 0
        subsitution_dict = {}
        for class_str in list(class_symbols.keys()):
            subsitution_dict[class_symbols[class_str]] = safe_num
        res = formula.evalf(subs=subsitution_dict)
        # We require that a numerical result is outputted and no symbols are left over.
        print(res)
        assert(isinstance(res, (sympy.core.numbers.Float, sympy.core.numbers.Zero)))
        return True

    def checkRuleDefinition(self, builtin_class_symbols, locations_constant_symbols):
        for i in range(len(self.targets)):
            if self.stoichiometies[i] is None:
                raise(ValueError(f"Incorrect rule definition for {self.rule_name}\nThe Location type {self.targets[i]} at rule position {str(i+1)} has no defined stochiometry."))
            elif self.propensities[i] is None:
                raise(ValueError(f"Incorrect rule definition for {self.rule_name}\nThe Location type {self.targets[i]} at rule position {str(i+1)} has no defined propensity."))
            elif self.propensity_classes[i] is None:
                raise(ValueError(f"Incorrect rule definition for {self.rule_name}\nThe Location type {self.targets[i]} at rule position {str(i+1)} has no defined propensity class requirement."))
            elif self.stoichiometry_classes[i] is None:
                raise(ValueError(f"Incorrect rule definition for {self.rule_name}\nThe Location type {self.targets[i]} at rule position {str(i+1)} has no defined stochiometry class requirement."))
            
        for index in range(len(self.propensities)):
            symbols = returnSympyClassVarsDict(self.propensity_classes[index]) | builtin_class_symbols | locations_constant_symbols
            sympy_formula = sympy.parse_expr(self.propensities[index], local_dict=symbols)
            self.validateFormula(sympy_formula, symbols)
            
    def mergeClassLists(self):
        # Maps new index to class label
        self.rule_classes = []
        for i, target in enumerate(self.targets):
            sorted_classes = sorted(set(self.propensity_classes[i] + self.stoichiometry_classes[i]))
            tmp_rule_class_dict = {i:comp_class for i, comp_class in enumerate(sorted_classes)}
            # Might be better to remap inputs for more complex functions rather than directly changing the definition of the function.
                # Use additive identity here
            new_stoichiometry = np.zeros(len(sorted_classes))
            for h, old_class in enumerate(self.stoichiometry_classes[i]):
                for j in range(len(tmp_rule_class_dict)):
                    if old_class == tmp_rule_class_dict[j]:
                        new_stoichiometry[j] = self.stoichiometies[i][h]
            self.stoichiometies[i] = list(new_stoichiometry)
            self.rule_classes.append(tmp_rule_class_dict)
        
    def returnRuleDict(self):
        # Check performed in Rules class
        # self.checkRuleDefinition(builtin_class_symbols, locations_constants)
        self.mergeClassLists()

        # UNPACK DEF TO SPECIFIC LOCATION
        rule_dict = {"name":self.rule_name, "target_types":self.targets, "required_classes":self.rule_classes,
                     "stoichiometries":self.stoichiometies, "propensities":self.propensities}
        return rule_dict

class Rules:
    def __init__(self, defined_classes, location_constants : list):
        self.rules = []
        self.defined_classes = defined_classes
        self.model_prefix = "model_"
        self.location_prefix = "loc_"

        builtin_classes = []

        for classes in defined_classes:
            if self.model_prefix in classes:
                builtin_classes.append(classes)


        self.builtin_symbols = returnSympyClassVarsDict(builtin_classes)
        # DOESN'T CHECK FOR EXISTENCE OF CONSTANTS FOR EACH LOCATION - THIS IS DONE IN THE RULE MATCHING
        self.location_constants_symbols = returnSympyClassVarsDict(location_constants)
    
    def addRule(self, rule:Rule):
        if isinstance(rule, Rule):
            self.rules.append(rule)
        else:
            raise(TypeError(f"rule is not a child type of Rule base class (type: {type(rule)})"))
        
    def addRules(self, rules):
        for rule in rules:
            self.addRule(rule)
    
    def checkRules(self):
        for rule in self.rules:
            rule.checkRuleDefinition(self.builtin_symbols, self.location_constants_symbols)

            for propensity_class_index in range(len(rule.propensity_classes)):
                location_propensity_class = rule.propensity_classes[propensity_class_index]
                for loc_prop_class in location_propensity_class:
                    if not loc_prop_class in self.defined_classes:
                        raise ValueError(f"Class required for the propensity, {loc_prop_class}, not defined (Rule name: {rule.rule_name})")
                    
            for stoichiometry_class_index in range(len(rule.stoichiometry_classes)):
                location_stoichiometry_class = rule.stoichiometry_classes[stoichiometry_class_index]
                print(location_stoichiometry_class)
                for loc_stoich_class in location_stoichiometry_class:
                    if not loc_stoich_class in self.defined_classes:
                        raise ValueError(f"Class required for the stoichiometry, {loc_stoich_class} not defined (Rule name: {rule.rule_name})")
        return True

    def writeJSON(self, filename:str):
        self.checkRules()
        rules_dict = {}
        for i, rule in enumerate(self.rules):
            rule_dict = rule.returnRuleDict()
            rules_dict[i] = rule_dict
        
        json_rules = json.dumps(rules_dict, indent=4, sort_keys=True)

        with open(filename, "w") as outfile:
            outfile.write(json_rules)
        return rules_dict