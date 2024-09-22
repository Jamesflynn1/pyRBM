""" Generic framework to match metarules to compartments, find all compartment indices that match and rewrite the propensities and stoichiometries to use array indices.
"""
from typing import Any, Optional
import re

import numpy as np

def isSubtypeOf(parent_type:str, child_type:str) -> bool:
    """ Indicates whether the "child_type" rule type is a subtype of the parent_type.
    
    Current returns parent_type == child_type.

    In the future this should be determined by a tree based hierachical graph.
    """
    # Equality for the moment
    return parent_type == child_type

def replaceVarName(propensity_str, var_name, replacement):
    # The regex matches var_name except when preceeded by any alphanumeric characters
    # or succeded by any alphanumeric characters.
    regex_str = fr"(?<!([A-z]|\d)){var_name}(?![A-z]|\d)"

    return re.sub(regex_str, replacement, propensity_str)

def returnRuleMatchingIndices(rules:dict[str,dict[str,Any]],
                              compartments:dict[str,dict[str,Any]]) -> dict[str, list[int]]:
    # For each rule, on each type that matches a general type
    filled_rules:dict[str, list[int]] = {str(i):[] for i in range(len(rules))}
    for rule_i in range(len(rules)):
        rule = rules[str(rule_i)]
        matched_type_to_indices = {i:[] for i in range(len(rule["target_types"]))}
        # Check all compartments to see which compartments correspond to which required types by the rule.
        # (note, a rule may correspond to multiple required types but it can only be used in one slot).

        # We obtain a dictionary mapping each required compartment type to a list of fufilling indices in our compartment set.
        for compartment_i in range(len(compartments)):
            for rule_targets_i in range(len(rule["target_types"])):
                if isSubtypeOf(rule["target_types"][rule_targets_i],
                               compartments[str(compartment_i)]["type"]):
                    matched_type_to_indices[rule_targets_i].append(compartment_i)
        # From the previously described compartment set, obtain a tuple of indices (if it exists) that satisfies the rule.
        # Do this iteratively, loop over all index sets in construction and add the new index if it isn't already inside.
        #print(f"MATCHED {matchedTypeToIndices}")
        rule_indices = {}
        for rule_targets_i in range(len(rule["target_types"])):
            atleast_one_satisifying = False
            if len(rule_indices) == 0:
                if len(matched_type_to_indices[0])>0:
                    for mtti in matched_type_to_indices[0]:
                        compartment = compartments[str(compartment_i)]
                        if not compartment["type"] in  rule_indices:
                             rule_indices[compartment["type"]] = []
                        rule_indices[compartment["type"]].append([mtti])
                    atleast_one_satisifying = True
            else:
                # Every index that can be subbed in at that place.
                # We keep a dictionary here so we can map explict types.
                correct_length_rules = {}
                for comp_index in matched_type_to_indices[rule_targets_i]:
                    comp_key = str(comp_index)
                    # Which explict types are being used.
                    for rule_key, index_matches in rule_indices.items():
                        for index_matching in index_matches:
                            if comp_index not in index_matching:
                                if rule_key+"_"+compartments[comp_key]["type"] not in correct_length_rules:
                                    correct_length_rules[rule_key+"_"+compartments[comp_key]["type"]] = [index_matching+[comp_index]]
                                else:
                                    correct_length_rules[rule_key+"_"+compartments[comp_key]["type"]].append(index_matching+[comp_index])
                                atleast_one_satisifying = True
                rule_indices = correct_length_rules

            # Prune rules that will never able to be completed to reduce size.
            #correct_length_rules = []
            #for rule_index in rule_indices:
                #if len(rule_index) == rule_targets_i+1:
                    #correct_length_rules.append(rule_index)

            if not atleast_one_satisifying:
                raise ValueError(f"Rule {rule_i} has no satisying compartment for required type index{rule_targets_i}, type {str(rule['target_types'][rule_targets_i])}. Rule will never be trigger - remove rule")
        filled_rules[str(rule_i)] = rule_indices
    return filled_rules

# Return the final propensity for a given rule provided concrete compartments.
# Assumption that compartments of the same type have the same compartments.
def obtainPropensity(rule:dict[str,Any], compartments:list[dict[str,Any]], builtin_classes:list[list[str]]) -> list[str]:
    propensities = rule["propensities"]
    new_propensities = []
    for compartment_i, compartment in enumerate(compartments):
        new_propensity = propensities[compartment_i]
        new_label_mapping = compartment["label_mapping"]
        # Order: model var, compartment const, compartment class
        for built_in_i, builtin_class in enumerate(builtin_classes):
            new_propensity = replaceVarName(new_propensity, builtin_class[0], f"x{built_in_i+len(new_label_mapping)}")

        for label_i in new_label_mapping:
            new_propensity  = replaceVarName(new_propensity, new_label_mapping[label_i], f"x{label_i}")

        new_propensities.append(new_propensity)
    return new_propensities

def obtainStochiometry(rule:dict[str,Any], compartments:list[dict[str,Any]]) -> list[list[np.float64]]:
    """ Remaps the rule to fit the class size found in each compartment
    
    Example: Original Rule mapping {0:"Class1", 1:"Class2"} 
    (size of input to Stochiometry and Propensity functions: 2)

    Compartment and Fitted Rule mapping {0:"ClassA", 1:"Class1", 2:"ClassB", 3:"Class2"} 
    (size of input to Stochiometry and Propensity functions: 4)


    Args:
        - rule: the Rule that we are remapping the propensity and stochiometry to fit each compartment.
        - compartments: compartment instances (a list the length of rule.types) that fit each of the rule.types.

    Returns: list of expanded stochiometries for all rule compartments  
    """
    # Rule
    stoichiometries = rule["stoichiometries"]

    current_class_mapping = rule["required_classes"]

    new_stoichiometries = []
    # Compartments
    for rule_compartment, compartment in enumerate(compartments):
        new_label_mapping = compartment["label_mapping"]
        new_stoichiometry = np.zeros(len(new_label_mapping))

        for rule_class_index in range(len(current_class_mapping[rule_compartment])):
            class_found = False
            for compartment_class_index in range(len(new_label_mapping)):
                if (current_class_mapping[rule_compartment][rule_class_index] ==
                    new_label_mapping[str(compartment_class_index)]):
                    new_stoichiometry[compartment_class_index] = stoichiometries[rule_compartment][rule_class_index]
                    # Only needs to happen once so can be placed here, possibly refactor
                    class_found = True
            if not class_found:
                raise ValueError("Rule class not found in compartment class in rule matching (missing stoichiometry class).")
        new_stoichiometries.append(list(new_stoichiometry))

    return new_stoichiometries

def returnMatchedRulesDict(rules:dict[str,dict[str,Any]], compartments:dict[str,dict[str,Any]],
                           builtin_classes:Optional[list[list[str]]]) -> dict[str, dict[str,Any]]:
    if builtin_classes is None:
        builtin_classes = []
    else:
        builtin_classes = sorted(builtin_classes)

    matched_rules = returnRuleMatchingIndices(rules, compartments)
    concrete_match_rules_dict = {}
    concrete_rules = 0
    for rule_i in range(len(matched_rules)):
        rule = rules[str(rule_i)]
        matched_rule = matched_rules[str(rule_i)]
        for concrete_rule_type in matched_rule:
            concrete_rule_dict = {"rule_num":rule_i, "rule_name":rule["name"],
                                  "rule_compartment_types":concrete_rule_type,
                                  "matching_indices":matched_rule[concrete_rule_type]}
            # Assume all compartments have the same classes - will be asserted in later versions.
            example_compartments:list[dict[str,Any]] = []
            # Take the first set as an example
            for compartment_index in matched_rule[concrete_rule_type][0]:
                example_compartments.append(compartments[str(compartment_index)])

            # TODO ensure compatibility with further propensity functions
            concrete_rule_dict["stoichiomety"] = obtainStochiometry(rule, example_compartments)
            concrete_rule_dict["propensity"] = obtainPropensity(rule, example_compartments,
                                                                builtin_classes)
            concrete_match_rules_dict[str(concrete_rules)] = concrete_rule_dict
            concrete_rules+= 1

    return concrete_match_rules_dict
