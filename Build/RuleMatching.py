""" Generic framework to match metarules to locations, find all location indices that match and rewrite the propensities and stoichiometries to use array indices.
"""

import json
import numpy as np

def isSubtypeOf(parent_type, child_type):
    """ Indicates whether the "child_type" rule type is a subtype of the parent_type.
    
    Current returns parent_type == child_type.

    In the future this should be determined by a tree based hierachical graph.
    """
    # Equality for the moment
    return parent_type == child_type

def returnRuleMatchingIndices(rules, locations):
    # For each rule, on each type that matches a general type
    filled_rules = {i:[] for i in range(len(rules))}
    for rule_i in range(len(rules)):
        rule = rules[rule_i]
        matchedTypeToIndices = {i:[] for i in range(len(rule["target_types"]))}
        # Check all locations to see which locations correspond to which required types by the rule.
        # (note, a rule may correspond to multiple required types but it can only be used in one slot).

        # We obtain a dictionary mapping each required location type to a list of fufilling indices in our location set.
        for location_i in range(len(locations)):
            for rule_targets_i in range(len(rule["target_types"])):
                if isSubtypeOf(rule["target_types"][rule_targets_i], locations[location_i]["type"]):
                    matchedTypeToIndices[rule_targets_i].append(location_i)
        # From the previously described location set, obtain a tuple of indices (if it exists) that satisfies the rule.
        # Do this iteratively, loop over all index sets in construction and add the new index if it isn't already inside.
        print(f"MATCHED {matchedTypeToIndices}")
        rule_indices = {}
        for rule_targets_i in range(len(rule["target_types"])):
            atleast_one_satisifying = False
            if len(rule_indices) == 0:
                if len(matchedTypeToIndices[0])>0:
                    for mtti in matchedTypeToIndices[0]:
                        if not locations[location_i]["type"] in  rule_indices.keys():
                             rule_indices[locations[location_i]["type"]] = []
                        rule_indices[locations[location_i]["type"]].append([mtti])
                    atleast_one_satisifying = True
            else:
                # Every index that can be subbed in at that place.
                # We keep a dictionary here so we can map explict types.
                correct_length_rules = {}
                for loc_index in matchedTypeToIndices[rule_targets_i]:
                    rule_keys = list(rule_indices.keys())
                    # Which explict types are being used.
                    for rule_key in rule_keys:
                        for index_matching in rule_indices[rule_key]:
                            if not loc_index in index_matching:
                                if not rule_key+"_"+locations[loc_index]["type"] in list(correct_length_rules.keys()):
                                    correct_length_rules[rule_key+"_"+locations[loc_index]["type"]] = [index_matching+[loc_index]]
                                else:
                                    correct_length_rules[rule_key+"_"+locations[loc_index]["type"]].append(index_matching+[loc_index])
                                atleast_one_satisifying = True
                rule_indices = correct_length_rules

            # Prune rules that will never able to be completed to reduce size.
            #correct_length_rules = [] 
            #for rule_index in rule_indices:
                #if len(rule_index) == rule_targets_i+1:
                    #correct_length_rules.append(rule_index)

            if not atleast_one_satisifying:
                raise(ValueError(f"Rule {rule_i} has no satisying location for required type index{rule_targets_i}, type {str(rule['target_types'][rule_targets_i])}. Rule will never be trigger - remove rule"))
        filled_rules[rule_i] = rule_indices
    return filled_rules

# Return the final propensity for a given rule provided concrete locations. 
# Assumption that locations of the same type have the same compartments.
def obtainPropensity(rule, locations, builtin_classes):
    propensities = rule["propensities"]
    new_propensities = []
    for location_i, location in enumerate(locations):
        new_propensity = propensities[location_i]
        new_label_mapping = location["label_mapping"]
        loc_used_constants = {}
        # Order: model var, location const, location class
        for built_in_i, builtin_class in enumerate(builtin_classes):
            new_propensity = new_propensity.replace(builtin_class[0], f"x{built_in_i+len(new_label_mapping)}")
            

        for label_i in list(new_label_mapping.keys()):
            new_propensity = new_propensity.replace(new_label_mapping[label_i], f"x{label_i}")
        # Add the built in class at the end of the location classes

        new_propensities.append(new_propensity)
    print(new_propensities)
    return new_propensities

def obtainStochiometry(rule, locations):
    """ Remaps the rule to fit the class size found in each location
    
    Example: Original Rule mapping {0:"Class1", 1:"Class2"} (size of input to Stochiometry and Propensity functions: 2)
    Location and Fitted Rule mapping {0:"ClassA", 1:"Class1", 2:"ClassB", 3:"Class2"}  (size of input to Stochiometry and Propensity functions: 4)


    Parameters:
        - rule: the Rule that we are remapping the propensity and stochiometry to fit each location.
        - locations: location instances (a list the length of rule.types) that fit each of the rule.types.

    Returns: list of expanded stochiometries for all rule locations  
    """
    # Rule
    stoichiometries = rule["stoichiometries"]

    current_class_mapping = rule["required_classes"]

    new_stoichiometries = []
    # Locations
    for rule_location, location in enumerate(locations):
        new_label_mapping = location["label_mapping"]
        new_stoichiometry = np.zeros(len(new_label_mapping))

        for rule_class_index in range(len(current_class_mapping[rule_location])):
            class_found = False
            for location_class_index in range(len(new_label_mapping)):
                if current_class_mapping[rule_location][rule_class_index] == new_label_mapping[location_class_index]:
                    new_stoichiometry[location_class_index] = stoichiometries[rule_location][rule_class_index]
                    # Only needs to happen once so can be placed here, possibly refactor
                    class_found = True
            if not class_found:
                raise(ValueError("Rule class not found in location class in rule matching (missing stoichiometry class)."))
        new_stoichiometries.append(list(new_stoichiometry))
        
    return new_stoichiometries

def writeMatchedRuleJSON(rules, locations, filename, builtin_classes):
    matched_rules = returnRuleMatchingIndices(rules, locations)
    builtin_classes = sorted(builtin_classes)
    concrete_match_rules_dict = {}
    concrete_rules = 0
    for rule_i in range(len(matched_rules)):
        concrete_rule_types = list(matched_rules[rule_i].keys())
        for concrete_rule_type in concrete_rule_types:
            concrete_rule_dict = {"rule_num":rule_i, "rule_name":rules[rule_i]["name"], 
                                  "rule_location_types":concrete_rule_type, "matching_indices":matched_rules[rule_i][concrete_rule_type]}
            # Assume all locations have the same classes - will be asserted in later versions.
            example_locations = []
            # Take the first set as an example
            for location_index in matched_rules[rule_i][concrete_rule_type][0]:
                example_locations.append(locations[location_index])
            
            # TODO ensure compatibility with further propensity functions
            concrete_rule_dict["stoichiomety"] = obtainStochiometry(rules[rule_i], example_locations)
            concrete_rule_dict["propensity"] = obtainPropensity(rules[rule_i], example_locations, builtin_classes)
            concrete_match_rules_dict[concrete_rules] = concrete_rule_dict
            concrete_rules+= 1
    
    json_concrete_rules = json.dumps(concrete_match_rules_dict, indent=4, sort_keys=True)
    with open(filename, "w") as outfile:
        outfile.write(json_concrete_rules)
    return concrete_match_rules_dict