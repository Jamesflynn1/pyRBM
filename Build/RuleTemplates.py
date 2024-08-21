import numpy as np
import sympy
import json
import pyRBM.Build.Rules as Rules


class SingleLocationRule(Rules.Rule):
       def __init__(self, target, propensity, stoichiomety,
                    propensity_classes, stoichiometry_classes,
                    rule_name = "SINGLE LOCATION RULE"):
              super().__init__(rule_name, [target])
              self.addLinearStoichiomety([0], [stoichiomety], [stoichiometry_classes])
              self.addSimplePropensityFunction([0], [propensity], [propensity_classes])

class SingleLocationProductionRule(SingleLocationRule):
       def __init__(self, target, reactant_classes, reactant_amount, 
                    product_classes, product_amount,
                    propensity, propensity_classes, 
                    rule_name="SINGLE LOCATION PRODUCTION RULE"):
            
            reactants_len = len(reactant_classes)
            product_len = len(product_classes)
            stoichiometry = np.zeros(reactants_len+product_len)
            for i in range(reactants_len):
                stoichiometry[i] = -reactant_amount[i]
            for i  in range(product_len):
                stoichiometry[i+reactants_len] = product_amount[i]
            stoichiometry_classes = reactant_classes+product_classes

            super().__init__(target, propensity, stoichiometry, propensity_classes, stoichiometry_classes, rule_name)

class TransportRule(Rules.Rule):
       def __init__(self, source, target, transport_class,
                          propensities, transport_amount, propensity_classes,
                          rule_name = "TRANSPORT RULE"):
              super().__init__(rule_name, [source, target])

              assert(len(propensities) == 2)
              assert(len(propensity_classes) == 2)

              source_stochiometry = np.zeros(1)
              source_stochiometry[0] = -transport_amount
              target_stochiometry = np.zeros(1)
              target_stochiometry[0] = transport_amount

              self.addLinearStoichiomety([0, 1], [source_stochiometry, target_stochiometry], [[transport_class], [transport_class]])
              self.addSimplePropensityFunction([0, 1], propensities, propensity_classes)

class ExitEntranceRule(Rules.Rule):
       def __init__(self, target, transport_class,
                    transport_amount, propensity, propensity_classes,
                    rule_name = "EXIT/ENTRANCE RULE"):
            super().__init__(rule_name, [target])

            self.addLinearStoichiomety([0], [[transport_amount]], [[transport_class]])
            self.addSimplePropensityFunction([0], [propensity], [propensity_classes])