import json
import os

import numpy as np
import pyRBM.Simulation.Rule as Rule
import pyRBM.Simulation.Location as Location

def writeDictToJSON(dict_to_write:dict, filename:str, dict_name:str=""):
    
    folder =''.join([folder+'/' for folder in filename.split("/")[:-1]])
    dir_to_create = os.path.join(os.curdir,folder)

    if not os.path.exists(dir_to_create):
        print(f"Creating folder: {dir_to_create}")
        os.makedirs(dir_to_create)

    json_file = json.dumps(dict_to_write, indent=4, sort_keys=True)
    with open(f"{filename}.json", "w+", encoding='utf-8') as outfile:
            if dict_name != "":
                dict_name += " "
            print(f"Writing {dict_name}to file: {filename}.json")
            outfile.write(json_file)

def readDictFromJSON(filename:str):
    file_data = None
    with open(filename, encoding='utf-8') as infile:
        file_data = json.load(infile)
    return file_data

def processFilenameOrDict(filename:str, provided_dict:dict):
    model_data = None
    if (filename is None) and (provided_dict is None):
        raise(ValueError("Provide either a "))
    elif not filename is None:
        model_data = readDictFromJSON(filename)
    else:
        model_data = provided_dict
    return model_data

def loadLocations(locations_filename:str = None, build_locations_dict:dict = None):
    """ Loads all locations from a model location json (see ModelCreation for details).

    Parameters: 
        - locations_filename: the string of the file location containing the location definitions.
        
    Returns: a list of Locations corresponding to all locations in the location_file
    """
    location_list = []
    locations_data = processFilenameOrDict(locations_filename, build_locations_dict)

    for loc_index in range(len(locations_data)):
        location_dict = locations_data[str(loc_index)]
        location = Location.Location(index=loc_index, name=location_dict["location_name"], lat=location_dict["lat"], long=location_dict["long"], loc_type=location_dict["type"],
                                         label_mapping=location_dict["label_mapping"],
                                         initial_class_values=np.array(location_dict["initial_values"]), location_constants=location_dict["location_constants"])
        location_list.append(location)
    return location_list
    

def loadMatchedRules(locations,  num_builtin_classes, matched_rules_filename:str = None, matched_rule_dict:dict=None):
    """ Loads all rules from a model matched rules json (see ModelCreation for details).

    Parameters: 
        - matched_rules_filename: the string of the file location containing the rule definitions.
    Returns: [a list of rules remapped to all possible location sets, 
              a 2d list of lists of satisfying indices for the corresponding rule]
    """
    rules_list = []
    applicable_indices = []
    rules_data =  processFilenameOrDict(matched_rules_filename, matched_rule_dict)
    
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

def loadClasses(model_prefix = "model_", classes_filename:str = None, classes_dict:dict = None):
    class_dict = {}
    built_in_class_dict = {}
    class_data = processFilenameOrDict(classes_filename, classes_dict)

    for class_key in list(class_data.keys()):
        if model_prefix in class_key:
            built_in_class_dict[class_key] = class_data[class_key]
        else:
            class_dict[class_key] = class_data[class_key]
    return [class_dict, built_in_class_dict]

