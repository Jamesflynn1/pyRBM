""" Provides classes to initialise common types of rules with simpler init functions.
"""

from typing import Union, Sequence

import numpy as np

from pyRBM.Build.Rules import Rule


class SingleLocationRule(Rule):
    """ A template for a rule at a single compartment.
    """
    def __init__(self, target:str, propensity:str, stoichiomety,
                  propensity_classes:Union[list[str], str], stoichiometry_classes:Union[str, list[str]],
                  rule_name:str = "SINGLE LOCATION RULE") -> None:
            """ A template for a rule at a single compartment. TODO
            """
            super().__init__(rule_name, [target])
            if isinstance(propensity_classes, str):
                 propensity_classes = [propensity_classes]
            if isinstance(stoichiometry_classes, str):
                 stoichiometry_classes = [stoichiometry_classes]
      
            self.addLinearStoichiomety([0], [stoichiomety],
                                        [stoichiometry_classes])
            self.addSimplePropensityFunction([0], [propensity],
                                              [propensity_classes])

class SingleLocationProductionRule(SingleLocationRule):
       def __init__(self, target:str,
                    reactant_classes:Union[list[str], str], reactant_amount:list[Union[float, int]],
                    product_classes:Union[list[str], str], product_amount:list[Union[float, int]],
                    propensity:str, propensity_classes:Union[list[str], str],
                    rule_name:str ="SINGLE LOCATION PRODUCTION RULE") -> None:
            if isinstance(reactant_classes, str):
                 assert isinstance(reactant_amount, (float,int))
                 reactant_classes = [reactant_classes]
                 reactant_amount = [reactant_amount]
            else:
                 assert isinstance(reactant_amount, list)

            if isinstance(product_classes, str):
                 assert isinstance(product_amount, (float,int))
                 product_classes = [product_classes]
                 product_amount = [product_amount]
            else:
                 assert isinstance(product_amount, list)
           
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
    """ A template for a transport rule for a single class between a single source compartment and a single target compartment.
    """
    def __init__(self, source:str, target:str, transport_class:str,
                    propensities:list[str], transport_amount:Union[float, int],
                    propensity_classes:list[list[str]],
                    rule_name:str = "TRANSPORT RULE") -> None:
          """ A template for a transport rule for a single class between a single source compartment and a single target compartment.
          Args:
            source (str): the type requirement to match for the source compartment.
            target (str): the type requirement to match for the target compartment.
            transport_class (str): the class that is being transported, required to exist at both compartments.
            propensities (list[str]): a two element array of the source and then target propensity functions as a string. Note the two functions are multiplied to find the final propensity.
            transport_amount (float, int): the decrease of class amount of the transport_class at the source compartment and the the increase of class amount of the transport_class at the target compartment.
            propensity_classes (list[list[str]]): a two element array of the classes required. The first element is a list of the classes required by the source propensity term, 
                the second element is a list of the classes required by the target propensity term.
            rule_name (str, optional):
          """
          assert len(propensities) == 2
          assert len(propensity_classes) == 2

          super().__init__(rule_name, [source, target])

          source_stochiometry = np.array([-transport_amount])
          target_stochiometry = np.array([transport_amount])

          self.addLinearStoichiomety([0, 1], [source_stochiometry, target_stochiometry],
                                      [[transport_class], [transport_class]])
          self.addSimplePropensityFunction([0, 1], propensities,
                                            propensity_classes)

class ExitEntranceRule(Rule):
  """ A template for either an exit rule or an entrance rule for a single class for a single compartment.
  """
  def __init__(self, target:str, transport_class:str,
                transport_amount:Union[float, int], propensity:str,
                propensity_classes:Union[list[str], str],
                rule_name:str = "EXIT/ENTRANCE RULE") -> None:
        """ A template for a transport rule for a single class between a single source compartment and a single target compartment.
        Args:
          target (str): the type requirement to match for the target compartment.
          transport_class (str): the class that is being transported to/from the target compartment.
          propensity (str): the propensity function for the rule. Can use any class values at the target compartment.
          transport_amount (float, int): the increase/decrease of class amount of the transport_class in the target compartment.
          propensity_classes (list[str]): A list of the classes required by the single propensity term.
            rule_name (str, optional):
        """
        super().__init__(rule_name, [target])
        if isinstance(propensity_classes, str):
             propensity_classes = [propensity_classes]
        self.addLinearStoichiomety([0], [[transport_amount]], [[transport_class]])
        self.addSimplePropensityFunction([0], [propensity], [propensity_classes])