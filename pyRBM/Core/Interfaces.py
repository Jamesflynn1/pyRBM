from typing import Optional, Iterable, Any

from pyRBM.Core.StringUtilities import parseVarName

class ICompartment:
    def __init__(self, name:str, comp_type:str, 
                 compartment_constants:Optional[Iterable[str]], comp_prefix:str="comp_"):
        self.name = parseVarName(name)
        self.comp_type = comp_type
        self.compartment_constants = compartment_constants
        self.comp_prefix = comp_prefix
    
    def setInitialConditions(self, inital_conditions_dict:dict[str, Any]) -> None:
        # check all classes are defined
        self.checkConditionDict(inital_conditions_dict)
        self.inital_conditions_dict = {parseVarName(cond_name) : inital_conditions_dict[cond_name]
                                       for cond_name in inital_conditions_dict}
    
    def checkConditionDict(self, inital_conditions_dict:dict[str, Any]) -> None:
        for condition_class in inital_conditions_dict:
            standardised_condition_class = parseVarName(condition_class)
            if standardised_condition_class not in self.class_labels:
                raise ValueError(f"Initial condition class {standardised_condition_class} not present at compartment {self.name}.")
    
    def setConstants(self, constants_dict:dict[str, Any]) -> None:
        # current_constant_keys
        for entered_constant in constants_dict:
            standardised_constant = parseVarName(entered_constant)
            if self.comp_prefix+standardised_constant in self.compartment_constants:
                self.compartment_constants[self.comp_prefix+standardised_constant] = constants_dict[entered_constant]
            else:
                raise ValueError(f"Provided constant {self.comp_prefix+standardised_constant}, does not exist at current compartment {self.name}\n Defined compartment constants: {str(self.compartment_constants)}")
class Rule: