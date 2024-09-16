import json
import os
from typing import Optional, Any

import numpy as np

from pyRBM.Simulation.Rule import Rule
from pyRBM.Simulation.Location import Location

class ModelPaths:
    """ Provides paths for created and loaded model files.

    All paths follow the format (model_folder_path_to)(model_name)(filename).

    Filenames should NOT include the file ending.
    
    A new ModelPaths object should overwrite the old object when a new model is saved/loaded.

    Attributes:
        location_path (str|None): the path to the locations .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None.
        classes_path (str|None): the path to the classes .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None.
        matched_rules_path (str|None): the path to the matched_rules .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None.
        metarule_path (str|None): the path to the metarule .json file saved or loaded at this object's creation, if it was saved/loaded, otherwise None.
        save_model_folder (str|None): the model folder that the 
    """
    def __init__(self, matched_rules_filename:Optional[str] = None,
                 locations_filename:Optional[str] = None,
                 model_folder_path_to:Optional[str] = None,
                 model_name:Optional[str] = "",
                 classes_filename:Optional[str] = None,
                 metarules_filename:Optional[str] = None):
        if model_name is None or model_folder_path_to is None:
            model_name = None
        else:
            self.save_model_folder = f"{model_folder_path_to}{model_name}/"
        self._matched_rules_filename = matched_rules_filename
        self._locations_filename = locations_filename
        self._classes_filename = classes_filename
        self._metarules_filename = metarules_filename
    # property decorator allows the function to be accessed as a standard class variable
    @property
    def locations_path(self) -> Optional[str]:
        """The path to the locations .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None."""
        if self._locations_filename is None or self.save_model_folder is None:
            return None
        else:
            return self.save_model_folder+self._locations_filename
    @property
    def classes_path(self) -> Optional[str]:
        """The path to the classes .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None"""
        if self._classes_filename is None or self.save_model_folder is None:
            return None
        else:
            return self.save_model_folder+self._classes_filename
    @property
    def matched_rules_path(self) -> Optional[str]:
        """ The path to the matched_rules .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None."""
        if self._matched_rules_filename is None or self.save_model_folder is None:
            return None
        else:
            return self.save_model_folder+self._matched_rules_filename
    @property
    def metarules_path(self) -> Optional[str]:
        """The path to the metarule .json file saved or loaded at this object's creation, if it was saved/loaded, otherwise None."""
        if self._metarules_filename is None or self.save_model_folder is None:
            return None
        else:
            return self.save_model_folder+self._metarules_filename

def writeDictToJSON(dict_to_write:dict, filename:str,
                    dict_name:str="") -> None:
    """ Writes dict_to_write to a json file at the filename path. Orders the json keys alphabetically and uses utf-8 encoding.

    Creates all folders and then the file if they don't already exist.

    Args:
        dict_to_write (dict): a dictionary to be written to a .json file.
        filename (str): the string representation of the path and filename of the json 
                file that is being written to (excluding the .json file ending).
        dict_name (str, optional): a string to include to provide user friendly output as to which file is being written.
    """
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

def readDictFromJSON(filename:str) -> dict:
    """ Read a JSON file found at the filename path and return the dictionary representation of it.
    Args:
        filename (str): the string representation of the path to the json file to be loaded (excluding the .json file ending).
    Returns:
        dict: dictionary representation of the JSON file found at the path, filename.
    """
    file_data = None
    with open(f"{filename}.json", encoding='utf-8') as infile:
        file_data = json.load(infile)
    return file_data

def processFilenameOrDict(filename:Optional[str],
                          provided_dict:Optional[dict[str,Any]]) -> Optional[dict[str,Any]]:
    """

    """
    model_data = None
    if (filename is None) and (provided_dict is None):
        raise(ValueError("Provide either a "))
    elif not filename is None:
        model_data = readDictFromJSON(filename)
    else:
        model_data = provided_dict
    return model_data

def loadLocations(locations_filename:Optional[str] = None,
                  build_locations_dict:Optional[dict[str,dict[str,Any]]] = None) -> list[Location]:
    """ Loads locations from either a model location json file (see ModelCreation for details) 
    or from a pyRBM.Build.Locations dictionary.

    Requires either locations_filename or build_locations_dict to be passed as an argument.

    If both arguments are provided, the function will load from the json at the locations_filename path.

    Args:
        locations_filename (str, optional): the string of the file location containing the location definitions.
        build_locations_dict (dict, optional): a dictionary of pyRBM.Build.Locations 
                (e.g. from calling Locations.returnLocationsDict())
    Returns:
        list: pyRBM.Simulation compatible Locations for each location in either location_file or build_locations_dict.
    """
    location_list = []
    locations_data = processFilenameOrDict(locations_filename, build_locations_dict)

    for loc_index in range(len(locations_data)):
        location_dict = locations_data[str(loc_index)]
        location = Location(index=loc_index, name=location_dict["location_name"], lat=float(location_dict["lat"]),
                                     long=float(location_dict["long"]), loc_type=location_dict["type"],
                                     label_mapping=location_dict["label_mapping"],
                                     initial_class_values=np.array(location_dict["initial_values"]),
                                     location_constants=location_dict["location_constants"])
        location_list.append(location)
    return location_list
    

def loadMatchedRules(locations,  num_builtin_classes:int, matched_rules_filename:Optional[str] = None,
                     matched_rule_dict:Optional[dict]=None) -> tuple[list[Rule], list[list[int]]]:
    """ Loads all rules from a model matched rules json (see ModelCreation for details).

    Args: 
        locations (): 
        num_builtin_classes: 
        matched_rules_filename: the string of the file location containing the rule definitions.
        matched_rule_dict: 
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
        # Convert stochiometries and propensities to numpy arrays -
        # need to use a list of arrays as the 2nd dimension of the array has varying dimension.
        for loc_stoichiometry in rules_dict["stoichiomety"]:
            stochiometries.append(np.array(loc_stoichiometry))
        for loc_propensity in rules_dict["propensity"]:
            propensities.append(loc_propensity)

        rule = Rule(propensity=propensities, stoichiometry=stochiometries, rule_name=rules_dict["rule_name"],
                         num_builtin_classes=num_builtin_classes, locations=locations,
                         rule_index_sets=rules_dict["matching_indices"])
        
        applicable_indices.append(rules_dict["matching_indices"])
        rules_list.append(rule)
    return (rules_list, applicable_indices)

def loadClasses(model_prefix:str = "model_", classes_filename:Optional[str] = None,
                classes_dict:Optional[dict] = None) -> tuple[dict, dict]:
    """ Loads classes from either a model class json file (see ModelCreation for details) or from a pyRBM.Build.Classes dictionary,
    and returns pyRBM.Simulation's requirements of a class_dict (a dict of all non-model classes) and 
    a built_in_class_dict (a dict of all model classes).

    Requires either classes_filename or classes_dict to be passed as an argument.

    If both arguments are provided, the function will load from the json at the classes_filename path.

    Args:
        model_prefix (str, optional): the prefix used to denote a model class in the model
        classes_filename (str) :ts
        classes_dict (dict) : a
    Returns:
        dict: class_dict
        dict: built_in_class_dict
    """
    class_dict = {}
    built_in_class_dict = {}
    class_data = processFilenameOrDict(classes_filename, classes_dict)

    for class_key in class_data:
        if model_prefix in class_key:
            built_in_class_dict[class_key] = class_data[class_key]
        else:
            class_dict[class_key] = class_data[class_key]
    return (class_dict, built_in_class_dict)

