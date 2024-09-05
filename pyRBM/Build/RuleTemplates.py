from typing import Union, Sequence

import numpy as np

from pyRBM.Build.Rules import Rule


class SingleLocationRule(Rule):
       def __init__(self, target:str, propensity:str, stoichiomety,
                    propensity_classes:list[str], stoichiometry_classes:list[str],
                    rule_name:str = "SINGLE LOCATION RULE") -> None:
              super().__init__(rule_name, [target])
              self.addLinearStoichiomety([0], [stoichiomety],
                                         [stoichiometry_classes])
              self.addSimplePropensityFunction([0], [propensity],
                                               [propensity_classes])

class SingleLocationProductionRule(SingleLocationRule):
       def __init__(self, target:str,
                    reactant_classes:list[str], reactant_amount:Sequence[Union[float, int]],
                    product_classes:list[str], product_amount:Sequence[Union[float, int]],
                    propensity:str, propensity_classes:list[str],
                    rule_name:str ="SINGLE LOCATION PRODUCTION RULE") -> None:
            
            reactants_len = len(reactant_classes)
            product_len = len(product_classes)
            stoichiometry = np.zeros(reactants_len+product_len)
            for i in range(reactants_len):
                stoichiometry[i] = -reactant_amount[i]
            for i  in range(product_len):
                stoichiometry[i+reactants_len] = product_amount[i]
            stoichiometry_classes = reactant_classes+product_classes

            super().__init__(target, propensity, stoichiometry, propensity_classes,
                             stoichiometry_classes, rule_name)

class TransportRule(Rule):
       def __init__(self, source:str, target:str, transport_class:str,
                          propensities:list[str], transport_amount:Union[float, int],
                          propensity_classes:list[list[str]],
                          rule_name:str = "TRANSPORT RULE") -> None:
              super().__init__(rule_name, [source, target])

              assert(len(propensities) == 2)
              assert(len(propensity_classes) == 2)

              source_stochiometry = np.zeros(1)
              source_stochiometry[0] = -transport_amount
              target_stochiometry = np.zeros(1)
              target_stochiometry[0] = transport_amount

              self.addLinearStoichiomety([0, 1], [source_stochiometry, target_stochiometry],
                                         [[transport_class], [transport_class]])
              self.addSimplePropensityFunction([0, 1], propensities,
                                               propensity_classes)

class ExitEntranceRule(Rule):
       def __init__(self, target:str, transport_class:str,
                    transport_amount:Union[float, int], propensity:str,
                    propensity_classes:list[str],
                    rule_name:str = "EXIT/ENTRANCE RULE") -> None:
            super().__init__(rule_name, [target])

            self.addLinearStoichiomety([0], [[transport_amount]], [[transport_class]])
            self.addSimplePropensityFunction([0], [propensity], [propensity_classes])