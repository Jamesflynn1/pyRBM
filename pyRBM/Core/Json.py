import json
import numpy as np
import pyRBM.Simulation.Rule as Rule

def loadLocations(locations_filename):
    """ Loads all locations from a model location json (see ModelCreation for details).

    Parameters: 
        - locations_filename: the string of the file location containing the location definitions.
        
    Returns: a list of Locations corresponding to all locations in the location_file
    """
    locations_data = None
    location_list = []
    with open(locations_filename) as locations_file:
        locations_data = json.load(locations_file)
    for loc_index in range(len(locations_data)):
        location_dict = locations_data[str(loc_index)]
        location = Rule.Location(index=loc_index, name=location_dict["location_name"], lat=location_dict["lat"], long=location_dict["long"], loc_type=location_dict["type"],
                                         label_mapping=location_dict["label_mapping"],
                                         initial_class_values=np.array(location_dict["initial_values"]), location_constants=location_dict["location_constants"])
        location_list.append(location)
    return location_list
    

def loadMatchedRules(matched_rules_filename, locations,  num_builtin_classes):
    """ Loads all rules from a model matched rules json (see ModelCreation for details).

    Parameters: 
        - matched_rules_filename: the string of the file location containing the rule definitions.
    Returns: [a list of rules remapped to all possible location sets, 
              a 2d list of lists of satisfying indices for the corresponding rule]
    """
    rules_data = None
    rules_list = []
    applicable_indices = []
    with open(matched_rules_filename) as rule_file:
        rules_data = json.load(rule_file)
    for rule_index in range(len(rules_data)):
        rules_dict = rules_data[str(rule_index)]
        stochiometries = []
        propensities = []
        # Convert stochiometries and propensities to numpy arrays - need to use a list of arrays as the 2nd dimension of the array has varying dimension.
        for loc_stoichiometry in rules_dict["stoichiomety"]:
            stochiometries.append(np.array(loc_stoichiometry))
        for loc_propensity in rules_dict["propensity"]:
            propensities.append(loc_propensity)

        rule = Rule.Rule(propensity=propensities, stoichiometry=stochiometries, rule_name=rules_dict["rule_name"], num_builtin_classes=num_builtin_classes, locations=locations, rule_index_sets=rules_dict["matching_indices"])
        applicable_indices.append(rules_dict["matching_indices"])
        rules_list.append(rule)
    return [rules_list, applicable_indices]

def loadClasses(classes_filename, model_prefix = "model_"):
    class_data = None
    class_dict = {}
    built_in_class_dict = {}
    with open(classes_filename) as class_file:
        class_data = json.load(class_file)

    for class_key in list(class_data.keys()):
        if model_prefix in class_key:
            built_in_class_dict[class_key] = class_data[class_key]
        else:
            class_dict[class_key] = class_data[class_key]
    return [class_dict, built_in_class_dict]

